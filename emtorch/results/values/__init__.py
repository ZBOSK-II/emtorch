# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing gathered values gathered to be included in the results.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ...case.instance import CaseId


@dataclass
class ValuePoint(ABC):
    case_id: CaseId

    @abstractmethod
    def to_dict(self) -> dict[str, str | int | float]:
        pass


@dataclass
class TypedValuePoint[T: (int | float)](ValuePoint):
    value: T

    def to_dict(self) -> dict[str, str | int | float]:
        return {
            "group": self.case_id.group,
            "iteration": self.case_id.iteration,
            "value": self.value,
        }


class Value:
    def __init__(self) -> None:
        self._values: list[ValuePoint] = []

    def to_dict(self) -> dict[str, list[dict[str, str | int | float]]]:
        return {"points": [v.to_dict() for v in self._values]}


class TypedValue[T: (int | float)](Value):
    def collect(self, case_id: CaseId, value: T) -> None:
        self._values.append(TypedValuePoint[T](case_id, value))
