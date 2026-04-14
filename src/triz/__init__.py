"""TURBO-CDI TRIZ Module"""

from .bridge import (
    C4TrizBridge,
    get_c4_triz_bridge,
    TRIZPrinciple,
    TRIZPrincipleInfo,
    TRIZ_PRINCIPLES,
    C4_TO_TRIZ_MAPPING,
    CONTRADICTION_MATRIX,
)

__all__ = [
    "C4TrizBridge",
    "get_c4_triz_bridge",
    "TRIZPrinciple",
    "TRIZPrincipleInfo",
    "TRIZ_PRINCIPLES",
    "C4_TO_TRIZ_MAPPING",
    "CONTRADICTION_MATRIX",
]
