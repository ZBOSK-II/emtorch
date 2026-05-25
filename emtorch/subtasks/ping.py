# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module holding sub-tasks related to network "ping".
"""

import asyncio
import asyncio.subprocess
from typing import Annotated

from ..config import Doc, configclass
from ..context.template import Template
from . import BasicSubTask, LoggerAdapter, SubTaskContext
from .subprocess import Exec, stream_logger


async def detect_ping_is_alive(
    process: asyncio.subprocess.Process,
    logger: LoggerAdapter,
    reader: asyncio.StreamReader | None,
) -> BasicSubTask.Result:
    assert reader

    header = await reader.readline()
    logger.info(f"{header!r}")

    response_received = False

    while not reader.at_eof():
        char = await reader.read(1)
        if len(char) == 0:
            break

        match char:
            case b"\b":
                if not response_received:
                    logger.info("Response received")
                response_received = True
            case b".":
                if response_received:
                    logger.info("Ping received")
                    process.terminate()
                else:
                    logger.info("Ping")
            case b"E":
                logger.warning("Error response")
                response_received = False

    return (
        BasicSubTask.Result.SUCCESS
        if response_received
        else BasicSubTask.Result.FAILURE
    )


class PingIsAlive(BasicSubTask):
    """
    Uses 'ping' to check if given network end point is responding (is alive).
    """

    @configclass
    class Config:
        host: Annotated[str, Doc("host to be checked")]
        timeout: Annotated[float, Doc("timeout to wait for any response")]
        interval: Annotated[int, Doc("interval between pings")]

    def __init__(self, config: Config):
        self._config = config

    async def execute(self, context: SubTaskContext) -> BasicSubTask.Result:
        context.logger.info(f"Starting ping-is-alive {self._config.host}")

        proc = await asyncio.create_subprocess_exec(
            "ping",
            "-f",
            "-i",
            str(self._config.interval),
            self._config.host,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            result, _, _ = await asyncio.gather(
                asyncio.create_task(
                    detect_ping_is_alive(proc, context.logger, proc.stdout)
                ),
                asyncio.wait_for(proc.wait(), self._config.timeout),
                asyncio.create_task(
                    stream_logger("STDERR", context.logger, proc.stderr)
                ),
            )
        except TimeoutError:
            context.logger.warning("Ping timed out")
            return self.Result.TIMEOUT

        return result


class PingIsStable(Exec):
    """
    Uses 'ping' to check if given network end point is stable responding.
    """

    @configclass
    class Config:
        host: Annotated[str, Doc("host to be checked")]
        count: Annotated[int, Doc("number of pings to be sent")]
        interval: Annotated[int, Doc("interval between pings")]

    def __init__(self, config: Config):
        timeout = (config.count + 1) * config.interval
        base_config = Exec.Config(
            program=Template("ping"),
            args=[
                Template(arg)
                for arg in [
                    "-c",
                    str(config.count),
                    "-i",
                    str(config.interval),
                    config.host,
                ]
            ],
            timeout=timeout,
        )
        super().__init__(base_config)
