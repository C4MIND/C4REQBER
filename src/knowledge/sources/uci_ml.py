"""
c4reqber: UCI ML Repository Client

Access to the UCI Machine Learning Repository datasets.
License: Free academic use
"""
from __future__ import annotations

import logging
from typing import Any

from .base_p6 import BaseP6Client

logger = logging.getLogger("c4reqber.knowledge.uci_ml")


class UciMlClient(BaseP6Client):
    """UCI Machine Learning Repository API client.

    Uses the JSON API endpoint exposed by the UCI ML Repository.
    """

    BASE_URL = "https://archive.ics.uci.edu/api"
    DEFAULT_TIMEOUT = 30.0

    async def search_datasets(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search datasets by keyword.

        Args:
            query: Keyword (e.g. "iris", "regression", "credit").
            limit: Max results.
        """
        try:
            data = await self._get(
                "/datasets",
                params={"search": query, "limit": limit},
                use_cache=True,
            )
            datasets = data.get("datasets", []) if isinstance(data, dict) else []
            results: list[dict[str, Any]] = []
            for item in datasets[:limit]:
                if not isinstance(item, dict):
                    continue
                results.append({
                    "id": item.get("id"),
                    "name": item.get("name", ""),
                    "abstract": item.get("abstract", ""),
                    "area": item.get("area", ""),
                    "task_types": item.get("task_types", []),
                    "source": "uci_ml",
                })
            return results
        except Exception as e:
            logger.warning("UCI ML search error: %s", e)
            return []

    async def get_dataset(self, dataset_id: int) -> dict[str, Any]:
        """Fetch metadata for a specific dataset.

        Args:
            dataset_id: Numeric dataset ID.
        """
        try:
            data = await self._get(f"/datasets/{dataset_id}", use_cache=True)
            return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.warning("UCI ML dataset error: %s", e)
            return {}
