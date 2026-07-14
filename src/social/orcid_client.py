"""c4reqber: ORCID Client — register works (metadata) on ORCID records."""
from __future__ import annotations

import os
from typing import Any

import httpx


class ORCIDClient:
    """ORCID Member API client for adding works to researcher profiles.

    Auth: ORCID_CLIENT_ID, ORCID_CLIENT_SECRET. Uses OAuth2 client credentials.
    ORCID Member API access: free for non-profits.
    """

    TOKEN_URL = "https://orcid.org/oauth/token"
    API_BASE = "https://api.orcid.org/v3.0"

    def __init__(self, dry_run: bool = False) -> None:
        self.client_id = os.getenv("ORCID_CLIENT_ID", "")
        self.client_secret = os.getenv("ORCID_CLIENT_SECRET", "")
        self.dry_run = dry_run
        self._token: str | None = None

    @property
    def configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    async def _get_token(self) -> str:
        if self._token:
            return self._token
        async with httpx.AsyncClient() as c:
            resp = await c.post(
                self.TOKEN_URL,
                data={"client_id": self.client_id, "client_secret": self.client_secret,
                      "grant_type": "client_credentials", "scope": "/activities/update /read-limited"},
                headers={"Accept": "application/json"},
                timeout=15,
            )
            if resp.status_code == 200:
                self._token = resp.json().get("access_token", "")
            return self._token or ""

    async def add_work(self, orcid_id: str, work: dict[str, Any]) -> dict[str, Any]:
        """Add a work entry to an ORCID record."""
        if self.dry_run:
            return {"status": "ok", "orcid": orcid_id, "_dry_run": True}
        if not self.configured:
            return {"error": "ORCID_CLIENT_ID and ORCID_CLIENT_SECRET required"}

        token = await self._get_token()
        if not token:
            return {"error": "ORCID OAuth2 token request failed"}

        async with httpx.AsyncClient() as c:
            resp = await c.post(
                f"{self.API_BASE}/{orcid_id}/work",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/vnd.orcid+json"},
                json={
                    "title": {"title": {"value": work.get("title", "Untitled")}},
                    "type": work.get("type", "preprint"),
                    "external-ids": {"external-id": [
                        {"external-id-type": "doi", "external-id-value": work.get("doi", ""),
                         "external-id-relationship": "self"}
                    ]} if work.get("doi") else None,
                },
                timeout=15,
            )
            if resp.status_code in (200, 201):
                return {"status": "ok", "orcid": orcid_id}
            return {"error": f"ORCID HTTP {resp.status_code}: {resp.text[:200]}"}
