# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Main module of the application.
"""

import asyncio
import logging
from typing import Any

from .arguments import Arguments
from .case import Case
from .case.instance import CaseInstance
from .context import Context
from .results import ResultsCollector

logger = logging.getLogger(__name__)


def execute(args: Arguments, config: dict[str, Any]) -> ResultsCollector:
    with asyncio.Runner() as runner:
        runner.get_loop().set_task_factory(asyncio.eager_task_factory)

        with Context(config, args) as context:
            case = Case.create(context)

            instances = CaseInstance.list_from(args)
            for index, instance in enumerate(instances):
                with context.enter_case(instance) as case_context:
                    logger.info(
                        f"Progress [{index+1}/{len(instances)}] - {case_context.case.identifier}"
                    )
                    runner.run(case.execute(case_context))

            return context.results
