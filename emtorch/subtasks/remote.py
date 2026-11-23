# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing remote (SSH) task as sub-tasks.
"""

import asyncio
import re
from typing import Annotated

import asyncssh

from ..config import Doc, configclass
from ..config.signal import Signal
from ..config.ssh import ConnectionConfig
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


class Remote(ProcessSubTask):
    """
    Executes command on remote machine connected via SSH.
    """

    @configclass
    class Config:
        connection: Annotated[ConnectionConfig, Doc("SSH connection configuration")]
        cmd: Annotated[Template, Doc("command to be executed remotely")]
        timeout: Annotated[float, Doc("operation timeout")] = 5
        signal: Annotated[Signal | None, SIGNAL_DOC] = None
        ready_pattern: Annotated[re.Pattern[str] | None, READY_PATTERN_DOC] = None
        ready_timeout: Annotated[float | None, READY_TIMEOUT_DOC] = None

    def __init__(self, config: Config):
        super().__init__(config.ready_pattern, config.ready_timeout)
        self._config = config

    def _install_signal(
        self,
        pid: str,
        conn: asyncssh.SSHClientConnection,
        context: SubTaskContext,
    ) -> None:
        if self._config.signal is None:
            return

        async def signal_process() -> None:
            assert self._config.signal

            signal = self._config.signal

            await context.wait_for_actions_ended()
            context.logger.info(f"Sending remote signal {signal.name} ({signal.value})")
            await conn.run(f"kill -{signal.value} -{pid}")
            # proc.send_signal(signal.name)

        asyncio.create_task(signal_process())

    async def execute(self, context: SubTaskContext) -> ProcessResult:
        cmd = "echo $$; exec " + self._config.cmd.evaluate(context.parent)

        context.logger.info(f"Executing remotely: {cmd}")

        try:
            async with self._config.connection.open() as conn:
                proc = await conn.create_process(cmd)

                pid = await proc.stdout.readline()
                context.logger.info(f"Started PID={pid}")

                self._install_signal(pid, conn, context)

                async def kill() -> None:
                    await conn.run(f"kill -KILL -{pid.strip()}")

                await self._readiness.supervise(
                    context,
                    asyncio.wait_for(proc.wait(), self._config.timeout),
                    [("STDOUT", proc.stdout), ("STDERR", proc.stderr)],
                    kill,
                )
                if proc.exit_status != 0:
                    context.logger.warning(
                        f"Command exited with code: {proc.exit_status}"
                    )
                    return self.Result.FAILURE

        except ConnectionError as ex:
            context.logger.error(f"Connection error: {ex}")
            return self.Result.ERROR
        except asyncssh.misc.Error as ex:
            context.logger.error(f"Error while executing command: {ex}")
            return self.Result.ERROR
        except TimeoutError:
            context.logger.warning("Command timed out")
            return self.Result.TIMEOUT
        except NotReadyError:
            return self.Result.NOT_READY

        context.logger.info("Command finished successfully")
        return self.Result.SUCCESS
