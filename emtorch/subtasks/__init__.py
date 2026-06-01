# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module holding experiment building blocks - sub tasks.
"""

import logging
from contextlib import contextmanager
from typing import Iterator, Self

from ..config import Config
from ..context import CaseContext, Context
from ..results import Results, SubTaskResults
from .subtask import SubTask

logger = logging.getLogger(__name__)


# pylint: disable=too-many-return-statements,too-many-locals
def subtask_from_config(config: Config, context: Context, *prefix: str) -> SubTask:
    task_type = config.get_str("type")
    name = ".".join(prefix) + "." + config.get_str("name")
    args = config.section("args")
    match task_type:
        case "subprocess":
            # pylint: disable=import-outside-toplevel
            from .subprocess import Subprocess

            return Subprocess.from_config(name, args, context)
        case "ping_stable":
            from .ping import PingIsStable  # pylint: disable=import-outside-toplevel

            return PingIsStable.from_config(name, args, context)
        case "ping_alive":
            from .ping import PingIsAlive  # pylint: disable=import-outside-toplevel

            return PingIsAlive.from_config(name, args, context)
        case "remote":
            from .remote import Remote  # pylint: disable=import-outside-toplevel

            return Remote.from_config(name, args)
        case "coap_monitor":
            # pylint: disable=import-outside-toplevel
            from ..coap import CoapMonitor

            return CoapMonitor.from_config(name, args, context)
        case "coap_send":
            from ..coap import CoapSend  # pylint: disable=import-outside-toplevel

            return CoapSend.from_config(name, args, context)
        case "sftp-upload":
            from .sftp import SftpUpload  # pylint: disable=import-outside-toplevel

            return SftpUpload.from_config(name, args)
        case "sftp-download":
            from .sftp import SftpDownload  # pylint: disable=import-outside-toplevel

            return SftpDownload.from_config(name, args)
        case "logger-int-matcher":
            # pylint: disable=import-outside-toplevel
            from .logger_matcher import LoggerIntMatcher

            return LoggerIntMatcher.from_config(name, args, context)
        case "logger-float-matcher":
            # pylint: disable=import-outside-toplevel
            from .logger_matcher import LoggerFloatMatcher

            return LoggerFloatMatcher.from_config(name, args, context)
        case "file-write":
            # pylint: disable=import-outside-toplevel
            from .files import FileWriter

            return FileWriter.from_config(name, args)
        case _:
            raise ValueError(f"Unknown sub-task type '{task_type}'")


class SubTaskExecution:
    def __init__(self, task: SubTask, results: SubTaskResults):
        self._task = task
        self._results = results
        self._start_result: SubTask.StartResult | None = None

    @property
    def name(self) -> str:
        return self._task.name

    def start(self, context: CaseContext) -> None:
        self._start_result = self._task.start(context)

    def finish_for(self, context: CaseContext) -> None:
        assert self._start_result is not None
        result = (
            self._task.finish()
            if isinstance(self._start_result, SubTask.StartedType)
            else self._start_result
        )
        self._results.collect(context.case.identifier, result)
        self._start_result = None

    def execute_for(self, context: CaseContext) -> None:
        self.start(context)
        self.finish_for(context)


class SubTasks:
    def __init__(self, results: Results, *prefix: str):
        self._results = results
        self._prefix = prefix
        self._tasks: list[SubTaskExecution] = []

    @property
    def name(self) -> str:
        return ".".join(self._prefix)

    def register(self, task: SubTask) -> None:
        logger.info(f"Registering <{task.name}>")
        execution = SubTaskExecution(
            task,
            self._results.register_subtask(task.name, task.result_type),
        )
        self._tasks.append(execution)

    def execute_for(self, context: CaseContext) -> None:
        logger.info(f"Start {self.name}")
        for task in self._tasks:
            logger.info(f"Executing {task.name}")
            task.execute_for(context)
        logger.info(f"End {self.name}")

    @contextmanager
    def monitor(self, context: CaseContext) -> Iterator[None]:
        try:
            self.start_all(context)
            yield
        finally:
            self.finish_all_for(context)

    def start_all(self, context: CaseContext) -> None:
        logger.info(f"Starting {self.name}")
        for task in self._tasks:
            logger.info(f"Starting {task.name}")
            task.start(context)
        logger.info(f"All {self.name} started")

    def finish_all_for(self, context: CaseContext) -> None:
        logger.info(f"Finishing {self.name}")
        for task in self._tasks:
            logger.info(f"Finishing {task.name}")
            task.finish_for(context)
        logger.info(f"All {self.name} finished")

    @classmethod
    def from_config(cls, *prefix: str, context: Context) -> Self:
        tasks = cls(context.results, *prefix)
        for conf in context.config_root.get_config_list(*prefix):
            tasks.register(subtask_from_config(conf, context, *prefix))
        return tasks
