"""
Additional domain entities for TURBO-CDI v8.4
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, NewType, List
from enum import Enum

# Additional Types
PresuppositionId = NewType("PresuppositionId", str)
TransformationId = NewType("TransformationId", str)


class PresuppositionType(Enum):
    """Types of presuppositions (hidden assumptions)"""

    ONTOLOGICAL = "ontological"  # Assumptions about existence/nature
    EPISTEMOLOGICAL = "epistemological"  # Assumptions about knowledge
    METHODOLOGICAL = "methodological"  # Assumptions about methods
    AXIOLOGICAL = "axiological"  # Assumptions about values


class TransformationType(Enum):
    """Types of cognitive transformations"""

    INVERT = "invert"  # Invert a presupposition
    BRIDGE = "bridge"  # Create interdisciplinary bridge
    SYNTHESIZE = "synthesize"  # Combine multiple concepts
    ABSTRACT = "abstract"  # Move to higher abstraction level
    CONCRETIZE = "concretize"  # Move to lower abstraction level


@dataclass(frozen=True)
class Presupposition:
    """Domain entity representing hidden assumptions in theories"""

    id: PresuppositionId
    theory_id: str
    theory_name: str
    statement: str
    type: PresuppositionType
    confidence: float = 0.8
    discovered_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.statement.strip():
            raise ValueError("Presupposition statement cannot be empty")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")

    def invert(self) -> Presupposition:
        """Create inverted version of this presupposition"""
        inverted_statement = f"NOT: {self.statement}"
        return Presupposition(
            id=PresuppositionId(f"{self.id}_inverted"),
            theory_id=self.theory_id,
            theory_name=self.theory_name,
            statement=inverted_statement,
            type=self.type,
            confidence=self.confidence * 0.8,  # Slightly less confident
            discovered_at=datetime.now(),
        )


@dataclass(frozen=True)
class Transformation:
    """Domain entity representing cognitive transformations"""

    id: TransformationId
    type: TransformationType
    input_concept: str
    output_concept: str
    domain: str
    operator: str  # QZRF operator name
    resonance: float
    effectiveness: float
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.input_concept.strip() or not self.output_concept.strip():
            raise ValueError("Input and output concepts cannot be empty")
        if not (0.0 <= self.resonance <= 1.0):
            raise ValueError("Resonance must be between 0.0 and 1.0")
        if not (0.0 <= self.effectiveness <= 1.0):
            raise ValueError("Effectiveness must be between 0.0 and 1.0")


class DomainEvent(ABC):
    """Base class for domain events"""

    event_id: str
    event_type: str
    timestamp: datetime
    version: int

    def __init__(self, event_id: str = None, event_type: str = None):
        self.event_id = event_id or f"event_{int(time.time() * 1000000) % 1000000}"
        self.event_type = event_type or "domain_event"
        self.timestamp = datetime.now()
        self.version = 1

        if not self.event_id:
            raise ValueError("Event ID cannot be empty")


@dataclass(frozen=True)
class CorpusCreated(DomainEvent):
    """Event fired when a new knowledge corpus is created"""

    corpus_id: str
    name: str
    domain: str

    def __post_init__(self):
        super().__init__(event_id=f"corpus_created_{int(time.time())}", event_type="corpus_created")
        if not self.corpus_id or not self.name or not self.domain:
            raise ValueError("Corpus ID, name, and domain are required")


@dataclass(frozen=True)
class AnomalyDetected(DomainEvent):
    """Event fired when knowledge anomalies are detected"""

    corpus_id: str
    anomaly_count: int
    anomalies: tuple  # frozenset converted to tuple for serialization

    def __post_init__(self):
        super().__init__(
            event_id=f"anomaly_detected_{int(time.time())}", event_type="anomaly_detected"
        )


@dataclass(frozen=True)
class TransformationApplied(DomainEvent):
    """Event fired when a cognitive transformation is applied"""

    transformation_id: str
    from_concept: str
    to_concept: str
    domain: str
    effectiveness: float

    def __post_init__(self):
        super().__init__(
            event_id=f"transformation_applied_{int(time.time())}",
            event_type="transformation_applied",
        )


@dataclass(frozen=True)
class PresuppositionDiscovered(DomainEvent):
    """Event fired when new presuppositions are discovered"""

    theory_id: str
    presupposition_count: int
    types_discovered: tuple  # tuple of PresuppositionType values

    def __post_init__(self):
        super().__init__(
            event_id=f"presupposition_discovered_{int(time.time())}",
            event_type="presupposition_discovered",
        )
