# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Building blocks shared by process-based sub-tasks (local and remote).
"""

import asyncio
import re
from abc import abstractmethod
from enum import StrEnum, auto
from typing import AsyncIterable, Awaitable, Callable, Sequence, TypeAlias

from ..config import Doc
from . import LoggerAdapter, SubTaskContext, TypedSubTask

SIGNAL_DOC = Doc("signal name to be sent to the program at the end of monitoring")
READY_PATTERN_DOC = Doc(
    "regular expression; the sub-task is considered ready (next monitoring sub-task"
    " is started) once an output line matches it, instead of right after start"
)
READY_TIMEOUT_DOC = Doc(
    "time to wait for `ready_pattern` to match, in seconds; when exceeded the program"
    " is killed and the sub-task results in `not_ready`; no limit when not set"
)


class ProcessResult(StrEnum):
    SUCCESS = auto()
    FAILURE = auto()
    ERROR = auto()
    TIMEOUT = auto()
    NOT_READY = auto()


class NotReadyError(Exception):
    pass


# called with each output line; returns True once no more lines are needed
LineHandler: TypeAlias = Callable[[str], bool]


async def stream_logger(
    name: str,
    logger: LoggerAdapter,
    lines: AsyncIterable[bytes] | AsyncIterable[str],
    on_line: LineHandler | None = None,
) -> None:
    async for line in lines:
        if not line:
            continue
        stripped = line.rstrip()
        if isinstance(stripped, bytes):
            logger.info(f"{name} - {stripped!r}")
        else:
            logger.info(f"{name} - {stripped}")
        if on_line is not None:
            text = (
                stripped.decode(errors="replace")
                if isinstance(stripped, bytes)
                else stripped
            )
            if on_line(text):
                on_line = None


class Readiness:
    """
    Readiness detection of a process sub-task: ready once an output line matches
    the pattern. Sub-tasks not configured with a pattern do not opt-in for it.
    """

    def __init__(self, pattern: re.Pattern[str] | None, timeout: float | None):
        self._pattern = pattern
        self._timeout = timeout

    @property
    def enabled(self) -> bool:
        return self._pattern is not None

    async def supervise[T](
        self,
        context: SubTaskContext,
        process: Awaitable[T],
        streams: Sequence[tuple[str, AsyncIterable[bytes] | AsyncIterable[str]]],
        kill: Callable[[], Awaitable[None]],
    ) -> T:
        """
        Awaits `process` while logging its output streams and detecting readiness.
        Raises NotReadyError if the process was killed as not ready in time.
        """
        pattern = self._pattern
        # set on readiness or process end, whichever comes first
        settled = asyncio.Event()
        matched = False

        def on_line(line: str) -> bool:
            # output buffered before the process end is still matched
            nonlocal matched
            if matched:
                return True
            if pattern is not None and pattern.search(line):
                matched = True
                settled.set()
                context.notify_ready()
                return True
            return False

        async def run_process() -> T:
            try:
                return await process
            finally:
                settled.set()

        async def watchdog(timeout: float) -> bool:
            try:
                await asyncio.wait_for(settled.wait(), timeout)
                return False
            except TimeoutError:
                context.logger.warning(
                    f"Not ready within {timeout} s, killing the program"
                )
                await kill()
                return True

        loggers = [
            asyncio.create_task(
                stream_logger(
                    name,
                    context.logger,
                    lines,
                    on_line if pattern is not None else None,
                )
            )
            for name, lines in streams
        ]
        if pattern is None or self._timeout is None:
            result, not_ready = await run_process(), False
        else:
            result, not_ready = await asyncio.gather(
                run_process(), watchdog(self._timeout)
            )
        if not_ready:
            # fallback for programs escaping the kill, still holding the output open
            for task in loggers:
                task.cancel()
            await asyncio.gather(*loggers, return_exceptions=True)
            raise NotReadyError()
        await asyncio.gather(*loggers)
        return result


class ProcessSubTask(TypedSubTask[ProcessResult]):
    """
    Base of sub-tasks running a program, optionally opting-in for readiness
    reporting based on the program output.
    """

    Result: TypeAlias = ProcessResult

    def __init__(
        self, ready_pattern: re.Pattern[str] | None, ready_timeout: float | None
    ):
        if ready_timeout is not None and ready_pattern is None:
            raise ValueError("'ready_timeout' requires 'ready_pattern'")
        self._readiness = Readiness(ready_pattern, ready_timeout)

    @property
    def result_type(self) -> type[Result]:
        return self.Result

    @property
    def signals_ready(self) -> bool:
        return self._readiness.enabled

    @abstractmethod
    async def execute(self, context: SubTaskContext) -> ProcessResult:
        pass
