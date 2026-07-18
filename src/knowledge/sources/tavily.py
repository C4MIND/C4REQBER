"""Tavily adapter for knowledge orchestrator."""

from __future__ import annotations

from typing import Any

from src.integrations.tavily_client import TavilyClient
from src.knowledge.sources.base import BaseSourceAdapter


class TavilyAdapter(BaseSourceAdapter):
    """Adapter for Tavily AI search (1000 credits/month)."""

    @property
    def source_id(self) -> str:
        return "tavily"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Search."""
        client = TavilyClient(self.api_key)
        result = await client.search(query, max_results=min(limit, 10), search_depth="basic")
        papers = []
        for r in result.get("results", []):
            papers.append(
                {
                    "title": r.get("title", ""),
                    "authors": [],
                    "year": None,
                    "url": r.get("url", ""),
                    "doi": None,
                    "abstract": r.get("content", "")[:500],
                    "source": "tavily",
                    "type": "web",
                    "citations": 0,
                }
            )
        return papers
