"""
In-Memory repository implementations for testing and development.
Thread-safe implementations without external dependencies.
"""

from typing import Optional, List, Dict, Any
import asyncio
from datetime import datetime
from turbo_cdi.domain.entities import KnowledgeCorpus, CorpusId, Fact, Theory
from turbo_cdi.domain.entities.advanced import (
    Presupposition,
    PresuppositionId,
    Transformation,
    TransformationId,
)
from turbo_cdi.domain.repositories import (
    DiscoveryRepository,
    PresuppositionRepository,
    TransformationRepository,
)


class InMemoryDiscoveryRepository(DiscoveryRepository):
    """In-memory implementation of DiscoveryRepository for testing"""

    def __init__(self):
        self._corpora: Dict[str, KnowledgeCorpus] = {}
        self._lock = asyncio.Lock()

    async def save_corpus(self, corpus: KnowledgeCorpus) -> None:
        async with self._lock:
            self._corpora[corpus.id] = corpus._replace(updated_at=datetime.now())

    async def get_corpus(self, corpus_id: CorpusId) -> Optional[KnowledgeCorpus]:
        return self._corpora.get(str(corpus_id))

    async def list_corpuses(self, domain: Optional[str] = None) -> List[KnowledgeCorpus]:
        corpora = list(self._corpora.values())
        if domain:
            corpora = [c for c in corpora if c.domain.lower() == domain.lower()]
        return sorted(corpora, key=lambda c: c.created_at, reverse=True)

    async def delete_corpus(self, corpus_id: CorpusId) -> None:
        async with self._lock:
            if str(corpus_id) in self._corpora:
                del self._corpora[str(corpus_id)]

    async def corpus_exists(self, corpus_id: CorpusId) -> bool:
        return str(corpus_id) in self._corpora

    async def health_check(self) -> dict:
        return {
            "status": "healthy",
            "type": "in_memory",
            "items": len(self._corpora),
            "message": "In-memory repository operational",
        }


class InMemoryPresuppositionRepository(PresuppositionRepository):
    """In-memory implementation of PresuppositionRepository for testing"""

    def __init__(self):
        self._presuppositions: Dict[str, Presupposition] = {}
        self._lock = asyncio.Lock()

    async def save_presupposition(self, presupposition: Presupposition) -> None:
        async with self._lock:
            self._presuppositions[str(presupposition.id)] = presupposition

    async def get_presupposition(self, p_id: PresuppositionId) -> Optional[Presupposition]:
        return self._presuppositions.get(str(p_id))

    async def list_presuppositions_by_theory(self, theory_id: str) -> List[Presupposition]:
        return [p for p in self._presuppositions.values() if p.theory_id == theory_id]

    async def list_presuppositions_by_type(self, p_type) -> List[Presupposition]:
        return [p for p in self._presuppositions.values() if p.type == p_type]

    async def delete_presupposition(self, p_id: PresuppositionId) -> None:
        async with self._lock:
            if str(p_id) in self._presuppositions:
                del self._presuppositions[str(p_id)]

    async def find_contradictory_presuppositions(self):
        # Simplified implementation - no contradictions detected
        return []


class InMemoryTransformationRepository(TransformationRepository):
    """In-memory implementation of TransformationRepository for testing"""

    def __init__(self):
        self._transformations: Dict[str, Transformation] = {}
        self._lock = asyncio.Lock()

    async def save_transformation(self, transformation: Transformation) -> None:
        async with self._lock:
            self._transformations[str(transformation.id)] = transformation

    async def get_transformation(self, t_id: TransformationId) -> Optional[Transformation]:
        return self._transformations.get(str(t_id))

    async def list_transformations_by_domain(self, domain: str) -> List[Transformation]:
        return [t for t in self._transformations.values() if t.domain == domain]

    async def list_transformations_by_type(self, t_type) -> List[Transformation]:
        return [t for t in self._transformations.values() if t.type == t_type]

    async def get_most_effective_transformations(self, limit: int = 10) -> List[Transformation]:
        sorted_transforms = sorted(
            self._transformations.values(),
            key=lambda t: (t.effectiveness + t.resonance) / 2,
            reverse=True,
        )
        return sorted_transforms[:limit]

    async def delete_transformation(self, t_id: TransformationId) -> None:
        async with self._lock:
            if str(t_id) in self._transformations:
                del self._transformations[str(t_id)]


# Factory function for test repositories
def create_test_repositories() -> Dict[str, Any]:
    """Create set of in-memory repositories for testing"""
    return {
        "discovery": InMemoryDiscoveryRepository(),
        "presupposition": InMemoryPresuppositionRepository(),
        "transformation": InMemoryTransformationRepository(),
    }
