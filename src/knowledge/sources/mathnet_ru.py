"""
c4reqber: Math-Net.Ru Client

All-Russian mathematical portal.
Limited API; uses page parsing.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from .base_p6 import BaseP6Client


logger = logging.getLogger("c4reqber.knowledge.mathnet_ru")


class MathNetRuClient(BaseP6Client):
    """Math-Net.Ru API/scraping client."""

    BASE_URL = "https://www.mathnet.ru"
    DEFAULT_TIMEOUT = 30.0

    async def search_articles(
        self, query: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Search mathematical articles by keyword."""
        try:
            params: dict[str, Any] = {"q": query}
            url = f"{self.BASE_URL}/php/search.phtml"
            if self._client is not None:
                resp = await self._client.get(url, params=params)
                resp.raise_for_status()
                html = resp.text
            else:
                html = ""
            results: list[dict[str, Any]] = []
            # Parse search result blocks
            blocks = re.findall(r'<div[^>]*class="[^"]*result[^"]*"[^>]*>(.*?)</div>', html, re.S)
            for block in blocks[:limit]:
                title_match = re.search(r'<a[^>]*href="/[^"]*"[^>]*>(.*?)</a>', block, re.S)
                title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip() if title_match else ""
                authors_match = re.search(r'<span[^>]*class="[^"]*author[^"]*"[^>]*>(.*?)</span>', block, re.S)
                authors = re.sub(r'<[^>]+>', '', authors_match.group(1)).strip() if authors_match else ""
                year_match = re.search(r'\b(19\d{2}|20\d{2})\b', block)
                year = year_match.group(1) if year_match else ""
                results.append({
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "source": "mathnet_ru",
                })
            return results
        except Exception as e:
            logger.warning("Math-Net.Ru search error: %s", e)
            return []
