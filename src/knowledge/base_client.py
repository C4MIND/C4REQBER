"""
BASE API Client (Bielefeld Academic Search Engine)
License: ✅ Open Access (free API key required)
"""

from __future__ import annotations

import logging
import os
from typing import Any


try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

logger = logging.getLogger("c4_cdi_turbo.knowledge.base")


class BASEClient:
    """
    BASE API Client (Bielefeld Academic Search Engine).

    License: ✅ Open Access (free API key required)
    Coverage: 150M+ documents from 10,000+ content providers
    API: base-search.net (free registration required)
    Docs: https://www.base-search.net/about/en/help_api.php
    """

    BASE_URL = "https://api.base-search.net/cgi-bin/BaseHttpSearch"

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key or os.getenv("BASE_API_KEY", "")
        if not self.api_key:
            logger.warning(
                "BASE_API_KEY not set. Get one from https://www.base-search.net/about/en/contact.php"
            )
        self._client: Any = None
        if HAS_HTTPX:
            self._client = httpx.Client(timeout=30.0)

    def __enter__(self) -> BASEClient:
        return self

    def __exit__(self, *args: Any) -> None:
        if self._client:
            self._client.close()

    def search(self, query: str, limit: int = 50) -> list[dict]:
        """
        Search BASE for academic documents.

        Args:
            query: Search query string
            limit: Maximum number of results (max 100)

        Returns:
            List of document dictionaries with keys:
            - paper_id, title, authors, year, abstract,
              doi, url, journal, content_type, source
        """
        if not HAS_HTTPX:
            logger.warning("httpx not installed. Install: pip install httpx")
            return []

        if not self.api_key:
            logger.error("BASE_API_KEY required for BASE API access")
            return []

        params = {
            "func": "search",
            "query": query,
            "hits": min(limit, 100),
            "apikey": self.api_key,
            "format": "json",
        }

        try:
            response = self._client.get(self.BASE_URL, params=params)  # type: ignore[union-attr]
            response.raise_for_status()
            data = response.json()

            results = []
            items = data.get("response", {}).get("docs", [])

            for item in items if isinstance(items, list) else []:
                if not isinstance(item, dict):
                    continue

                authors = []
                raw_authors = item.get("dcdocauthor", [])
                if isinstance(raw_authors, list):
                    authors = [str(a) for a in raw_authors if a]
                elif isinstance(raw_authors, str):
                    authors = [a.strip() for a in raw_authors.split(";") if a.strip()]

                title = ""
                titles = item.get("dctitle", [])
                if isinstance(titles, list) and len(titles) > 0:
                    title = str(titles[0])
                elif isinstance(titles, str):
                    title = titles

                year = 0
                dates = item.get("dcdate", [])
                if isinstance(dates, list) and len(dates) > 0:
                    date_str = str(dates[0])
                    if len(date_str) >= 4:
                        try:
                            year = int(date_str[:4])
                        except ValueError:
                            pass

                doi = ""
                dois = item.get("dcdoi", [])
                if isinstance(dois, list) and len(dois) > 0:
                    doi = str(dois[0])
                elif isinstance(dois, str):
                    doi = dois

                url = ""
                urls = item.get("dclink", [])
                if isinstance(urls, list) and len(urls) > 0:
                    url = str(urls[0])
                elif isinstance(urls, str):
                    url = urls

                abstract = ""
                descs = item.get("dcdescription", [])
                if isinstance(descs, list) and len(descs) > 0:
                    abstract = str(descs[0])
                elif isinstance(descs, str):
                    abstract = descs

                journal = ""
                publishers = item.get("dcpublisher", [])
                if isinstance(publishers, list) and len(publishers) > 0:
                    journal = str(publishers[0])
                elif isinstance(publishers, str):
                    journal = publishers

                content_type = ""
                types = item.get("dctype", [])
                if isinstance(types, list) and len(types) > 0:
                    content_type = str(types[0])
                elif isinstance(types, str):
                    content_type = types

                results.append(
                    {
                        "paper_id": item.get("id", ""),
                        "title": title,
                        "authors": authors,
                        "year": year,
                        "abstract": abstract,
                        "doi": doi,
                        "url": url,
                        "journal": journal,
                        "content_type": content_type,
                        "source": "base",
                    }
                )
            return results

        except Exception as e:
            logger.warning("BASE search error: %s", e)
            return []


class AsyncBASEClient:
    """
    Async BASE API Client (Bielefeld Academic Search Engine).
    """

    BASE_URL = "https://api.base-search.net/cgi-bin/BaseHttpSearch"

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key or os.getenv("BASE_API_KEY", "")
        self._client: Any = None

    async def __aenter__(self) -> AsyncBASEClient:
        if HAS_HTTPX:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()

    async def search(self, query: str, limit: int = 50) -> list[dict]:
        """Async search BASE for academic documents."""
        if not HAS_HTTPX:
            logger.warning("httpx not installed. Install: pip install httpx")
            return []

        if not self.api_key:
            logger.error("BASE_API_KEY required for BASE API access")
            return []

        params = {
            "func": "search",
            "query": query,
            "hits": min(limit, 100),
            "apikey": self.api_key,
            "format": "json",
        }

        try:
            response = await self._client.get(self.BASE_URL, params=params)  # type: ignore[union-attr]
            response.raise_for_status()
            data = response.json()

            results = []
            items = data.get("response", {}).get("docs", [])

            for item in items if isinstance(items, list) else []:
                if not isinstance(item, dict):
                    continue

                authors = []
                raw_authors = item.get("dcdocauthor", [])
                if isinstance(raw_authors, list):
                    authors = [str(a) for a in raw_authors if a]
                elif isinstance(raw_authors, str):
                    authors = [a.strip() for a in raw_authors.split(";") if a.strip()]

                title = ""
                titles = item.get("dctitle", [])
                if isinstance(titles, list) and len(titles) > 0:
                    title = str(titles[0])
                elif isinstance(titles, str):
                    title = titles

                year = 0
                dates = item.get("dcdate", [])
                if isinstance(dates, list) and len(dates) > 0:
                    date_str = str(dates[0])
                    if len(date_str) >= 4:
                        try:
                            year = int(date_str[:4])
                        except ValueError:
                            pass

                doi = ""
                dois = item.get("dcdoi", [])
                if isinstance(dois, list) and len(dois) > 0:
                    doi = str(dois[0])
                elif isinstance(dois, str):
                    doi = dois

                url = ""
                urls = item.get("dclink", [])
                if isinstance(urls, list) and len(urls) > 0:
                    url = str(urls[0])
                elif isinstance(urls, str):
                    url = urls

                abstract = ""
                descs = item.get("dcdescription", [])
                if isinstance(descs, list) and len(descs) > 0:
                    abstract = str(descs[0])
                elif isinstance(descs, str):
                    abstract = descs

                journal = ""
                publishers = item.get("dcpublisher", [])
                if isinstance(publishers, list) and len(publishers) > 0:
                    journal = str(publishers[0])
                elif isinstance(publishers, str):
                    journal = publishers

                content_type = ""
                types = item.get("dctype", [])
                if isinstance(types, list) and len(types) > 0:
                    content_type = str(types[0])
                elif isinstance(types, str):
                    content_type = types

                results.append(
                    {
                        "paper_id": item.get("id", ""),
                        "title": title,
                        "authors": authors,
                        "year": year,
                        "abstract": abstract,
                        "doi": doi,
                        "url": url,
                        "journal": journal,
                        "content_type": content_type,
                        "source": "base",
                    }
                )
            return results

        except Exception as e:
            logger.warning("BASE search error: %s", e)
            return []
