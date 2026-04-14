"""
Simple in-memory repository implementation for TURBO-CDI v8.4
No external database dependencies for initial testing.
"""

from typing import Optional, List, Dict
from turbo_cdi.domain.entities import KnowledgeCorpus, CorpusId
from turbo_cdi.domain.repositories import DiscoveryRepository


class InMemoryDiscoveryRepository(DiscoveryRepository):
    """
    In-memory implementation of DiscoveryRepository for testing.

    Stores corpora in a simple dict. Not thread-safe or persistent.
    """

    def __init__(self):
        self._storage: Dict[str, KnowledgeCorpus] = {}

    async def save_corpus(self, corpus: KnowledgeCorpus) -> None:
        """Save a knowledge corpus"""
        self._storage[corpus.id] = corpus

    async def get_corpus(self, corpus_id: CorpusId) -> Optional[KnowledgeCorpus]:
        """Retrieve a corpus by ID"""
        return self._storage.get(corpus_id)

    async def list_corpuses(self, domain: Optional[str] = None) -> List[KnowledgeCorpus]:
        """List all corpora, optionally filtered by domain"""
        corpora = list(self._storage.values())
        if domain:
            corpora = [c for c in corpora if c.domain == domain]
        return corpora

    async def delete_corpus(self, corpus_id: CorpusId) -> None:
        """Delete a corpus by ID"""
        self._storage.pop(corpus_id, None)

    async def corpus_exists(self, corpus_id: CorpusId) -> bool:
        """Check if corpus exists"""
        return corpus_id in self._storage
