from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from .base import BaseSourceAdapter


logger = logging.getLogger("c44tcdi.knowledge.multi_source")


class CoreAdapter(BaseSourceAdapter):
    """CORE — 10M+ open access full-text."""

    @property
    def source_id(self) -> str:
        return "core"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Search."""
        key = self.api_key or os.environ.get("CORE_API_KEY", "")
        if not key:
            logger.debug("CORE: API key required")
            return []
        self.api_key = key

        url = "https://api.core.ac.uk/v3/search/works"
        params: dict[str, Any] = {
            "q": query,
            "limit": min(limit, 100),
            "scroll": "false",
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=5.0, headers=headers) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 401:
                return []
            resp.raise_for_status()
            data = resp.json()
            return self._normalize(data.get("results", []))

    def _normalize(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for item in data:
            authors = []
            raw = item.get("authors", [])
            for a in (raw if isinstance(raw, list) else []):
                if isinstance(a, dict):
                    authors.append(a.get("name", str(a)))
                elif isinstance(a, str):
                    authors.append(a)
            result.append({
                "title": item.get("title", ""),
                "authors": authors,
                "year": item.get("yearPublished", 0) or 0,
                "abstract": item.get("abstract", item.get("description", "")) or "",
                "doi": item.get("doi", ""),
                "venue": "",
                "citation_count": 0,
                "source": "core",
                "source_name": "CORE",
                "sources": ["CORE"],
            })
        return result
