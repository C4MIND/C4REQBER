from __future__ import annotations

import logging
from typing import Any

import httpx

from .base import BaseSourceAdapter


logger = logging.getLogger("c44tcdi.knowledge.multi_source")


class InspireHepAdapter(BaseSourceAdapter):
    """INSPIRE-HEP — high energy physics literature."""

    @property
    def source_id(self) -> str:
        return "inspire_hep"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Search."""
        url = "https://inspirehep.net/api/literature"
        params: dict[str, Any] = {
            "q": query,
            "size": min(limit, 100),
            "sort": "mostrecent",
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                results: list[dict[str, Any]] = []
                for hit in data.get("hits", {}).get("hits", []):
                    meta = hit.get("metadata", {})
                    titles = meta.get("titles", [])
                    title = titles[0].get("title", "") if titles else ""
                    dois = [
                        v.get("value", "")
                        for v in meta.get("dois", [])
                        if isinstance(v, dict)
                    ]
                    results.append({
                        "title": title,
                        "year": int(meta.get("publication_info", [{}])[0].get("year", 0) or 0),
                        "doi": dois[0] if dois else "",
                        "arxiv_id": (
                            meta.get("arxiv_eprints", [{}])[0].get("value", "")
                            if meta.get("arxiv_eprints") else ""
                        ),
                        "abstract": (meta.get("abstracts", [{}])[0].get("value", "") if meta.get("abstracts") else ""),
                        "citation_count": meta.get("citation_count", 0) or 0,
                        "source": "inspire_hep",
                        "source_name": "INSPIRE-HEP",
                    })
                return results
            except (ImportError, AttributeError, ConnectionError, TimeoutError):
                return []
