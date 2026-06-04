from __future__ import annotations

import logging
from typing import Any

from .base_p6_adapter import BaseP6SourceAdapter


logger = logging.getLogger("c4reqber.knowledge.semantic_scholar")


class SemanticScholarAdapter(BaseP6SourceAdapter):
    """Semantic Scholar — 200M+ papers, citation graph, free."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    DEFAULT_TIMEOUT = 15.0

    @property
    def source_id(self) -> str:
        return "semantic_scholar"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        params = {
            "query": query,
            "limit": min(limit, 100),
            "fields": "title,authors,year,abstract,externalIds,citationCount,publicationVenue,url",
        }
        data = await self._get_with_retry("/paper/search", params=params, use_cache=True)
        return self._normalize(data.get("data", []))

    def _normalize(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for item in data:
            authors = [a.get("name", "") for a in item.get("authors", []) if isinstance(a, dict)]
            ex_ids = item.get("externalIds") or {}
            doi = ex_ids.get("DOI", "") if isinstance(ex_ids, dict) else ""
            venue = item.get("publicationVenue") or {}
            venue_name = venue.get("name", "") if isinstance(venue, dict) else ""
            result.append({
                "title": item.get("title", ""),
                "authors": authors,
                "year": int(item.get("year") or 0),
                "abstract": item.get("abstract") or "",
                "doi": doi,
                "arxiv_id": ex_ids.get("ArXiv", "") if isinstance(ex_ids, dict) else "",
                "venue": venue_name,
                "citation_count": item.get("citationCount", 0) or 0,
                "url": item.get("url", ""),
                "source": self.source_id,
                "source_name": "Semantic Scholar",
                "sources": ["Semantic Scholar"],
            })
        return result
