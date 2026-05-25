# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing 'delay' in experiment execution.
"""

import asyncio
import logging

logger = logging.getLogger(__name__)


class Delay:
    """
    Class representing single 'delay' in the experiment.
    Forces experiment to wait for a given number of seconds.
    """

    def __init__(self, value: float, name: str):
        self._value = value
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    async def wait(self) -> None:
        logger.info(f"Waiting on {self.name} ({self._value}s)")
        await asyncio.sleep(self._value)
        logger.info(f"Wait on {self.name} done")
