# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
'config-check' command implementation.
"""

import tomllib
from typing import TYPE_CHECKING

from .command import Command

if TYPE_CHECKING:
    import argparse
    from pathlib import Path


class ConfigCheckCommand(Command):
    def __init__(self, parser: argparse.ArgumentParser):
        super().__init__(parser)

        self._add_config_argument()
        self._add_override_argument()

    def execute(self, args: argparse.Namespace) -> int:
        # pylint: disable=import-outside-toplevel
        from omegaconf.errors import OmegaConfBaseException

        from ..config.check import validate_config
        from ..config.loader import ConfigLoader

        try:
            config = ConfigLoader.load_toml(args.config)
        except (tomllib.TOMLDecodeError, UnicodeDecodeError) as ex:
            return self._report(args.config, [f"invalid TOML: {ex}"])
        try:
            config = ConfigLoader.apply_overrides(config, args.override or [])
        except OmegaConfBaseException as ex:
            # may be caused by the overrides or by values OmegaConf does not support
            reason = next(iter(str(ex).splitlines()), "") or type(ex).__name__
            location = f"{ex.full_key}: " if ex.full_key else ""
            return self._report(
                args.config, [f"{location}cannot apply overrides, {reason}"]
            )

        return self._report(args.config, validate_config(config, ConfigLoader()))

    @staticmethod
    def _report(path: Path, errors: list[str]) -> int:
        if not errors:
            print(f"{path}: OK")
            return 0

        print(f"{path}: {len(errors)} error(s) found")
        for error in errors:
            print(f"  {error}")
        return 1
