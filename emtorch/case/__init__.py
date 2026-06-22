# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing "case" - a single instance of the experiment execution.
"""

import logging
from dataclasses import field
from typing import Self

from ..config import configclass
from ..context import CaseContext, Context
from ..delay import Delay
from ..subtasks import SubTasks, SubTasksBuilder

logger = logging.getLogger(__name__)


# pylint: disable=duplicate-code
class CaseDelays:
    @configclass
    class Config:
        between_cases: float
        before_actions: float

    def __init__(self, between_cases: Delay, before_actions: Delay):
        self._between_cases = between_cases
        self._before_actions = before_actions

    async def wait_before_actions(self) -> None:
        await self._before_actions.wait(logger)

    async def wait_between_cases(self) -> None:
        await self._between_cases.wait(logger)

    @classmethod
    def from_config(cls, config: Config) -> Self:
        return cls(
            between_cases=Delay(config.between_cases, "between cases"),
            before_actions=Delay(config.before_actions, "before actions"),
        )


class Case:
    # pylint: disable=invalid-field-call
    @configclass
    class Config:
        delays: CaseDelays.Config
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
            await self._delays.wait_before_actions()
            await self._actions.execute(context)
            context.notify_actions_ended()
        await self._checks.execute(context)

        logger.info(f"Finished case {context.case.identifier}")

    @classmethod
    def create(cls, context: Context) -> Self:
        config = context.config_loader.from_dict(Case.Config, context.config_raw)
        builder = SubTasksBuilder(context.config_loader, context.results)
        return cls(
            delays=CaseDelays.from_config(config.delays),
            setups=builder.build("setups", config.setups),
            monitoring=builder.build("monitoring", config.monitoring),
            actions=builder.build("actions", config.actions),
            checks=builder.build("checks", config.checks),
        )
