"""
c4reqber: Mega-Database Integration — Unified Search Interface

Thin compatibility layer over ``src.knowledge.orchestrator.MultiSourceSearcher``.
All business logic, rate limiting, dedup, and source adapters live in
``orchestrator.py`` (25/26 real sources).

This module provides the legacy ``MegaDatabase`` API for backward compatibility.
"""
from __future__ import annotations

import logging
import warnings
from typing import Any


logger = logging.getLogger(__name__)

from src.knowledge.orchestrator import MultiSourceSearcher as _RealSearcher


class LicenseType:
    """Source license classification."""
    FREE = "free"
    RESTRICTED = "restricted"
    PAID = "paid"
    UNKNOWN = "unknown"


class RateLimiter:
    """Simple sliding-window rate limiter."""

    def __init__(self, max_calls: int = 10, period: float = 1.0) -> None:
        import time
        self.max_calls = max_calls
        self.period = period
        self._calls: list[float] = []
        self._time = time

    def acquire(self) -> bool:
        now = self._time.time()
        self._calls = [t for t in self._calls if now - t < self.period]
        if len(self._calls) >= self.max_calls:
            return False
        self._calls.append(now)
        return True

    def wait_available(self) -> None:
        import time
        while not self.acquire():
            time.sleep(self.period / self.max_calls)


SOURCES = [
    "arxiv", "pubmed", "crossref", "semantic_scholar", "openalex",
    "doi", "orcid", "doaj", "europe_pmc", "dblp", "datacite",
    "zenodo", "figshare", "brave", "core", "base", "unpaywall",
    "oa_mg", "lens_org", "inspire_hep", "tavily", "exa",
    "cinii", "github_datasets", "rsci", "scimatic", "arxivgg",
    "crossref_funders", "bibsonomy",
]


class SearchResult(dict):
    """Backward-compatible SearchResult (dict subclass with attribute access).

    Delegates to ``orchestrator.MultiSourceSearcher`` for actual searching.
    """

    def __getattr__(self, name: str) -> Any:
        if name in self:
            return self[name]
        raise AttributeError(name)


class SourceInfo:
    """Backward-compatible SourceInfo."""

    def __init__(
        self,
        name: str = "",
        license_type: str = "unknown",
        commercial_use_allowed: bool = False,
        requires_api_key: bool = False,
    ) -> None:
        self.name = name
        self.license_type = license_type
        self.commercial_use_allowed = commercial_use_allowed
        self.requires_api_key = requires_api_key


