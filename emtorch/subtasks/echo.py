# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module containing echo subtask.
"""

from typing import Annotated

from ..config import Doc, configclass
from ..context.template import Template
from . import BasicSubTask, SubTaskContext


class Echo(BasicSubTask):
    """
    Basic echo command, prints to log a provided message.
    """

    @configclass
    class Config:
        message: Annotated[Template, Doc("message to write to log")]

    def __init__(self, config: Config):
        self._config = config

    async def execute(self, context: SubTaskContext) -> BasicSubTask.Result:
        message = self._config.message.evaluate(context.parent)
        context.logger.info(message)
        return self.Result.SUCCESS
