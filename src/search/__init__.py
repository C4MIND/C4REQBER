"""
TURBO-CDI: Search Module
Paper search and literature review capabilities
"""

from src.search.semantic_scholar import (
    SemanticScholarClient,
    SemanticPaper,
    get_semantic_scholar_client,
)

__all__ = [
    "SemanticScholarClient",
    "SemanticPaper",
    "get_semantic_scholar_client",
]
