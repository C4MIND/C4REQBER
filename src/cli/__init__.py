"""c4reqber CLI package.

The canonical entry point is `src.cli.blast_app:app` (typer) used by the
`blast` console script (pyproject.toml). Legacy argparse helpers (parser.py,
commands.py) were deleted in audit 2026-06-22 M-1.
"""
from src.cli.core import format_solution, get_llm_client, print_banner
from src.cli.utils import cmd_operators, cmd_test_llm


__all__ = [
    "cmd_operators",
    "cmd_test_llm",
    "format_solution",
    "get_llm_client",
    "print_banner",
]
