#!/usr/bin/env python3
"""
C4REQBER CLI v2.1
Command-line interface with LLM synthesis

Compatibility wrapper — imports from cli package.
"""
from __future__ import annotations

import sys
from typing import Any

from src.cli.commands import build_parser, dispatch


def main() -> Any:
    """Main CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return dispatch(args)


if __name__ == "__main__":
    sys.exit(main())
