# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module for representing SSH connection configuration.
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

import asyncssh

from ..config import configclass


@configclass
class ConnectionConfig:
    host: str
    port: int = 22
    username: str
    password: str
    known_hosts: str = "~/.ssh/known_hosts"

    @asynccontextmanager
    async def open(self) -> AsyncIterator[asyncssh.SSHClientConnection]:
        async with asyncssh.connect(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            known_hosts=self.known_hosts,
        ) as conn:
            yield conn
