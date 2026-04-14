"""
Additional application use cases for TURBO-CDI v8.4
"""

from __future__ import annotations

from typing import Optional
from turbo_cdi.application.use_cases import ApplicationError
from turbo_cdi.domain.entities import KnowledgeCorpus, CorpusId
from turbo_cdi.domain.entities.advanced import CorpusCreated
from turbo_cdi.domain.repositories import DiscoveryRepository
from turbo_cdi.domain.factories import KnowledgeCorpusFactory


# Application Exceptions
class CorpusAlreadyExistsError(ApplicationError):
    """Corpus with this ID already exists"""

    pass


# Import local DTOs for now


@dataclass
class CreateCorpusRequest:
    """Request DTO for corpus creation"""

    corpus_id: str
    name: str
    domain: str
    subdomains: Optional[list[str]] = None
    epoch_end: str = "2024"

    def __post_init__(self):
        if not self.corpus_id.strip():
            raise ValueError("corpus_id cannot be empty")
        if not self.name.strip():
            raise ValueError("name cannot be empty")
        if not self.domain.strip():
            raise ValueError("domain cannot be empty")


@dataclass
class CreateCorpusResponse:
    """Response DTO for corpus creation"""

    corpus_id: str
    name: str
    domain: str
    status: str = "created"


# Additional Use Cases
class CreateCorpusUseCase:
    """
    Use case for creating new knowledge corpora.

    Handles validation, creation, and event publishing.
    """

    def __init__(self, repository: DiscoveryRepository):
        self.repository = repository

    async def execute(self, request: CreateCorpusRequest) -> CreateCorpusResponse:
        """
        Execute corpus creation use case.

        Steps:
        1. Validate request
        2. Check if corpus already exists
        3. Create corpus using factory
        4. Save to repository
        5. Publish domain event
        """
        # Validate request
        if not request.corpus_id or not request.name or not request.domain:
            raise ValueError("Invalid request parameters")

        corpus_id = CorpusId(request.corpus_id)

        # Check if corpus already exists
        existing = await self.repository.get_corpus(corpus_id)
        if existing:
            raise CorpusAlreadyExistsError(f"Corpus {corpus_id} already exists")

        # Create corpus using factory
        corpus = KnowledgeCorpusFactory.create_empty(
            corpus_id=request.corpus_id,
            name=request.name,
            domain=request.domain,
            subdomains=request.subdomains,
            epoch_end=request.epoch_end,
        )

        # Save to repository
        await self.repository.save_corpus(corpus)

        # Note: Domain event publishing would be handled by infrastructure layer
        # or through event publishing service injected into use case

        return CreateCorpusResponse(
            corpus_id=request.corpus_id, name=request.name, domain=request.domain
        )
