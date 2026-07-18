from __future__ import annotations

import logging
from typing import Any

import httpx

from .base import BaseSourceAdapter


logger = logging.getLogger("c44tcdi.knowledge.multi_source")


class BraveAdapter(BaseSourceAdapter):
    """Brave Search — web + academic search."""

    @property
    def source_id(self) -> str:
        return "brave"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Search."""
        if not self.api_key:
            logger.debug("Brave Search: BRAVE_API_KEY not set")
            return []

        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {"Accept": "application/json", "X-Subscription-Token": self.api_key}
        params: dict[str, str | int] = {"q": query, "count": min(limit, 10)}
        async with httpx.AsyncClient(timeout=self.timeout or 15.0) as client:
            try:
                resp = await client.get(url, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
                results: list[dict[str, Any]] = []
                for item in (
                    data.get("web", {}).get("results", [])
                    if isinstance(data.get("web"), dict)
                    else []
                ):
                    results.append(
                        {
                            "title": item.get("title", ""),
                            "authors": [],
                            "year": None,
                            "abstract": item.get("description", "")[:500],
                            "doi": "",
                            "url": item.get("url", ""),
                            "source": "brave",
                            "source_name": "Brave Search",
                            "citation_count": 0,
                            "type": "web",
                        }
                    )
                return results[:limit]
            except (ImportError, AttributeError, ConnectionError, TimeoutError) as e:
                logger.debug("Brave Search error: %s", e)
                return []
