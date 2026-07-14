"""
c4reqber: CyberLeninka Client

Russian open-access scientific journal library.
No official API — uses web scraping with respectful delays.
"""
from __future__ import annotations

import logging
from typing import Any

from .base_p6 import BaseP6Client


logger = logging.getLogger("c4reqber.knowledge.cyberleninka")


class CyberLeninkaClient(BaseP6Client):
    """CyberLeninka web-scraping client."""

    BASE_URL = "https://cyberleninka.ru"
    DEFAULT_TIMEOUT = 30.0

    async def search_articles(
        self, query: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Search articles by keyword via CyberLeninka search page."""
        try:
            params: dict[str, Any] = {"q": query}
            url = f"{self.BASE_URL}/search"
            if self._client is not None:
                resp = await self._client.get(url, params=params)
                resp.raise_for_status()
                html = resp.text
            else:
                html = ""
            results: list[dict[str, Any]] = []
            # Simple regex-based extraction as fallback
            import re
            # Extract article blocks
            articles = re.findall(r'<li[^>]*class="[^"]*article[^"]*"[^>]*>(.*?)</li>', html, re.S)
            for block in articles[:limit]:
                title_match = re.search(r'<h2[^>]*>(.*?)</h2>', block, re.S)
                title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip() if title_match else ""
                authors_match = re.search(r'<span[^>]*class="[^"]*author[^"]*"[^>]*>(.*?)</span>', block, re.S)
                authors = re.sub(r'<[^>]+>', '', authors_match.group(1)).strip() if authors_match else ""
                year_match = re.search(r'\b(19\d{2}|20\d{2})\b', block)
                year = year_match.group(1) if year_match else ""
                journal_match = re.search(r'<span[^>]*class="[^"]*journal[^"]*"[^>]*>(.*?)</span>', block, re.S)
                journal = re.sub(r'<[^>]+>', '', journal_match.group(1)).strip() if journal_match else ""
                results.append({
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "journal": journal,
                    "source": "cyberleninka",
                })
            return results
        except Exception as e:
            logger.warning("CyberLeninka search error: %s", e)
            return []
