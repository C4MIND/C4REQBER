"""
Data Transfer Objects (DTOs) for TURBO-CDI v8.4 Application Layer
Handles data serialization and API boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum

from turbo_cdi.domain.entities import KnowledgeCorpus, Anomaly
from turbo_cdi.domain.entities.advanced import (
    Presupposition,
    Transformation,
    PresuppositionType,
    TransformationType,
)


# Base DTO Response
@dataclass
class BaseResponse:
    """Base response structure"""

    status: str = "success"
    message: Optional[str] = None
    timestamp: datetime = datetime.now()


# Corpus DTOs
@dataclass
class CorpusSummaryDTO:
    """Summary view of a corpus for list operations"""

    id: str
    name: str
    domain: str
    subdomains: List[str]
    fact_count: int
    theory_count: int
    anomaly_count: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, corpus: KnowledgeCorpus) -> CorpusSummaryDTO:
        """Convert domain entity to DTO"""
        return cls(
            id=corpus.id,
            name=corpus.name,
            domain=corpus.domain,
            subdomains=list(corpus.subdomains),
            fact_count=corpus.fact_count,
            theory_count=len(corpus.theories),
            anomaly_count=len(corpus.anomalies),
            created_at=corpus.created_at,
            updated_at=corpus.updated_at,
        )


@dataclass
class CorpusDetailDTO:
    """Detailed view of a corpus for retrieval operations"""

    id: str
    name: str
    domain: str
    subdomains: List[str]
    epoch_end: str
    facts: List[FactDTO]
    theories: List[TheoryDTO]
    anomalies: List[AnomalyDTO]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, corpus: KnowledgeCorpus) -> CorpusDetailDTO:
        """Convert domain entity to DTO"""
        return cls(
            id=corpus.id,
            name=corpus.name,
            domain=corpus.domain,
            subdomains=list(corpus.subdomains),
            epoch_end=corpus.epoch_end,
            facts=[FactDTO.from_entity(f) for f in corpus.facts],
            theories=[TheoryDTO.from_entity(t) for t in corpus.theories],
            anomalies=[AnomalyDTO.from_entity(a) for a in corpus.anomalies],
            created_at=corpus.created_at,
            updated_at=corpus.updated_at,
        )


@dataclass
class FactDTO:
    """DTO for knowledge facts"""

    id: str
    statement: str
    source: str
    year: Optional[int]
    domain: str
    confidence: float

    @classmethod
    def from_entity(cls, fact) -> FactDTO:
        """Convert domain fact to DTO"""
        return cls(
            id=fact.id,
            statement=fact.statement,
            source=fact.source,
            year=getattr(fact, "year", None),
            domain=fact.domain,
            confidence=getattr(fact, "confidence", 1.0),
        )


@dataclass
class TheoryDTO:
    """DTO for theories"""

    id: str
    name: str
    principles: List[str]
    equations: List[str]

    @classmethod
    def from_entity(cls, theory) -> TheoryDTO:
        """Convert domain theory to DTO"""
        return cls(
            id=theory.id,
            name=theory.name,
            principles=getattr(list(theory.principles), "principles", list(theory.principles)),
            equations=list(getattr(theory, "equations", [])),
        )


@dataclass
class AnomalyDTO:
    """DTO for knowledge anomalies"""

    id: str
    type: str
    fact_statement: str
    theory_name: str
    conflict_description: str
    criticality: str
    confidence: float
    detected_at: datetime

    @classmethod
    def from_entity(cls, anomaly) -> AnomalyDTO:
        """Convert domain anomaly to DTO"""
        return cls(
            id=anomaly.id,
            type=anomaly.type.value if hasattr(anomaly.type, "value") else str(anomaly.type),
            fact_statement=anomaly.fact_statement,
            theory_name=anomaly.theory_name,
            conflict_description=anomaly.conflict_description,
            criticality=anomaly.criticality.value
            if hasattr(anomaly.criticality, "value")
            else str(anomaly.criticality),
            confidence=anomaly.confidence,
            detected_at=anomaly.detected_at,
        )


# Presupposition DTOs
@dataclass
class PresuppositionDTO:
    """DTO for presuppositions"""

    id: str
    theory_id: str
    theory_name: str
    statement: str
    type: str
    confidence: float
    discovered_at: datetime

    @classmethod
    def from_entity(cls, presupposition: Presupposition) -> PresuppositionDTO:
        """Convert domain presupposition to DTO"""
        return cls(
            id=presupposition.id,
            theory_id=presupposition.theory_id,
            theory_name=presupposition.theory_name,
            statement=presupposition.statement,
            type=presupposition.type.value,
            confidence=presupposition.confidence,
            discovered_at=presupposition.discovered_at,
        )


# Transformation DTOs
@dataclass
class TransformationDTO:
    """DTO for cognitive transformations"""

    id: str
    type: str
    input_concept: str
    output_concept: str
    domain: str
    operator: str
    resonance: float
    effectiveness: float
    created_at: datetime

    @classmethod
    def from_entity(cls, transformation: Transformation) -> TransformationDTO:
        """Convert domain transformation to DTO"""
        return cls(
            id=transformation.id,
            type=transformation.type.value,
            input_concept=transformation.input_concept,
            output_concept=transformation.output_concept,
            domain=transformation.domain,
            operator=transformation.operator,
            resonance=transformation.resonance,
            effectiveness=transformation.effectiveness,
            created_at=transformation.created_at,
        )


# Request DTOs
@dataclass
class CreateCorpusRequestDTO:
    """Request for creating a new corpus"""

    id: str
    name: str
    domain: str
    subdomains: Optional[List[str]] = None
    epoch_end: str = "2024"

    def __post_init__(self):
        if not self.id.strip():
            raise ValueError("Corpus ID cannot be empty")
        if not self.name.strip():
            raise ValueError("Corpus name cannot be empty")
        if not self.domain.strip():
            raise ValueError("Domain cannot be empty")


@dataclass
class DiscoverKnowledgeRequestDTO:
    """Request for knowledge discovery"""

    corpus_id: str
    anomaly_threshold: float = 0.7
    max_analysis_time: int = 300  # seconds

    def __post_init__(self):
        if not self.corpus_id.strip():
            raise ValueError("Corpus ID cannot be empty")
        if not (0.0 <= self.anomaly_threshold <= 1.0):
            raise ValueError("Anomaly threshold must be between 0.0 and 1.0")
        if self.max_analysis_time <= 0:
            raise ValueError("Max analysis time must be positive")


@dataclass
class AnalyzePresuppositionsRequestDTO:
    """Request for presupposition analysis"""

    theory_id: str
    theory_text: str
    analysis_depth: str = "standard"  # "basic", "standard", "deep"

    def __post_init__(self):
        if not self.theory_id.strip():
            raise ValueError("Theory ID cannot be empty")
        if not self.theory_text.strip():
            raise ValueError("Theory text cannot be empty")
        if self.analysis_depth not in ["basic", "standard", "deep"]:
            raise ValueError("Invalid analysis depth")


@dataclass
class ApplyTransformationRequestDTO:
    """Request for cognitive transformation"""

    input_concept: str
    transformation_type: str  # "invert", "bridge", "synthesize", "abstract", "concretize"
    domain: str
    operator: Optional[str] = None

    def __post_init__(self):
        if not self.input_concept.strip():
            raise ValueError("Input concept cannot be empty")
        if not self.domain.strip():
            raise ValueError("Domain cannot be empty")
        if self.transformation_type not in [
            "invert",
            "bridge",
            "synthesize",
            "abstract",
            "concretize",
        ]:
            raise ValueError("Invalid transformation type")


# Response DTOs
@dataclass
class CorpusResponseDTO(BaseResponse):
    """Response for corpus operations"""

    corpus: Optional[CorpusDetailDTO] = None


@dataclass
class CorpusListResponseDTO(BaseResponse):
    """Response for corpus list operations"""

    corpora: List[CorpusSummaryDTO] = field(default_factory=list)
    total_count: int = 0


@dataclass
class DiscoveryResponseDTO(BaseResponse):
    """Response for knowledge discovery"""

    corpus_id: str = ""
    anomalies: List[AnomalyDTO] = field(default_factory=list)
    anomaly_count: int = 0
    processing_time: float = 0.0


@dataclass
class PresuppositionAnalysisResponseDTO(BaseResponse):
    """Response for presupposition analysis"""

    theory_id: str = ""
    presuppositions: List[PresuppositionDTO] = field(default_factory=list)
    analysis_score: float = 0.0


@dataclass
class TransformationResponseDTO(BaseResponse):
    """Response for cognitive transformation"""

    transformation: Optional[TransformationDTO] = None
    transformation_applied: bool = False


@dataclass
class HealthCheckResponseDTO(BaseResponse):
    """Response for health check operations"""

    services: dict[str, str] = field(default_factory=dict)
    overall_health: str = "unknown"
