"""
c4reqber: USPTO PatentsView API Client

12M+ US patents. Open access, no API key.
"""
from __future__ import annotations

import logging
from typing import Any

from .base_p6 import BaseP6Client


logger = logging.getLogger("c4reqber.knowledge.uspto_patentsview")


class UsptoPatentsviewClient(BaseP6Client):
    """USPTO PatentsView API client."""

    BASE_URL = "https://api.patentsview.org"
    DEFAULT_TIMEOUT = 30.0

    async def search_patents(
        self, query: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Search US patents by keyword in title/abstract."""
        try:
            body = {
                "q": {"_text_any": {"patent_title": query}},
                "f": ["patent_id", "patent_title", "patent_date", "patent_abstract", "inventor_first_name", "assignee_organization"],
                "o": {"per_page": min(limit, 100)},
            }
            data = await self._post("/patents/query", json=body)
            patents = data.get("patents", []) if isinstance(data, dict) else []
            results: list[dict[str, Any]] = []
            for item in patents[:limit]:
                if not isinstance(item, dict):
                    continue
                inventors = item.get("inventors", [])
                assignees = item.get("assignees", [])
                results.append({
                    "patent_id": item.get("patent_id"),
                    "title": item.get("patent_title"),
                    "date": item.get("patent_date"),
                    "abstract": item.get("patent_abstract"),
                    "inventors": [i.get("inventor_first_name", "") for i in inventors[:3]],
                    "assignee": assignees[0].get("assignee_organization", "") if assignees else "",
                    "source": "uspto_patentsview",
                })
            return results
        except Exception as e:
            logger.warning("USPTO PatentsView search error: %s", e)
            return []
