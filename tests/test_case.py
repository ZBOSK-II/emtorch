# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
case module tests.
"""

from pathlib import Path

from emtorch.arguments import Arguments, RepeatMode
from emtorch.case.instance import CaseInstance


def _given_data(*args: str) -> Arguments:
    return Arguments(
        data=[Path(p) for p in args],
        output_prefix="",
        config=Path("."),
        repeats=1,
        repeat_mode=RepeatMode.AABB,
        verbose=True,
    )


def _cases_ids(cases: list[CaseInstance]) -> list[str]:
    return [c.identifier.unique for c in cases]


def _data_ids(cases: list[CaseInstance]) -> list[str]:
    return [c.data.identifier for c in cases]


def test_empty_args_builds_empty_list() -> None:
    args = _given_data()

    cases = CaseInstance.list_from(args)

    assert len(cases) == 0


def test_single_item_args_builds_simple_list() -> None:
    args = _given_data("a")

    cases = CaseInstance.list_from(args)

    assert _cases_ids(cases) == ["a"]
    assert _data_ids(cases) == ["a"]


def test_multiple_items_args_builds_list() -> None:
    args = _given_data("a", "b", "c")

    cases = CaseInstance.list_from(args)

    assert _cases_ids(cases) == ["a", "b", "c"]
    assert _data_ids(cases) == ["a", "b", "c"]


def test_repeats_repeat_identifiers() -> None:
    args = _given_data("a", "b", "c")
    args.repeats = 2

    cases = CaseInstance.list_from(args)

    assert _cases_ids(cases) == ["a[1]", "a[2]", "b[1]", "b[2]", "c[1]", "c[2]"]
    assert _data_ids(cases) == ["a", "a", "b", "b", "c", "c"]


def test_repeats_respects_abab_mode() -> None:
    args = _given_data("a", "b", "c")
    args.repeats = 2
    args.repeat_mode = RepeatMode.ABAB

    cases = CaseInstance.list_from(args)

    assert _cases_ids(cases) == ["a[1]", "b[1]", "c[1]", "a[2]", "b[2]", "c[2]"]
    assert _data_ids(cases) == ["a", "b", "c", "a", "b", "c"]


def test_repeats_handles_large_number() -> None:
    args = _given_data("a", "b", "c")
    args.repeats = 200

    cases = CaseInstance.list_from(args)

    assert len(cases) == 600
    assert _cases_ids(cases)[0] == "a[001]"
    assert _cases_ids(cases)[-1] == "c[200]"


def test_repeats_handles_large_number_edge_case() -> None:
    args = _given_data("a", "b", "c")
    args.repeats = 1000

    cases = CaseInstance.list_from(args)

    assert len(cases) == 3000
    assert _cases_ids(cases)[0] == "a[0001]"
    assert _cases_ids(cases)[-1] == "c[1000]"
