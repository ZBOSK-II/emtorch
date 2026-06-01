# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
SSH client helper methods.
"""

import paramiko

from .connectionconfig import ConnectionConfig


def open_ssh(config: ConnectionConfig) -> paramiko.SSHClient:
    try:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.WarningPolicy())
        client.connect(
            config.host,
            config.port,
            config.username,
            config.password,
        )
        return client
    except Exception:
        if client is not None and client.get_transport() is not None:
            client.close()
        raise
