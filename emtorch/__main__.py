# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Main entry point to the application.
"""

import sys

from .cli import Cli


def main() -> int:
    cli = Cli()
    return cli.execute()


if __name__ == "__main__":
    sys.exit(main())
