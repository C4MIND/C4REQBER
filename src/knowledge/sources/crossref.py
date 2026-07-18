from __future__ import annotations

from typing import Any

from src.knowledge.contact_email import contact_email

from .base_p6_adapter import BaseP6SourceAdapter


class CrossrefAdapter(BaseP6SourceAdapter):
    """CrossRef — DOI metadata, 140M+ records."""

    BASE_URL = "https://api.crossref.org"
    DEFAULT_TIMEOUT = 15.0

    @property
    def source_id(self) -> str:
        return "crossref"

    def __init__(self, **kwargs: Any) -> None:
        headers = kwargs.pop("headers", {})
        email = contact_email()
        headers.setdefault("User-Agent", f"c4reqber (mailto:{email})")
        super().__init__(headers=headers, **kwargs)

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "query": query,
            "rows": min(limit, 1000),
            "mailto": contact_email(),
        }
        data = await self._get_with_retry("/works", params=params, use_cache=True)
        items = data.get("message", {}).get("items", [])
        return self._normalize(items)

    def _normalize(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for item in data:
            authors = []
            for a in item.get("author", []):
                given = a.get("given", "")
                family = a.get("family", "")
                name = f"{given} {family}".strip()
                if name:
                    authors.append(name)
            date_parts = (
                item.get("published-print")
                or item.get("published-online")
                or item.get("published")
                or {}
            ).get("date-parts") or [[0]]
            year = date_parts[0][0] if date_parts and date_parts[0] else 0
            containers = item.get("container-title", [])
            venue_name = containers[0] if containers else ""
            doi = item.get("DOI", "")
            result.append(
                {
                    "title": (item.get("title") or [""])[0],
                    "authors": authors,
                    "year": year or 0,
                    "abstract": item.get("abstract", "") or "",
                    "doi": doi,
                    "venue": venue_name,
                    "citation_count": item.get("is-referenced-by-count", 0) or 0,
                    "source": self.source_id,
                    "source_name": "CrossRef",
                    "sources": ["CrossRef"],
                }
            )
        return result
