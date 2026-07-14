from __future__ import annotations

from typing import Any

import httpx

from .base import BaseSourceAdapter


class DoajAdapter(BaseSourceAdapter):
    """DOAJ — Directory of Open Access Journals."""

    @property
    def source_id(self) -> str:
        return "doaj"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Search."""
        url = "https://doaj.org/api/v2/search/articles"
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{url}/{query}",
                params={
                    "pageSize": min(limit, 100),
                    "page": 1,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return self._normalize(data.get("results", []))

    def _normalize(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for item in data:
            bibjson = item.get("bibjson", {})
            title = bibjson.get("title", "")
            abstract = bibjson.get("abstract", "")
            authors: list[str] = []
            for a in bibjson.get("author", []):
                name = a.get("name", "")
                if name:
                    authors.append(name)
            year = int(bibjson.get("year", 0) or 0)
            journals = bibjson.get("journal", {})
            journal = journals.get("title", "") if isinstance(journals, dict) else ""
            doi = ""
            for ident in bibjson.get("identifier", []):
                if isinstance(ident, dict) and ident.get("type") == "doi":
                    doi = ident.get("id", "")
            result.append({
                "title": title,
                "authors": authors,
                "year": year,
                "abstract": abstract,
                "doi": doi,
                "venue": journal,
                "citation_count": 0,
                "source": "doaj",
                "source_name": "DOAJ",
                "sources": ["DOAJ"],
            })
        return result
