# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module containing base building blocks of the experiment - sub tasks.
"""

import logging
from abc import ABC, abstractmethod
from enum import StrEnum
from typing import TYPE_CHECKING, TypeAlias

from ..context import CaseContext
from ..results.basic import BasicResult

if TYPE_CHECKING:
    LoggerAdapter = logging.LoggerAdapter[logging.Logger]
else:
    LoggerAdapter = logging.LoggerAdapter


class SubTask(ABC):
    # pylint: disable=too-few-public-methods
    class StartedType:
        pass

    type StartResult = str | StartedType
    STARTED = StartedType()

    # pylint: disable=duplicate-code
    def __init__(self, name: str, logger: logging.Logger):
        self._name = name
        self._logger = logging.LoggerAdapter(logger, extra={"subtask": name})

    @property
    def name(self) -> str:
        return self._name

    @property
    def logger(self) -> LoggerAdapter:
        return self._logger

    @abstractmethod
    def start(self, context: CaseContext) -> StartResult:
        pass

    @abstractmethod
    def finish(self) -> str:
        pass

    @property
    @abstractmethod
    def result_type(self) -> type[StrEnum]:
        pass


class TypedSubTask[T: StrEnum](SubTask):

    @abstractmethod
    def start(self, context: CaseContext) -> T | SubTask.StartedType:
        pass

    @abstractmethod
    def finish(self) -> T:
        pass

    @property
    @abstractmethod
    def result_type(self) -> type[T]:
        pass


class BasicSubTask(TypedSubTask[BasicResult]):
    type StartResult = BasicResult | SubTask.StartedType
    Result: TypeAlias = BasicResult

    def start(self, context: CaseContext) -> StartResult:
        return SubTask.STARTED if self.basic_start(context) else BasicResult.NOT_STARTED

    @abstractmethod
    def basic_start(self, context: CaseContext) -> bool:
        pass

    @property
    def result_type(self) -> type[Result]:
        return self.Result
