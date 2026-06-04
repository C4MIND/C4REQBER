"""
Semantic Scholar Client
License: ⚠️ Non-commercial use only
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

logger = logging.getLogger("c4_cdi_turbo.knowledge.semantic")


class SemanticClient:
    """
    Semantic Scholar API Client.

    License: ⚠️ Non-commercial use only
    Coverage: 200M+ papers
    API: semanticscholar.org/api (unofficial)
    """

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key or os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
        self._client: Any = None
        if HAS_HTTPX:
            headers = {}
            if self.api_key:
                headers["x-api-key"] = self.api_key
            self._client = httpx.Client(headers=headers, timeout=30.0)

    def __enter__(self) -> SemanticClient:
        return self

    def __exit__(self, *args: Any) -> None:
        if self._client:
            self._client.close()

    def search(self, query: str, limit: int = 20) -> list[dict]:
        """
        Search Semantic Scholar for papers.

        Args:
            query: Search query string
            limit: Maximum number of results (max 100)

        Returns:
            List of paper dictionaries with keys:
            - paper_id, title, authors, year, abstract,
              citation_count, doi, url, venue
        """
        if not HAS_HTTPX:
            logger.warning("httpx not installed. Install: pip install httpx")
            return []

        self._log_license_warning()

        fields = "paperId,title,authors,year,abstract,citationCount,externalIds,url,venue"
        url = f"{self.BASE_URL}/paper/search"
        params = {
            "query": query,
            "limit": min(limit, 100),
            "fields": fields,
        }

        try:
            response = self._client.get(url, params=params)  # type: ignore[union-attr]
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("data", []):
                authors = [
                    a.get("name", "") for a in item.get("authors", []) if isinstance(a, dict)
                ]
                doi = ""
                external_ids = item.get("externalIds") or {}
                if isinstance(external_ids, dict):
                    doi = external_ids.get("DOI", "")

                results.append(
                    {
                        "paper_id": item.get("paperId", ""),
                        "title": item.get("title", ""),
                        "authors": authors,
                        "year": item.get("year", 0) or 0,
                        "abstract": item.get("abstract", "") or "",
                        "citation_count": item.get("citationCount", 0) or 0,
                        "doi": doi,
                        "url": item.get("url", ""),
                        "venue": item.get("venue", "") or "",
                        "source": "semantic_scholar",
                    }
                )
            return results

        except Exception as e:
            logger.warning("Semantic Scholar search error: %s", e)
            return []

    def _log_license_warning(self) -> None:
        """Log warning about non-commercial license."""
        logger.warning(
            "⚠️ Semantic Scholar API is for NON-COMMERCIAL USE ONLY. "
            "Ensure compliance with their license terms."
        )
