# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module holding sub-tasks related to files.
"""

import asyncio
from typing import Annotated

from ..config import Doc, configclass
from ..context.template import Template
from . import BasicSubTask, SubTaskContext


class FileWriter(BasicSubTask):
    """
    Writes specified contents to a selected file.
    """

    @configclass
    class Config:
        path: Annotated[Template, Doc("path to the file to save")]
        append: Annotated[
            bool, Doc("if true appends to the file, overwrite it otherwise")
        ] = False
        contents: Annotated[Template, Doc("contents of the file to write")]
        encoding: Annotated[str, Doc("encoding of the file")] = "utf-8"

    def __init__(self, config: Config):
        self._config = config

    def _write_to_file(
        self, path: str, contents: str, context: SubTaskContext
    ) -> BasicSubTask.Result:
        try:
            mode = "ab" if self._config.append else "wb"
            with open(path, mode) as file:
                file.write(contents.encode(self._config.encoding))
        except IOError as ex:
            context.logger.error(f"Failed to write to file {path}: {ex}")
            return self.Result.ERROR

        return self.Result.SUCCESS

    async def execute(self, context: SubTaskContext) -> BasicSubTask.Result:
        path = self._config.path.evaluate(context.parent)
        contents = self._config.contents.evaluate(context.parent)
        result = await asyncio.to_thread(self._write_to_file, path, contents, context)
        return result
