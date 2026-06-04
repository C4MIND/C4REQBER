"""
Mastodon Client — AGPLv3, FREE API
License: AGPLv3 (open-source)
Note: Free to use, requires instance account
"""

from __future__ import annotations

import os
from typing import Any

import httpx


class MastodonClient:
    """Mastodon API client (free, AGPLv3)."""

    def __init__(self, instance: str = "mastodon.social", access_token: str | None = None, token: str | None = None) -> None:
        self.instance = instance
        self.base_url = f"https://{instance}/api/v1"
        # Support both 'access_token' and 'token' parameters
        self.access_token = access_token or token or os.getenv("MASTODON_ACCESS_TOKEN")
        self.headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}

    async def search(self, query: str, max_results: int = 50, search_type: str = "statuses") -> list[dict[str, Any]]:
        """Search Mastodon posts, accounts, or hashtags."""
        if not self.access_token:
            return []

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/search",
                headers=self.headers,
                params={"q": query, "limit": max_results, "type": search_type},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data.get(search_type, [])

    async def get_trending_tags(self) -> list[dict[str, Any]]:
        """Get trending hashtags."""
        async with httpx.AsyncClient() as client:
            headers = self.headers if self.access_token else {}
            response = await client.get(
                f"{self.base_url}/trends/tags",
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_account(self, username: str) -> dict[str, Any]:
        """Get account info by username."""
        if not self.access_token:
            return {"error": "MASTODON_ACCESS_TOKEN required"}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/accounts/lookup",
                headers=self.headers,
                params={"acct": username},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def post_status(self, content: str, visibility: str = "public") -> dict[str, Any]:
        """Post a status/toot."""
        if not self.access_token:
            return {"error": "MASTODON_ACCESS_TOKEN required"}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/statuses",
                headers=self.headers,
                data={"status": content, "visibility": visibility},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_timeline(self, timeline: str = "home", limit: int = 40) -> list[dict[str, Any]]:
        """Get timeline (home, local, public, tag/:hashtag)."""
        if not self.access_token:
            return []

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/timelines/{timeline}",
                headers=self.headers,
                params={"limit": limit},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_status(self, status_id: str) -> dict[str, Any]:
        """Get a single status by ID."""
        if not self.access_token:
            return {"error": "MASTODON_ACCESS_TOKEN required"}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/statuses/{status_id}",
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_instance_info(self) -> dict[str, Any]:
        """Get instance information."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/instance",
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
