# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module interacting with configuration in files.
"""

import dataclasses
import tomllib
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter


class TypeAdapterCache:
    def __init__(self) -> None:
        self._cache: dict[type[Any], TypeAdapter[Any]] = {}

    def get_adapter[T](self, type_to_adapt: type[T]) -> TypeAdapter[T]:
        result = self._cache.get(type_to_adapt)
        if result is not None:
            return result
        result = TypeAdapter(type_to_adapt)
        self._cache[type_to_adapt] = result
        return result


class ConfigLoader:

    def __init__(self) -> None:
        self._cache = TypeAdapterCache()

    @staticmethod
    def load_toml(path: Path) -> Any:
        with path.open("rb") as file:
            return tomllib.load(file)

    def from_dict[T](self, config_type: type[T], data: dict[str, Any]) -> T:
        assert dataclasses.is_dataclass(config_type)
        adapter = self._cache.get_adapter(config_type)
        return adapter.validate_python(data, extra="forbid")
