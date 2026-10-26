# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
'subtasks' command implementation.
"""

from typing import TYPE_CHECKING

from .command import Command

if TYPE_CHECKING:
    import argparse


class SubTasksCommand(Command):
    def execute(self, args: argparse.Namespace) -> int:
        # pylint: disable=import-outside-toplevel
        from ..subtasks import SubTasksLibrary

        library = SubTasksLibrary()
        print("Known Sub Tasks:\n")
        for name in sorted(library.names()):
            print("\t", name)
        print(
            "\nType 'emtorch subtask <TASK-NAME>' to get help on the given task's arguments"
        )
        return 0
