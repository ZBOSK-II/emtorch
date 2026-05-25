# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing value collector.
"""

from typing import Self

from ...case.instance import CaseId
from ...results import Results
from . import TypedValue

type SupportedCollectorTypes = int | float


class Collector[T: SupportedCollectorTypes]:

    def __init__(self, value: TypedValue[T]):
        self._value = value
        self._current_value: None | T = None

    def commit(self, case_id: CaseId) -> None:
        if self._current_value is not None:
            self._value.collect(case_id, self._current_value)
            self._current_value = None

    def set_current(self, value: T) -> None:
        self._current_value = value

    def has_value(self) -> bool:
        return self._current_value is not None

    @classmethod
    def create(cls, name: str, results: Results) -> Self:
        value = TypedValue[T]()
        results.register_value(name, value)
        return cls(value)
