# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
'run' command implementation.
"""

import argparse
import logging
from datetime import datetime
from pathlib import Path

from .. import execute as emtorch_exec
from ..arguments import Arguments, RepeatMode
from ..config.loader import ConfigLoader
from ..results.file import write_results
from ..version import VERSION
from .command import Command


def _parse_mapping(s: str) -> tuple[str, str]:
    try:
        key, value = s.split("=", 1)
        return key, value
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Expected format KEY=VALUE") from exc


class RunCommand(Command):
    def __init__(self, parser: argparse.ArgumentParser):
        super().__init__(parser)

        parser.add_argument(
            "data",
            nargs="+",
            help="list of files containing binary data to send to the target",
        )
        parser.add_argument(
            "--output-prefix",
            help="prefix to be used for saving output (logs, reports, etc.)",
            default="emtorch",
            type=str,
        )
        parser.add_argument(
            "--config",
            help="path to the configuration file",
            default="default-config.toml",
            type=Path,
        )
        parser.add_argument(
            "--repeats",
            help="number of times to repeat each data file",
            default=1,
            type=int,
        )
        parser.add_argument(
            "--repeat-mode",
            help="pattern used when repeating ('aabb' or 'abab')",
            choices=("aabb", "abab"),
            default="aabb",
            type=str,
        )
        parser.add_argument(
            "--map",
            action="append",
            type=_parse_mapping,
            metavar="KEY=VALUE",
            help="provide mapping for $-string interpolation",
        )
        parser.add_argument(
            "--verbose",
            help="output all logs to the console",
            default=False,
            action=argparse.BooleanOptionalAction,
        )

    def __parse_data(self, data: list[str]) -> list[Path]:
        result = [Path(f) for f in data]
        for f in result:
            if not f.is_file():
                self._parser.error(f"Specified path is not a file: {f}")
        if len(result) != len(set(result)):
            self._parser.error(
                "Non-unique file names as inputs - results would be inconsistent"
            )
        return result

    def __parse_args(self, args: argparse.Namespace) -> Arguments:
        if args.repeats < 1:
            self._parser.error("--repeats must be >= 1")

        date_suffix = f"-{datetime.now():%Y%m%d-%H%M%S}"

        return Arguments(
            data=self.__parse_data(args.data),
            output_prefix=args.output_prefix + date_suffix,
            config=args.config,
            repeat_mode=RepeatMode(args.repeat_mode),
            repeats=args.repeats,
            mapping=dict(args.map or []),
            verbose=args.verbose,
        )

    @staticmethod
    def __logger_filter(record: logging.LogRecord) -> bool:
        if record.name != "root" and not record.name.startswith("emtorch"):
            return False
        return record.__dict__.get("subtask") is None

    @classmethod
    def __setup_logger(cls, log_file: Path, verbose: bool) -> None:
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        log_format = (
            "%(asctime)s [%(levelname)8s](%(name)24s)<%(subtask)24s>: %(message)s"
        )
        formatter = logging.Formatter(fmt=log_format, defaults={"subtask": "-" * 24})

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        if not verbose:
            console_handler.addFilter(cls.__logger_filter)
        root_logger.addHandler(console_handler)

        root_logger.info(f"Started instance ({VERSION})")

    def execute(self, args: argparse.Namespace) -> int:
        run_args = self.__parse_args(args)
        self.__setup_logger(run_args.output(".log"), run_args.verbose)

        results = emtorch_exec(run_args, ConfigLoader.load_toml(run_args.config))

        logging.getLogger().info(f"Results:\n{results.summary()}")

        write_results(run_args.output(".json"), results.data)

        return results.failed_count
