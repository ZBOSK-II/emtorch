# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing experiment results.
"""

import sys
from collections import defaultdict
from datetime import datetime
from enum import StrEnum
from typing import Any, Collection, Mapping

from ..case.instance import CaseId
from ..version import VERSION
from .values import Value


class SubTaskResults:

    def __init__(self, results_names: list[str], success: str) -> None:
        self.subtasks: dict[str, list[str]] = {}
        for result in results_names:
            self.subtasks[result] = []

        self.success = success

        self.failed_cases: dict[str, str] = {}
        self.failed_groups: dict[str, list[str]] = defaultdict(list)

    def collect(self, case_id: CaseId, result: str) -> None:
        self.subtasks[result].append(case_id.unique)
        if result != self.success:
            self.failed_cases[case_id.unique] = result
            self.failed_groups[case_id.group].append(case_id.unique)

    def total(self) -> int:
        return sum(len(v) for v in self.subtasks.values())

    def total_errors(self) -> int:
        return len(self.failed_cases)

    def summary(self, indent: str = "\t") -> str:
        return "\n".join(f"{indent}{k}: {len(v)}" for k, v in self.subtasks.items())

    def to_dict(self) -> dict[str, list[str]]:
        return self.subtasks

    def to_failed_ids_dict(self) -> dict[str, str]:
        return self.failed_cases

    def to_failed_groups_dict(self) -> dict[str, list[str]]:
        return self.failed_groups


class Results:

    def __init__(self, config: dict[str, Any]):
        self.subtasks: dict[str, SubTaskResults] = {}
        self.values: dict[str, Value] = {}
        self.cases: list[str] = []
        self.groups: set[str] = set()
        self.info = {
            "version": VERSION,
            "args": " ".join(sys.argv[1:]),
            "config": config,
            "start": self.__iso_timestamp(),
        }

    def register_subtask(self, name: str, results: type[StrEnum]) -> SubTaskResults:
        r = list(str(item) for item in results)
        s = SubTaskResults(r, r[0])
        if name in self.subtasks:
            raise RuntimeError(
                f"Subtask results already registered: '{name}'. Probably duplicated name."
            )
        self.subtasks[name] = s
        return s

    def register_value(self, name: str, value: Value) -> Value:
        if name in self.values:
            raise RuntimeError(
                f"Value results already registered: '{name}'. Probably duplicated name."
            )
        self.values[name] = value
        return value

    def add_case(self, case_id: CaseId) -> None:
        self.cases.append(case_id.unique)
        self.groups.add(case_id.group)

    def finish(self) -> None:
        self.info["end"] = self.__iso_timestamp()

    def summary(self) -> str:
        header = f"Processed: {len(self.cases)}\n"
        header += f"Groups: {len(self.groups)}\n"
        return header + "\n".join(
            f"{k} ({v.total_errors()}/{v.total()}):\n{v.summary()}"
            for k, v in self.subtasks.items()
        )

    def total_errors(self) -> int:
        return sum(g.total_errors() for g in self.subtasks.values())

    def failed_cases(self) -> dict[str, list[str]]:
        result = defaultdict(list)
        for g, d in self.subtasks.items():
            for k, v in d.to_failed_ids_dict().items():
                result[k].append(g + "." + v)
        return dict(result)

    def failed_groups(self) -> dict[str, list[str]]:
        result: dict[str, list[str]] = defaultdict(list)
        for d in self.subtasks.values():
            for k, v in d.to_failed_groups_dict().items():
                result[k] += v
        return dict(result)

    def to_dict(self) -> Mapping[str, Collection[Any]]:
        return {
            "info": self.info,
            "cases": {
                "all": self.cases,
                "failed": self.failed_cases(),
            },
            "groups": {
                "all": list(self.groups),
                "failed": self.failed_groups(),
            },
            "subtasks": {k: v.to_dict() for k, v in self.subtasks.items()},
            "values": {k: v.to_dict() for k, v in self.values.items()},
        }

    @staticmethod
    def __iso_timestamp() -> str:
        return datetime.now().astimezone().isoformat()
