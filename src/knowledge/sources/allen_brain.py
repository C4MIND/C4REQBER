"""
c4reqber: Allen Brain Atlas API Client

Neuroanatomical data, gene expression, connectivity.
Open access, no API key required.
"""
from __future__ import annotations

import logging
from typing import Any

from .base_p6 import BaseP6Client

logger = logging.getLogger("c4reqber.knowledge.allen_brain")


class AllenBrainClient(BaseP6Client):
    """Allen Brain Atlas API client (RMA-based)."""

    BASE_URL = "https://api.brain-map.org/api/v2"
    DEFAULT_TIMEOUT = 30.0

    async def search_genes(
        self, query: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Search genes in Allen Brain Atlas."""
        try:
            params: dict[str, Any] = {
                "criteria": f"[acronym$il'{query}']",
                "num_rows": limit,
            }
            data = await self._get("/data/Gene/query.json", params=params, use_cache=True)
            results: list[dict[str, Any]] = []
            msg = data.get("msg", []) if isinstance(data, dict) else []
            for item in msg:
                if not isinstance(item, dict):
                    continue
                results.append({
                    "id": item.get("id"),
                    "acronym": item.get("acronym"),
                    "name": item.get("name"),
                    "organism_id": item.get("organism_id"),
                    "chromosome": item.get("chromosome"),
                    "source": "allen_brain",
                })
            return results[:limit]
        except Exception as e:
            logger.warning("Allen Brain search error: %s", e)
            return []

    async def search_structures(
        self, query: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Search neuroanatomical structures."""
        try:
            params: dict[str, Any] = {
                "criteria": f"[name$il'{query}']",
                "num_rows": limit,
            }
            data = await self._get("/data/Structure/query.json", params=params, use_cache=True)
            results: list[dict[str, Any]] = []
            msg = data.get("msg", []) if isinstance(data, dict) else []
            for item in msg:
                if not isinstance(item, dict):
                    continue
                results.append({
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "acronym": item.get("acronym"),
                    "source": "allen_brain",
                })
            return results[:limit]
        except Exception as e:
            logger.warning("Allen Brain structure search error: %s", e)
            return []
