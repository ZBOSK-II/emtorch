# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Network configuratio.
"""

from dataclasses import dataclass
from typing import Self


@dataclass
class NetworkAddress:
    host: str
    port: int

    def as_tuple(self) -> tuple[str, int]:
        return self.host, self.port

    @classmethod
    def from_tuple(cls, addr: tuple[str, int]) -> Self:
        return cls(host=addr[0], port=addr[1])
