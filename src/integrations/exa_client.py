"""Exa.ai Search Integration — Neural search for research papers and web."""
from __future__ import annotations

import os
from typing import Any

import httpx


EXA_API_URL = "https://api.exa.ai"


class ExaClient:
    """Exa.ai search client — $9.91 balance."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("EXA_API_KEY")
        self.enabled = bool(self.api_key)

    async def search(
        self,
        query: str,
        num_results: int = 5,
        category: str = "research paper",  # research paper | news | tweet | etc.
    ) -> dict[str, Any]:
        """Search Exa.ai and return results."""
        if not self.enabled:
            raise RuntimeError("EXA_API_KEY not set")

        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{EXA_API_URL}/search",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "query": query,
                    "numResults": num_results,
                    "type": "auto",
                    "category": category if category else None,
                },
                timeout=30,
            )
            r.raise_for_status()
            return r.json()

    async def get_contents(self, urls: list[str]) -> dict[str, Any]:
        """Fetch contents for URLs from Exa."""
        if not self.enabled:
            raise RuntimeError("EXA_API_KEY not set")

        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{EXA_API_URL}/contents",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"urls": urls},
                timeout=30,
            )
            r.raise_for_status()
            return r.json()

    def status(self) -> dict[str, Any]:
        """Return client status for dashboard."""
        return {
            "name": "Exa.ai",
            "enabled": self.enabled,
            "provider": "exa",
            "icon": "🧠",
            "balance": "$9.91",
        }
