from __future__ import annotations

from typing import Any

from .base_p6_adapter import BaseP6SourceAdapter


class EuropePmcAdapter(BaseP6SourceAdapter):
    """Europe PMC — 41M+ abstracts, life sciences."""

    BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest"
    DEFAULT_TIMEOUT = 15.0

    @property
    def source_id(self) -> str:
        return "europe_pmc"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "query": query,
            "resultType": "core",
            "pageSize": min(limit, 100),
            "format": "json",
        }
        data = await self._get_with_retry("/search", params=params, use_cache=True)
        return self._normalize(data.get("resultList", {}).get("result", []))

    def _normalize(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for item in data:
            ai = item.get("authorString", "")
            authors = [a.strip() for a in ai.split(",") if a.strip()] if ai else []
            result.append({
                "title": item.get("title", ""),
                "authors": authors,
                "year": int(item.get("pubYear", 0) or 0),
                "abstract": item.get("abstractText", "") or "",
                "doi": item.get("doi", ""),
                "pmid": item.get("pmid", ""),
                "pmcid": item.get("pmcid", ""),
                "venue": item.get("journalTitle", ""),
                "citation_count": item.get("citedByCount", 0) or 0,
                "source": self.source_id,
                "source_name": "Europe PMC",
                "sources": ["Europe PMC"],
            })
        return result
