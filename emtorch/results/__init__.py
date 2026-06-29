# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing experiment results.
"""

import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from ..case.instance import CaseId
from ..version import VERSION

type ValuePoint = int | float


class SubTaskResults:

    def __init__(
        self, name: str, collector: ResultsCollector, results: list[str]
    ) -> None:
        self._name = name
        self._collector = collector
        self._success = results[0]
        self._counter: dict[str, int] = {}
        for r in results:
            self._counter[r] = 0

    def collect(self, result: str) -> None:
        if result != self._success:
            self._collector.failed_count += 1
        self._counter[result] += 1
        self._collector.data.current.subtasks[self._name] = result

    def summary(self) -> str:
        header = f"{self._name}:\n"
        return (
            header + "\n".join(f"\t{k}: {v}" for k, v in self._counter.items()) + "\n"
        )


def _iso_timestamp() -> str:
    return datetime.now().astimezone().isoformat()


@dataclass(kw_only=True)
class ExperimentInfo:
    version: str = field(init=False)
    args: list[str] = field(init=False)
    config: dict[str, Any]
    start: str = field(init=False)
    finish: str | None = field(init=False)

    def __post_init__(self) -> None:
        self.version = VERSION
        self.args = sys.argv[1:]
        self.start = _iso_timestamp()
        self.finish = None


@dataclass
class CaseResult:
    case_id: CaseId
    subtasks: dict[str, str] = field(default_factory=dict)
    values: dict[str, ValuePoint] = field(default_factory=dict)


@dataclass
class SubTaskInfo:
    name: str
    results: list[str]


@dataclass
class ValueInfo:
    name: str
    type: str


@dataclass
class Results:
    info: ExperimentInfo
    subtasks: list[SubTaskInfo] = field(default_factory=list)
    values: list[ValueInfo] = field(default_factory=list)
    cases: list[CaseResult] = field(default_factory=list)

    @property
    def current(self) -> CaseResult:
        return self.cases[-1]


class ResultsCollector:
    def __init__(self, config: dict[str, Any]) -> None:
        self._collector = Results(info=ExperimentInfo(config=config))
        self._subtasks: list[SubTaskResults] = []
        self.failed_count = 0

    @property
    def data(self) -> Results:
        return self._collector

    def add_subtask(self, name: str, results: type[StrEnum]) -> SubTaskResults:
        if name in [s.name for s in self.data.subtasks]:
            raise RuntimeError(
                f"Subtask already registered: '{name}'. Probably duplicated name."
            )
        r = list(str(item) for item in results)
        info = SubTaskInfo(name=name, results=r)
        self.data.subtasks.append(info)
        subresults = SubTaskResults(name, self, r)
        self._subtasks.append(subresults)
        return subresults

    def add_value[T: int | float](self, name: str, value_type: type[T]) -> None:
        if name in [s.name for s in self.data.values]:
            raise RuntimeError(
                f"Value already registered: '{name}'. Probably duplicated name."
            )
        info = ValueInfo(name=name, type=value_type.__name__)
        self.data.values.append(info)

    def add_case(self, case_id: CaseId) -> None:
        self.data.cases.append(CaseResult(case_id=case_id))

    def finish(self) -> None:
        self.data.info.finish = _iso_timestamp()

    def summary(self) -> str:
        result = ""
        for s in self._subtasks:
            result += s.summary()
        result += "\n"
        result += f"Processed cases: {len(self.data.cases)}\n"
        result += f"Failed subtasks: {self.failed_count}\n"
        return result
