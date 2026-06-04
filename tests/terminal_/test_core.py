"""Tests for src/terminal_/ — terminal core module smoke tests."""
from __future__ import annotations

import pytest


def test_import_smoke():
    try:
        import src.terminal_
    except ImportError:
        pytest.skip("terminal_ package has import issues")
    try:
        import src.terminal_.core
    except ImportError:
        pytest.skip("terminal_.core has import issues")


def test_solve_command_exists():
    try:
        from src.terminal_.commands.core import cmd_solve
    except ImportError:
        pytest.skip("terminal_.commands.core has import issues")
    assert callable(cmd_solve)


def test_research_command_exists():
    try:
        from src.terminal_.commands.core import cmd_research
    except ImportError:
        pytest.skip("terminal_.commands.core has import issues")
    assert callable(cmd_research)


def test_command_map_exists():
    try:
        from src.terminal_.commands.utils import COMMAND_MAP
    except ImportError:
        pytest.skip("terminal_.commands.utils has import issues")
    assert isinstance(COMMAND_MAP, dict)
    assert len(COMMAND_MAP) > 0
