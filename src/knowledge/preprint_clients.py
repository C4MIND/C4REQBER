"""
bioRxiv/medRxiv API Clients.
License: Open Access preprints
"""

from __future__ import annotations

import logging
from typing import Any


try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

logger = logging.getLogger("c4_cdi_turbo.knowledge.preprint")


class BioRxivClient:
    """
    bioRxiv/medRxiv API Client.

    License: Open Access preprints
    Coverage: 400K+ preprints
    API: api.biorxiv.org (no API key required)
    """

    BASE_URL = "https://api.biorxiv.org"

    def __init__(self) -> None:
        self._client: Any = None
        if HAS_HTTPX:
            self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()

    async def __aenter__(self) -> BioRxivClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def search(self, query: str, max_results: int = 50) -> list[dict]:
        """
        Search bioRxiv/medRxiv for preprints.

        Args:
            query: Search query string
            max_results: Maximum number of results

        Returns:
            List of preprint dictionaries with keys:
            - preprint_id, title, authors, abstract, doi, url, date, server
        """
        if not HAS_HTTPX:
            logger.warning("httpx not installed. Install: pip install httpx")
            return []

        url = f"{self.BASE_URL}/details/biorxiv/{query}"
        try:
            response = await self._client.get(url)  # type: ignore[union-attr]
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("collection", [])[:max_results]:
                results.append(
                    {
                        "preprint_id": item.get("doi", ""),
                        "title": item.get("title", ""),
                        "authors": self._parse_authors(item.get("authors", "")),
                        "abstract": item.get("abstract", ""),
                        "doi": item.get("doi", ""),
                        "url": f"https://www.biorxiv.org/content/{item.get('doi', '')}",
                        "date": item.get("date", ""),
                        "server": "biorxiv",
                        "source": "biorxiv",
                    }
                )
            return results

        except Exception as e:
            logger.warning("bioRxiv search error: %s", e)
            return []

    async def search_medrxiv(self, query: str, max_results: int = 50) -> list[dict]:
        """Search medRxiv for health sciences preprints."""
        if not HAS_HTTPX:
            return []

        url = f"{self.BASE_URL}/details/medrxiv/{query}"
        try:
            response = await self._client.get(url)  # type: ignore[union-attr]
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("collection", [])[:max_results]:
                results.append(
                    {
                        "preprint_id": item.get("doi", ""),
                        "title": item.get("title", ""),
                        "authors": self._parse_authors(item.get("authors", "")),
                        "abstract": item.get("abstract", ""),
                        "doi": item.get("doi", ""),
                        "url": f"https://www.medrxiv.org/content/{item.get('doi', '')}",
                        "date": item.get("date", ""),
                        "server": "medrxiv",
                        "source": "medrxiv",
                    }
                )
            return results

        except Exception as e:
            logger.warning("medRxiv search error: %s", e)
            return []

    async def get_paper(self, doi: str) -> dict:
        """
        Get paper by DOI.

        Args:
            doi: DOI of the paper

        Returns:
            Paper dictionary or empty dict if not found
        """
        if not HAS_HTTPX:
            return {}

        url = f"{self.BASE_URL}/details/biorxiv/{doi}"
        try:
            response = await self._client.get(url)  # type: ignore[union-attr]
            response.raise_for_status()
            data = response.json()

            items = data.get("collection", [])
            if not items:
                return {}

            item = items[0]
            return {
                "preprint_id": doi,
                "title": item.get("title", ""),
                "authors": self._parse_authors(item.get("authors", "")),
                "abstract": item.get("abstract", ""),
                "doi": doi,
                "url": f"https://www.biorxiv.org/content/{doi}",
                "date": item.get("date", ""),
                "server": "biorxiv",
                "source": "biorxiv",
            }

        except Exception as e:
            logger.warning("bioRxiv get_paper error: %s", e)
            return {}

    def _parse_authors(self, authors_str: str) -> list[str]:
        """Parse authors string into list."""
        if not authors_str:
            return []
        return [a.strip() for a in authors_str.split(";") if a.strip()]


class MedRxivClient(BioRxivClient):
    """medRxiv-specific client (health sciences preprints)."""

    async def search(self, query: str, max_results: int = 50) -> list[dict]:
        """Search medRxiv for health sciences preprints."""
        return await self.search_medrxiv(query, max_results)

    async def get_paper(self, doi: str) -> dict:
        """Get paper by DOI from medRxiv."""
        if not HAS_HTTPX:
            return {}

        url = f"{self.BASE_URL}/details/medrxiv/{doi}"
        try:
            response = await self._client.get(url)  # type: ignore[union-attr]
            response.raise_for_status()
            data = response.json()

            items = data.get("collection", [])
            if not items:
                return {}

            item = items[0]
            return {
                "preprint_id": doi,
                "title": item.get("title", ""),
                "authors": self._parse_authors(item.get("authors", "")),
                "abstract": item.get("abstract", ""),
                "doi": doi,
                "url": f"https://www.medrxiv.org/content/{doi}",
                "date": item.get("date", ""),
                "server": "medrxiv",
                "source": "medrxiv",
            }

        except Exception as e:
            logger.warning("medRxiv get_paper error: %s", e)
            return {}
