# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Configuration JSON Schema tests.
"""

import tomllib
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from emtorch.config.schema import build_schema
from emtorch.subtasks import SubTasksLibrary

ROOT = Path(__file__).parent.parent


@pytest.fixture(name="validator", scope="module")
def _validator() -> jsonschema.Draft7Validator:
    schema = build_schema(SubTasksLibrary())
    jsonschema.Draft7Validator.check_schema(schema)
    return jsonschema.Draft7Validator(schema)


def _errors(validator: jsonschema.Draft7Validator, config: dict[str, Any]) -> list[str]:
    return sorted(
        ".".join(str(p) for p in e.absolute_path) for e in validator.iter_errors(config)
    )


def _echo(**kwargs: Any) -> dict[str, Any]:
    return {"type": "echo", "message": "hello"} | kwargs


@pytest.mark.parametrize(
    "path", [ROOT / "default-config.toml", ROOT / "tests" / "cli" / "experiment.toml"]
)
def test_example_configs_are_valid(
    validator: jsonschema.Draft7Validator, path: Path
) -> None:
    with path.open("rb") as file:
        config = tomllib.load(file)

    assert not _errors(validator, config)


@pytest.mark.parametrize(
    "config",
    [
        {"actions": {"a": _echo(when="per-data", delays={"before": 1})}},
        {"actions": {"a": {"type": "shell", "cmd": "x", "signal": "SIGKILL"}}},
        {"actions": {"a": {"type": "shell", "cmd": "x", "signal": 9}}},
        {"mappings": {"X": "y"}, "delays": {"between_cases": 0.5}},
    ],
)
def test_valid_configs(
    validator: jsonschema.Draft7Validator, config: dict[str, Any]
) -> None:
    assert not _errors(validator, config)


@pytest.mark.parametrize(
    ("config", "location"),
    [
        ({"unknown": 1}, ""),
        ({"delays": {"between_cases": "x"}}, "delays.between_cases"),
        ({"mappings": {"X": 1}}, "mappings.X"),
        ({"actions": {"a.b": _echo()}}, "actions"),
        ({"actions": {"a": {"message": "x"}}}, "actions.a"),
        ({"actions": {"a": {"type": "nope"}}}, "actions.a.type"),
        ({"actions": {"a": _echo(foo=1)}}, "actions.a"),
        ({"actions": {"a": {"type": "echo"}}}, "actions.a"),
        ({"actions": {"a": _echo(when="sometimes")}}, "actions.a.when"),
        ({"actions": {"a": _echo(delays={"during": 1})}}, "actions.a.delays"),
        (
            {"actions": {"a": {"type": "shell", "cmd": "x", "signal": "KILL"}}},
            "actions.a.signal",
        ),
        (
            {
                "actions": {
                    "a": {"type": "remote", "cmd": "x", "connection": {"host": "h"}}
                }
            },
            "actions.a.connection",
        ),
    ],
)
def test_invalid_configs(
    validator: jsonschema.Draft7Validator, config: dict[str, Any], location: str
) -> None:
    assert location in _errors(validator, config)


def test_descriptions_are_present() -> None:
    schema = build_schema(SubTasksLibrary())
    subtask = schema["definitions"]["subtask"]
    echo = next(
        b["then"]
        for b in subtask["allOf"]
        if b["if"]["properties"]["type"]["const"] == "echo"
    )

    assert schema["properties"]["actions"]["description"]
    assert subtask["properties"]["when"]["description"]
    assert echo["description"].startswith("Basic echo command")
    assert echo["properties"]["message"]["description"] == "message to write to log"


def test_all_subtasks_are_described() -> None:
    library = SubTasksLibrary()
    subtask = build_schema(library)["definitions"]["subtask"]

    assert subtask["properties"]["type"]["enum"] == sorted(library.names())
    assert [b["if"]["properties"]["type"]["const"] for b in subtask["allOf"]] == sorted(
        library.names()
    )


def test_broken_subtask_arguments_are_not_checked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = SubTasksLibrary.get

    def get(self: SubTasksLibrary, name: str) -> Any:
        if name == "echo":
            raise ImportError("broken")
        return original(self, name)

    monkeypatch.setattr(SubTasksLibrary, "get", get)
    schema = build_schema(SubTasksLibrary())
    validator = jsonschema.Draft7Validator(schema)

    assert not _errors(validator, {"actions": {"a": _echo(anything=1)}})
    assert _errors(validator, {"actions": {"a": {"type": "shell", "foo": 1}}})
