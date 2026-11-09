# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module holding experiment building blocks - sub tasks.
"""

import asyncio
import dataclasses
import inspect
import logging
import re
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import field
from enum import StrEnum, auto
from importlib.metadata import entry_points
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    AsyncIterator,
    Callable,
    Iterable,
    Self,
    TypeAlias,
    cast,
)

from ..config import Doc, configclass
from ..delay import Delay

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from pydantic import GetJsonSchemaHandler
    from pydantic_core import CoreSchema

    from ..case import CaseInstance
    from ..config.loader import ConfigLoader
    from ..context import (
        CaseContext,
        CollectorRegistry,
        Context,
        DataRegistry,
    )
    from ..results import (
        ResultsCollector,
        SubTaskResults,
    )

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


class BasicResult(StrEnum):
    SUCCESS = auto()
    FAILURE = auto()
    ERROR = auto()
    TIMEOUT = auto()


class BasicSubTask(TypedSubTask[BasicResult]):
    Result: TypeAlias = BasicResult

    @property
    def result_type(self) -> type[Result]:
        return self.Result

    @abstractmethod
    async def execute(self, context: SubTaskContext) -> BasicResult:
        pass


class SubTaskDelays:
    @configclass
    class Config:
        before: Annotated[
            float | None, Doc("delay before the sub-task, in seconds")
        ] = None
        after: Annotated[float | None, Doc("delay after the sub-task, in seconds")] = (
            None
        )

    def __init__(self, before: Delay, after: Delay):
        self._before = before
        self._after = after

    async def wait_before(self, context: SubTaskContext) -> None:
        await self._before.wait(context.logger)

    async def wait_after(self, context: SubTaskContext) -> None:
        await self._after.wait(context.logger)

    @classmethod
    def from_config(cls, config: Config) -> Self:
        return cls(
            before=Delay(config.before, "before subtask"),
            after=Delay(config.after, "after subtask"),
        )


class RunMode(StrEnum):
    ALWAYS = auto()
    NEVER = auto()
    ONCE = auto()
    PER_DATA = auto()

    @classmethod
    def _missing_(cls, value: Any) -> RunMode | None:
        if isinstance(value, str):
            normalized = value.replace("-", "_")
            for member in cls:
                if member.value == normalized:
                    return member
        return None

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> dict[str, Any]:
        schema = handler(core_schema)
        schema["enum"] = [m.value for m in cls] + [
            m.value.replace("_", "-") for m in cls if "_" in m.value
        ]
        return schema


class RunPolicy(ABC):
    @abstractmethod
    def should_run(self, context: SubTaskContext) -> bool:
        return False

    @staticmethod
    def from_mode(mode: RunMode) -> RunPolicy:
        match mode:
            case RunMode.ALWAYS:
                return AlwaysRunPolicy()
            case RunMode.NEVER:
                return NeverRunPolicy()
            case RunMode.ONCE:
                return OnceRunPolicy()
            case RunMode.PER_DATA:
                return PerDataRunPolicy()
        raise ValueError(f"Unknown RunMode {mode}")


class AlwaysRunPolicy(RunPolicy):
    def should_run(self, context: SubTaskContext) -> bool:
        return True


class NeverRunPolicy(RunPolicy):
    def should_run(self, context: SubTaskContext) -> bool:
        return False


class OnceRunPolicy(RunPolicy):
    def __init__(self) -> None:
        self._executed = False

    def should_run(self, context: SubTaskContext) -> bool:
        if self._executed:
            return False
        self._executed = True
        return True


class PerDataRunPolicy(RunPolicy):
    def __init__(self) -> None:
        self._executed: set[str] = set()

    def should_run(self, context: SubTaskContext) -> bool:
        identifier = context.case.data.identifier
        if identifier in self._executed:
            return False
        self._executed.add(identifier)
        return True


class SubTaskNameError(ValueError):
    def __init__(self, location: str, reason: str):
        super().__init__(f"Sub-task name '{location}' {reason}")
        self.location = location
        self.reason = reason


class SubTaskInstance:
    # pylint: disable=invalid-field-call
    @configclass
    class Config:
        type: Annotated[str, Doc("type of the sub-task, see 'emtorch subtasks'")]
        delays: Annotated[
            SubTaskDelays.Config, Doc("delays around the sub-task execution")
        ] = field(default_factory=SubTaskDelays.Config)
        when: Annotated[
            RunMode, Doc("when the sub-task is executed, considering all test cases")
        ] = RunMode.ALWAYS

    # TOML bare key characters - names usable in results and '--override' paths
    NAME_PATTERN = re.compile(r"[A-Za-z0-9_-]+")

    # keys of a sub-task table handled by the instance, not by the sub-task itself
    RESERVED_KEYS = frozenset(f.name for f in dataclasses.fields(Config))

    @classmethod
    def separate_args(
        cls, table: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        instance = {k: v for k, v in table.items() if k in cls.RESERVED_KEYS}
        args = {k: v for k, v in table.items() if k not in cls.RESERVED_KEYS}
        return instance, args

    @classmethod
    def check_name(cls, prefix: str, name: str) -> str:
        fullname = prefix + "." + name
        if not cls.NAME_PATTERN.fullmatch(name):
            raise SubTaskNameError(
                fullname, "must consist only of letters, digits, '_' and '-'"
            )
        return fullname

    @classmethod
    def parse_config(
        cls, config_loader: ConfigLoader, prefix: str, name: str, table: dict[str, Any]
    ) -> tuple[str, Config, dict[str, Any]]:
        fullname = cls.check_name(prefix, name)
        instance, args = cls.separate_args(table)
        config = config_loader.from_dict(cls.Config, instance)
        return fullname, config, args

    def __init__(
        self,
        fullname: str,
        config: Config,
        subtask: SubTask,
        results: SubTaskResults,
    ):
        self._name = fullname
        self._config = config
        self._subtask = subtask
        self._results = results

        self._logger = logging.LoggerAdapter(logger, extra={"subtask": self.name})
        self._delays = SubTaskDelays.from_config(config.delays)

        self._when = RunPolicy.from_mode(config.when)

    @property
    def name(self) -> str:
        return self._name

    @property
    def logger(self) -> LoggerAdapter:
        return self._logger

    async def execute(self, context: CaseContext) -> None:
        self.logger.info(f"Starting {self.name}")
        subcontext = SubTaskContext(context, self)
        if self._when.should_run(subcontext):
            await self._delays.wait_before(subcontext)
            result = await self._subtask.execute(subcontext)
            self._results.collect(result)
            await self._delays.wait_after(subcontext)
        else:
            self.logger.info(f"Skipping {self.name}")
            self._results.skip()
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
    def results(self) -> ResultsCollector:
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


class _SubTasksJsonSchema:
    def __get_pydantic_json_schema__(
        self, _core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> dict[str, Any]:
        # pylint: disable=import-outside-toplevel
        from pydantic import TypeAdapter

        tables = TypeAdapter(dict[str, SubTaskInstance.Config]).core_schema
        schema = handler(tables)
        schema["propertyNames"] = {
            "pattern": f"^{SubTaskInstance.NAME_PATTERN.pattern}$"
        }
        return schema


class SubTasks:
    # sub-task name -> raw sub-task table, in definition order
    type Config = Annotated[dict[str, dict[str, Any]], _SubTasksJsonSchema()]

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
        self._check_subtask_class(name, cls)
        config = cls.Config
        self._check_config_class(name, config)

        self._cache[name] = (cls, config)
        return cast(type[SubTask], cls), config

    @staticmethod
    def _check_subtask_class(name: str, cls: Any) -> None:
        if (
            not issubclass(cls, SubTask)
            or not hasattr(cls, "Config")
            or not inspect.isclass(cls.Config)
        ):
            raise RuntimeError(
                f"Type registered as '{name}' is not a proper Emtorch subtask"
            )

    @staticmethod
    def _check_config_class(name: str, config: ConfigClass) -> None:
        if not dataclasses.is_dataclass(config):
            return
        reserved = SubTaskInstance.RESERVED_KEYS.intersection(
            f.name for f in dataclasses.fields(config)
        )
        if reserved:
            raise RuntimeError(
                f"Type registered as '{name}' uses reserved config keys: "
                + ", ".join(sorted(reserved))
            )


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
    def __init__(self, config_loader: ConfigLoader, results: ResultsCollector):
        self._config_loader = config_loader
        self._factories = SubTaskFactoryCache(config_loader)
        self._results = results

    def build_subtask(
        self, prefix: str, name: str, table: dict[str, Any]
    ) -> SubTaskInstance:
        fullname, config, args = SubTaskInstance.parse_config(
            self._config_loader, prefix, name, table
        )
        subtask = self._factories.get(config.type)(args)
        subresults = self._results.add_subtask(fullname, subtask.result_type)
        return SubTaskInstance(fullname, config, subtask, subresults)

    def build(self, name: str, config: SubTasks.Config) -> SubTasks:
        subtasks = [self.build_subtask(name, n, table) for n, table in config.items()]
        return SubTasks(name, subtasks)
