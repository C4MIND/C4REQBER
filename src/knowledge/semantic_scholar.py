"""
Semantic Scholar API Client — Async HTTP with Rate Limiting

License: ⚠️ Non-Commercial (check use case before commercial deployment)
Coverage: 200M+ papers, 80M+ authors
API: api.semanticscholar.org (API key optional for higher limits)
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any


try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

logger = logging.getLogger("c4_cdi_turbo.knowledge.semanticscholar")


class SemanticScholarClient:
    """
    Async Semantic Scholar API Client.

    License: ⚠️ Non-Commercial — check terms before commercial use
    Coverage: 200M+ papers, 80M+ authors
    Rate Limit: 5k requests/5min without key, higher with key
    """

    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    RATE_LIMIT = 100.0 / 300.0

    DEFAULT_FIELDS = "paperId,title,authors,year,abstract,doi,url,journal,citationCount,referenceCount,publicationDate"

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        if not HAS_HTTPX:
            raise ImportError("httpx required: pip install httpx")

        self.api_key = api_key or os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._last_request: float = 0.0
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> SemanticScholarClient:
        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        self._client = httpx.AsyncClient(timeout=self._timeout, headers=headers)
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()

    async def _rate_limit(self) -> None:
        async with self._lock:
            now = time.monotonic()
            wait_time = self._last_request + (1.0 / self.RATE_LIMIT) - now
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self._last_request = time.monotonic()

    async def search(
        self,
        query: str,
        max_results: int = 50,
        fields: str | None = None,
        year_range: tuple[int, int] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search Semantic Scholar for papers.

        Args:
            query: Search query
            max_results: Maximum number of results (default 50, max 100)
            fields: Comma-separated fields to return
            year_range: Optional tuple of (start_year, end_year)

        Returns:
            List of paper dictionaries
        """
        await self._rate_limit()

        params: dict[str, Any] = {
            "query": query,
            "limit": min(max_results, 100),
            "fields": fields or self.DEFAULT_FIELDS,
        }

        if year_range:
            params["year"] = f"{year_range[0]}-{year_range[1]}"

        try:
            assert self._client is not None
            response = await self._client.get(f"{self.BASE_URL}/paper/search", params=params)
            response.raise_for_status()
            data = response.json()
            return [self._normalize_paper(p) for p in data.get("data", [])]
        except Exception as e:
            logger.warning("Semantic Scholar search error: %s", e)
            return []

    async def get_paper(
        self,
        paper_id: str,
        fields: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Get paper by S2 paper ID or DOI.

        Args:
            paper_id: Semantic Scholar paper ID or DOI
            fields: Comma-separated fields to return

        Returns:
            Paper dictionary or None
        """
        await self._rate_limit()

        params = {"fields": fields or self.DEFAULT_FIELDS}

        try:
            assert self._client is not None
            response = await self._client.get(
                f"{self.BASE_URL}/paper/{paper_id}",
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            return self._normalize_paper(data)
        except Exception as e:
            logger.warning("Semantic Scholar get paper error: %s", e)
            return None

    async def get_citations(
        self,
        paper_id: str,
        max_results: int = 50,
        fields: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get papers that cite the given paper.

        Args:
            paper_id: Semantic Scholar paper ID or DOI
            max_results: Maximum number of results
            fields: Comma-separated fields to return

        Returns:
            List of citing papers
        """
        await self._rate_limit()

        params: dict[str, Any] = {
            "limit": min(max_results, 1000),
            "fields": fields or self.DEFAULT_FIELDS,
        }

        try:
            assert self._client is not None
            response = await self._client.get(
                f"{self.BASE_URL}/paper/{paper_id}/citations",
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            return [
                self._normalize_paper(item.get("citingPaper", {}))
                for item in data.get("data", [])
            ]
        except Exception as e:
            logger.warning("Semantic Scholar citations error: %s", e)
            return []

    async def get_references(
        self,
        paper_id: str,
        max_results: int = 50,
        fields: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get papers referenced by the given paper.

        Args:
            paper_id: Semantic Scholar paper ID or DOI
            max_results: Maximum number of results
            fields: Comma-separated fields to return

        Returns:
            List of referenced papers
        """
        await self._rate_limit()

        params: dict[str, Any] = {
            "limit": min(max_results, 1000),
            "fields": fields or self.DEFAULT_FIELDS,
        }

        try:
            assert self._client is not None
            response = await self._client.get(
                f"{self.BASE_URL}/paper/{paper_id}/references",
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            return [
                self._normalize_paper(item.get("referencedPaper", {}))
                for item in data.get("data", [])
                if item.get("referencedPaper")
            ]
        except Exception as e:
            logger.warning("Semantic Scholar references error: %s", e)
            return []

    async def get_author(self, author_id: str) -> dict[str, Any] | None:
        """
        Get author profile by S2 author ID.

        Args:
            author_id: Semantic Scholar author ID

        Returns:
            Author profile dictionary
        """
        await self._rate_limit()

        fields = "authorId,name,affiliations,paperCount,citationCount,hIndex"

        try:
            assert self._client is not None
            response = await self._client.get(
                f"{self.BASE_URL}/author/{author_id}",
                params={"fields": fields},
            )
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result
        except Exception as e:
            logger.warning("Semantic Scholar author error: %s", e)
            return None

    async def get_author_papers(
        self,
        author_id: str,
        max_results: int = 50,
        fields: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get papers by author.

        Args:
            author_id: Semantic Scholar author ID
            max_results: Maximum number of results
            fields: Comma-separated fields to return

        Returns:
            List of papers
        """
        await self._rate_limit()

        params: dict[str, Any] = {
            "limit": min(max_results, 1000),
            "fields": fields or self.DEFAULT_FIELDS,
        }

        try:
            assert self._client is not None
            response = await self._client.get(
                f"{self.BASE_URL}/author/{author_id}/papers",
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            return [self._normalize_paper(p) for p in data.get("data", [])]
        except Exception as e:
            logger.warning("Semantic Scholar author papers error: %s", e)
            return []

    def _normalize_paper(self, paper: dict[str, Any]) -> dict[str, Any]:
        """Normalize paper dict to common format."""
        authors = []
        for a in paper.get("authors", []):
            if isinstance(a, dict):
                authors.append(a.get("name", ""))
            elif isinstance(a, str):
                authors.append(a)

        journal_info = paper.get("journal", {}) or {}
        journal_name = journal_info.get("name", "") if isinstance(journal_info, dict) else ""

        return {
            "paper_id": paper.get("paperId", ""),
            "s2_id": paper.get("paperId", ""),
            "title": paper.get("title", ""),
            "authors": authors,
            "year": paper.get("year") or 0,
            "abstract": paper.get("abstract", ""),
            "doi": paper.get("doi", ""),
            "url": paper.get("url", "") or f"https://semanticscholar.org/paper/{paper.get('paperId', '')}",
            "journal": journal_name,
            "citation_count": paper.get("citationCount", 0),
            "reference_count": paper.get("referenceCount", 0),
            "publication_date": paper.get("publicationDate", ""),
            "source": "semantic_scholar",
        }


class SyncSemanticScholarClient:
    """
    Sync Semantic Scholar API Client (backward compatibility).
    """

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key
        self._timeout = timeout

    def search(
        self,
        query: str,
        max_results: int = 50,
        year_range: tuple[int, int] | None = None,
    ) -> list[dict[str, Any]]:
        """Search."""
        async def _search() -> list[dict[str, Any]]:
            async with SemanticScholarClient(self.api_key, self._timeout) as client:
                return await client.search(query, max_results, year_range=year_range)

        return asyncio.run(_search())

    def get_paper(self, paper_id: str) -> dict[str, Any] | None:
        """Get paper."""
        async def _get() -> dict[str, Any] | None:
            async with SemanticScholarClient(self.api_key, self._timeout) as client:
                return await client.get_paper(paper_id)

        return asyncio.run(_get())

    def get_citations(self, paper_id: str, max_results: int = 50) -> list[dict[str, Any]]:
        """Get citations."""
        async def _get() -> list[dict[str, Any]]:
            async with SemanticScholarClient(self.api_key, self._timeout) as client:
                return await client.get_citations(paper_id, max_results)

        return asyncio.run(_get())

    def get_references(self, paper_id: str, max_results: int = 50) -> list[dict[str, Any]]:
        """Get references."""
        async def _get() -> list[dict[str, Any]]:
            async with SemanticScholarClient(self.api_key, self._timeout) as client:
                return await client.get_references(paper_id, max_results)

        return asyncio.run(_get())

    def get_author(self, author_id: str) -> dict[str, Any] | None:
        """Get author."""
        async def _get() -> dict[str, Any] | None:
            async with SemanticScholarClient(self.api_key, self._timeout) as client:
                return await client.get_author(author_id)

        return asyncio.run(_get())
