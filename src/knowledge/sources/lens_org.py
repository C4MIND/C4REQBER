from __future__ import annotations

import logging
from typing import Any

import httpx

from .base import BaseSourceAdapter


logger = logging.getLogger("c44tcdi.knowledge.multi_source")


class LensOrgAdapter(BaseSourceAdapter):
    """Lens.org — 225M+ scholarly works + patents."""

    @property
    def source_id(self) -> str:
        return "lens_org"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Search."""
        if not self.api_key:
            logger.debug("Lens.org: API token required")
            return []

        url = "https://api.lens.org/scholarly/search"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload: dict[str, Any] = {
            "query": {"bool": {"must": [{"query_string": {"query": query}}]}},
            "size": min(limit, 100),
            "_source": ["title", "author", "year_published", "external_ids", "abstract"],
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 401:
                return []
            resp.raise_for_status()
            data = resp.json()
            results: list[dict[str, Any]] = []
            for hit in data.get("hits", {}).get("hits", data.get("data", [])):
                src = hit.get("_source", hit)
                results.append({
                    "title": src.get("title", "") if isinstance(src.get("title"), str) else " ".join(src.get("title", [])),
                    "year": src.get("year_published", 0) or 0,
                    "doi": (src.get("external_ids") or {}).get("doi", ""),
                    "source": "lens_org",
                    "source_name": "Lens.org",
                })
            return results
