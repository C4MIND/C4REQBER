"""
c4-cdi-turbo: Patents Module
Patent search and white space analysis
"""
from __future__ import annotations

from src.patents.client import (
    Patent,
    PatentSearchClient,
    get_patent_client,
)


__all__ = [
    "PatentSearchClient",
    "Patent",
    "get_patent_client",
]
