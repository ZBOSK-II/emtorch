# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module holding sub-tasks related to files.
"""

import logging
import os
from typing import Self

from ..config import Config
from ..context import CaseContext, Context
from ..context.template import Template
from ..io import IOLoop
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
        timeout: float,
        io: IOLoop,
    ):
        super().__init__(name, logging.getLogger(__name__))

        self._path = path
        self._lines = lines
        self._append = append
        self._encoding = encoding
        self._timeout = timeout
        self._io = io
        self._writer: None | StreamWriter = None

    def basic_start(self, context: CaseContext) -> bool:
        lines = [line.evaluate(context) for line in self._lines]
        data = "\n".join(lines).encode(self._encoding)

        path = self._path.evaluate(context)
        mode = ("a" if self._append else "w") + "b"
        flags = os.O_WRONLY | os.O_CREAT | (os.O_APPEND if self._append else os.O_TRUNC)
        try:
            fd = os.open(path, flags, 0o666)
            os.set_blocking(fd, False)
            file = os.fdopen(fd, mode)
        except IOError as ex:
            self.logger.error(f"Open file failed '{path}' - {ex}")
            return False

        self._writer = StreamWriter(self.name, file, data)
        self._io.register(self._writer)

        return True

    def finish(self) -> BasicSubTask.Result:
        assert self._writer

        if self._writer.wait_for_done(self._timeout):
            self.logger.info(f"File written: {self._writer.name()}")
            return self.Result.SUCCESS

        self.logger.error(f"File write timeout: {self._writer.name()}")
        return self.Result.TIMEOUT

    @classmethod
    def from_config(cls, name: str, config: Config, context: Context) -> Self:
        return cls(
            name=name,
            path=Template(config.get_str("path")),
            append=config.get_bool("append", fallback=False),
            lines=[Template(line) for line in config.get_str_list("lines")],
            encoding=config.get_str("encoding", fallback="utf-8"),
            timeout=config.get_float("timeout", fallback=5),
            io=context.worker(IOLoop),
        )