class MegaDatabase:
    """Unified search across 26 knowledge sources.

    Thin wrapper around ``MultiSourceSearcher`` (25/26 real adapters).
    24 real + Semantic Scholar. All adapters are real API clients.

    Usage::

        db = MegaDatabase()
        results = await db.search_all("quantum computing", max_per_source=5)
    """

    def __init__(self) -> None:
        self._searcher: _RealSearcher | None = None

    def _get(self) -> _RealSearcher:
        if self._searcher is None:
            self._searcher = _RealSearcher()
        return self._searcher

    async def search_all(
        self,
        query: str,
        max_per_source: int = 5,
    ) -> dict[str, list[dict[str, Any]]]:
        """Search ALL active sources in parallel.

        Returns dict mapping source_id → list of paper dicts.
        """
        result = await self._get().search_all(
            query=query,
            max_per_source=max_per_source,
        )
        # Extract per-source results from orchestrator's response
        sources = result.get("sources", {})
        if isinstance(sources, dict):
            return sources
        return {"all": result.get("papers", [])}

    async def search_papers(
        self,
        query: str,
        max_results: int = 20,
    ) -> list[dict[str, Any]]:
        """Search across ALL sources and deduplicate."""
        per_source = max(5, max_results // 3)
        raw = await self._get().search_all(
            query=query,
            max_per_source=per_source,
        )
        papers = raw.get("papers", []) if isinstance(raw, dict) else []
        # Deduplicate by DOI
        seen: dict[str, dict[str, Any]] = {}
        for p in papers[:max_results]:
            doi = p.get("doi") or p.get("id", "")
            if doi not in seen:
                seen[doi] = p
        return list(seen.values())[:max_results]

    async def get_paper(self, identifier: str) -> dict[str, Any] | None:
        """Get paper by DOI, arXiv ID, or PMID — searches all orchestrator sources.

        Uses ``MultiSourceSearcher.search_all`` to query across all 25+ real
        adapters. Falls back to direct CrossRef/arXiv/PubMed API calls if
        the orchestrator returns no results.
        """
        # Try orchestrator first (25+ sources)
        import asyncio

        searcher = self._get()
        result = await searcher.search_all(query=identifier, max_per_source=5)
        papers = result.get("papers", [])
        if papers:
            for p in papers[:10]:
                pid = p.get("doi") or p.get("id", "") or p.get("arxiv_id", "") or ""
                if identifier in pid:
                    return p
            return papers[0]

        # Fallback: direct API calls
        import re

        if re.match(r"10\.\d{4,}/.+", identifier):
            return await self._fetch_by_doi(identifier)
        if re.match(r"\d{4}\.\d{4,}", identifier):
            return await self._fetch_by_arxiv(identifier)
        return None

    async def _fetch_by_doi(self, doi: str) -> dict[str, Any] | None:
        """Fetch paper by DOI via CrossRef API."""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"https://api.crossref.org/works/{doi}",
                    headers={"User-Agent": "c4reqber/5.4.0 (mailto:research@c4reqber.dev)"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    msg = data.get("message", {})
                    return {
                        "doi": doi,
                        "title": (msg.get("title") or [""])[0],
                        "authors": [a.get("given", "") + " " + a.get("family", "") for a in msg.get("author", [])],
                        "abstract": msg.get("abstract", ""),
                        "year": (msg.get("published-print") or msg.get("issued", {}) or {}).get("date-parts", [[None]])[0][0],
                        "source": "crossref",
                    }
        except Exception:
            logger.warning("CrossRef fetch failed for DOI %s", doi, exc_info=True)
        return None

    async def _fetch_by_arxiv(self, arxiv_id: str) -> dict[str, Any] | None:
        """Fetch paper by arXiv ID via arXiv API."""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"http://export.arxiv.org/api/query?id_list={arxiv_id}&max_results=1",
                )
                if resp.status_code == 200:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(resp.text)
                    ns = {"a": "http://www.w3.org/2005/Atom"}
                    entry = root.find("a:entry", ns)
                    if entry is not None:
                        title_el = entry.find("a:title", ns)
                        return {
                            "arxiv_id": arxiv_id,
                            "title": (title_el.text or "").strip() if title_el is not None else "",
                            "doi": (entry.find('a:link[@title="doi"]', ns) or {}).get("href", ""),  # type: ignore[union-attr,call-overload]
                            "source": "arxiv",
                        }
        except Exception:
            logger.warning("arXiv fetch failed for ID %s", arxiv_id, exc_info=True)
        return None

    async def _fetch_by_pubmed(self, pmid: str) -> dict[str, Any] | None:
        """Fetch paper by PMID via PubMed API."""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json",
                )
                if resp.status_code == 200:
                    data = resp.json()
                    result = data.get("result", {}).get(pmid, {})
                    if result:
                        return {
                            "pmid": pmid,
                            "title": result.get("title", ""),
                            "source": "pubmed",
                        }
        except Exception:
            logger.warning("PubMed fetch failed for PMID %s", pmid, exc_info=True)
        return None

    async def get_author(self, name: str) -> dict[str, Any]:
        """Get author info by name."""
        # Use orchestrator's search to find author papers
        results = await self._get().search_all(query=name, max_per_source=3)
        papers = results.get("papers", [])
        return {
            "name": name,
            "paper_count": len(papers),
            "papers": papers[:10],
        }

    @staticmethod
    def deduplicate(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Remove duplicates by DOI / arXiv ID."""
        seen: dict[str, dict[str, Any]] = {}
        for p in papers:
            key = p.get("doi") or p.get("arxiv_id") or p.get("id", "")
            if key not in seen:
                seen[key] = p
        return list(seen.values())

    async def close(self) -> None:
        """Cleanup (no-op, orchestrator handles lifecycle)."""
        pass

# Backward compatibility alias
MegaDB = MegaDatabase
