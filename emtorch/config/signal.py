# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing signal configuration.
"""

import signal
from typing import Annotated, Any

from pydantic import BeforeValidator


def parse_signal(value: Any) -> signal.Signals:
    match value:
        case signal.Signals():
            return value
        case int():
            return signal.Signals(value)
        case str():
            try:
                return signal.Signals[value]
            except KeyError as exc:
                raise ValueError(f"Invalid signal name: {value}") from exc
        case _:
            raise TypeError(f"Unsupported type for Signal: {type(value)}")

    raise AssertionError("Unreachable: parse_signal did not return or raise in match")


Signal = Annotated[
    signal.Signals,
    BeforeValidator(parse_signal),
]
