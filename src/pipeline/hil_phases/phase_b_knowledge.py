from __future__ import annotations


"""Phase B: Knowledge Acquisition — MultiSourceSearcher, bibliography."""

import logging
from typing import Any

from src.knowledge.orchestrator import MultiSourceSearcher


logger = logging.getLogger(__name__)


class PhaseB_KnowledgeAcquisition:
    """Fetch bibliography from all integrated knowledge sources."""

    def __init__(self, api_keys: dict[str, str] | None = None) -> None:
        self.multi_searcher = MultiSourceSearcher(api_keys=api_keys or {})

    async def run(
        self, topic: str, min_sources: int = 5, fallback_to_web: bool = True
    ) -> list[dict[str, Any]]:
        """Fetch bibliography from all sources (include_web when under min)."""
        print("\n[Phase B] Knowledge Acquisition...")
        print("\n[B1/7] Searching all knowledge sources...")

        bibliography = await self._fetch_bibliography(topic, include_web=False)

        if fallback_to_web and len(bibliography) < min_sources:
            print(
                f"      ⚠ Only {len(bibliography)} sources (min {min_sources}) — "
                "retrying with web-capable sources (Tavily/Exa if keyed)..."
            )
            extra = await self._fetch_bibliography(topic, include_web=True)
            seen = {b.get("title") for b in bibliography}
            for s in extra:
                if s.get("title") and s.get("title") not in seen:
                    bibliography.append(s)
                    seen.add(s.get("title"))
            print(f"      After web-capable search: {len(bibliography)} sources")

        if len(bibliography) < min_sources:
            logger.warning(
                "Bibliography below min_sources (%d < %d) — no fake padding",
                len(bibliography),
                min_sources,
            )

        print(f"      Found {len(bibliography)} sources from integrated databases")
        return bibliography

    async def _fetch_bibliography(self, topic: str, *, include_web: bool) -> list[dict[str, Any]]:
        """Fetch from integrated knowledge sources."""
        bibliography: list[dict[str, Any]] = []

        try:
            result = await self.multi_searcher.search_all(topic, include_web=include_web)
            papers = result.get("papers", [])
            for r in papers:
                title = r.get("title", "")
                real_url = (r.get("url") or r.get("link") or "").strip()
                if real_url and "example.com" in real_url:
                    real_url = ""
                if real_url and "scholar.google.com/scholar?q=" in real_url:
                    real_url = ""  # synthesized search links are not citations
                bibliography.append(
                    {
                        "title": title,
                        "authors": r.get("authors", "Unknown"),
                        "year": r.get("year", ""),
                        "venue": r.get("venue", r.get("_source", "")),
                        "url": real_url,
                        "source": r.get("_source", "multi"),
                        "citations": r.get("citationCount", 0),
                        "snippet": r.get("abstract", r.get("snippet", "")),
                    }
                )
            print(
                f"      MultiSourceSearcher: {len(papers)} papers from "
                f"{result.get('sources_used', 0)} sources"
            )
            if len(bibliography) < 5:
                logger.warning(
                    "MultiSourceSearcher returned <5 bibliography entries (%d)",
                    len(bibliography),
                )
        except Exception as e:
            logger.warning("MultiSourceSearcher failed: %s", e)

        return bibliography
