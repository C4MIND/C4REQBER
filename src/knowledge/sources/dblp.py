from __future__ import annotations

from typing import Any

import httpx

from .base import BaseSourceAdapter


class DblpAdapter(BaseSourceAdapter):
    """DBLP — 7M+ CS publications."""

    @property
    def source_id(self) -> str:
        return "dblp"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Search."""
        url = "https://dblp.org/search/publ/api"
        params: dict[str, Any] = {
            "q": query,
            "h": min(limit, 100),
            "format": "json",
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            hits = data.get("result", {}).get("hits", {}).get("hit", [])
            return self._normalize(hits)

    def _normalize(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for item in data:
            info = item.get("info", {})
            authors_info = info.get("authors", {})
            author_list: list[str] = []
            raw_authors = authors_info.get("author", [])
            if isinstance(raw_authors, dict):
                raw_authors = [raw_authors]
            for a in raw_authors:
                if isinstance(a, dict):
                    author_list.append(a.get("text", ""))
            result.append({
                "title": info.get("title", ""),
                "authors": author_list,
                "year": int(info.get("year", 0) or 0),
                "doi": info.get("doi", ""),
                "venue": info.get("venue", ""),
                "citation_count": 0,
                "source": "dblp",
                "source_name": "DBLP",
                "sources": ["DBLP"],
            })
        return result
