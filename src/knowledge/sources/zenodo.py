from __future__ import annotations

from typing import Any

import httpx

from .base import BaseSourceAdapter


class ZenodoAdapter(BaseSourceAdapter):
    """Zenodo — 2M+ research outputs."""

    @property
    def source_id(self) -> str:
        return "zenodo"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Search."""
        import urllib.parse
        url = "https://zenodo.org/api/records"
        # Zenodo requires URL-encoded query
        encoded_query = urllib.parse.quote(query)
        params: dict[str, Any] = {
            "q": encoded_query,
            "size": min(limit, 100),
            "sort": "bestmatch",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                return self._normalize(data.get("hits", {}).get("hits", []))
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 400:
                    # Try simplified query (remove special chars)
                    simple_query = "".join(c for c in query if c.isalnum() or c.isspace())
                    params["q"] = urllib.parse.quote(simple_query)
                    resp = await client.get(url, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                    return self._normalize(data.get("hits", {}).get("hits", []))
                raise

    def _normalize(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for item in data:
            meta = item.get("metadata", {})
            authors = [c.get("name", "") for c in meta.get("creators", []) if isinstance(c, dict)]
            result.append({
                "title": meta.get("title", ""),
                "authors": authors,
                "year": int(meta.get("publication_date", "0")[:4]) if meta.get("publication_date") else 0,
                "abstract": meta.get("description", "") or "",
                "doi": meta.get("doi", ""),
                "venue": "",
                "citation_count": 0,
                "source": "zenodo",
                "source_name": "Zenodo",
                "sources": ["Zenodo"],
            })
        return result
