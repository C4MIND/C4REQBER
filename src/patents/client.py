"""
C4REQBER: Patent Search Integration (Updated)
Unified patent search with USPTO real API + demo fallback.
"""

from __future__ import annotations

from src.patents.uspto_client import Patent, PatentSearchClient, USPTOClient, get_patent_client


__all__ = ["PatentSearchClient", "USPTOClient", "Patent", "get_patent_client"]
