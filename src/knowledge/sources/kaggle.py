"""
c4reqber: Kaggle Dataset Client

Access to 200k+ public datasets for causal discovery and benchmarking.
License: Free API key required for download
Docs: https://www.kaggle.com/docs/api
"""
from __future__ import annotations

import logging
import os
from typing import Any

from .base_p6 import BaseP6Client

logger = logging.getLogger("c4reqber.knowledge.kaggle")


class KaggleClient(BaseP6Client):
    """Kaggle API client for dataset search and metadata."""

    BASE_URL = "https://www.kaggle.com/api/v1"
    DEFAULT_TIMEOUT = 60.0

    def __init__(self, username: str = "", api_key: str = "") -> None:
        self.username = username or os.getenv("KAGGLE_USERNAME", "")
        self.api_key = api_key or os.getenv("KAGGLE_KEY", "")
        if self.username and self.api_key:
            from httpx import BasicAuth
            auth = BasicAuth(self.username, self.api_key)
            super().__init__(auth=auth)
        else:
            super().__init__()

    async def search_datasets(
        self,
        query: str,
        page: int = 1,
        max_size_bytes: int | None = None,
    ) -> list[dict[str, Any]]:
        """Search public datasets."""
        if not self.username or not self.api_key:
            logger.warning("KAGGLE_USERNAME and KAGGLE_KEY not set")
            return []
        params: dict[str, Any] = {"search": query, "page": page}
        if max_size_bytes:
            params["maxSize"] = max_size_bytes
        try:
            result: Any = await self._get("/datasets/list", params=params)
            return result
        except Exception as e:
            logger.warning("Kaggle search error: %s", e)
            return []

    async def get_dataset(self, owner: str, dataset: str) -> dict[str, Any]:
        """Get metadata for a specific dataset."""
        if not self.username:
            return {}
        try:
            return await self._get(f"/datasets/view/{owner}/{dataset}")
        except Exception as e:
            logger.warning("Kaggle dataset error: %s", e)
            return {}

    async def list_files(self, owner: str, dataset: str) -> list[dict[str, Any]]:
        """List files in a dataset."""
        if not self.username:
            return []
        try:
            result: Any = await self._get(f"/datasets/list/{owner}/{dataset}")
            return result
        except Exception as e:
            logger.warning("Kaggle list files error: %s", e)
            return []

    async def download_link(self, owner: str, dataset: str, file_name: str) -> str:
        """Get a direct download URL for a file (requires auth)."""
        if not self.username:
            return ""
        try:
            response = await self._client.get(  # type: ignore[union-attr]
                f"{self.BASE_URL}/datasets/download/{owner}/{dataset}/{file_name}",
                follow_redirects=True,
            )
            response.raise_for_status()
            return str(response.url)
        except Exception as e:
            logger.warning("Kaggle download error: %s", e)
            return ""
