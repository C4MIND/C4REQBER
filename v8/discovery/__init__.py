from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from .lab import (
    DiscoveryLab,
    KnowledgeCorpus,
    Anomaly,
    Presupposition,
    SynthesizedTheory,
)
from .sources import SourceDiscoveryService
from .operators import apply_transformation, find_shortest_path


@dataclass
class DiscoveryResult:
    """Container for discovery operation results."""

    query: str
    domain: str
    corpus_id: Optional[str] = None
    corpus: Optional[Any] = None
    anomalies: List[Any] = None
    presuppositions: List[Any] = None
    inversions: List[Any] = None
    trajectories: List[Any] = None
    isomorphisms: List[Any] = None
    synthesis: Optional[Any] = None
    gaps: List[Dict] = None
    knowledge_map: Dict = None
    status: str = "pending"


__all__ = [
    "DiscoveryLab",
    "KnowledgeCorpus",
    "DiscoveryResult",
    "SourceDiscoveryService",
    "apply_transformation",
    "find_shortest_path",
    "Anomaly",
    "Presupposition",
    "SynthesizedTheory",
]
