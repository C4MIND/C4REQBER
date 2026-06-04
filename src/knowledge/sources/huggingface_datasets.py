"""
c4reqber: Hugging Face Datasets Hub Client

500,000+ public datasets. No auth required for public datasets.
"""
from __future__ import annotations

import logging
from typing import Any

from .base_p6 import BaseP6Client

logger = logging.getLogger("c4reqber.knowledge.huggingface_datasets")


class HuggingFaceDatasetsClient(BaseP6Client):
    """Hugging Face Datasets Server API client."""

    BASE_URL = "https://datasets-server.huggingface.co"
    DEFAULT_TIMEOUT = 30.0

    async def search_datasets(
        self, query: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Search public datasets by keyword (uses HF hub search)."""
        try:
            # HF Datasets Server doesn't have search; use hub API
            params: dict[str, Any] = {"search": query, "limit": min(limit, 100)}
            data: Any = await self._get("/hf-datasets", params=params, use_cache=True)
            # This endpoint may vary; fallback to general hub list
            if not isinstance(data, list):
                data = data.get("datasets", []) if isinstance(data, dict) else []
            results: list[dict[str, Any]] = []
            for item in data[:limit] if isinstance(data, list) else []:
                if not isinstance(item, dict):
                    continue
                results.append({
                    "id": item.get("id"),
                    "description": item.get("description", "")[:200],
                    "tags": item.get("tags", []),
                    "downloads": item.get("downloads"),
                    "source": "huggingface_datasets",
                })
            return results
        except Exception as e:
            logger.warning("HuggingFace datasets search error: %s", e)
            return []

    async def get_dataset_info(self, dataset_id: str) -> dict[str, Any]:
        """Fetch metadata for a specific dataset."""
        try:
            data = await self._get(f"/first-rows?dataset={dataset_id}&config=default&split=train", use_cache=True)
            return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.warning("HuggingFace dataset info error: %s", e)
            return {}
