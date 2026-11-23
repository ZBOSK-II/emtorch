# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
SubTasks.monitor readiness tests.
"""

import asyncio
import logging
import re
import time
from pathlib import Path
from typing import Any, Awaitable, Callable, cast

import pytest

from emtorch.context.template import Template
from emtorch.subtasks import (
    BasicSubTask,
    RunMode,
    SubTaskContext,
    SubTaskDelays,
    SubTaskInstance,
    SubTasks,
)
from emtorch.subtasks.process import ProcessResult
from emtorch.subtasks.subprocess import Shell


class _FakeResults:
    def __init__(self) -> None:
        self.collected: list[Any] = []

    def collect(self, result: Any) -> None:
        self.collected.append(result)

    def skip(self) -> None:
        pass


class _FakeCaseContext:
    def __init__(self) -> None:
        self._actions_ended = asyncio.Event()
        self.mapping: dict[str, str] = {}  # read by Template.evaluate
        self.case_aborted = False

    async def wait_for_actions_ended(self) -> None:
        await self._actions_ended.wait()

    def notify_actions_ended(self) -> None:
        self._actions_ended.set()


Body = Callable[[SubTaskContext], Awaitable[None]]


class _FakeSubTask(BasicSubTask):
    def __init__(self, body: Body, signals_ready: bool) -> None:
        self._body = body
        self._signals_ready = signals_ready

    @property
    def signals_ready(self) -> bool:
        return self._signals_ready

    async def execute(self, context: SubTaskContext) -> BasicSubTask.Result:
        await self._body(context)
        return self.Result.SUCCESS


def _instance(
    name: str,
    subtask: Any,
    when: RunMode = RunMode.ALWAYS,
    before: float | None = None,
    results: _FakeResults | None = None,
) -> SubTaskInstance:
    config = SubTaskInstance.Config(
        type="fake", when=when, delays=SubTaskDelays.Config(before=before)
    )
    return SubTaskInstance(
        f"monitoring.{name}", config, subtask, cast(Any, results or _FakeResults())
    )


def _fake(
    name: str, body: Body, signals_ready: bool = False, when: RunMode = RunMode.ALWAYS
) -> SubTaskInstance:
    return _instance(name, _FakeSubTask(body, signals_ready), when)


def _run_monitor(subtasks: list[SubTaskInstance], events: list[str]) -> float:
    """Runs monitoring around no-op actions; returns the time actions started at."""

    async def main() -> float:
        loop = asyncio.get_running_loop()
        start = loop.time()
        context = _FakeCaseContext()
        async with SubTasks("monitoring", subtasks).monitor(cast(Any, context)):
            events.append("actions")
            actions_start = loop.time() - start
            context.notify_actions_ended()
        return actions_start

    return asyncio.run(asyncio.wait_for(main(), 5))


def _shell(cmd: str, **kwargs: Any) -> Shell:
    return Shell(Shell.Config(cmd=Template(cmd), **kwargs))


def _recorder(events: list[str], name: str) -> Body:
    async def body(context: SubTaskContext) -> None:
        events.append(f"{name} started")
        await context.wait_for_actions_ended()

    return body


def test_next_task_starts_only_after_previous_is_ready() -> None:
    events: list[str] = []

    async def first(context: SubTaskContext) -> None:
        events.append("first started")
        await asyncio.sleep(0.05)
        events.append("first ready")
        context.notify_ready()
        await context.wait_for_actions_ended()

    _run_monitor(
        [
            _fake("first", first, signals_ready=True),
            _fake("second", _recorder(events, "second")),
        ],
        events,
    )

    assert events == ["first started", "first ready", "second started", "actions"]


def test_non_signaling_tasks_are_ready_when_started() -> None:
    events: list[str] = []

    _run_monitor(
        [_fake("a", _recorder(events, "a")), _fake("b", _recorder(events, "b"))],
        events,
    )

    assert events == ["a started", "b started", "actions"]


def test_task_finishing_without_ready_unblocks_next() -> None:
    events: list[str] = []

    async def quiet(_context: SubTaskContext) -> None:
        events.append("quiet finished")

    _run_monitor(
        [
            _fake("quiet", quiet, signals_ready=True),
            _fake("next", _recorder(events, "next")),
        ],
        events,
    )

    assert events == ["quiet finished", "next started", "actions"]


def test_skipped_task_unblocks_next() -> None:
    events: list[str] = []

    _run_monitor(
        [
            _fake("skipped", _recorder(events, "skipped"), when=RunMode.NEVER),
            _fake("next", _recorder(events, "next")),
        ],
        events,
    )

    assert events == ["next started", "actions"]


def test_shell_ready_pattern_delays_next_task() -> None:
    shell = _shell(
        "echo start; sleep 0.1; echo ready-now",
        timeout=5,
        ready_pattern=re.compile(r"ready-\w+"),
    )
    events: list[str] = []

    actions_start = _run_monitor(
        [_instance("shell", shell), _fake("next", _recorder(events, "next"))], events
    )

    assert events == ["next started", "actions"]
    assert actions_start >= 0.1


def test_non_opted_task_delay_does_not_hold_back_next() -> None:
    events: list[str] = []
    delayed = _instance(
        "delayed", _FakeSubTask(_recorder(events, "delayed"), False), before=0.05
    )

    _run_monitor([delayed, _fake("next", _recorder(events, "next"))], events)

    assert events[0] == "next started"


@pytest.mark.parametrize(
    "pattern, opted_in",
    [(None, False), (re.compile("x"), True), (re.compile(""), True)],
)
def test_shell_opts_in_when_ready_pattern_set(
    pattern: re.Pattern[str] | None, opted_in: bool
) -> None:
    assert _shell("true", ready_pattern=pattern).signals_ready == opted_in


def test_ready_timeout_kills_program_and_releases_next_task() -> None:
    shell = _shell(
        "echo started; sleep 10; echo done",
        timeout=20,
        ready_pattern=re.compile("never"),
        ready_timeout=0.1,
    )
    results = _FakeResults()
    events: list[str] = []

    _run_monitor(
        [
            _instance("shell", shell, results=results),
            _fake("next", _recorder(events, "next")),
        ],
        events,
    )

    assert events == ["next started", "actions"]
    assert results.collected == [ProcessResult.NOT_READY]


def test_ready_is_logged_only_when_signalled(caplog: pytest.LogCaptureFixture) -> None:
    async def signals(context: SubTaskContext) -> None:
        context.notify_ready()

    async def silent(_context: SubTaskContext) -> None:
        pass

    caplog.set_level(logging.INFO)
    _run_monitor(
        [
            _fake("signals", signals, signals_ready=True),
            _fake("plain", silent),
            _fake("skipped", silent, signals_ready=True, when=RunMode.NEVER),
            _fake("silent", silent, signals_ready=True),
        ],
        [],
    )

    messages = [(r.levelno, r.getMessage()) for r in caplog.records]
    ready = [m for _, m in messages if m.startswith("Ready")]
    warnings = [m for level, m in messages if level == logging.WARNING]
    assert ready == ["Ready monitoring.signals"]
    assert warnings == ["monitoring.silent finished without becoming ready"]


def test_ready_line_printed_right_before_exit_is_matched() -> None:
    shell = _shell("echo ready", timeout=5, ready_pattern=re.compile("ready"))
    for _ in range(20):
        events: list[str] = []
        _run_monitor([_instance("shell", shell)], events)
        assert events == ["actions"]


def test_not_ready_kill_stops_program_children(tmp_path: Path) -> None:
    marker = tmp_path / "marker"
    shell = _shell(
        f"(sleep 0.5; touch {marker}) & sleep 10",
        timeout=20,
        ready_pattern=re.compile("never"),
        ready_timeout=0.1,
    )

    _run_monitor([_instance("shell", shell)], [])
    time.sleep(0.8)

    assert not marker.exists()


def test_output_reading_errors_are_not_swallowed() -> None:
    shell = _shell(
        "head -c 200000 /dev/zero | tr '\\0' x",
        timeout=5,
        ready_pattern=re.compile("never"),
    )

    with pytest.raises(ExceptionGroup) as error:
        _run_monitor([_instance("shell", shell)], [])

    assert error.group_contains(ValueError)
