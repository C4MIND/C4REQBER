from __future__ import annotations

from typing import Any

import httpx

from .base import BaseSourceAdapter


class FigshareAdapter(BaseSourceAdapter):
    """Figshare — 10M+ research items."""

    @property
    def source_id(self) -> str:
        return "figshare"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Search."""
        url = "https://api.figshare.com/v2/articles/search"
        params: dict[str, Any] = {
            "search_for": query,
            "page_size": min(limit, 100),
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, json=params)
            resp.raise_for_status()
            items = resp.json()
            return self._normalize(items if isinstance(items, list) else [])

    def _normalize(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for item in data:
            authors = []
            for a in item.get("authors", []):
                if isinstance(a, dict):
                    authors.append(a.get("full_name", a.get("name", "")))
                elif isinstance(a, str):
                    authors.append(a)
            result.append({
                "title": item.get("title", ""),
                "authors": authors,
                "year": int(item.get("published_date", "0")[:4]) if item.get("published_date") else 0,
                "abstract": item.get("description", "") or "",
                "doi": item.get("doi", ""),
                "venue": "",
                "citation_count": 0,
                "source": "figshare",
                "source_name": "Figshare",
                "sources": ["Figshare"],
            })
        return result
