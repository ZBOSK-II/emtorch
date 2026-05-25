# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Subpackage representing context of the experiment.
"""

from __future__ import annotations

import asyncio
from types import TracebackType
from typing import Any, Self, cast

from ..case.instance import CaseInstance
from ..config.loader import ConfigLoader
from ..results import Results
from ..results.values.collector import Collector, SupportedCollectorTypes


class DataRegistry:

    def __init__(self) -> None:
        self._data: dict[str, object] = {}

    def register(self, name: str, item: object) -> None:
        if name in self._data:
            raise RuntimeError(f"Data already registered: '{name}'")

        self._data[name] = item

    def get[T](self, data_type: type[T], name: str) -> T:
        if item := self._data.get(name):
            if isinstance(item, data_type):
                return item
            raise RuntimeError(f"Invalid data type for: '{name}'")
        raise RuntimeError(f"Unknown data: '{name}'")


class CollectorRegistry:

    def __init__(self, parent: Context):
        self._collectors: dict[str, Collector[SupportedCollectorTypes]] = {}
        self._parent = parent

    def get[T: SupportedCollectorTypes](
        self, data_type: type[T], name: str
    ) -> Collector[T]:
        if item := self._collectors.get(name):
            return cast(Collector[T], item)

        _ = data_type
        result = Collector[T].create(name, self._parent.results)

        self._collectors[name] = cast(Collector[SupportedCollectorTypes], result)
        return result


class Context:

    def __init__(self, config: dict[str, Any]):
        self._data = DataRegistry()
        self._collectors = CollectorRegistry(self)
        self._config_loader = ConfigLoader()
        self._config_raw = config
        self._results = Results(config)
        self._first_case_executed = False

    @property
    def config_raw(self) -> dict[str, Any]:
        return self._config_raw

    @property
    def config_loader(self) -> ConfigLoader:
        return self._config_loader

    @property
    def global_data(self) -> DataRegistry:
        return self._data

    @property
    def collectors(self) -> CollectorRegistry:
        return self._collectors

    @property
    def results(self) -> Results:
        return self._results

    @property
    def first_case_executed(self) -> bool:
        return self._first_case_executed

    def mark_first_case_executed(self) -> None:
        self._first_case_executed = True

    def enter_case(self, case: CaseInstance) -> "CaseContext":
        return CaseContext(self, case)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_traceback: TracebackType | None,
    ) -> None:
        self.results.finish()


class CaseContext:
    def __init__(self, parent: Context, case: CaseInstance):
        self._parent = parent
        self._case = case
        self._data = DataRegistry()
        self._actions_ended = asyncio.Event()

        self.results.add_case(self.case.identifier)

    @property
    def parent(self) -> Context:
        return self._parent

    @property
    def case(self) -> CaseInstance:
        return self._case

    @property
    def results(self) -> Results:
        return self._parent.results

    @property
    def data(self) -> DataRegistry:
        return self._data

    @property
    def collectors(self) -> CollectorRegistry:
        return self.parent.collectors

    @property
    def first_case_executed(self) -> bool:
        return self.parent.first_case_executed

    async def wait_for_actions_ended(self) -> None:
        await self._actions_ended.wait()

    def notify_actions_ended(self) -> None:
        self._actions_ended.set()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_traceback: TracebackType | None,
    ) -> None:
        self._parent.mark_first_case_executed()
