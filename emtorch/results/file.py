# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module responsible for results file management.
"""

from pathlib import Path

from pydantic import TypeAdapter

from . import Results


def write_results(path: Path, results: Results) -> None:
    with path.open("wb") as f:
        f.write(TypeAdapter(Results).dump_json(results, indent=2))


def load_results(path: Path) -> Results:
    return TypeAdapter(Results).validate_json(path.read_bytes())
