# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
subtasks module tests.
"""

import tomllib
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from emtorch import subtasks
from emtorch.arguments import Arguments, RepeatMode
from emtorch.case import Case
from emtorch.config import configclass
from emtorch.config.loader import ConfigLoader
from emtorch.context import Context
from emtorch.subtasks import BasicSubTask, SubTaskContext, SubTasksLibrary


# pylint: disable=duplicate-code
def _given_context(config: dict[str, Any]) -> Context:
    args = Arguments(
        data=[],
        output_prefix="",
        config=Path("."),
        config_overrides=[],
        repeats=1,
        repeat_mode=RepeatMode.AABB,
        verbose=True,
        mapping={},
    )
    return Context(config, args)


def _built_subtasks(config: dict[str, Any]) -> list[str]:
    context = _given_context(config)
    Case.create(context)
    return [s.name for s in context.results.data.subtasks]


def test_subtasks_built_in_definition_order() -> None:
    config = tomllib.loads("""
        [setups.zeta]
        type = "shell"
        cmd = "true"

        [setups.alpha]
        type = "shell"
        cmd = "true"

        [setups.zeta.delays]
        before = 0.1

        [setups.mid]
        type = "shell"
        cmd = "true"
        """)

    names = _built_subtasks(config)

    assert names == ["setups.zeta", "setups.alpha", "setups.mid"]


def test_override_of_flat_key_is_applied() -> None:
    config = tomllib.loads("""
        [actions.process]
        type = "shell"
        cmd = "true"
        """)

    config = ConfigLoader.apply_overrides(config, [("actions.process.cmd", "false")])

    assert config["actions"]["process"]["cmd"] == "false"
    assert _built_subtasks(config) == ["actions.process"]


def test_unknown_subtask_argument_is_rejected() -> None:
    config = {"actions": {"process": {"type": "shell", "cmd": "true", "foo": 1}}}

    with pytest.raises(ValidationError):
        _built_subtasks(config)


def test_missing_type_is_rejected() -> None:
    config = {"actions": {"process": {"cmd": "true"}}}

    with pytest.raises(ValidationError):
        _built_subtasks(config)


def test_unknown_type_is_rejected() -> None:
    config = {"actions": {"process": {"type": "no-such-type"}}}

    with pytest.raises(KeyError):
        _built_subtasks(config)


@pytest.mark.parametrize("name", ["a.b", "", "a b", "a[0]"])
def test_name_with_non_bare_key_characters_is_rejected(name: str) -> None:
    config = {"actions": {name: {"type": "shell", "cmd": "true"}}}

    with pytest.raises(ValueError, match="must consist only of"):
        _built_subtasks(config)


def test_name_with_bare_key_characters_is_accepted() -> None:
    config = {"actions": {"Run-test_2": {"type": "shell", "cmd": "true"}}}

    assert _built_subtasks(config) == ["actions.Run-test_2"]


class _ReservedKeySubTask(BasicSubTask):
    @configclass
    class Config:
        when: str

    def __init__(self, config: Config):
        self._config = config

    async def execute(self, context: SubTaskContext) -> BasicSubTask.Result:
        return self.Result.SUCCESS


class _FakeEntryPoint:
    name = "reserved"

    @staticmethod
    def load() -> type:
        return _ReservedKeySubTask


def test_subtask_config_with_reserved_key_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(subtasks, "entry_points", lambda group: [_FakeEntryPoint()])
    library = SubTasksLibrary()

    with pytest.raises(RuntimeError, match="reserved config keys: when"):
        library.get("reserved")
