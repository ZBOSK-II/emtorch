# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing SFTP operation as sub-tasks.
"""

import asyncio
from abc import abstractmethod
from typing import Annotated

import asyncssh

from ..config import Doc, configclass
from ..config.ssh import ConnectionConfig
from ..context.template import Template
from . import BasicSubTask, SubTaskContext


class SftpTask(BasicSubTask):
    @configclass
    class Config:
        local_path: Annotated[
            Template, Doc("path to the local file used in SFTP transfer")
        ]
        remote_path: Annotated[
            Template, Doc("path to the remote file used in SFTP transfer")
        ]
        connection: Annotated[ConnectionConfig, Doc("SFTP connection config")]
        timeout: Annotated[float, Doc("operation timeout")] = 5

    def __init__(self, config: Config):
        self._config = config

    @abstractmethod
    async def perform_operation(
        self,
        sftp: asyncssh.sftp.SFTPClient,
        local_path: str,
        remote_path: str,
        context: SubTaskContext,
    ) -> None:
        pass

    @property
    @abstractmethod
    def dir_infix(self) -> str:
        pass

    async def execute(self, context: SubTaskContext) -> BasicSubTask.Result:
        local_path = self._config.local_path.evaluate(context.parent)
        remote_path = self._config.remote_path.evaluate(context.parent)
        transfer_info = f"{local_path} {self.dir_infix} {remote_path}"

        try:
            async with self._config.connection.open() as conn:
                async with conn.start_sftp_client() as sftp:
                    context.logger.info(f"Starting transfer: {transfer_info}")
                    await asyncio.wait_for(
                        self.perform_operation(sftp, local_path, remote_path, context),
                        timeout=self._config.timeout,
                    )
        except ConnectionError as ex:
            context.logger.error(f"Transfer ({transfer_info}) - connection error: {ex}")
            return self.Result.ERROR
        except asyncssh.misc.Error as ex:
            context.logger.error(f"Transfer ({transfer_info}) failed: {ex}")
            return self.Result.ERROR
        except TimeoutError:
            context.logger.warning(f"Transfer ({transfer_info}) timed out")
            return self.Result.TIMEOUT

        return self.Result.SUCCESS

    def make_progress_handler(
        self, context: SubTaskContext
    ) -> asyncssh.sftp.SFTPProgressHandler:
        def progress_handler(src: bytes, dst: bytes, uploaded: int, total: int) -> None:
            context.logger.info(
                f"{src!r} {self.dir_infix} {dst!r} ({uploaded} / {total} bytes)"
            )

        return progress_handler


class SftpPut(SftpTask):
    """
    Uploads file using SFTP.
    """

    async def perform_operation(
        self,
        sftp: asyncssh.sftp.SFTPClient,
        local_path: str,
        remote_path: str,
        context: SubTaskContext,
    ) -> None:
        await sftp.put(
            localpaths=local_path,
            remotepath=remote_path,
            progress_handler=self.make_progress_handler(context),
        )

    @property
    def dir_infix(self) -> str:
        return "->"


class SftpGet(SftpTask):
    """
    Downloads file using SFTP.
    """

    async def perform_operation(
        self,
        sftp: asyncssh.sftp.SFTPClient,
        local_path: str,
        remote_path: str,
        context: SubTaskContext,
    ) -> None:
        await sftp.get(
            localpath=local_path,
            remotepaths=remote_path,
            progress_handler=self.make_progress_handler(context),
        )

    @property
    def dir_infix(self) -> str:
        return "<-"
