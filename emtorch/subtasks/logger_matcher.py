# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing collector for extracting values from log.
"""

import logging
import re
from typing import Annotated, cast

from ..config import Doc, configclass
from ..results.values.collector import SupportedCollectorTypes
from . import BasicSubTask, SubTaskContext


class LoggerMatcher[T: SupportedCollectorTypes](BasicSubTask):

    @configclass
    class Config:
        value: Annotated[str, Doc("name for the value to store")]
        pattern: Annotated[
            str,
            Doc(
                "regular expression containing named group `value` used to extract the value \
                (e.g. `prefix=(?P<value>\\d+.\\d+)`)"
            ),
        ]
        subtask: Annotated[str, Doc("subtask which logs should be scanned")]

    def __init__(
        self,
        config: Config,
        value_type: type[T],
    ):
        self._config = config
        self._regex = re.compile(config.pattern)
        self._value_type = value_type

    async def execute(self, context: SubTaskContext) -> BasicSubTask.Result:

        collector = context.collectors.get(self._value_type, self._config.value)
        error = False

        def log_filter(r: logging.LogRecord) -> bool:
            nonlocal error
            if r.__dict__.get("subtask") == self._config.subtask:
                match = self._regex.search(r.getMessage())
                if match is not None:
                    try:
                        collector.set_current(
                            cast(T, self._value_type(match.group("value")))
                        )
                    except ValueError:
                        error = True
            return True

        root_logger = logging.getLogger()
        handler = root_logger.handlers[0] if root_logger.handlers else None
        if handler is not None:
            handler.addFilter(log_filter)

        try:
            await context.wait_for_actions_ended()
        finally:
            if handler is not None:
                handler.removeFilter(log_filter)

        if error:
            return self.Result.ERROR
        if collector.has_value():
            collector.commit(context.case.identifier)
            return self.Result.SUCCESS
        return self.Result.FAILURE


class LoggerIntMatcher(LoggerMatcher[int]):
    """
    Scans Sub Task logs for occurrence of integer value.
    """

    def __init__(self, config: LoggerIntMatcher.Config):
        super().__init__(config, int)


class LoggerFloatMatcher(LoggerMatcher[float]):
    """
    Scans Sub Task logs for occurrence of float value.
    """

    def __init__(self, config: LoggerFloatMatcher.Config):
        super().__init__(config, float)
