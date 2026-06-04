"""c4reqber: Reddit OAuth2 Client — submit link, search."""
from __future__ import annotations

import os
from typing import Any

import httpx


class RedditClient:
    """Reddit API OAuth2 client for posting preprint links.

    Auth: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD.
    App registration: https://www.reddit.com/prefs/apps (script type).

    Free tier: 100 requests/minute. OAuth2 required.
    """

    BASE = "https://oauth.reddit.com"

    def __init__(self, dry_run: bool = False) -> None:
        self.client_id = os.getenv("REDDIT_CLIENT_ID", "")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
        self.username = os.getenv("REDDIT_USERNAME", "")
        self.password = os.getenv("REDDIT_PASSWORD", "")
        self.dry_run = dry_run
        self._token: str | None = None

    @property
    def configured(self) -> bool:
        return bool(self.client_id and self.username)

    async def _auth(self) -> str:
        if self._token:
            return self._token
        async with httpx.AsyncClient() as c:
            resp = await c.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=(self.client_id, self.client_secret),
                data={"grant_type": "password", "username": self.username, "password": self.password},
                headers={"User-Agent": "c4reqber/5.4.0"},
                timeout=15,
            )
            if resp.status_code == 200:
                self._token = resp.json()["access_token"]
            return self._token or ""

    async def submit_link(self, subreddit: str, title: str, url: str) -> dict[str, Any]:
        """Post a link to a subreddit."""
        if self.dry_run:
            return {"id": "dry-run-post", "url": url, "_dry_run": True}
        if not self.configured:
            return {"error": "Reddit not configured. Set REDDIT_CLIENT_ID, REDDIT_USERNAME, REDDIT_PASSWORD."}

        token = await self._auth()
        if not token:
            return {"error": "Reddit OAuth2 authentication failed"}

        async with httpx.AsyncClient() as c:
            resp = await c.post(
                f"{self.BASE}/api/submit",
                headers={"Authorization": f"Bearer {token}", "User-Agent": "c4reqber/5.4.0"},
                data={"sr": subreddit, "kind": "link", "title": title[:300], "url": url, "resubmit": "true"},
                timeout=15,
            )
            if resp.status_code == 200:
                return resp.json()
            return {"error": f"Reddit HTTP {resp.status_code}: {resp.text[:200]}"}
