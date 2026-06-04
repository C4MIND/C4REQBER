from __future__ import annotations

import logging
from typing import Any

import httpx

from .base import BaseSourceAdapter


logger = logging.getLogger("c44tcdi.knowledge.multi_source")


class BaseSearchAdapter(BaseSourceAdapter):
    """BASE — Bielefeld Academic Search Engine, 150M+ docs."""

    @property
    def source_id(self) -> str:
        return "base"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Search."""
        if not self.api_key:
            logger.debug("BASE: API key required")
            return []

        url = "https://api.base-search.net/cgi-bin/BaseHttpSearch"
        params: dict[str, Any] = {
            "func": "search",
            "query": query,
            "hits": min(limit, 100),
            "apikey": self.api_key,
            "format": "json",
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            return self._normalize(data.get("response", {}).get("docs", []))

    def _normalize(self, data: list[Any]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            titles = item.get("dctitle", [])
            title = str(titles[0]) if isinstance(titles, list) and titles else str(titles) if titles else ""
            raw_authors = item.get("dcdocauthor", [])
            authors: list[str] = []
            if isinstance(raw_authors, list):
                authors = [str(a) for a in raw_authors if a]
            elif isinstance(raw_authors, str):
                authors = [a.strip() for a in raw_authors.split(";") if a.strip()]
            dates = item.get("dcdate", [])
            year = 0
            if isinstance(dates, list) and dates:
                d = str(dates[0])
                if len(d) >= 4:
                    try:
                        year = int(d[:4])
                    except ValueError:
                        pass
            dois = item.get("dcdoi", [])
            doi = str(dois[0]) if isinstance(dois, list) and dois else str(dois) if dois else ""
            descs = item.get("dcdescription", [])
            abstract = str(descs[0]) if isinstance(descs, list) and descs else str(descs) if descs else ""
            result.append({
                "title": title,
                "authors": authors,
                "year": year,
                "abstract": abstract,
                "doi": doi,
                "venue": "",
                "citation_count": 0,
                "source": "base",
                "source_name": "BASE",
                "sources": ["BASE"],
            })
        return result
