"""
c4reqber: NASA Earthdata API Client

Satellite data via CMR (Common Metadata Repository).
Requires URS token (JWT) for some collections.
"""
from __future__ import annotations

import logging
import os
from typing import Any

from .base_p6 import BaseP6Client


logger = logging.getLogger("c4reqber.knowledge.nasa_earthdata")


class NasaEarthdataClient(BaseP6Client):
    """NASA CMR API client."""

    BASE_URL = "https://cmr.earthdata.nasa.gov/search"
    DEFAULT_TIMEOUT = 60.0

    def __init__(self, token: str = "", api_key: str = "") -> None:
        self.token = token or api_key or os.getenv("NASA_EARTHDATA_TOKEN", "")
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        super().__init__(headers=headers)

    async def search_collections(
        self, query: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Search NASA data collections by keyword."""
        try:
            params: dict[str, Any] = {
                "keyword": query,
                "page_size": min(limit, 100),
            }
            data = await self._get("/collections.json", params=params, use_cache=True)
            entries = data.get("feed", {}).get("entry", []) if isinstance(data, dict) else []
            results: list[dict[str, Any]] = []
            for item in entries[:limit]:
                if not isinstance(item, dict):
                    continue
                results.append({
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "summary": item.get("summary", "")[:300],
                    "short_name": item.get("short_name"),
                    "version": item.get("version_id"),
                    "source": "nasa_earthdata",
                })
            return results
        except Exception as e:
            logger.warning("NASA Earthdata search error: %s", e)
            return []

    async def search_granules(
        self, collection_concept_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Search granules (data files) within a collection."""
        try:
            params: dict[str, Any] = {
                "collection_concept_id": collection_concept_id,
                "page_size": min(limit, 100),
            }
            data = await self._get("/granules.json", params=params, use_cache=True)
            entries = data.get("feed", {}).get("entry", []) if isinstance(data, dict) else []
            results: list[dict[str, Any]] = []
            for item in entries[:limit]:
                if not isinstance(item, dict):
                    continue
                results.append({
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "time_start": item.get("time_start"),
                    "time_end": item.get("time_end"),
                    "source": "nasa_earthdata",
                })
            return results
        except Exception as e:
            logger.warning("NASA Earthdata granules error: %s", e)
            return []
