from __future__ import annotations

import logging
from typing import Any

import httpx

from .base import BaseSourceAdapter


logger = logging.getLogger("c44tcdi.knowledge.multi_source")


class OaMgAdapter(BaseSourceAdapter):
    """OA.mg — 250M+ papers, OA focus."""

    @property
    def source_id(self) -> str:
        return "oa_mg"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Search."""
        if not self.api_key:
            logger.debug("OA.mg: API key required")
            return []

        url = "https://api.oa.mg/v2/search"
        headers = {"X-Api-Key": self.api_key}
        params: dict[str, Any] = {
            "query": query,
            "limit": min(limit, 50),
        }
        async with httpx.AsyncClient(timeout=5.0, headers=headers) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            results: list[dict[str, Any]] = []
            for item in data.get("data", []):
                results.append({
                    "title": item.get("title", ""),
                    "year": item.get("year", 0) or 0,
                    "doi": item.get("doi", ""),
                    "oa_status": item.get("oa", ""),
                    "source": "oa_mg",
                    "source_name": "OA.mg",
                })
            return results
