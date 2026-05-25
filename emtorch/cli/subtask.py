# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
'subtask' command implementation.
"""

import argparse
from typing import Any

from ..config.docgen import fields_descriptions
from ..subtasks import SubTask, SubTasksLibrary
from .command import Command


class SubTaskCommand(Command):
    def __init__(self, parser: argparse.ArgumentParser):
        super().__init__(parser)

        parser.add_argument(
            "name",
            nargs=1,
            help="name of the Sub Task",
        )

    @staticmethod
    def _print_doc(subtask: type[SubTask]) -> None:
        if subtask.__doc__ is None:
            return
        print()
        print(subtask.__doc__.strip())
        print()

    @staticmethod
    def _format_default(value: str | None) -> str:
        if value:
            return f" (default: {value})"
        return ""

    @classmethod
    def _print_config(cls, config: Any) -> None:
        print()
        print("Arguments")
        print("---------")
        for field_desc in fields_descriptions(config):
            desc = f"{field_desc.description}{cls._format_default(field_desc.defaultvalue)}"
            print(f"  {field_desc.name:24} - ({field_desc.typename}) {desc}")

    def execute(self, args: argparse.Namespace) -> int:
        name = args.name[0]
        library = SubTasksLibrary()
        subtask, configclass = library.get(name)
        print()
        print(name)
        print("=" * len(name))
        self._print_doc(subtask)
        self._print_config(configclass)
        return 0
