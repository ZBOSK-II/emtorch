# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module containing subprocess subtask.
"""

import asyncio
import asyncio.subprocess
import os
import re
from abc import abstractmethod
from dataclasses import field
from signal import SIGKILL
from typing import Annotated

from ..config import Doc, configclass
from ..config.signal import Signal
from ..context.template import Template
from . import SubTaskContext
from .process import (
    READY_PATTERN_DOC,
    READY_TIMEOUT_DOC,
    SIGNAL_DOC,
    NotReadyError,
    ProcessResult,
    ProcessSubTask,
)


class Subprocess(ProcessSubTask):

    def __init__(
        self,
        signal: Signal | None,
        timeout: float,
        ready_pattern: re.Pattern[str] | None,
        ready_timeout: float | None,
    ):
        super().__init__(ready_pattern, ready_timeout)
        self._signal = signal
        self._timeout = timeout

    @abstractmethod
    async def create_process(
        self, context: SubTaskContext
    ) -> asyncio.subprocess.Process:
        pass

    async def execute(self, context: SubTaskContext) -> ProcessResult:
        proc = await self.create_process(context)

        self._install_signal(proc, context)

        async def kill() -> None:
            # the whole group, as a shell does not pass the signal to its children
            try:
                os.killpg(proc.pid, SIGKILL)
            except ProcessLookupError:
                pass

        assert proc.stdout and proc.stderr
        try:
            retcode = await self._readiness.supervise(
                context,
                asyncio.wait_for(proc.wait(), self._timeout),
                [("STDOUT", proc.stdout), ("STDERR", proc.stderr)],
                kill,
            )
        except TimeoutError:
            context.logger.warning("Operation timed out")
            return self.Result.TIMEOUT
        except NotReadyError:
            return self.Result.NOT_READY

        if retcode != 0:
            context.logger.warning(f"Operation returned {retcode}")
            return self.Result.FAILURE

        context.logger.info("Operation finished successfully")
        return self.Result.SUCCESS

    def _install_signal(
        self, proc: asyncio.subprocess.Process, context: SubTaskContext
    ) -> None:
        if self._signal is None:
            return

        async def signal_process() -> None:
            assert self._signal

            await context.wait_for_actions_ended()
            context.logger.info(
                f"Sending signal {self._signal.name} ({self._signal.value})"
            )
            proc.send_signal(self._signal.value)

        asyncio.create_task(signal_process())


class Shell(Subprocess):
    """
    Executes system shell command.
    """

    @configclass
    class Config:
        cmd: Annotated[Template, Doc("shell command to be executed")]
        timeout: Annotated[float, Doc("execution timeout")] = 1.0
        signal: Annotated[Signal | None, SIGNAL_DOC] = None
        ready_pattern: Annotated[re.Pattern[str] | None, READY_PATTERN_DOC] = None
        ready_timeout: Annotated[float | None, READY_TIMEOUT_DOC] = None

    def __init__(self, config: Config):
        super().__init__(
            config.signal, config.timeout, config.ready_pattern, config.ready_timeout
        )
        self._config = config

    async def create_process(
        self, context: SubTaskContext
    ) -> asyncio.subprocess.Process:
        cmd = self._config.cmd.evaluate(context.parent)

        context.logger.info(f"Starting shell command: {cmd}")

        return await asyncio.create_subprocess_shell(
            cmd=cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            process_group=0,
        )


class Exec(Subprocess):
    """
    Executes provided program as subprocess.
    """

    # pylint: disable=invalid-field-call
    @configclass
    class Config:
        program: Annotated[Template, Doc("program to be executed")]
        args: Annotated[list[Template], Doc("program arguments")] = field(
            default_factory=list
        )
        timeout: Annotated[float, Doc("execution timeout")] = 1.0
        signal: Annotated[Signal | None, SIGNAL_DOC] = None
        ready_pattern: Annotated[re.Pattern[str] | None, READY_PATTERN_DOC] = None
        ready_timeout: Annotated[float | None, READY_TIMEOUT_DOC] = None

    def __init__(self, config: Config):
        super().__init__(
            config.signal, config.timeout, config.ready_pattern, config.ready_timeout
        )
        self._config = config

    async def create_process(
        self, context: SubTaskContext
    ) -> asyncio.subprocess.Process:
        program = self._config.program.evaluate(context.parent)
        args = [arg.evaluate(context.parent) for arg in self._config.args]

        context.logger.info(f"Starting process: {program} {' '.join(args)}")

        return await asyncio.create_subprocess_exec(
            program,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            process_group=0,
        )
