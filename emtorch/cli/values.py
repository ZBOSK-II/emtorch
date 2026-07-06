# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
'values' command implementation.
"""

import argparse
from contextlib import contextmanager
from pathlib import Path
from sys import stdout
from typing import Iterator, TextIO

from prettytable import PrettyTable

from ..results.file import load_results
from .command import Command


@contextmanager
def _select_output(args: argparse.Namespace) -> Iterator[TextIO]:
    if args.output:
        with args.output.open("w") as output:
            yield output
    else:
        yield stdout


class ValuesCommand(Command):
    def __init__(self, parser: argparse.ArgumentParser):
        super().__init__(parser)

        parser.add_argument(
            "results",
            type=Path,
            help="JSON results file to extract values from",
        )

        parser.add_argument(
            "--output",
            type=Path,
            help="output file (if not provided, STDOUT will be used)",
        )

        # format
        # filtering values
        # filtering rows
        # displayed columns
        # header

    def execute(self, args: argparse.Namespace) -> int:
        results = load_results(args.results)
        table = PrettyTable()
        values = [v.name for v in results.values]
        table.field_names = ["Case"] + [v.name for v in results.values]
        for case in results.cases:
            row: list[str | int | float | None] = [str(case.case_id)]
            row += [case.values.get(v) for v in values]
            table.add_row(row)

        with _select_output(args) as output:
            print(table.get_formatted_string(out_format="csv"), file=output)

        # missing rows
        # missing columns
        return 0
