# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
'shell-completions' command implementation.
"""

import argparse
import os
from pathlib import Path

from argcomplete.completers import FilesCompleter
from argcomplete.shell_integration import shellcode

from .command import Command

EXECUTABLE = "emtorch"
SHELLS = ("bash", "zsh", "fish", "tcsh", "powershell")


def _xdg_dir(variable: str, default: str) -> Path:
    return Path(os.environ.get(variable) or Path.home() / default)


def _default_path(shell: str) -> Path | None:
    match shell:
        case "bash":
            return (
                _xdg_dir("XDG_DATA_HOME", ".local/share")
                / "bash-completion"
                / "completions"
                / EXECUTABLE
            )
        case "zsh":
            return (
                _xdg_dir("XDG_DATA_HOME", ".local/share")
                / "zsh"
                / "site-functions"
                / f"_{EXECUTABLE}"
            )
        case "fish":
            return (
                _xdg_dir("XDG_CONFIG_HOME", ".config")
                / "fish"
                / "completions"
                / f"{EXECUTABLE}.fish"
            )
    return None


def _detect_shell() -> str | None:
    shell = Path(os.environ.get("SHELL", "")).name
    return shell if shell in SHELLS else None


class ShellCompletionsCommand(Command):
    def __init__(self, parser: argparse.ArgumentParser):
        super().__init__(parser)

        self._add_argument(
            "--shell",
            help="target shell (detected from $SHELL if not provided)",
            choices=SHELLS,
            default=_detect_shell(),
        )
        self._add_argument(
            "--print",
            help="print the completion script to STDOUT instead of installing it",
            action="store_true",
        )
        self._add_argument(
            "--path",
            help="destination of the completion script (default depends on the shell)",
            type=Path,
            completer=FilesCompleter(),
        )

    def execute(self, args: argparse.Namespace) -> int:
        if args.shell is None:
            self._error("Unable to detect the shell, use --shell")

        script = shellcode([EXECUTABLE], shell=args.shell)
        if args.print:
            print(script)
            return 0

        path = args.path or _default_path(args.shell)
        if path is None:
            self._error(
                f"No default location for {args.shell} completions, use --path or --print"
            )

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(script)
        print(f"Completion script for {args.shell} installed to: {path}")
        if args.shell == "zsh":
            print(
                f"Make sure '{path.parent}' is in your $fpath before 'compinit' is called,"
                " e.g. add to ~/.zshrc:"
            )
            print(f"  fpath=({path.parent} $fpath)")
        print("Restart your shell to enable completions.")
        return 0
