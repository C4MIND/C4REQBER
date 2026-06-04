"""L6 Literature Intelligence — backward-compat shim → src.discovery."""
from __future__ import annotations

from src.discovery.already_shifted import AlreadyShiftedDetector
from src.discovery.contradiction import (
    CitationSentimentAnalyzer,
    Claim,
    ClaimExtractor,
    ContradictionDetector,
    ContradictionResult,
)
from src.discovery.paradigm_shift import (
    AnomalyDetector,
    CrisisIndicator,
    ParadigmShiftDetector,
    ScientificClaim,
    TemporalClaimAnalyzer,
)
from src.discovery.temporal_kg import (
    ConsensusEvolution,
    ConsensusQuery,
    TemporalKnowledgeGraph,
    TimeStampedClaim,
)


__all__ = [
    "AlreadyShiftedDetector",
    "Claim",
    "ClaimExtractor",
    "CitationSentimentAnalyzer",
    "ContradictionDetector",
    "ContradictionResult",
    "AnomalyDetector",
    "CrisisIndicator",
    "ParadigmShiftDetector",
    "ScientificClaim",
    "TemporalClaimAnalyzer",
    "ConsensusEvolution",
    "ConsensusQuery",
    "TemporalKnowledgeGraph",
    "TimeStampedClaim",
]
