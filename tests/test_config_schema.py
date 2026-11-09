# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Configuration JSON Schema tests.
"""

import tomllib
from importlib.metadata import entry_points as installed_entry_points
from pathlib import Path
from typing import Any, TypedDict

import jsonschema
import pytest

from emtorch import subtasks
from emtorch.config import configclass
from emtorch.config.schema import REF_TEMPLATE, build_schema
from emtorch.config.ssh import ConnectionConfig
from emtorch.subtasks import BasicSubTask, SubTaskContext, SubTasksLibrary

ROOT = Path(__file__).parent.parent


@pytest.fixture(name="schema", scope="module")
def _schema() -> dict[str, Any]:
    return build_schema(SubTasksLibrary())


@pytest.fixture(name="validator", scope="module")
def _validator(schema: dict[str, Any]) -> jsonschema.Draft7Validator:
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


def _resolve(schema: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
    if "$ref" not in node:
        (node,) = node["allOf"]
    name = node["$ref"].removeprefix(REF_TEMPLATE.format(model=""))
    return dict(schema["definitions"][name])


def _subtask_definition(schema: dict[str, Any]) -> dict[str, Any]:
    tables = _resolve(schema, schema["properties"]["actions"])
    return _resolve(schema, tables["additionalProperties"])


def test_descriptions_are_present(schema: dict[str, Any]) -> None:
    subtask = _subtask_definition(schema)
    echo = next(
        b["then"]
        for b in subtask["allOf"]
        if b["if"]["properties"]["type"]["const"] == "echo"
    )

    assert schema["properties"]["actions"]["description"]
    assert subtask["properties"]["when"]["description"]
    assert echo["description"].startswith("Basic echo command")
    assert echo["properties"]["message"]["description"] == "message to write to log"


def test_no_keywords_next_to_references(schema: dict[str, Any]) -> None:
    def check(node: Any) -> None:
        if isinstance(node, list):
            for n in node:
                check(n)
        elif isinstance(node, dict):
            assert "$ref" not in node or len(node) == 1, node
            for n in node.values():
                check(n)

    check(schema)


def test_shared_types_are_defined_once(schema: dict[str, Any]) -> None:
    connections = [n for n in schema["definitions"] if n.endswith("ConnectionConfig")]

    assert len(connections) == 1
    assert all("title" not in d for d in schema["definitions"].values())


def test_all_subtasks_are_described(schema: dict[str, Any]) -> None:
    names = sorted(SubTasksLibrary().names())
    subtask = _subtask_definition(schema)

    assert subtask["properties"]["type"]["enum"] == names
    assert [b["if"]["properties"]["type"]["const"] for b in subtask["allOf"]] == names


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


class _Plugin(BasicSubTask):
    """Plugin sub-task."""

    def __init__(self, config: Any):
        self._config = config

    async def execute(self, context: SubTaskContext) -> BasicSubTask.Result:
        return self.Result.SUCCESS


class _FakeEntryPoint:
    def __init__(self, name: str, config: type):
        self.name = name
        self._subtask = type(f"Plugin_{name}", (_Plugin,), {"Config": config})

    def load(self) -> type:
        return self._subtask


def _with_plugins(monkeypatch: pytest.MonkeyPatch, **configs: type) -> SubTasksLibrary:
    def entry_points(group: str) -> list[Any]:
        fakes = [_FakeEntryPoint(name, config) for name, config in configs.items()]
        return [*installed_entry_points(group=group), *fakes]

    monkeypatch.setattr(subtasks, "entry_points", entry_points)
    return SubTasksLibrary()


@configclass
class _PluginConfig:
    value: int


@pytest.mark.parametrize("name", ["case", "subtasks", "instance", "internal"])
def test_plugin_names_do_not_collide_with_internal_schemas(
    monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    schema = build_schema(_with_plugins(monkeypatch, **{name: _PluginConfig}))
    validator = jsonschema.Draft7Validator(schema)

    assert not _errors(validator, {"actions": {"a": {"type": name, "value": 1}}})
    assert _errors(validator, {"actions": {"a": {"type": name, "value": "x"}}})
    assert _errors(validator, {"unknown": 1})


def test_reserved_keys_do_not_leak_into_shared_types(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    schema = build_schema(_with_plugins(monkeypatch, conn=ConnectionConfig))
    validator = jsonschema.Draft7Validator(schema)
    connection = {"host": "h", "username": "u", "password": "p"}
    remote = {"type": "remote", "cmd": "x", "connection": connection | {"when": "once"}}

    assert not _errors(validator, {"actions": {"a": {"type": "conn"} | connection}})
    assert "actions.a.connection" in _errors(validator, {"actions": {"a": remote}})


class _Nested(TypedDict):
    value: int


@configclass
class _NestedConfig:
    nested: _Nested


def test_unknown_keys_are_forbidden_in_typed_dicts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    schema = build_schema(_with_plugins(monkeypatch, nested=_NestedConfig))
    validator = jsonschema.Draft7Validator(schema)
    subtask = {"type": "nested", "nested": {"value": 1}}

    assert not _errors(validator, {"actions": {"a": subtask}})
    subtask["nested"] = {"value": 1, "other": 2}
    assert "actions.a.nested" in _errors(validator, {"actions": {"a": subtask}})
