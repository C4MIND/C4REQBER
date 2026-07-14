"""Deprecated C4 core module — use src.c4.state and src.c4.engine."""
from __future__ import annotations

from src.c4.engine import C4Path, C4Space  # noqa: F401
from src.c4.state import (  # noqa: F401
    Agency,
    AgencyAxis,
    AgencyPosition,
    C4Operator,
    C4State,
    Scale,
    ScaleAxis,
    Time,
    TimeAxis,
    all_27_states,
    apply_path,
    canonical_path,
    cyclic_distance,
    hamming_distance,
    verify_theorem_11,
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
    "AgencyPosition",
    "C4Operator",
    "all_27_states",
    "apply_path",
    "canonical_path",
    "cyclic_distance",
    "hamming_distance",
    "verify_theorem_11",
]
