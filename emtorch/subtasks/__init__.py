# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module holding experiment building blocks - sub tasks.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from enum import StrEnum
from importlib.metadata import entry_points
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Callable,
    Iterable,
    TypeAlias,
    cast,
)

from ..case.instance import CaseInstance
from ..config import configclass
from ..config.loader import ConfigLoader
from ..context import (
    CaseContext,
    CollectorRegistry,
    Context,
    DataRegistry,
)
from ..results import Results, SubTaskResults
from ..results.basic import BasicResult

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    LoggerAdapter = logging.LoggerAdapter[logging.Logger]
else:
    LoggerAdapter = logging.LoggerAdapter


class SubTask(ABC):

    @property
    @abstractmethod
    def result_type(self) -> type[StrEnum]:
        pass

    @abstractmethod
    async def execute(self, context: SubTaskContext) -> str:
        pass


class TypedSubTask[T: StrEnum](SubTask):

    @property
    @abstractmethod
    def result_type(self) -> type[T]:
        pass

    @abstractmethod
    async def execute(self, context: SubTaskContext) -> T:
        pass


class BasicSubTask(TypedSubTask[BasicResult]):
    Result: TypeAlias = BasicResult

    @property
    def result_type(self) -> type[Result]:
        return self.Result

    @abstractmethod
    async def execute(self, context: SubTaskContext) -> BasicResult:
        pass


class SubTaskInstance:
    @configclass
    class Config:
        name: str
        type: str
        args: dict[str, Any]

    def __init__(
        self, fullname: str, config: Config, subtask: SubTask, results: SubTaskResults
    ):
        self._name = fullname
        self._config = config
        self._subtask = subtask
        self._results = results

        self._logger = logging.LoggerAdapter(logger, extra={"subtask": self.name})

    @property
    def name(self) -> str:
        return self._name

    @property
    def logger(self) -> LoggerAdapter:
        return self._logger

    async def execute(self, context: CaseContext) -> None:
        self.logger.info(f"Staring {self.name}")
        subcontext = SubTaskContext(context, self)
        result = await self._subtask.execute(subcontext)
        self._results.collect(context.case.identifier, result)
        self.logger.info(f"Finished {self.name}")


class SubTaskContext:

    def __init__(self, parent: CaseContext, subtask: SubTaskInstance):
        self._parent = parent
        self._subtask = subtask

    @property
    def parent(self) -> CaseContext:
        return self._parent

    @property
    def root(self) -> Context:
        return self.parent.parent

    @property
    def subtask(self) -> SubTaskInstance:
        return self._subtask

    @property
    def case(self) -> CaseInstance:
        return self.parent.case

    @property
    def results(self) -> Results:
        return self.parent.results

    @property
    def data(self) -> DataRegistry:
        return self.parent.data

    @property
    def collectors(self) -> CollectorRegistry:
        return self.parent.collectors

    @property
    def logger(self) -> LoggerAdapter:
        return self.subtask.logger

    async def wait_for_actions_ended(self) -> None:
        await self.parent.wait_for_actions_ended()


class SubTasks:
    type Config = list[SubTaskInstance.Config]

    def __init__(self, name: str, subtasks: list[SubTaskInstance]):
        self._subtasks = subtasks
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    async def execute(self, context: CaseContext) -> None:
        logger.info(f"Executing {self.name}")

        for task in self._subtasks:
            await task.execute(context)

        logger.info(f"Finished {self.name}")

    @asynccontextmanager
    async def monitor(self, context: CaseContext) -> AsyncIterator[None]:
        logger.info(f"Starting {self.name}")
        async with asyncio.TaskGroup() as group:
            for task in self._subtasks:
                group.create_task(task.execute(context))
            yield
        logger.info(f"Finished {self.name}")


class SubTasksLibrary:
    type ConfigClass = Any
    type SubTaskEntry = tuple[type[SubTask], ConfigClass]

    def __init__(self) -> None:
        self._entries = {e.name: e for e in entry_points(group="emtorch.subtasks")}
        self._cache: dict[str, SubTasksLibrary.SubTaskEntry] = {}

    def names(self) -> Iterable[str]:
        return self._entries.keys()

    def get(self, name: str) -> SubTaskEntry:
        if subtask := self._cache.get(name):
            return subtask

        entry = self._entries.get(name)
        if entry is None:
            raise KeyError(f"Unknown subtask type '{name}'")

        cls = entry.load()

        if (
            not issubclass(cls, SubTask)
            or not hasattr(cls, "Config")
            or not inspect.isclass(cls.Config)
        ):
            raise RuntimeError(
                f"Type registered as '{name}' is not a proper Emtorch subtask"
            )

        config = cls.Config
        self._cache[name] = (cls, cls.Config)
        return cast(type[SubTask], cls), config


class SubTaskFactoryCache:
    type Factory = Callable[[dict[str, Any]], SubTask]

    def __init__(self, config_loader: ConfigLoader):
        self._library = SubTasksLibrary()
        self._cache: dict[str, SubTaskFactoryCache.Factory] = {}
        self._config_loader = config_loader

    def get(self, name: str) -> Factory:
        if factory := self._cache.get(name):
            return factory

        subtask, configtype = self._library.get(name)

        def new_factory(args: dict[str, Any]) -> SubTask:
            cls = cast(Any, subtask)
            config = self._config_loader.from_dict(configtype, args)
            return cast(SubTask, cls(config))

        factory = new_factory

        self._cache[name] = factory

        return factory


class SubTasksBuilder:
    def __init__(self, config_loader: ConfigLoader, results: Results):
        self._factories = SubTaskFactoryCache(config_loader)
        self._results = results

    def build_subtask(
        self, prefix: str, config: SubTaskInstance.Config
    ) -> SubTaskInstance:
        name = prefix + "." + config.name
        factory = self._factories.get(config.type)
        subtask = factory(config.args)
        subresults = self._results.register_subtask(name, subtask.result_type)
        return SubTaskInstance(name, config, subtask, subresults)

    def build(self, name: str, config: SubTasks.Config) -> SubTasks:
        subtasks = [self.build_subtask(name, c) for c in config]
        return SubTasks(name, subtasks)
