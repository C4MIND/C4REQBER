"""C4REQBER Verification Module — formal and statistical hypothesis validation."""
from __future__ import annotations

from .rag_retriever import ProofExampleRetriever
from .stats_validator import StatisticalValidator
from .unified_score import (
    BackendResult,
    UnifiedVerificationScore,
    compute_unified_score,
)


__all__ = [
    "StatisticalValidator",
    "ProofExampleRetriever",
    "BackendResult",
    "UnifiedVerificationScore",
    "compute_unified_score",
]
