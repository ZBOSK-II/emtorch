# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
pytest configuration.
"""

import os
import sys
from pathlib import Path

import pytest


def pytest_configure(config: pytest.Config) -> None:  # pylint: disable=unused-argument
    # make CLI tests (prysk *.t files) use `emtorch` installed in the same environment as pytest
    bin_dir = str(Path(sys.executable).parent)
    os.environ["PATH"] = os.pathsep.join([bin_dir, os.environ.get("PATH", "")])
