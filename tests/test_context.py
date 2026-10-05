# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
context module tests.
"""

from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from emtorch.arguments import Arguments, RepeatMode
from emtorch.context import Context


def _given_context(config: dict[str, Any], mapping: dict[str, str]) -> Context:
    args = Arguments(
        data=[],
        output_prefix="",
        config=Path("."),
        repeats=1,
        repeat_mode=RepeatMode.ABAB,
        verbose=True,
        mapping=mapping,
    )
    return Context(config, args)


def test_mapping_empty_without_config_and_arguments() -> None:
    context = _given_context({}, {})

    assert not context.mapping


def test_mapping_taken_from_config() -> None:
    context = _given_context({"mappings": {"A": "1", "B": "2"}}, {})

    assert context.mapping == {"A": "1", "B": "2"}


def test_mapping_from_arguments_overrides_config() -> None:
    context = _given_context({"mappings": {"A": "1", "B": "2"}}, {"B": "3", "C": "4"})

    assert context.mapping == {"A": "1", "B": "3", "C": "4"}


def test_mapping_config_rejects_non_string_values() -> None:
    with pytest.raises(ValidationError):
        _given_context({"mappings": {"A": 1}}, {})
