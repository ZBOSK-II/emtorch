# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
'values' command implementation.
"""

import argparse
import re
from contextlib import contextmanager
from pathlib import Path
from sys import stdout
from typing import Iterator, TextIO

from prettytable import PrettyTable

from ..case.instance import CaseId
from ..results import Results
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
        parser.add_argument(
            "--format",
            help="output format",
            choices=["csv", "text", "latex", "mediawiki", "html", "json"],
            default="csv",
        )
        parser.add_argument(
            "--include",
            help="""
include only specified value (can be provided multiple times, supports regular expressions)""",
            action="append",
            default=[],
        )
        parser.add_argument(
            "--exclude",
            help="""
do not include specified value (can be provided multiple times, supports regular expressions)""",
            action="append",
            default=[],
        )

    @staticmethod
    def _case_header(results: Results) -> list[str]:
        if results.info.args.repeats > 1:
            return ["Case", "Iteration"]
        return ["Case"]

    @staticmethod
    def _case_id(case_id: CaseId) -> list[str | int | float]:
        if case_id.iteration is not None:
            return [case_id.group, case_id.iteration]
        return [case_id.group]

    @staticmethod
    def _filter_values(args: argparse.Namespace, results: Results) -> list[str]:
        values = [v.name for v in results.values]
        if args.include:
            included = [re.compile(i) for i in args.include]
            values = [
                v for v in values if any(i.fullmatch(v) is not None for i in included)
            ]
        if args.exclude:
            excluded = [re.compile(e) for e in args.exclude]
            values = [
                v for v in values if all(e.fullmatch(v) is None for e in excluded)
            ]
        return values

    def execute(self, args: argparse.Namespace) -> int:
        results = load_results(args.results)
        table = PrettyTable()
        values = self._filter_values(args, results)
        table.field_names = self._case_header(results) + values
        for case in results.cases:
            row: list[str | int | float] = self._case_id(case.case_id)
            row += [case.values.get(v, "") for v in values]
            table.add_row(row)

        with _select_output(args) as output:
            print(table.get_formatted_string(out_format=args.format), file=output)

        return 0
