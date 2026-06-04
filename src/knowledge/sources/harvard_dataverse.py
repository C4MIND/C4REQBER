"""
c4reqber: Harvard Dataverse Client

Search across the Harvard Dataverse repository network.
License: Free academic use (API key optional for higher rate limits)
"""
from __future__ import annotations

import logging
import os
from typing import Any

from .base_p6 import BaseP6Client

logger = logging.getLogger("c4reqber.knowledge.harvard_dataverse")


class HarvardDataverseClient(BaseP6Client):
    """Harvard Dataverse API client."""

    BASE_URL = "https://dataverse.harvard.edu/api"
    DEFAULT_TIMEOUT = 30.0

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key or os.getenv("HARVARD_DATAVERSE_API_KEY", "")
        headers = {}
        if self.api_key:
            headers["X-Dataverse-key"] = self.api_key
        super().__init__(headers=headers)

    async def search_datasets(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search datasets across Harvard Dataverse.

        Args:
            query: Search term.
            limit: Max results.
        """
        try:
            params: dict[str, Any] = {
                "q": query,
                "type": "dataset",
                "per_page": limit,
            }
            if self.api_key:
                params["key"] = self.api_key
            data = await self._get("/search", params=params, use_cache=True)
            items = data.get("data", {}).get("items", []) if isinstance(data, dict) else []
            results: list[dict[str, Any]] = []
            for item in items[:limit]:
                if not isinstance(item, dict):
                    continue
                results.append({
                    "global_id": item.get("global_id", ""),
                    "name": item.get("name", ""),
                    "url": item.get("url", ""),
                    "authors": item.get("authors", []),
                    "published_at": item.get("published_at", ""),
                    "source": "harvard_dataverse",
                })
            return results
        except Exception as e:
            logger.warning("Harvard Dataverse search error: %s", e)
            return []

    async def get_dataset_metadata(self, persistent_id: str) -> dict[str, Any]:
        """Fetch metadata for a dataset by its persistent ID.

        Args:
            persistent_id: DOI or Handle (e.g. 'doi:10.7910/DVN/ABC123').
        """
        try:
            params: dict[str, Any] = {}
            if self.api_key:
                params["key"] = self.api_key
            data = await self._get(
                f"/datasets/:persistentId",
                params={"persistentId": persistent_id, **params},
                use_cache=True,
            )
            return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.warning("Harvard Dataverse metadata error: %s", e)
            return {}
