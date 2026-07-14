from __future__ import annotations


"""
DEPRECATED: use sources/openalex.py adapter instead

OpenAlex Client — Academic search via OpenAlex API.
License: Open Access (see Terms & Conditions)
Coverage: 250M+ scholarly works across all fields.
API: https://api.openalex.org/works
"""

import json
import logging
from typing import Any


try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    httpx = None  # type: ignore

logger = logging.getLogger("c44tcdi.knowledge.openalex")


class OpenAlexClient:
    """Async client for OpenAlex API."""

    BASE_URL = "https://api.openalex.org/works"
    RATE_LIMIT = 10.0  # Requests per second for registered users

    def __init__(self, api_key: str | None = None, timeout: float = 30.0) -> None:
        if not HAS_HTTPX:
            raise ImportError("httpx required: pip install httpx")
        self.api_key = api_key
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> OpenAlexClient:
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={"User-Agent": "C44TCDI/4.2 (academic research)"},
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()

    async def search(
        self, query: str, max_results: int = 20, year_min: int | None = None, year_max: int | None = None
    ) -> list[dict[str, Any]]:
        """Search works by keyword."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        params: dict[str, Any] = {
            "search": query,
            "per_page": min(max_results, 200),
            "select": "id,doi,title,authorships,publication_date,cited_by_count,open_access,type",
        }

        if self.api_key:
            params["api_key"] = self.api_key
        if year_min:
            params["filter"] = f"from_publication_date:{year_min}-01-01"
        if year_max:
            if "filter" in params:
                params["filter"] += f",to_publication_date:{year_max}-12-31"
            else:
                params["filter"] = f"to_publication_date:{year_max}-12-31"

        try:
            response = await self._client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            return self._parse_results(data)
        except (TimeoutError, TypeError, httpx.HTTPError, json.JSONDecodeError) as e:
            logger.warning("OpenAlex search error: %s", e)
            return []

    def _parse_results(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        results = []
        for item in data.get("results", []):
            authors = []
            for authorship in item.get("authorships", []):
                author = authorship.get("author", {})
                if author.get("display_name"):
                    authors.append(author["display_name"])

            results.append(
                {
                    "paper_id": item.get("id", "").replace("https://openalex.org/W", ""),
                    "title": item.get("display_name", ""),
                    "authors": authors,
                    "year": int(item.get("publication_date", "0000")[:4]) if item.get("publication_date") else 0,
                    "abstract": "",  # OpenAlex doesn't provide abstract in free tier
                    "doi": item.get("doi", ""),
                    "url": item.get("id", ""),
                    "journal": "",
                    "source": "openalex",
                    "citation_count": item.get("cited_by_count", 0) or 0,
                    "is_open_access": item.get("open_access", {}).get("is_oa", False),
                }
            )
        return results

    async def get_paper(self, paper_id: str) -> dict[str, Any] | None:
        """Get paper by OpenAlex ID (W123456)."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        try:
            response = await self._client.get(f"{self.BASE_URL}/{paper_id}")
            response.raise_for_status()
            data = response.json()
            results = self._parse_results({"results": [data]})
            return results[0] if results else None
        except (TimeoutError, IndexError, KeyError, TypeError, httpx.HTTPError, json.JSONDecodeError) as e:
            logger.warning("OpenAlex get_paper error: %s", e)
            return None
