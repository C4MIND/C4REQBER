"""
c4reqber: X (Twitter) API v2 Client

Posts discoveries, fetches timeline, searches tweets.
Requires X API v2 credentials in environment:
  TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET

Get keys at: https://developer.x.com/en/portal/dashboard
"""
from __future__ import annotations

import os
from typing import Any

import httpx


class TwitterClient:
    """X (Twitter) API v2 client for posting and reading."""

    BASE_URL = "https://api.twitter.com/2"

    def __init__(self) -> None:
        self.api_key = os.getenv("TWITTER_API_KEY", "")
        self.api_secret = os.getenv("TWITTER_API_SECRET", "")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN", "")
        self.access_secret = os.getenv("TWITTER_ACCESS_SECRET", "")
        self._bearer: str | None = None

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.access_token)

    async def _ensure_bearer(self) -> str:
        if not self._bearer:
            async with httpx.AsyncClient():
                pass  # type: ignore[import-untyped]
            self._bearer = f"{self.api_key}:{self.api_secret}"
        return self._bearer

    async def post_tweet(self, text: str) -> dict[str, Any]:
        """Post a tweet. Requires OAuth 1.0a User Context."""
        if not self.configured:
            return {"error": "Twitter API not configured. Set TWITTER_* env vars."}

        try:
            from requests_oauthlib import OAuth1Session  # type: ignore[import-untyped]

            oauth = OAuth1Session(
                self.api_key,
                client_secret=self.api_secret,
                resource_owner_key=self.access_token,
                resource_owner_secret=self.access_secret,
            )
            resp = oauth.post(
                f"{self.BASE_URL}/tweets",
                json={"text": text[:280]},
                timeout=30,
            )
            if resp.status_code in (200, 201):
                return resp.json()
            return {"error": f"Twitter API error {resp.status_code}: {resp.text[:200]}"}
        except ImportError:
            return await self._post_bearer(text)
        except Exception as e:
            return {"error": str(e)}

    async def _post_bearer(self, text: str) -> dict[str, Any]:
        """Fallback: OAuth 2.0 Bearer token (read-only, may fail for posting)."""
        async with httpx.AsyncClient() as c:
            resp = await c.post(
                f"{self.BASE_URL}/tweets",
                headers={"Authorization": f"Bearer {self.access_token}"},
                json={"text": text[:280]},
                timeout=30,
            )
            if resp.status_code == 201:
                return resp.json()
            return {"error": f"OAuth 2.0 posting not supported ({resp.status_code}). Set TWITTER_ACCESS_SECRET for OAuth 1.0a."}

    async def get_user_tweets(self, username: str, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent tweets from a user."""
        if not self.configured:
            return []

        async with httpx.AsyncClient() as c:
            resp = await c.get(
                f"{self.BASE_URL}/users/by/username/{username}",
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=15,
            )
            if resp.status_code != 200:
                return []
            user_id = resp.json().get("data", {}).get("id", "")

            resp2 = await c.get(
                f"{self.BASE_URL}/users/{user_id}/tweets",
                headers={"Authorization": f"Bearer {self.access_token}"},
                params={"max_results": limit, "tweet.fields": "created_at,public_metrics"},
                timeout=15,
            )
            if resp2.status_code == 200:
                return resp2.json().get("data", [])
            return []

    async def search_tweets(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search recent tweets."""
        if not self.configured:
            return []

        async with httpx.AsyncClient() as c:
            resp = await c.get(
                f"{self.BASE_URL}/tweets/search/recent",
                headers={"Authorization": f"Bearer {self.access_token}"},
                params={"query": query, "max_results": limit, "tweet.fields": "created_at,public_metrics"},
                timeout=15,
            )
            if resp.status_code == 200:
                return resp.json().get("data", [])
            return []
