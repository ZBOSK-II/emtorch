# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Provides Template class based on string.Template ($-string) but case-sensitive.
"""

from re import RegexFlag
from string import Template as StringTemplate

from . import CaseContext


class Template(StringTemplate):
    idpattern = r"[A-Za-z][_A-Za-z0-9]*"
    flags = RegexFlag(0)

    def evaluate(self, context: CaseContext) -> str:
        return self.safe_substitute(
            EMTORCH_CASE_ID=context.case.identifier.unique,
            EMTORCH_DATA_PATH=str(context.case.data.path),
            EMTORCH_DATA_FILENAME=context.case.data.path.name,
        )
