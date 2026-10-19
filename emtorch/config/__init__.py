# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module containing types related to experiment configuration.
"""

import dataclasses
from enum import StrEnum
from typing import Any, dataclass_transform


@dataclass_transform(eq_default=False, frozen_default=True, kw_only_default=True)
def configclass[T](cls: type[T]) -> type[T]:
    return dataclasses.dataclass(cls, eq=False, frozen=True, kw_only=True)


@dataclasses.dataclass(frozen=True)
class Doc:
    text: str


class ConfigEnum(StrEnum):
    @classmethod
    def _missing_(cls, value: Any) -> StrEnum | None:
        if isinstance(value, str):
            normalized = value.replace("-", "_")
            for member in cls:
                if member.value == normalized:
                    return member
        return None
