"""
TURBO-CDI: Patents Module
Patent search and white space analysis
"""

from src.patents.client import (
    PatentSearchClient,
    Patent,
    get_patent_client,
)

__all__ = [
    "PatentSearchClient",
    "Patent",
    "get_patent_client",
]
