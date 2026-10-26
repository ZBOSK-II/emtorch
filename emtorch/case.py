# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing "case" - a single instance of the experiment execution.
"""

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Self

from .arguments import Arguments, RepeatMode
from .config import configclass
from .delay import Delay
from .subtasks import SubTasks, SubTasksBuilder

if TYPE_CHECKING:
    from pathlib import Path

    from .context import CaseContext, Context

logger = logging.getLogger(__name__)


class CaseData:
    def __init__(self, path: Path):
        self._path = path
        self._id = str(path)
        self._contents: bytes | None = None

    @property
    def path(self) -> Path:
        return self._path

    @property
    def identifier(self) -> str:
        return self._id

    @property
    def contents(self) -> bytes:
        if self._contents is None:
            logger.info(f"Opening {self._path}")
            with self._path.open("rb") as file:
                self._contents = file.read()
        return self._contents


@dataclass
class CaseId:
    group: str
    iteration: int | None

    def __repr__(self) -> str:
        if self.iteration:
            return f"{self.group}[{self.iteration}]"
        return self.group

    @staticmethod
    def from_id(identifier: str) -> CaseId:
        return CaseId(identifier, None)


class CaseInstance:
    def __init__(self, case_id: CaseId, data: CaseData):
        self._id = case_id
        self._data = data

    @property
    def identifier(self) -> CaseId:
        return self._id

    @property
    def data(self) -> CaseData:
        return self._data

    @staticmethod
    def list_from(args: Arguments) -> list[CaseInstance]:
        data = [CaseData(p) for p in args.data]

        if args.repeats < 2:
            return [CaseInstance(CaseId.from_id(d.identifier), d) for d in data]

        match args.repeat_mode:
            case RepeatMode.AABB:
                pairs = ((d, i) for d in data for i in range(args.repeats))
            case RepeatMode.ABAB:
                pairs = ((d, i) for i in range(args.repeats) for d in data)
            case _:
                raise ValueError(f"Unsupported repeat mode: {args.repeat_mode!r}")

        return [CaseInstance(CaseId(d.identifier, i + 1), d) for d, i in pairs]


# pylint: disable=duplicate-code
class CaseDelays:
    @configclass
    class Config:
        between_cases: float | None = None

    def __init__(self, between_cases: Delay):
        self._between_cases = between_cases

    async def wait_between_cases(self) -> None:
        await self._between_cases.wait(logger)

    @classmethod
    def from_config(cls, config: Config) -> Self:
        return cls(
            between_cases=Delay(config.between_cases, "between cases"),
        )


class Case:
    # pylint: disable=invalid-field-call
    @configclass
    class Config:
        delays: CaseDelays.Config = field(default_factory=CaseDelays.Config)
        mappings: dict[str, str] = field(default_factory=dict)
        setups: SubTasks.Config = field(default_factory=list)
        monitoring: SubTasks.Config = field(default_factory=list)
        actions: SubTasks.Config = field(default_factory=list)
        checks: SubTasks.Config = field(default_factory=list)

    def __init__(
        self,
        *,
        delays: CaseDelays,
        setups: SubTasks,
        monitoring: SubTasks,
        actions: SubTasks,
        checks: SubTasks,
    ):
        self._delays = delays
        self._setups = setups
        self._monitoring = monitoring
        self._actions = actions
        self._checks = checks

    async def execute(self, context: CaseContext) -> None:
        if context.first_case_executed:
            await self._delays.wait_between_cases()

        logger.info(f"Starting case {context.case.identifier}")

        await self._setups.execute(context)
        async with self._monitoring.monitor(context):
            await self._actions.execute(context)
            context.notify_actions_ended()
        await self._checks.execute(context)

        logger.info(f"Finished case {context.case.identifier}")

    @classmethod
    def create(cls, context: Context) -> Self:
        builder = SubTasksBuilder(context.config_loader, context.results)
        return cls(
            delays=CaseDelays.from_config(context.config.delays),
            setups=builder.build("setups", context.config.setups),
            monitoring=builder.build("monitoring", context.config.monitoring),
            actions=builder.build("actions", context.config.actions),
            checks=builder.build("checks", context.config.checks),
        )
