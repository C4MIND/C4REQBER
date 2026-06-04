"""
c4reqber: CERN Open Data Portal Client

LHC and accelerator experiment data. Open access.
"""
from __future__ import annotations

import logging
from typing import Any

from .base_p6 import BaseP6Client

logger = logging.getLogger("c4reqber.knowledge.cern_opendata")


class CernOpenDataClient(BaseP6Client):
    """CERN Open Data Portal API client."""

    BASE_URL = "https://opendata.cern.ch/api"
    DEFAULT_TIMEOUT = 30.0

    async def search_records(
        self, query: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Search open data records by keyword."""
        try:
            params: dict[str, Any] = {"q": query, "size": min(limit, 100)}
            data = await self._get("/records", params=params, use_cache=True)
            hits = data.get("hits", {}).get("hits", []) if isinstance(data, dict) else []
            results: list[dict[str, Any]] = []
            for item in hits[:limit]:
                if not isinstance(item, dict):
                    continue
                src = item.get("_source", {})
                metadata = src.get("metadata", {})
                results.append({
                    "recid": src.get("id") or item.get("_id"),
                    "title": metadata.get("title", "") if isinstance(metadata.get("title"), str) else str(metadata.get("title", "")),
                    "experiment": metadata.get("experiment", ""),
                    "date_published": metadata.get("date_published", ""),
                    "type": metadata.get("type", {}).get("primary", "") if isinstance(metadata.get("type"), dict) else "",
                    "source": "cern_opendata",
                })
            return results
        except Exception as e:
            logger.warning("CERN Open Data search error: %s", e)
            return []
