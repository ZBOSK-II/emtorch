# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing specific case instance (with id and data).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from ..arguments import Arguments, RepeatMode

logger = logging.getLogger(__name__)


class CaseData:
    def __init__(self, path: Path):
        self._path = path
        self._id = str(path)
        self._contents: bytes | None = None

    @property
    def path(self) -> Path:
        return self._path

    @property
    def identifier(self) -> str:
        return self._id

    @property
    def contents(self) -> bytes:
        if self._contents is None:
            logger.info(f"Opening {self._path}")
            with self._path.open("rb") as file:
                self._contents = file.read()
        return self._contents


class CaseId:
    def __init__(self, identifier: str, group: str, iteration: int):
        self._group = group
        self._iteration = iteration
        self._id = identifier

    @property
    def unique(self) -> str:
        return self._id

    @property
    def group(self) -> str:
        return self._group

    @property
    def iteration(self) -> int:
        return self._iteration

    def __repr__(self) -> str:
        return self.unique

    @staticmethod
    def builder_from(args: Arguments) -> Callable[[str, int], CaseId]:
        width = max(1, len(str(args.repeats - 1)))

        def builder(group: str, iteration: int) -> CaseId:
            return CaseId(f"{group}[{iteration:0{width}}]", group, iteration)

        return builder

    @staticmethod
    def from_id(identifier: str) -> CaseId:
        return CaseId(identifier, identifier, 0)


class CaseInstance:
    def __init__(self, case_id: CaseId, data: CaseData):
        self._id = case_id
        self._data = data

    @property
    def identifier(self) -> CaseId:
        return self._id

    @property
    def data(self) -> CaseData:
        return self._data

    @staticmethod
    def list_from(args: Arguments) -> list[CaseInstance]:
        data = [CaseData(p) for p in args.data]

        if args.repeats < 2:
            return [CaseInstance(CaseId.from_id(d.identifier), d) for d in data]

        match args.repeat_mode:
            case RepeatMode.AABB:
                pairs = ((d, i) for d in data for i in range(args.repeats))
            case RepeatMode.ABAB:
                pairs = ((d, i) for i in range(args.repeats) for d in data)
            case _:
                raise ValueError(f"Unsupported repeat mode: {args.repeat_mode!r}")

        id_builder = CaseId.builder_from(args)
        return [CaseInstance(id_builder(d.identifier, i + 1), d) for d, i in pairs]
