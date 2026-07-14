"""
c4-cdi-turbo Knowledge Module — Unified Academic Search

Mega-Database Integration for 30+ sources with:
- Async HTTP clients (httpx)
- Rate limiting per source
- Deduplication by DOI/arXiv ID
- License compliance checker
"""

from __future__ import annotations

from .arxiv_client import ArxivClient, AsyncArxivClient
from .base_client import AsyncBASEClient, BASEClient
from .cinii_client import AsyncCiNiiClient, CiNiiClient
from .crossref_client import CrossRefClient, SyncCrossRefClient
from .dataset_clients import FigshareClient, ZenodoClient
from .github_client import GitHubSearchClient
from .mega_db import MegaDatabase, SearchResult, SourceInfo
from .orcid_client import AsyncORCIDClient, ORCIDClient
from .preprint_clients import BioRxivClient, MedRxivClient
from .pubmed_client import AsyncPubMedClient, PubMedClient
from .rsci_client import AsyncRSCIClient, RSCIClient
from .semantic_scholar import SemanticScholarClient, SyncSemanticScholarClient


__all__ = [
    "MegaDatabase",
    "SearchResult",
    "SourceInfo",
    "ArxivClient",
    "AsyncArxivClient",
    "PubMedClient",
    "AsyncPubMedClient",
    "ORCIDClient",
    "AsyncORCIDClient",
    "SemanticScholarClient",
    "SyncSemanticScholarClient",
    "CrossRefClient",
    "SyncCrossRefClient",
    "BioRxivClient",
    "MedRxivClient",
    "GitHubSearchClient",
    "ZenodoClient",
    "FigshareClient",
    "CiNiiClient",
    "AsyncCiNiiClient",
    "RSCIClient",
    "AsyncRSCIClient",
    "BASEClient",
    "AsyncBASEClient",
]
