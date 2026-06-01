# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module holding sub-tasks related to files.
"""

import logging
from typing import Self

from ..config import Config
from ..context import CaseContext
from ..context.template import Template
from ..io.streams import StreamWriter
from .subtask import BasicSubTask


class FileWriter(BasicSubTask):
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self,
        name: str,
        path: Template,
        append: bool,
        lines: list[Template],
        encoding: str,
    ):
        super().__init__(name, logging.getLogger(__name__))

        self._path = path
        self._lines = lines
        self._append = append
        self._encoding = encoding
        self._writer: None | StreamWriter = None

        self._context: CaseContext | None = None

    def basic_start(self, context: CaseContext) -> bool:
        self._context = context
        return True

    def finish(self) -> BasicSubTask.Result:
        assert self._context

        lines = [line.evaluate(self._context) for line in self._lines]
        data = "\n".join(lines).encode(self._encoding)

        path = self._path.evaluate(self._context)

        try:
            with open(path, "wb") as file:
                file.write(data)
        except IOError as ex:
            self.logger.error(f"File write error: {ex}")
            return self.Result.ERROR

        return self.Result.SUCCESS

    @classmethod
    def from_config(cls, name: str, config: Config) -> Self:
        return cls(
            name=name,
            path=Template(config.get_str("path")),
            append=config.get_bool("append", fallback=False),
            lines=[Template(line) for line in config.get_str_list("lines")],
            encoding=config.get_str("encoding", fallback="utf-8"),
        )
