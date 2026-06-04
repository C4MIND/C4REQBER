"""Web-Enhanced Discovery — enrich CDI pipeline with Tavily + Exa search.

Usage in discovery pipeline:
  1. Extract contradiction
  2. Search Tavily + Exa for recent context
  3. Feed results into hypothesis synthesizer
  4. Generate falsifiability criteria
"""
from __future__ import annotations

import asyncio
from typing import Any

from src.integrations.exa_client import ExaClient
from src.integrations.tavily_client import TavilyClient


class WebEnhancedDiscovery:
    """Enriches discovery with real-time web search before hypothesis synthesis."""

    def __init__(self) -> None:
        self.tavily = TavilyClient()
        self.exa = ExaClient()

    async def enrich_context(
        self,
        problem: str,
        contradiction: str = "",
        max_results: int = 5,
    ) -> dict[str, Any]:
        """Search Tavily + Exa for context, return merged results."""
        query = f"{problem} {contradiction}".strip()
        if len(query) > 200:
            query = query[:200]

        tasks: list[Any] = []
        if self.tavily.enabled and self.tavily.budget.can_search("basic"):
            tasks.append(self._search_tavily(query, max_results))
        else:
            tasks.append(asyncio.sleep(0))  # no-op

        if self.exa.enabled:
            tasks.append(self._search_exa(query, max_results))
        else:
            tasks.append(asyncio.sleep(0))

        tavily_result, exa_result = await asyncio.gather(*tasks)

        # Merge and deduplicate by URL
        seen_urls = set()
        merged = []
        for source, result in [("tavily", tavily_result), ("exa", exa_result)]:
            for item in result:
                url = item.get("url", "")
                if url and url in seen_urls:
                    continue
                if url:
                    seen_urls.add(url)
                merged.append({
                    **item,
                    "source": source,
                })

        return {
            "query": query,
            "tavily_hits": len(tavily_result),
            "exa_hits": len(exa_result),
            "merged_results": merged[:max_results * 2],
            "context_summary": self._summarize(merged[:max_results * 2]),
        }

    async def _search_tavily(self, query: str, limit: int) -> list[dict[str, Any]]:
        try:
            result = await self.tavily.search(query, max_results=limit, search_depth="basic")
            return result.get("results", [])
        except (ConnectionError, TimeoutError, RuntimeError):
            return []

    async def _search_exa(self, query: str, limit: int) -> list[dict[str, Any]]:
        try:
            result = await self.exa.search(query, num_results=limit)
            return result.get("results", [])
        except (ConnectionError, TimeoutError, RuntimeError):
            return []

    @staticmethod
    def _summarize(results: list[dict]) -> str:
        """Create a brief summary of search results for LLM context."""
        if not results:
            return "No recent web context found."
        summaries = []
        for r in results[:5]:
            title = r.get("title", "")[:80]
            source = r.get("source", "?")
            summaries.append(f"- [{source}] {title}")
        return "\n".join(summaries)
