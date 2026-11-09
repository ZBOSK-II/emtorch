# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
CLI command module.
"""

import argparse
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, NoReturn

from argcomplete.completers import FilesCompleter

if TYPE_CHECKING:
    from argcomplete.completers import BaseCompleter


def parse_kv(s: str) -> tuple[str, str]:
    try:
        key, value = s.split("=", 1)
        return key, value
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Expected format KEY=VALUE") from exc


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

    def _add_config_argument(self) -> None:
        self._add_argument(
            "--config",
            help="path to the configuration file",
            default="default-config.toml",
            type=Path,
            completer=FilesCompleter(["toml"]),
        )

    def _add_override_argument(self) -> None:
        self._add_argument(
            "--override",
            action="append",
            type=parse_kv,
            metavar="path.to.key=value",
            help="provide configuration keys override (e.g. setups.NAME.KEY=VALUE)",
        )

    def _error(self, message: str) -> NoReturn:
        self.__parser.error(message)

    @abstractmethod
    def execute(self, args: argparse.Namespace) -> int:
        pass
