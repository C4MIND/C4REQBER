"""c4reqber CLI package.

The canonical entry point is `src.cli.blast_app:app` (typer) used by the
`blast` console script (pyproject.toml). Legacy argparse helpers (parser.py,
commands.py, utils.py) and the legacy `src.cli.py` wrapper were deleted
in audit 2026-06-22 M-1 — see CHANGELOG v9.14.0 §M-1.
"""
from src.cli.core import format_solution, get_llm_client, print_banner


__all__ = [
    "format_solution",
    "get_llm_client",
    "print_banner",
]
