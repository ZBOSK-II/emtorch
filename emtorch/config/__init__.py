# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module containing types related to experiment configuration.
"""

import dataclasses
from typing import dataclass_transform


@dataclass_transform(eq_default=False, frozen_default=True, kw_only_default=True)
def configclass[T](cls: type[T]) -> type[T]:
    return dataclasses.dataclass(cls, eq=False, frozen=True, kw_only=True)


@dataclasses.dataclass(frozen=True)
class Doc:
    text: str
