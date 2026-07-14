"""Deprecated C4 state module — use src.c4.state and src.c4.engine."""
from __future__ import annotations

from src.c4.engine import C4Path, C4Space  # noqa: F401
from src.c4.state import (  # noqa: F401
    Agency,
    AgencyAxis,
    C4Operator,
    C4State,
    Scale,
    ScaleAxis,
    Time,
    TimeAxis,
)


__all__ = [
    "C4State",
    "C4Space",
    "C4Path",
    "Time",
    "Scale",
    "Agency",
    "TimeAxis",
    "ScaleAxis",
    "AgencyAxis",
    "C4Operator",
]
