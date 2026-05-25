# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
CoAP - Constrained Application Protocol support module.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Annotated

from ..config import Doc, configclass
from ..config.net import NetworkAddress
from ..delay import Delay
from ..subtasks import LoggerAdapter, SubTaskContext, TypedSubTask
from .code import code_reports_success, code_to_string, decode_code


class CoapMonitorResult(StrEnum):
    SUCCESS = auto()
    UNEXPECTED_MESSAGE_RECEIVED = auto()


class CoapProtocol(asyncio.DatagramProtocol):
    class Result(StrEnum):
        SUCCESS = auto()
        ERROR = auto()
        UNEXPECTED_ORIGIN = auto()
        MESSAGE_TOO_SHORT = auto()
        OPERATION_FAILURE = auto()
        TIMEOUT = auto()

    def __init__(
        self,
        future: asyncio.Future[CoapProtocol.Result],
        logger: LoggerAdapter,
        expected_ip: NetworkAddress,
    ):
        self._logger = logger
        self._unexpected_messages = 0
        self._expected_ip = expected_ip
        self._expecting = False
        self._result = future

    def check_message(self, address: NetworkAddress, data: bytes) -> Result:
        if address != self._expected_ip:
            self._logger.warning(
                f"Message received from unexpected origin: {address} vs {self._expected_ip}"
            )
            return self.Result.UNEXPECTED_ORIGIN

        if len(data) < 2:
            self._logger.warning("Too short message")
            return self.Result.MESSAGE_TOO_SHORT

        code = decode_code(data[1])

        self._logger.info(f"Received {code_to_string(code)}")

        if not code_reports_success(code):
            self._logger.warning("Operation reported as failed")
            return self.Result.OPERATION_FAILURE

        return self.Result.SUCCESS

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        if not self._expecting or self._result.done():
            self.__unexpected_message()
            return

        self._result.set_result(
            self.check_message(NetworkAddress.from_tuple(addr), data)
        )

    def error_received(self, exc: Exception) -> None:
        self._logger.error(f"Exception while processing UDP: {exc}")
        if not self._result.done():
            self._result.set_result(self.Result.ERROR)

    def connection_made(
        self, transport: asyncio.DatagramTransport  # type: ignore[override]
    ) -> None:
        self._logger.info("Connection established")

    def connection_lost(self, exc: Exception | None) -> None:
        if exc:
            self._logger.warning(f"Connection lost: {exc}")
        else:
            self._logger.info("Connection closed")

    def __unexpected_message(self) -> None:
        self._logger.warning("Message unexpected at this stage")
        self._unexpected_messages += 1

    @property
    def unexpected_messages(self) -> int:
        return self._unexpected_messages

    @property
    def result(self) -> asyncio.Future[CoapProtocol.Result]:
        return self._result


@dataclass(eq=False, frozen=True)
class CoapConnection:
    transport: asyncio.DatagramTransport
    protocol: CoapProtocol


class CoapMonitor(TypedSubTask[CoapMonitorResult]):
    """
    Monitors CoAP messages.
    """

    @configclass
    class Config:
        address: Annotated[NetworkAddress, Doc("CoAP device UDP address")]
        observation_timeout: Annotated[float, Doc("period of time to monitor")]

    def __init__(self, config: Config):
        self._config = config

    @property
    def result_type(self) -> type[CoapMonitorResult]:
        return CoapMonitorResult

    async def execute(self, context: SubTaskContext) -> CoapMonitorResult:

        loop = asyncio.get_running_loop()

        result = loop.create_future()

        delay = Delay(
            self._config.observation_timeout, context.subtask.name + ".observation"
        )

        transport, protocol = await loop.create_datagram_endpoint(
            lambda: CoapProtocol(result, context.logger, self._config.address),
            remote_addr=self._config.address.as_tuple(),
        )

        context.data.register(context.subtask.name, CoapConnection(transport, protocol))

        try:
            await delay.wait()
        finally:
            transport.close()

        return (
            CoapMonitorResult.SUCCESS
            if protocol.unexpected_messages == 0
            else CoapMonitorResult.UNEXPECTED_MESSAGE_RECEIVED
        )


class CoapSend(TypedSubTask[CoapProtocol.Result]):
    """
    Sends experiment data as CoAP message and waits for response.
    """

    @configclass
    class Config:
        monitor: Annotated[str, Doc("name of a monitor task to use for sending")]
        response_timeout: Annotated[float, Doc("timeout for the response")]

    def __init__(self, config: Config):
        self._config = config

    @property
    def result_type(self) -> type[CoapProtocol.Result]:
        return CoapProtocol.Result

    async def execute(self, context: SubTaskContext) -> CoapProtocol.Result:
        monitor = context.data.get(CoapConnection, self._config.monitor)

        monitor.transport.sendto(context.case.data.contents)

        try:
            return await asyncio.wait_for(
                monitor.protocol.result, self._config.response_timeout
            )
        except TimeoutError:
            return CoapProtocol.Result.TIMEOUT
