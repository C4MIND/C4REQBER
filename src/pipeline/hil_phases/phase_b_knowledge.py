from __future__ import annotations


"""Phase B: Knowledge Acquisition — MultiSourceSearcher, bibliography."""

import logging
from typing import Any

from src.knowledge.orchestrator import MultiSourceSearcher
from src.plugins.registry import WebSearchPlugin


logger = logging.getLogger(__name__)


class PhaseB_KnowledgeAcquisition:
    """Fetch bibliography from all integrated knowledge sources."""

    def __init__(self, api_keys: dict[str, str] | None = None) -> None:
        self.searcher = WebSearchPlugin()
        self.multi_searcher = MultiSourceSearcher(api_keys=api_keys or {})

    async def run(self, topic: str, min_sources: int = 5, fallback_to_web: bool = True) -> list[dict[str, Any]]:
        """Fetch bibliography from all sources with optional web augmentation."""
        print("\n[Phase B] Knowledge Acquisition...")
        print("\n[B1/7] Searching all knowledge sources...")

        bibliography = await self._fetch_bibliography(topic)

        # Web augmentation if not enough sources
        if fallback_to_web and len(bibliography) < min_sources:
            print(f"      ⚠ Only {len(bibliography)} sources (min {min_sources}) — fetching web search...")
            extra = self.searcher.execute(topic, max_results=min_sources * 2)
            for s in extra:
                if not any(b.get("title") == s.get("title") for b in bibliography):
                    bibliography.append({
                        "title": s.get("title", ""),
                        "authors": "Unknown",
                        "year": "",
                        "venue": s.get("source_engine", "web"),
                        "url": s.get("url", ""),
                        "source": "web_search",
                        "snippet": s.get("snippet", ""),
                    })
            print(f"      After web search: {len(bibliography)} sources")

        print(f"      Found {len(bibliography)} sources from integrated databases")
        return bibliography

    async def _fetch_bibliography(self, topic: str) -> list[dict[str, Any]]:
        """Fetch from ALL integrated knowledge sources."""
        bibliography: list[dict[str, Any]] = []

        # Orchestrator-based MultiSourceSearcher (33 sources, caching, dedup)
        try:
            result = await self.multi_searcher.search_all(topic, include_web=True)
            papers = result.get("papers", [])
            for r in papers:
                bibliography.append({
                    "title": r.get("title", ""),
                    "authors": r.get("authors", "Unknown"),
                    "year": r.get("year", ""),
                    "venue": r.get("venue", r.get("_source", "")),
                    "url": r.get("url") or r.get("link") or f"https://scholar.google.com/scholar?q={r.get('title', '')[:80].replace(' ', '+')}" if r.get("title") else "",
                    "source": r.get("_source", "multi"),
                    "citations": r.get("citationCount", 0),
                    "snippet": r.get("abstract", r.get("snippet", "")),
                })
            print(f"      MultiSourceSearcher: {len(papers)} papers from {result.get('sources_used', 0)} sources")
            if len(bibliography) < 5:
                logger.warning("MultiSourceSearcher returned <5 bibliography entries (%d) — quality gate will flag", len(bibliography))
        except Exception as e:
            logger.warning("MultiSourceSearcher failed: %s", e)

        return bibliography
