# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
'config-schema' command implementation.
"""

import json
from pathlib import Path
from typing import TYPE_CHECKING

from argcomplete.completers import FilesCompleter

from .command import Command

if TYPE_CHECKING:
    import argparse


class ConfigSchemaCommand(Command):
    def __init__(self, parser: argparse.ArgumentParser):
        super().__init__(parser)

        self._add_argument(
            "--output",
            help="path of the file to write the schema to (standard output if omitted)",
            type=Path,
            completer=FilesCompleter(["json"]),
        )

    def execute(self, args: argparse.Namespace) -> int:
        # pylint: disable=import-outside-toplevel
        from ..config.schema import build_schema
        from ..subtasks import SubTasksLibrary

        schema = json.dumps(build_schema(SubTasksLibrary()), indent=2) + "\n"
        if args.output is None:
            print(schema, end="")
        else:
            args.output.write_text(schema, encoding="utf-8")
        return 0
