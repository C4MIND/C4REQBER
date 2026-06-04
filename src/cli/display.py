"""Reqber CLI Display — Backwards-compatible facade.

All components have been split into focused modules:
  - cli.cube_mascot   : CubeMascot, CUBE_STATES, CUBE_COMMENTS
  - cli.header        : C44TCDIHeader
  - cli.layout_manager: LayoutManager
  - cli.timeline      : SessionTimeline
  - cli.beep          : beep()
"""
from __future__ import annotations

from src.cli.beep import beep
from src.cli.cube_mascot import CUBE_COMMENTS, CUBE_STATES, CubeMascot
from src.cli.header import C44TCDIHeader
from src.cli.layout_manager import LayoutManager
from src.cli.timeline import SessionTimeline
from src.terminal_.cyberpunk_theme import CyberpunkTheme as T


# Legacy color aliases (for backwards compat)
GRAY = T.FG_MUTED
GREEN = T.FG_PRIMARY
CYAN = T.FG_SECONDARY
YELLOW = T.FG_WARNING
BLUE = T.FG_SECONDARY
BOLD = T.BOLD
DIM = T.DIM
RESET = T.RESET

__all__ = [
    "GRAY", "GREEN", "CYAN", "YELLOW", "BLUE", "BOLD", "DIM", "RESET",
    "CUBE_STATES", "CUBE_COMMENTS",
    "CubeMascot", "C44TCDIHeader", "LayoutManager", "SessionTimeline", "beep",
]
