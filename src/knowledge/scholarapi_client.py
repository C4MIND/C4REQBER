from __future__ import annotations

import json
import os
from typing import Any

import httpx


class ScholarAPIClient:
    """ScholarAPIClient."""
    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key or os.getenv("SCHOLARA_API_KEY", "")
        self.base_url = "https://scholarapi.net/api/v1"

    async def __aenter__(self) -> ScholarAPIClient:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    async def search(self, query: str, max_results: int = 10, limit: int = 10) -> list[dict[str, Any]]:
        """Search academic papers via ScholarAPI."""
        if not self.api_key:
            return []

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.base_url}/search",
                    params={"q": query, "limit": max_results or limit},
                    headers={"X-API-Key": self.api_key},
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("results", [])
                else:
                    print(f"ScholarAPI error: {response.status_code} - {response.text[:200]}")
                    return []
        except (TimeoutError, TypeError, httpx.HTTPError, json.JSONDecodeError) as e:
            print(f"ScholarAPI exception: {e}")
            return []

    def search_sync(self, query: str, max_results: int = 10) -> list[dict[str, Any]]:
        """Synchronous search (for non-async contexts)."""
        if not self.api_key:
            return []

        try:
            with httpx.Client(timeout=10) as client:
                response = client.get(
                    f"{self.base_url}/search",
                    params={"q": query, "limit": max_results},
                    headers={"X-API-Key": self.api_key},
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("results", [])
                else:
                    return []
        except (httpx.HTTPError, json.JSONDecodeError):
            return []
