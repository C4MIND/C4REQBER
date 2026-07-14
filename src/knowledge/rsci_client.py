"""
RSCI API Client (Russian Science Citation Index / eLibrary.ru)
License: ⚠️ Registration required, terms vary
"""

from __future__ import annotations

import logging
import os
from typing import Any


try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

logger = logging.getLogger("c4_cdi_turbo.knowledge.rsci")


class RSCIClient:
    """
    RSCI API Client (Russian Science Citation Index).

    License: ⚠️ Registration required, terms vary
    Coverage: Russian academic papers, citations
    API: elibrary.ru (API access may require institutional subscription)
    Note: RSCI is integrated with Web of Science
    """

    BASE_URL = "https://elibrary.ru/api"
    SEARCH_URL = "https://www.elibrary.ru/search_results.asp"

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key or os.getenv("RSCI_API_KEY", "")
        if not self.api_key:
            logger.warning(
                "RSCI_API_KEY not set. Access may require institutional subscription. "
                "See: https://elibrary.ru/"
            )
        self._client: Any = None
        if HAS_HTTPX:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._client = httpx.Client(headers=headers, timeout=30.0)

    def __enter__(self) -> RSCIClient:
        return self

    def __exit__(self, *args: Any) -> None:
        if self._client:
            self._client.close()

    def search(self, query: str, limit: int = 50) -> list[dict]:
        """
        Search RSCI for Russian academic papers.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of paper dictionaries with keys:
            - paper_id, title, authors, year, abstract,
              doi, url, journal, language, citation_count, source
        """
        if not HAS_HTTPX:
            logger.warning("httpx not installed. Install: pip install httpx")
            return []

        self._log_license_warning()

        params = {
            "query": query,
            "limit": min(limit, 100),
        }

        try:
            if self.api_key:
                url = f"{self.BASE_URL}/search"
                response = self._client.get(url, params=params)  # type: ignore[union-attr]
                response.raise_for_status()
                data = response.json()
                return self._parse_api_response(data)
            else:
                logger.warning(
                    "RSCI requires API key for programmatic access. "
                    "See: https://elibrary.ru/ for manual search."
                )
                return []

        except Exception as e:
            logger.warning("RSCI search error: %s", e)
            return []

    def _parse_api_response(self, data: dict) -> list[dict]:
        """Parse RSCI API response."""
        results = []
        items = data.get("results", []) or data.get("items", [])

        for item in items if isinstance(items, list) else []:
            if not isinstance(item, dict):
                continue

            authors = []
            raw_authors = item.get("authors", [])
            if isinstance(raw_authors, list):
                authors = [a.get("name", str(a)) if isinstance(a, dict) else str(a) for a in raw_authors]
            elif isinstance(raw_authors, str):
                authors = [a.strip() for a in raw_authors.split(",") if a.strip()]

            results.append(
                {
                    "paper_id": str(item.get("id", "")),
                    "title": item.get("title", "") or item.get("name", ""),
                    "authors": authors,
                    "year": item.get("year", 0) or 0,
                    "abstract": item.get("abstract", "") or item.get("summary", "") or "",
                    "doi": item.get("doi", "") or "",
                    "url": f"https://elibrary.ru/item.asp?id={item.get('id', '')}" if item.get("id") else "",
                    "journal": item.get("journal", "") or item.get("source", "") or "",
                    "language": "ru",
                    "citation_count": item.get("citations", 0) or 0,
                    "source": "rsci",
                }
            )
        return results

    def _log_license_warning(self) -> None:
        """Log warning about license terms."""
        logger.warning(
            "⚠️ RSCI/eLibrary.ru access may require institutional subscription. "
            "Ensure compliance with their license terms."
        )


class AsyncRSCIClient:
    """
    Async RSCI API Client (Russian Science Citation Index).
    """

    BASE_URL = "https://elibrary.ru/api"

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key or os.getenv("RSCI_API_KEY", "")
        self._client: Any = None

    async def __aenter__(self) -> AsyncRSCIClient:
        if HAS_HTTPX:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._client = httpx.AsyncClient(headers=headers, timeout=30.0)
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()

    async def search(self, query: str, limit: int = 50) -> list[dict]:
        """Async search RSCI for Russian academic papers."""
        if not HAS_HTTPX:
            logger.warning("httpx not installed. Install: pip install httpx")
            return []

        logger.warning(
            "⚠️ RSCI/eLibrary.ru access may require institutional subscription."
        )

        if not self.api_key:
            logger.warning("RSCI requires API key for programmatic access.")
            return []

        params = {
            "query": query,
            "limit": min(limit, 100),
        }

        try:
            url = f"{self.BASE_URL}/search"
            response = await self._client.get(url, params=params)  # type: ignore[union-attr]
            response.raise_for_status()
            data = response.json()
            return self._parse_api_response(data)

        except Exception as e:
            logger.warning("RSCI search error: %s", e)
            return []

    def _parse_api_response(self, data: dict) -> list[dict]:
        """Parse RSCI API response."""
        results = []
        items = data.get("results", []) or data.get("items", [])

        for item in items if isinstance(items, list) else []:
            if not isinstance(item, dict):
                continue

            authors = []
            raw_authors = item.get("authors", [])
            if isinstance(raw_authors, list):
                authors = [a.get("name", str(a)) if isinstance(a, dict) else str(a) for a in raw_authors]
            elif isinstance(raw_authors, str):
                authors = [a.strip() for a in raw_authors.split(",") if a.strip()]

            results.append(
                {
                    "paper_id": str(item.get("id", "")),
                    "title": item.get("title", "") or item.get("name", ""),
                    "authors": authors,
                    "year": item.get("year", 0) or 0,
                    "abstract": item.get("abstract", "") or item.get("summary", "") or "",
                    "doi": item.get("doi", "") or "",
                    "url": f"https://elibrary.ru/item.asp?id={item.get('id', '')}" if item.get("id") else "",
                    "journal": item.get("journal", "") or item.get("source", "") or "",
                    "language": "ru",
                    "citation_count": item.get("citations", 0) or 0,
                    "source": "rsci",
                }
            )
        return results
