"""
Repository interfaces for domain layer.
Following Repository pattern for data access abstraction.
"""

from abc import ABC, abstractmethod
from typing import Optional, Protocol, runtime_checkable, List
from turbo_cdi.domain.entities import KnowledgeCorpus, CorpusId
from turbo_cdi.domain.entities.advanced import (
    Presupposition,
    Transformation,
    PresuppositionId,
    TransformationId,
    PresuppositionType,
    TransformationType,
)


@runtime_checkable
class DiscoveryRepository(Protocol):
    """
    Repository interface for discovery operations.

    This interface defines the contract for data access operations
    related to knowledge corpora, facts, theories, and anomalies.
    """

    @abstractmethod
    async def save_corpus(self, corpus: KnowledgeCorpus) -> None:
        """Save a knowledge corpus"""
        ...

    @abstractmethod
    async def get_corpus(self, corpus_id: CorpusId) -> Optional[KnowledgeCorpus]:
        """Retrieve a corpus by ID"""
        ...

    @abstractmethod
    async def list_corpuses(self, domain: Optional[str] = None) -> List[KnowledgeCorpus]:
        """List all corpora, optionally filtered by domain"""
        ...

    @abstractmethod
    async def delete_corpus(self, corpus_id: CorpusId) -> None:
        """Delete a corpus by ID"""
        ...

    @abstractmethod
    async def corpus_exists(self, corpus_id: CorpusId) -> bool:
        """Check if corpus exists"""
        ...


@runtime_checkable
class PresuppositionRepository(Protocol):
    """
    Repository interface for presupposition operations.

    Defines data access operations for hidden assumptions in theories.
    """

    @abstractmethod
    async def save_presupposition(self, presupposition: Presupposition) -> None:
        """Save a presupposition"""
        ...

    @abstractmethod
    async def get_presupposition(self, p_id: PresuppositionId) -> Optional[Presupposition]:
        """Retrieve a presupposition by ID"""
        ...

    @abstractmethod
    async def list_presuppositions_by_theory(self, theory_id: str) -> List[Presupposition]:
        """List all presuppositions for a theory"""
        ...

    @abstractmethod
    async def list_presuppositions_by_type(
        self, p_type: PresuppositionType
    ) -> List[Presupposition]:
        """List presuppositions by type"""
        ...

    @abstractmethod
    async def delete_presupposition(self, p_id: PresuppositionId) -> None:
        """Delete a presupposition"""
        ...

    @abstractmethod
    async def find_contradictory_presuppositions(
        self,
    ) -> List[tuple[Presupposition, Presupposition]]:
        """Find presuppositions that contradict each other"""
        ...


@runtime_checkable
class TransformationRepository(Protocol):
    """
    Repository interface for transformation operations.

    Defines data access operations for cognitive transformations.
    """

    @abstractmethod
    async def save_transformation(self, transformation: Transformation) -> None:
        """Save a transformation"""
        ...

    @abstractmethod
    async def get_transformation(self, t_id: TransformationId) -> Optional[Transformation]:
        """Retrieve a transformation by ID"""
        ...

    @abstractmethod
    async def list_transformations_by_domain(self, domain: str) -> List[Transformation]:
        """List transformations for a specific domain"""
        ...

    @abstractmethod
    async def list_transformations_by_type(
        self, t_type: TransformationType
    ) -> List[Transformation]:
        """List transformations by type"""
        ...

    @abstractmethod
    async def get_most_effective_transformations(self, limit: int = 10) -> List[Transformation]:
        """Get transformations ordered by effectiveness"""
        ...

    @abstractmethod
    async def delete_transformation(self, t_id: TransformationId) -> None:
        """Delete a transformation"""
        ...
