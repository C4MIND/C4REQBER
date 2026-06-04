"""c4-cdi-turbo CLI package."""
from src.cli.commands import dispatch
from src.cli.core import format_solution, get_llm_client, print_banner
from src.cli.parser import build_parser
from src.cli.utils import cmd_operators, cmd_test_llm


__all__ = [
    "build_parser",
    "cmd_operators",
    "cmd_test_llm",
    "dispatch",
    "format_solution",
    "get_llm_client",
    "print_banner",
]
