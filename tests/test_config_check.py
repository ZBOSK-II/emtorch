# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Configuration validation tests.
"""

import tomllib
from pathlib import Path
from typing import Any

import pytest

from emtorch.case import Case
from emtorch.config import configclass
from emtorch.config.check import validate_config
from emtorch.config.loader import ConfigLoader
from emtorch.subtasks import SubTasksLibrary

ROOT = Path(__file__).parent.parent


def _validate(config: dict[str, Any]) -> list[str]:
    return validate_config(config, ConfigLoader())


def _echo(**kwargs: Any) -> dict[str, Any]:
    return {"type": "echo", "message": "hello"} | kwargs


@pytest.mark.parametrize(
    "path", [ROOT / "default-config.toml", ROOT / "tests" / "cli" / "experiment.toml"]
)
def test_example_configs_are_valid(path: Path) -> None:
    with path.open("rb") as file:
        config = tomllib.load(file)

    assert not _validate(config)


def test_empty_config_is_valid() -> None:
    assert not _validate({})


def test_unknown_top_level_key() -> None:
    assert _validate({"unknown": 1}) == ["unknown: Unexpected keyword argument"]


def test_subtasks_are_validated_despite_top_level_errors() -> None:
    errors = _validate(
        {"delays": {"between_cases": "x"}, "actions": {"a": {"type": "nope"}}}
    )

    assert [e.split(":")[0] for e in errors] == [
        "delays.between_cases",
        "actions.a.type",
    ]


def test_malformed_subtasks_keys_are_reported_once() -> None:
    errors = _validate({"actions": 1, "checks": {"a": 2}})

    assert [e.split(":")[0] for e in errors] == ["actions", "checks.a"]


def test_unknown_subtask_type() -> None:
    errors = _validate({"actions": {"a": {"type": "nope"}}})

    assert errors == ["actions.a.type: Unknown subtask type 'nope'"]


def test_missing_subtask_type() -> None:
    assert _validate({"actions": {"a": {"message": "x"}}}) == [
        "actions.a.type: Field required"
    ]


def test_unexpected_subtask_argument() -> None:
    errors = _validate({"actions": {"a": _echo(foo=1)}})

    assert errors == ["actions.a.foo: Unexpected keyword argument"]


def test_missing_subtask_argument() -> None:
    errors = _validate({"actions": {"a": {"type": "echo"}}})

    assert errors == ["actions.a.message: Field required"]


def test_invalid_subtask_argument_value() -> None:
    errors = _validate(
        {"actions": {"a": {"type": "shell", "cmd": "x", "timeout": "y"}}}
    )

    assert len(errors) == 1
    assert errors[0].startswith("actions.a.timeout: ")


def test_invalid_when() -> None:
    errors = _validate({"checks": {"a": _echo(when="sometimes")}})

    assert len(errors) == 1
    assert errors[0].startswith("checks.a.when: ")


def test_alternative_when_spelling_is_valid() -> None:
    assert not _validate({"checks": {"a": _echo(when="per-data")}})


def test_invalid_delays() -> None:
    errors = _validate({"setups": {"a": _echo(delays={"during": 1})}})

    assert errors == ["setups.a.delays.during: Unexpected keyword argument"]


def test_invalid_subtask_name() -> None:
    errors = _validate({"actions": {"a.b": _echo()}})

    assert errors == [
        "actions.a.b: invalid sub-task name, "
        "must consist only of letters, digits, '_' and '-'"
    ]


def test_subtask_construction_errors_are_reported() -> None:
    matcher = {
        "type": "logger-int-matcher",
        "value": "v",
        "pattern": "(?P<value>",
        "subtask": "actions.b",
    }
    errors = _validate({"monitoring": {"a": matcher}, "actions": {"b": _echo(x=1)}})

    assert len(errors) == 2
    assert errors[0].startswith("monitoring.a: ")
    assert errors[0].endswith("[PatternError]")
    assert errors[1] == "actions.b.x: Unexpected keyword argument"


def test_subtask_library_errors_are_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken_get(self: SubTasksLibrary, name: str) -> Any:
        raise ImportError(f"cannot load {name}")

    monkeypatch.setattr(SubTasksLibrary, "get", broken_get)
    errors = _validate({"actions": {"a": _echo(), "b": _echo()}})

    assert errors == [
        "actions.a.type: cannot load echo [ImportError]",
        "actions.b.type: cannot load echo [ImportError]",
    ]


def test_subtasks_keys_match_case_config() -> None:
    assert Case.Config.subtasks_keys() == ("setups", "monitoring", "actions", "checks")


def test_all_errors_are_reported() -> None:
    errors = _validate(
        {
            "setups": {"ok": _echo(), "a": _echo(foo=1)},
            "monitoring": {"b": {"type": "nope"}},
            "actions": {"c": {"type": "echo"}},
            "checks": {"d": _echo(when="x")},
        }
    )

    assert [e.split(":")[0] for e in errors] == [
        "setups.a.foo",
        "monitoring.b.type",
        "actions.c.message",
        "checks.d.when",
    ]


def test_arguments_are_validated_despite_invalid_instance_keys() -> None:
    errors = _validate({"setups": {"a": _echo(when="bad", foo=1)}})

    assert [e.split(":")[0] for e in errors] == ["setups.a.when", "setups.a.foo"]


def test_contents_are_validated_despite_invalid_name() -> None:
    errors = _validate({"setups": {"a b": _echo(foo=1)}})

    assert [e.split(":")[0] for e in errors] == ["setups.a b", "setups.a b.foo"]


def test_arguments_are_not_validated_without_type() -> None:
    errors = _validate({"setups": {"a": {"message": "x", "foo": 1}}})

    assert errors == ["setups.a.type: Field required"]


def test_constructor_key_error_keeps_its_type(monkeypatch: pytest.MonkeyPatch) -> None:
    class Broken:
        @configclass
        class Config:
            pass

        def __init__(self, config: Config):
            raise KeyError("x")

    monkeypatch.setattr(
        SubTasksLibrary, "get", lambda self, name: (Broken, Broken.Config)
    )
    errors = _validate({"actions": {"a": {"type": "broken"}}})

    assert errors == ["actions.a: 'x' [KeyError]"]


def test_empty_keys_are_shown_in_locations() -> None:
    errors = _validate({"": 1, "setups": {"a": _echo(**{"": 1})}})

    assert errors == [
        '"": Unexpected keyword argument',
        'setups.a."": Unexpected keyword argument',
    ]
