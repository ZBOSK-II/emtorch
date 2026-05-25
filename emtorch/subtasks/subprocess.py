# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module containing subprocess subtask.
"""

import asyncio
import asyncio.subprocess
from abc import abstractmethod
from dataclasses import field
from typing import Annotated

from ..config import Doc, configclass
from ..config.signal import Signal
from ..context.template import Template
from . import BasicSubTask, LoggerAdapter, SubTaskContext


async def stream_logger(
    name: str, logger: LoggerAdapter, reader: asyncio.StreamReader | None
) -> None:
    assert reader
    while not reader.at_eof():
        line = await reader.readline()
        if line:
            logger.info(f"{name} - {bytes(line.rstrip())!r}")


class Subprocess(BasicSubTask):

    def __init__(self, signal: Signal | None, timeout: float):
        self._signal = signal
        self._timeout = timeout

    @abstractmethod
    async def create_process(
        self, context: SubTaskContext
    ) -> asyncio.subprocess.Process:
        pass

    async def execute(self, context: SubTaskContext) -> BasicSubTask.Result:
        proc = await self.create_process(context)

        self._install_signal(proc, context)

        try:
            retcode, _, _ = await asyncio.gather(
                asyncio.wait_for(proc.wait(), self._timeout),
                asyncio.create_task(
                    stream_logger("STDOUT", context.logger, proc.stdout)
                ),
                asyncio.create_task(
                    stream_logger("STDERR", context.logger, proc.stderr)
                ),
            )
        except TimeoutError:
            context.logger.warning("Operation timed out")
            return self.Result.TIMEOUT

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
        signal: Annotated[
            Signal | None,
            Doc("signal name to be sent to the program at the end of monitoring"),
        ] = None

    def __init__(self, config: Config):
        super().__init__(config.signal, config.timeout)
        self._config = config

    async def create_process(
        self, context: SubTaskContext
    ) -> asyncio.subprocess.Process:
        cmd = self._config.cmd.evaluate(context.parent)

        context.logger.info(f"Starting shell command: {cmd}")

        return await asyncio.create_subprocess_shell(
            cmd=cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
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
        signal: Annotated[
            Signal | None,
            Doc("signal name to be sent to the program at the end of monitoring"),
        ] = None

    def __init__(self, config: Config):
        super().__init__(config.signal, config.timeout)
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
        )
