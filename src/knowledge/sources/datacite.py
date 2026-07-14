from __future__ import annotations

from typing import Any

import httpx

from .base import BaseSourceAdapter


class DataciteAdapter(BaseSourceAdapter):
    """DataCite — 50M+ DOIs, datasets and publications."""

    @property
    def source_id(self) -> str:
        return "datacite"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Search."""
        url = "https://api.datacite.org/dois"
        params: dict[str, Any] = {
            "query": query,
            "page[size]": min(limit, 100),
            "sort": "relevance",
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            return self._normalize(data.get("data", []))

    def _normalize(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for item in data:
            attrs = item.get("attributes", {})
            titles = attrs.get("titles", [])
            title = titles[0].get("title", "") if titles else ""
            creators = attrs.get("creators", [])
            authors = [c.get("name", "") for c in creators if isinstance(c, dict)]
            result.append({
                "title": title,
                "authors": authors,
                "year": attrs.get("publicationYear", 0) or 0,
                "abstract": (attrs.get("descriptions", [{}])[0].get("description", "") if attrs.get("descriptions") else ""),
                "doi": attrs.get("doi", ""),
                "venue": attrs.get("publisher", ""),
                "citation_count": 0,
                "source": "datacite",
                "source_name": "DataCite",
                "sources": ["DataCite"],
            })
        return result
