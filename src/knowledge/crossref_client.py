"""
CrossRef API Client — Async HTTP for DOI Metadata

License: ✅ Open Access (attribution appreciated)
Coverage: 140M+ DOI records
API: api.crossref.org (no key required, polite pool with mailto)
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

logger = logging.getLogger("c4_cdi_turbo.knowledge.crossref")


class CrossRefClient:
    """
    Async CrossRef API Client.

    License: ✅ Open Access (attribution appreciated)
    Coverage: 140M+ DOI records
    Rate Limit: ~50/sec (polite pool with mailto)
    """

    BASE_URL = "https://api.crossref.org"
    RATE_LIMIT = 50.0

    def __init__(
        self,
        mailto: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        if not HAS_HTTPX:
            raise ImportError("httpx required: pip install httpx")

        if mailto:
            self.mailto = mailto
        else:
            from src.knowledge.contact_email import contact_email

            self.mailto = contact_email()
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._last_request: float = 0.0
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> CrossRefClient:
        headers = {"User-Agent": f"c4reqber (mailto:{self.mailto})"}
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

    async def get_by_doi(self, doi: str) -> dict[str, Any] | None:
        """
        Get paper metadata by DOI.

        Args:
            doi: DOI string (with or without https://doi.org/ prefix)

        Returns:
            Paper metadata dictionary or None
        """
        await self._rate_limit()

        doi_clean = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")

        try:
            assert self._client is not None
            response = await self._client.get(f"{self.BASE_URL}/works/{doi_clean}")
            response.raise_for_status()
            data = response.json()
            return self._normalize_work(data.get("message", {}))
        except Exception as e:
            logger.warning("CrossRef DOI lookup error: %s", e)
            return None

    async def search(
        self,
        query: str,
        max_results: int = 50,
        filters: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search CrossRef database.

        Args:
            query: Search query
            max_results: Maximum number of results (default 50, max 1000)
            filters: Optional filters (e.g., {'type': 'journal-article', 'from-pub-date': '2020'})

        Returns:
            List of paper dictionaries
        """
        await self._rate_limit()

        params: dict[str, Any] = {
            "query": query,
            "rows": min(max_results, 1000),
        }

        if filters:
            filter_parts = [f"{k}:{v}" for k, v in filters.items()]
            params["filter"] = ",".join(filter_parts)

        try:
            assert self._client is not None
            response = await self._client.get(f"{self.BASE_URL}/works", params=params)
            response.raise_for_status()
            data = response.json()
            items = data.get("message", {}).get("items", [])
            return [self._normalize_work(item) for item in items]
        except Exception as e:
            logger.warning("CrossRef search error: %s", e)
            return []

    async def get_by_issn(self, issn: str) -> dict[str, Any] | None:
        """
        Get journal info by ISSN.

        Args:
            issn: ISSN string (e.g., '1234-5678')

        Returns:
            Journal metadata dictionary or None
        """
        await self._rate_limit()

        issn_clean = issn.replace("-", "")

        try:
            assert self._client is not None
            response = await self._client.get(f"{self.BASE_URL}/journals/{issn_clean}")
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            result: dict[str, Any] = data.get("message", {})
            return result
        except Exception as e:
            logger.warning("CrossRef ISSN lookup error: %s", e)
            return None

    async def get_works_by_issn(
        self,
        issn: str,
        max_results: int = 50,
        year: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get works from a journal by ISSN.

        Args:
            issn: ISSN string
            max_results: Maximum number of results
            year: Optional publication year filter

        Returns:
            List of paper dictionaries
        """
        filters = {"issn": issn}
        if year:
            filters["from-pub-date"] = str(year)
            filters["until-pub-date"] = str(year)

        return await self.search("", max_results=max_results, filters=filters)

    async def get_author_works(
        self,
        orcid: str | None = None,
        author_name: str | None = None,
        max_results: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Get works by author (via ORCID or name search).

        Args:
            orcid: Author's ORCID ID
            author_name: Author name (if ORCID not available)
            max_results: Maximum number of results

        Returns:
            List of paper dictionaries
        """
        if orcid:
            filters = {"orcid": orcid}
            return await self.search("", max_results=max_results, filters=filters)
        elif author_name:
            return await self.search(author_name, max_results=max_results)
        return []

    async def get_types(self) -> list[dict[str, Any]]:
        """Get list of available work types."""
        await self._rate_limit()

        try:
            assert self._client is not None
            response = await self._client.get(f"{self.BASE_URL}/types")
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            items: list[dict[str, Any]] = data.get("message", {}).get("items", [])
            return items
        except Exception as e:
            logger.warning("CrossRef types error: %s", e)
            return []

    def _normalize_work(self, work: dict[str, Any]) -> dict[str, Any]:
        """Normalize work dict to common format."""
        authors = []
        for a in work.get("author", []):
            name_parts = []
            given = a.get("given", "")
            family = a.get("family", "")
            if given:
                name_parts.append(given)
            if family:
                name_parts.append(family)
            authors.append(" ".join(name_parts))

        doi = work.get("DOI", "")

        year = 0
        published = (
            work.get("published-print") or work.get("published-online") or work.get("published")
        )
        if published:
            date_parts = published.get("date-parts", [[]])
            if date_parts and date_parts[0]:
                year = date_parts[0][0]

        journal_name = ""
        container = work.get("container-title", [])
        if container:
            journal_name = container[0] if isinstance(container, list) else container

        abstract = ""
        if "abstract" in work:
            abstract = work["abstract"]

        return {
            "paper_id": doi,
            "doi": doi,
            "title": work.get("title", [""])[0] if work.get("title") else "",
            "authors": authors,
            "year": year,
            "abstract": abstract,
            "url": f"https://doi.org/{doi}" if doi else "",
            "journal": journal_name,
            "publisher": work.get("publisher", ""),
            "type": work.get("type", ""),
            "issn": work.get("ISSN", [""])[0] if work.get("ISSN") else "",
            "source": "crossref",
            "is_open_access": work.get("is-referenced-by-count", 0) > 0,
            "reference_count": work.get("is-referenced-by-count", 0),
            "citation_count": work.get("references-count", 0),
        }


class SyncCrossRefClient:
    """
    Sync CrossRef API Client (backward compatibility).
    """

    def __init__(
        self,
        mailto: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.mailto = mailto
        self._timeout = timeout

    def get_by_doi(self, doi: str) -> dict[str, Any] | None:
        """Get by doi."""

        async def _get() -> dict[str, Any] | None:
            async with CrossRefClient(self.mailto, self._timeout) as client:
                return await client.get_by_doi(doi)

        return asyncio.run(_get())

    def search(
        self,
        query: str,
        max_results: int = 50,
        filters: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """Search."""

        async def _search() -> list[dict[str, Any]]:
            async with CrossRefClient(self.mailto, self._timeout) as client:
                return await client.search(query, max_results, filters)

        return asyncio.run(_search())

    def get_by_issn(self, issn: str) -> dict[str, Any] | None:
        """Get by issn."""

        async def _get() -> dict[str, Any] | None:
            async with CrossRefClient(self.mailto, self._timeout) as client:
                return await client.get_by_issn(issn)

        return asyncio.run(_get())
