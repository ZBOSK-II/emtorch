# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing basic results of the single sub-task.
"""

from enum import StrEnum, auto


class BasicResult(StrEnum):
    SUCCESS = auto()
    FAILURE = auto()
    ERROR = auto()
    TIMEOUT = auto()
