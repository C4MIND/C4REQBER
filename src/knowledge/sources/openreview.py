"""
c4reqber: OpenReview API v2 Client

NeurIPS, ICML, ICLR and other conference papers/reviews.
Read access is open; write requires account.
"""
from __future__ import annotations

import logging
from typing import Any

from .base_p6 import BaseP6Client


logger = logging.getLogger("c4reqber.knowledge.openreview")


class OpenReviewClient(BaseP6Client):
    """OpenReview API v2 client."""

    BASE_URL = "https://api2.openreview.net"
    DEFAULT_TIMEOUT = 30.0

    async def search_notes(
        self, query: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Search papers/notes by keyword."""
        try:
            params: dict[str, Any] = {
                "content.title": query,
                "limit": min(limit, 100),
            }
            data = await self._get("/notes", params=params, use_cache=True)
            notes = data.get("notes", []) if isinstance(data, dict) else []
            results: list[dict[str, Any]] = []
            for item in notes[:limit]:
                if not isinstance(item, dict):
                    continue
                content = item.get("content", {})
                results.append({
                    "id": item.get("id"),
                    "title": content.get("title", "") if isinstance(content.get("title"), str) else str(content.get("title", "")),
                    "authors": content.get("authors", []) if isinstance(content.get("authors"), list) else [],
                    "abstract": content.get("abstract", "") if isinstance(content.get("abstract"), str) else str(content.get("abstract", "")),
                    "forum": item.get("forum"),
                    "invitation": item.get("invitation"),
                    "source": "openreview",
                })
            return results
        except Exception as e:
            logger.warning("OpenReview search error: %s", e)
            return []

    async def get_note(self, note_id: str) -> dict[str, Any]:
        """Fetch a single note by ID."""
        try:
            data = await self._get(f"/notes/id={note_id}", use_cache=True)
            return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.warning("OpenReview get_note error: %s", e)
            return {}
