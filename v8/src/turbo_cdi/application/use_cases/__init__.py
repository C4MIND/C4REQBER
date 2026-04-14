"""
Application layer for TURBO-CDI v8.4
Use cases orchestrate domain logic and handle cross-cutting concerns.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Protocol, runtime_checkable
from datetime import datetime

from turbo_cdi.domain.entities import KnowledgeCorpus, CorpusId, Anomaly
from turbo_cdi.domain.repositories import DiscoveryRepository
from turbo_cdi.domain.services import AnomalyDetectionService
from turbo_cdi.domain.events import DomainEventPublisher


# Application Exceptions
class ApplicationError(Exception):
    """Base application error"""

    pass


class CorpusNotFoundError(ApplicationError):
    """Corpus not found"""

    pass


class ValidationError(ApplicationError):
    """Input validation error"""

    pass


# DTOs (Data Transfer Objects)
@dataclass
class DiscoverKnowledgeRequest:
    """Request DTO for knowledge discovery"""

    corpus_id: str
    anomaly_threshold: float = 0.7

    def __post_init__(self):
        if not self.corpus_id.strip():
            raise ValidationError("corpus_id cannot be empty")
        if not (0.0 <= self.anomaly_threshold <= 1.0):
            raise ValidationError("anomaly_threshold must be between 0.0 and 1.0")


@dataclass
class DiscoverKnowledgeResponse:
    """Response DTO for knowledge discovery"""

    corpus_id: str
    anomalies: list[AnomalyDTO]
    anomaly_count: int
    processing_time: float
    status: str = "success"


@dataclass
class AnomalyDTO:
    """DTO for anomaly data"""

    id: str
    type: str
    fact_statement: str
    theory_name: str
    conflict_description: str
    criticality: str
    confidence: float
    detected_at: datetime

    @classmethod
    def from_entity(cls, anomaly: Anomaly) -> AnomalyDTO:
        """Convert domain entity to DTO"""
        return cls(
            id=anomaly.id,
            type=anomaly.type.value,
            fact_statement=anomaly.fact_statement,
            theory_name=anomaly.theory_name,
            conflict_description=anomaly.conflict_description,
            criticality=anomaly.criticality.value,
            confidence=anomaly.confidence,
            detected_at=anomaly.detected_at,
        )


# Use Cases
class DiscoverKnowledgeUseCase:
    """
    Use case for discovering knowledge gaps in a corpus.

    Orchestrates the discovery process, handling validation,
    business logic, and data persistence.
    """

    def __init__(
        self,
        anomaly_service: AnomalyDetectionService,
        repository: DiscoveryRepository,
        event_publisher: DomainEventPublisher,
    ):
        self.anomaly_service = anomaly_service
        self.repository = repository
        self.event_publisher = event_publisher

    async def execute(self, request: DiscoverKnowledgeRequest) -> DiscoverKnowledgeResponse:
        """
        Execute the knowledge discovery use case.

        This method orchestrates the entire discovery workflow:
        1. Validate input
        2. Retrieve corpus
        3. Run anomaly detection
        4. Persist results
        5. Return response
        """
        import time

        start_time = time.time()

        try:
            # Step 1: Validate input
            if not request.corpus_id:
                raise ValidationError("corpus_id is required")

            # Step 2: Retrieve corpus
            corpus_id = CorpusId(request.corpus_id)
            corpus = await self.repository.get_corpus(corpus_id)
            if not corpus:
                raise CorpusNotFoundError(f"Corpus {corpus_id} not found")

            # Step 3: Run anomaly detection
            anomalies = await self.anomaly_service.analyze_corpus_for_anomalies(request.corpus_id)

            # Step 4: Update corpus with new anomalies
            updated_corpus = corpus.add_anomalies(anomalies)
            await self.repository.save_corpus(updated_corpus)

            # Step 5: Build response
            processing_time = time.time() - start_time
            anomaly_dtos = [AnomalyDTO.from_entity(a) for a in anomalies]

            return DiscoverKnowledgeResponse(
                corpus_id=request.corpus_id,
                anomalies=anomaly_dtos,
                anomaly_count=len(anomalies),
                processing_time=round(processing_time, 2),
            )

        except Exception as e:
            # Re-raise domain exceptions
            if isinstance(e, (ValidationError, CorpusNotFoundError)):
                raise

            # Wrap unexpected errors
            raise ApplicationError(f"Discovery failed: {str(e)}") from e
