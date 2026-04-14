"""TURBO-CDI: Ultimate CDI-Mega-Algorithm for Scientific Hypothesis Generation"""

__version__ = "2.0.0"
__author__ = "TURBO-CDI Team"

from .core.c4_state import C4State, C4Space
from .core.operators import Operators, C4Operator
from .core.cdi_engine import (
    CDIEngine,
    CDISolution,
    C4Transition,
    PhysicalContradiction,
    ContradictionType,
    EinsteinValidator,
)
from .extractors.contradiction import ContradictionExtractor, ContradictionLibrary

__all__ = [
    "C4State",
    "C4Space",
    "Operators",
    "C4Operator",
    "CDIEngine",
    "CDISolution",
    "C4Transition",
    "PhysicalContradiction",
    "ContradictionType",
    "EinsteinValidator",
    "ContradictionExtractor",
    "ContradictionLibrary",
]
