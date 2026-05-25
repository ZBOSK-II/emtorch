# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
CLI command module.
"""

import argparse
from abc import ABC, abstractmethod


class Command(ABC):
    def __init__(self, parser: argparse.ArgumentParser):
        self._parser = parser

    @property
    def parser(self) -> argparse.ArgumentParser:
        return self._parser

    @abstractmethod
    def execute(self, args: argparse.Namespace) -> int:
        pass
