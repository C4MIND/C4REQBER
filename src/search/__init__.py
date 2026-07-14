"""
c4-cdi-turbo: Search Module
Paper search and literature review capabilities
"""
from __future__ import annotations

from src.search.semantic_scholar import (
    SemanticPaper,
    SemanticScholarClient,
    get_semantic_scholar_client,
)


__all__ = [
    "SemanticScholarClient",
    "SemanticPaper",
    "get_semantic_scholar_client",
]
