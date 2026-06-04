"""Contradiction Miner — extract claims and detect contradictions"""

from .detector import Contradiction, ContradictionDetector, detect_contradictions
from .extractor import Claim, ClaimExtractor, extract_claims
from .router import router as contradiction_miner_router


__all__ = [
    "ClaimExtractor",
    "Claim",
    "extract_claims",
    "ContradictionDetector",
    "Contradiction",
    "detect_contradictions",
    "contradiction_miner_router",
]
