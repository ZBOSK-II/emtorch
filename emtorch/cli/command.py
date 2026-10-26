# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
CLI command module.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, NoReturn

if TYPE_CHECKING:
    import argparse

    from argcomplete.completers import BaseCompleter


class Command(ABC):
    def __init__(self, parser: argparse.ArgumentParser):
        self.__parser = parser

    def _add_argument(
        self, *args: Any, completer: BaseCompleter | None = None, **kwargs: Any
    ) -> argparse.Action:
        action = self.__parser.add_argument(*args, **kwargs)
        if completer is not None:
            setattr(action, "completer", completer)
        return action

    def _error(self, message: str) -> NoReturn:
        self.__parser.error(message)

    @abstractmethod
    def execute(self, args: argparse.Namespace) -> int:
        pass
