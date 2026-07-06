# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Command Line Interface module.
"""

import argparse
import sys
from typing import cast

from ..version import VERSION
from .command import Command
from .run import RunCommand
from .subtask import SubTaskCommand
from .subtasks import SubTasksCommand
from .values import ValuesCommand


class Cli:
    def __init__(self) -> None:
        self._parser = argparse.ArgumentParser(
            prog="emtorch",
            description="Experiments orchestrator for embedded systems",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            suggest_on_error=True,
            epilog="Run 'emtorch <COMMAND> --help' to get help on a specific command",
        )
        self._parser.add_argument(
            "--version",
            action="version",
            version=VERSION,
        )

        self._subparsers = self._parser.add_subparsers(
            metavar="COMMAND",
            help="emtorch command to be executed (listed below)",
            required=True,
        )

        self.__add_command(
            RunCommand, "run", "execute the experiment using configuration"
        )
        self.__add_command(
            SubTasksCommand, "subtasks", "lists all available subcommands"
        )
        self.__add_command(
            SubTaskCommand, "subtask", "provides documentation for the given task"
        )
        self.__add_command(ValuesCommand, "values", "extracts values from results")

    def __add_command[T: Command](
        self, command: type[T], name: str, description: str
    ) -> None:
        parser = self._subparsers.add_parser(
            name, help=description, description=description
        )
        cmd = command(parser)
        parser.set_defaults(command=cmd.execute)

    def execute(self) -> int:
        args = self._parser.parse_args()
        try:
            return cast(int, args.command(args))
        except Exception as ex:  # pylint: disable=broad-exception-caught
            print(f"ERROR: {ex} [{type(ex).__name__}]", file=sys.stderr)
            return -1
