"""
CORE API Client (core.ac.uk/api)
License: ✅ Open Access
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

logger = logging.getLogger("c4_cdi_turbo.knowledge.core")


class COREClient:
    """
    CORE API Client.

    License: ✅ Open Access (20M+ papers)
    Coverage: 10M+ open access papers
    API: core.ac.uk/api (API key required)
    """

    BASE_URL = "https://core.ac.uk/api-v2"

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key or os.getenv("CORE_API_KEY", "")
        if not self.api_key:
            logger.warning(
                "CORE_API_KEY not set. Get one from https://core.ac.uk/api/"
            )
        self._client: Any = None
        if HAS_HTTPX:
            self._client = httpx.Client(timeout=30.0)

    def __enter__(self) -> COREClient:
        return self

    def __exit__(self, *args: Any) -> None:
        if self._client:
            self._client.close()

    def search(self, query: str, limit: int = 20) -> list[dict]:
        """
        Search CORE for open access papers.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of paper dictionaries with keys:
            - paper_id, title, authors, year, abstract,
              doi, url, journal, download_url
        """
        if not HAS_HTTPX:
            logger.warning("httpx not installed. Install: pip install httpx")
            return []

        if not self.api_key:
            logger.error("CORE_API_KEY required for CORE API access")
            return []

        url = f"{self.BASE_URL}/search/{query}"
        params = {
            "apiKey": self.api_key,
            "pageSize": min(limit, 100),
            "metadata": True,
            "fulltext": False,
        }

        try:
            response = self._client.get(url, params=params)  # type: ignore[union-attr]
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("data", []):
                authors = []
                raw_authors = item.get("authors", [])
                if isinstance(raw_authors, str):
                    authors = [a.strip() for a in raw_authors.split(";") if a.strip()]
                elif isinstance(raw_authors, list):
                    authors = [str(a) for a in raw_authors if a]

                results.append(
                    {
                        "paper_id": str(item.get("id", "")),
                        "title": item.get("title", ""),
                        "authors": authors,
                        "year": item.get("year", 0) or 0,
                        "abstract": item.get("description", "") or "",
                        "doi": item.get("doi", "") or "",
                        "url": item.get("sourceFulltextUrls", [None])[0]
                        or item.get("sourceUrl", ""),
                        "journal": item.get("publisher", "") or "",
                        "download_url": item.get("downloadUrl", "") or "",
                        "citation_count": item.get("citationCount", 0) or 0,
                        "source": "core",
                    }
                )
            return results

        except Exception as e:
            logger.warning("CORE search error: %s", e)
            return []
