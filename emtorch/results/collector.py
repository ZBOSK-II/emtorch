# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing value collector.
"""

from typing import Self

from . import Results, ResultsCollector, ValuePoint


class Collector[T: ValuePoint]:

    def __init__(self, name: str, results: Results):
        self._name = name
        self._current_value: None | T = None
        self._results = results

    def commit(self) -> None:
        if self._current_value is not None:
            self._results.current.values[self._name] = self._current_value
            self._current_value = None

    def set_current(self, value: T) -> None:
        self._current_value = value

    def has_value(self) -> bool:
        return self._current_value is not None

    @classmethod
    def create(
        cls,
        name: str,
        results: ResultsCollector,
        value_type: type[T],
    ) -> Self:
        results.add_value(name, value_type)
        return cls(name, results.data)
