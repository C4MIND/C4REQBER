"""
Domain entities for TURBO-CDI v8.4
Pure business objects with business rules and validation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, NewType, Protocol, runtime_checkable
from enum import Enum

# Domain Types
CorpusId = NewType("CorpusId", str)
FactId = NewType("FactId", str)
TheoryId = NewType("TheoryId", str)
AnomalyId = NewType("AnomalyId", str)


class AnomalyType(Enum):
    """Types of knowledge anomalies"""

    EMPIRICAL = "empirical"  # Observation contradicts theory
    THEORETICAL = "theoretical"  # Internal theory contradiction
    METHODOLOGICAL = "methodological"  # Method vs. claimed result
    ONTOLOGICAL = "ontological"  # Fundamental assumption conflict


class Severity(Enum):
    """Anomaly severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Value Objects
@dataclass(frozen=True)
class Fact:
    """Immutable fact entity"""

    id: FactId
    statement: str
    source: str
    year: Optional[int]
    domain: str
    confidence: float = 1.0

    def __post_init__(self):
        if not self.statement.strip():
            raise ValueError("Fact statement cannot be empty")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")


@dataclass(frozen=True)
class Theory:
    """Immutable theory entity"""

    id: TheoryId
    name: str
    principles: tuple[str, ...]  # Immutable tuple
    equations: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("Theory name cannot be empty")
        if not self.principles:
            raise ValueError("Theory must have at least one principle")


@dataclass(frozen=True)
class Anomaly:
    """Immutable anomaly entity"""

    id: AnomalyId
    corpus_id: CorpusId
    type: AnomalyType
    fact_statement: str
    theory_name: str
    conflict_description: str
    criticality: Severity
    confidence: float = 0.8
    detected_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.conflict_description.strip():
            raise ValueError("Conflict description cannot be empty")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")


# Core Entity
@dataclass
class KnowledgeCorpus:
    """
    Core domain entity representing a bounded knowledge space.

    This is the central entity in the discovery domain.
    All operations revolve around analyzing and evolving corpora.
    """

    id: CorpusId
    name: str
    domain: str
    subdomains: tuple[str, ...] = field(default_factory=tuple)
    epoch_end: str = "2024"  # Knowledge cutoff date
    facts: frozenset[Fact] = field(default_factory=frozenset)
    theories: frozenset[Theory] = field(default_factory=frozenset)
    anomalies: frozenset[Anomaly] = field(default_factory=frozenset)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("Corpus name cannot be empty")
        if not self.domain.strip():
            raise ValueError("Corpus domain cannot be empty")

    # Pure functions for evolution
    def add_fact(self, fact: Fact) -> KnowledgeCorpus:
        """Return new corpus with added fact"""
        return KnowledgeCorpus(
            id=self.id,
            name=self.name,
            domain=self.domain,
            subdomains=self.subdomains,
            epoch_end=self.epoch_end,
            facts=self.facts | {fact},
            theories=self.theories,
            anomalies=self.anomalies,
            created_at=self.created_at,
            updated_at=datetime.now(),
        )

    def add_theory(self, theory: Theory) -> KnowledgeCorpus:
        """Return new corpus with added theory"""
        return KnowledgeCorpus(
            id=self.id,
            name=self.name,
            domain=self.domain,
            subdomains=self.subdomains,
            epoch_end=self.epoch_end,
            facts=self.facts,
            theories=self.theories | {theory},
            anomalies=self.anomalies,
            created_at=self.created_at,
            updated_at=datetime.now(),
        )

    def add_anomaly(self, anomaly: Anomaly) -> KnowledgeCorpus:
        """Return new corpus with added anomaly"""
        return KnowledgeCorpus(
            id=self.id,
            name=self.name,
            domain=self.domain,
            subdomains=self.subdomains,
            epoch_end=self.epoch_end,
            facts=self.facts,
            theories=self.theories,
            anomalies=self.anomalies | {anomaly},
            created_at=self.created_at,
            updated_at=datetime.now(),
        )

    def add_anomalies(self, anomalies: list[Anomaly]) -> KnowledgeCorpus:
        """Return new corpus with multiple anomalies added"""
        return KnowledgeCorpus(
            id=self.id,
            name=self.name,
            domain=self.domain,
            subdomains=self.subdomains,
            epoch_end=self.epoch_end,
            facts=self.facts,
            theories=self.theories,
            anomalies=self.anomalies | frozenset(anomalies),
            created_at=self.created_at,
            updated_at=datetime.now(),
        )

    # Computed properties
    @property
    def fact_count(self) -> int:
        return len(self.facts)

    @property
    def theory_count(self) -> int:
        return len(self.theories)

    @property
    def anomaly_count(self) -> int:
        return len(self.anomalies)

    @property
    def is_consistent(self) -> bool:
        """Check if corpus has no critical anomalies"""
        return not any(a.criticality == Severity.CRITICAL for a in self.anomalies)
