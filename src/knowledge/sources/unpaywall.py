from __future__ import annotations

import logging
import os
import re
from typing import Any

import httpx

from .base import BaseSourceAdapter


logger = logging.getLogger("c44tcdi.knowledge.multi_source")


def _extract_doi(text: str) -> str | None:
    m = re.search(r"(10\.\d{4,}/[^\s]+)", text)
    return m.group(1).rstrip(".,;:") if m else None


class UnpaywallAdapter(BaseSourceAdapter):
    """Unpaywall — 40M+ OA articles by DOI."""

    @property
    def source_id(self) -> str:
        return "unpaywall"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Search."""
        doi = _extract_doi(query)
        if not doi:
            return []

        email = self.api_key or os.environ.get("UNPAYWALL_EMAIL", "c44tcdi@example.com")
        url = f"https://api.unpaywall.org/v2/{doi}"
        params = {"email": email}
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            if data.get("title"):
                return [{
                    "doi": doi,
                    "title": data.get("title", ""),
                    "year": data.get("year", 0) or 0,
                    "oa_status": data.get("oa_status", ""),
                    "source": "unpaywall",
                    "source_name": "Unpaywall",
                }]
            return []
