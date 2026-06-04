"""
c4reqber: ORCID Public API Client

Author disambiguation and works retrieval.
Requires free client registration.
"""
from __future__ import annotations

import base64
import logging
import os
from typing import Any

from .base_p6 import BaseP6Client

logger = logging.getLogger("c4reqber.knowledge.orcid")


class OrcidClient(BaseP6Client):
    """ORCID Public API v3.0 client."""

    BASE_URL = "https://pub.orcid.org/v3.0"
    DEFAULT_TIMEOUT = 30.0

    def __init__(self, client_id: str = "", client_secret: str = "") -> None:
        self.client_id = client_id or os.getenv("ORCID_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("ORCID_CLIENT_SECRET", "")
        self._token: str | None = None
        super().__init__(headers={"Accept": "application/json"})

    async def _ensure_token(self) -> str | None:
        if self._token:
            return self._token
        if not self.client_id or not self.client_secret:
            return None
        try:
            creds = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
            headers = {
                "Authorization": f"Basic {creds}",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            }
            response = await self._client.post(  # type: ignore[union-attr]
                "https://orcid.org/oauth/token",
                data={"grant_type": "client_credentials", "scope": "/read-public"},
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            self._token = data.get("access_token") if isinstance(data, dict) else None
            return self._token
        except Exception as e:
            logger.warning("ORCID token error: %s", e)
            return None

    async def search_orcid(
        self, query: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Search researchers by name or keyword."""
        token = await self._ensure_token()
        if not token:
            logger.warning("ORCID: no token, skipping search")
            return []
        try:
            headers = {**self._client.headers, "Authorization": f"Bearer {token}"}
            params: dict[str, Any] = {"q": query, "rows": min(limit, 100)}
            url = f"{self.BASE_URL}/expanded-search"
            response = await self._client.get(url, params=params, headers=headers)  # type: ignore[union-attr]
            response.raise_for_status()
            data = response.json()
            results = data.get("expanded-result", []) if isinstance(data, dict) else []
            out: list[dict[str, Any]] = []
            for item in results[:limit]:
                if not isinstance(item, dict):
                    continue
                out.append({
                    "orcid_id": item.get("orcid-id"),
                    "given_names": item.get("given-names"),
                    "family_names": item.get("family-names"),
                    "institution": item.get("institution-name", []),
                    "source": "orcid",
                })
            return out
        except Exception as e:
            logger.warning("ORCID search error: %s", e)
            return []

    async def get_works(self, orcid_id: str) -> list[dict[str, Any]]:
        """Fetch works for a given ORCID iD."""
        token = await self._ensure_token()
        if not token:
            return []
        try:
            headers = {**self._client.headers, "Authorization": f"Bearer {token}"}
            url = f"{self.BASE_URL}/{orcid_id}/works"
            response = await self._client.get(url, headers=headers)  # type: ignore[union-attr]
            response.raise_for_status()
            data = response.json()
            groups = data.get("group", []) if isinstance(data, dict) else []
            out: list[dict[str, Any]] = []
            for g in groups:
                summaries = g.get("work-summary", [])
                for s in summaries[:5]:
                    out.append({
                        "title": s.get("title", {}).get("title", {}).get("value"),
                        "type": s.get("type"),
                        "publication_date": s.get("publication-date", {}),
                        "source": "orcid",
                    })
            return out
        except Exception as e:
            logger.warning("ORCID works error: %s", e)
            return []
