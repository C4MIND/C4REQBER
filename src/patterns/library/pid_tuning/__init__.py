"""
c4-cdi-turbo v6.0 - PID Tuning Pattern
PID controller with Ziegler-Nichols and auto-tuning methods.

Pattern Structure (Christopher Alexander):
- Context: Control systems requiring proportional-integral-derivative feedback
- Forces: Stability vs response time, overshoot vs settling time, manual tuning complexity
- Solution: Automated tuning algorithms with configurable objectives
"""

from __future__ import annotations

from .config import PIDConfig, PIDStructure, TuningMethod
from .core import PIDTuningPattern
from .utils import PIDController


__all__ = [
    "TuningMethod",
    "PIDStructure",
    "PIDConfig",
    "PIDController",
    "PIDTuningPattern",
]
