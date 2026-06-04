"""
c4reqber: OEIS Client

Online Encyclopedia of Integer Sequences — 360,000+ sequences.
Open JSON API.
"""
from __future__ import annotations

import logging
from typing import Any

from .base_p6 import BaseP6Client

logger = logging.getLogger("c4reqber.knowledge.oeis")


class OeisClient(BaseP6Client):
    """OEIS JSON API client."""

    BASE_URL = "https://oeis.org"
    DEFAULT_TIMEOUT = 30.0

    async def search_sequences(
        self, query: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Search integer sequences by keyword or numbers."""
        try:
            params: dict[str, Any] = {"q": query, "fmt": "json", "start": 0}
            data: Any = await self._get("/search", params=params, use_cache=True)
            results: list[dict[str, Any]] = []
            # OEIS returns a list directly
            for item in data[:limit] if isinstance(data, list) else []:
                if not isinstance(item, dict):
                    continue
                results.append({
                    "number": item.get("number"),
                    "name": item.get("name"),
                    "data": item.get("data", ""),
                    "comment": item.get("comment", []),
                    "formula": item.get("formula", []),
                    "reference": item.get("reference", []),
                    "link": item.get("link", []),
                    "source": "oeis",
                })
            return results
        except Exception as e:
            logger.warning("OEIS search error: %s", e)
            return []
