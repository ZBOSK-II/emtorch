# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing specific case instance (with id and data).
"""

import logging
from dataclasses import dataclass
from pathlib import Path

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


@dataclass
class CaseId:
    group: str
    iteration: int | None

    def __repr__(self) -> str:
        if self.iteration:
            return f"{self.group}[{self.iteration}]"
        return self.group

    @staticmethod
    def from_id(identifier: str) -> CaseId:
        return CaseId(identifier, None)


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

        return [CaseInstance(CaseId(d.identifier, i + 1), d) for d, i in pairs]
