"""Exa.ai adapter for knowledge orchestrator."""

from __future__ import annotations

from typing import Any

from src.integrations.exa_client import ExaClient
from src.knowledge.sources.base import BaseSourceAdapter


class ExaAdapter(BaseSourceAdapter):
    """Adapter for Exa.ai neural search ($9.91 balance)."""

    @property
    def source_id(self) -> str:
        return "exa"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Search."""
        client = ExaClient(self.api_key)
        result = await client.search(query, num_results=min(limit, 10))
        papers = []
        for r in result.get("results", []):
            papers.append(
                {
                    "title": r.get("title", ""),
                    "authors": [],
                    "year": None,
                    "url": r.get("url", ""),
                    "doi": None,
                    "abstract": r.get("text", "")[:500] if "text" in r else "",
                    "source": "exa",
                    "type": "web",
                    "citations": 0,
                }
            )
        return papers
