"""
ResearchGate Client — LIMITED SCRAPING
License: ⚠️ NO OFFICIAL API

WARNINGS:
- ResearchGate has NO official API
- This uses limited web scraping
- May break at any time
- Respect robots.txt and rate limits
- For personal/research use only
"""

from __future__ import annotations

import asyncio
import re
from typing import Any
from urllib.parse import quote_plus, urljoin

import httpx
from bs4 import BeautifulSoup


class ResearchGateClient:
    """ResearchGate client (limited scraping, no official API)."""

    BASE_URL = "https://www.researchgate.net"
    SEARCH_URL = "https://www.researchgate.net/search"
    RATE_LIMIT_DELAY = 2.0

    def __init__(self) -> None:
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; C4Reqber/8.0; +https://github.com/c4reqber)",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self._last_request_time = 0.0

    async def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        elapsed = asyncio.get_event_loop().time() - self._last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            await asyncio.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = asyncio.get_event_loop().time()

    async def search_author(self, name: str, max_results: int = 10) -> list[dict[str, Any]]:
        """Search for author profile."""
        await self._rate_limit()

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.SEARCH_URL}/author/{quote_plus(name)}",
                    headers=self.headers,
                    params={"page": 1},
                    timeout=30.0,
                    follow_redirects=True,
                )
                response.raise_for_status()
            except httpx.HTTPError:
                return []

        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        for item in soup.select(".nova-legacy-e-link--theme-bare")[:max_results]:
            href = item.get("href", "")
            if isinstance(href, str) and "/profile/" in href:
                results.append({
                    "name": item.get_text(strip=True),
                    "profile_url": urljoin(self.BASE_URL, href),
                    "source": "researchgate",
                })

        return results

    async def get_publications(self, profile_url: str, max_results: int = 20) -> list[dict[str, Any]]:
        """Get publications from profile."""
        await self._rate_limit()

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    profile_url,
                    headers=self.headers,
                    timeout=30.0,
                    follow_redirects=True,
                )
                response.raise_for_status()
            except httpx.HTTPError:
                return []

        soup = BeautifulSoup(response.text, "html.parser")
        publications = []

        for item in soup.select(".nova-legacy-v-publication-item")[:max_results]:
            title_elem = item.select_one(".nova-legacy-e-link--theme-bare")
            title = title_elem.get_text(strip=True) if title_elem else "Unknown"

            year_elem = item.select_one(".nova-legacy-e-text--color-grey-500")
            year_match = re.search(r"\d{4}", year_elem.get_text()) if year_elem else None
            year = year_match.group() if year_match else None

            citations_elem = item.select_one(".nova-legacy-e-badge--theme-solid-grey")
            citations = 0
            if citations_elem:
                cites_match = re.search(r"\d+", citations_elem.get_text())
                citations = int(cites_match.group()) if cites_match else 0

            publications.append({
                "title": title,
                "year": year,
                "citations": citations,
                "source": "researchgate",
            })

        return publications

    async def get_paper_details(self, paper_url: str) -> dict[str, Any]:
        """Get details for a specific paper."""
        await self._rate_limit()

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    paper_url,
                    headers=self.headers,
                    timeout=30.0,
                    follow_redirects=True,
                )
                response.raise_for_status()
            except httpx.HTTPError:
                return {"error": "Failed to fetch paper"}

        soup = BeautifulSoup(response.text, "html.parser")

        title_elem = soup.select_one(".nova-legacy-e-text--size-xxl")
        title = title_elem.get_text(strip=True) if title_elem else "Unknown"

        abstract_elem = soup.select_one(".nova-legacy-e-text--spacing-none")
        abstract = abstract_elem.get_text(strip=True) if abstract_elem else None

        authors = []
        for author_elem in soup.select(".nova-legacy-v-person-inline-item__align-content a"):
            authors.append(author_elem.get_text(strip=True))

        doi_elem = soup.select_one("a[href*='doi.org']")
        doi_raw = doi_elem.get("href", "") if doi_elem else ""
        doi = doi_raw.replace("https://doi.org/", "") if isinstance(doi_raw, str) else None

        return {
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "doi": doi,
            "source": "researchgate",
        }

    async def check_availability(self) -> bool:
        """Check if ResearchGate is accessible."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.head(
                    self.BASE_URL,
                    headers=self.headers,
                    timeout=10.0,
                )
                return response.status_code == 200
        except httpx.HTTPError:
            return False
