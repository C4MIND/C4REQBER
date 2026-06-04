"""Paradigm Shift Detection Module"""

from src.paradigm.detector import (  # type: ignore[attr-defined]
    Anomaly,
    DetectRequest,
    DetectResult,
    ParadigmShiftDetector,
    ParadigmShiftSignal,
)
from src.paradigm.router import router


__all__ = [
    "ParadigmShiftDetector",
    "DetectRequest",
    "DetectResult",
    "ParadigmShiftSignal",
    "Anomaly",
    "router",
]
