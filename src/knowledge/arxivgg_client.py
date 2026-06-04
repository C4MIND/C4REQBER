from __future__ import annotations

import json


"""
arXiv.gg Client — Academic search via arXiv.gg API.
License: Open Access (arXiv.org content)
Coverage: 2.4M+ physics, math, CS preprints.
API: https://arxiv.gg/api/v1
"""

import logging
from typing import Any


try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    httpx = None  # type: ignore

logger = logging.getLogger("c44tcdi.knowledge.arxivgg")


class ArxivGGClient:
    """Async client for arXiv.gg API."""

    BASE_URL = "https://arxiv.gg/api/v1"
    RATE_LIMIT = 10.0  # requests per second

    def __init__(self, timeout: float = 30.0) -> None:
        if not HAS_HTTPX:
            raise ImportError("httpx required: pip install httpx")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> ArxivGGClient:
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()

    async def search(
        self, query: str, max_results: int = 20, year_min: int | None = None, year_max: int | None = None
    ) -> list[dict[str, Any]]:
        """Search papers by keyword."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        params: dict[str, Any] = {
            "q": query,
            "limit": min(max_results, 100),
        }
        if year_min:
            params["filter"] = f"publication_year:{year_min}:"
        if year_max:
            if "filter" in params:
                params["filter"] += f",{year_max}:"
            else:
                params["filter"] = f"publication_year:{year_max}:"

        try:
            response = await self._client.get(f"{self.BASE_URL}/search", params=params)
            response.raise_for_status()
            data = response.json()
            return self._parse_results(data)
        except (TimeoutError, TypeError, httpx.HTTPError, json.JSONDecodeError) as e:
            logger.warning("arXiv.gg search error: %s", e)
            return []

    def _parse_results(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        results = []
        for item in data.get("results", []):
            authors = [a.get("name", "") for a in item.get("authors", [])]
            results.append(
                {
                    "paper_id": item.get("id", "").replace("https://arxiv.org/abs/", ""),
                    "title": item.get("title", ""),
                    "authors": authors,
                    "year": item.get("published", "")[:4] if item.get("published") else 0,
                    "abstract": item.get("summary", ""),
                    "doi": item.get("doi", ""),
                    "url": item.get("id", ""),
                    "journal": "arXiv",
                    "source": "arxivgg",
                    "citation_count": item.get("citation_count", 0) or 0,
                    "is_open_access": True,
                }
            )
        return results

    async def search_semantic(
        self, query: str, max_results: int = 20
    ) -> list[dict[str, Any]]:
        """Semantic search using vector similarity (requires embeddings)."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        params: dict[str, str | int] = {
            "q": query,
            "limit": min(max_results, 100),
        }

        try:
            response = await self._client.get(f"{self.BASE_URL}/search/semantic", params=params)
            response.raise_for_status()
            data = response.json()
            return self._parse_results(data)
        except (TimeoutError, TypeError, httpx.HTTPError, json.JSONDecodeError) as e:
            logger.warning("arXiv.gg semantic search error: %s", e)
            return []

    async def search_pdf(
        self, query: str, max_results: int = 50, fuzzy: bool = True
    ) -> list[dict[str, Any]]:
        """Search within downloaded PDF content."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        params: dict[str, str | int] = {
            "q": query,
            "limit": min(max_results, 100),
            "fuzzy": "true" if fuzzy else "false",
        }

        try:
            response = await self._client.get(f"{self.BASE_URL}/search/pdf", params=params)
            response.raise_for_status()
            data = response.json()
            return self._parse_results(data)
        except (TimeoutError, TypeError, httpx.HTTPError, json.JSONDecodeError) as e:
            logger.warning("arXiv.gg PDF search error: %s", e)
            return []
