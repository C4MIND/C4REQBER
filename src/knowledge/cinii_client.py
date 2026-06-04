"""
CiNii API Client (Japanese Academic Database)
License: ✅ Open Access (free registration required)
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

logger = logging.getLogger("c4_cdi_turbo.knowledge.cinii")


class CiNiiClient:
    """
    CiNii API Client (Japanese academic database).

    License: ✅ Open Access (free registration required)
    Coverage: Japanese academic papers, journals, dissertations
    API: ci.nii.ac.jp/api (appid required)
    Docs: https://support.nii.ac.jp/en/cinii/api/ws_search
    """

    BASE_URL = "https://ci.nii.ac.jp/api"

    def __init__(self, appid: str = "") -> None:
        self.appid = appid or os.getenv("CINII_APPID", "")
        if not self.appid:
            logger.warning(
                "CINII_APPID not set. Get one from https://ci.nii.ac.jp/registration/"
            )
        self._client: Any = None
        if HAS_HTTPX:
            self._client = httpx.Client(timeout=30.0)

    def __enter__(self) -> CiNiiClient:
        return self

    def __exit__(self, *args: Any) -> None:
        if self._client:
            self._client.close()

    def search(self, query: str, limit: int = 50) -> list[dict]:
        """
        Search CiNii for Japanese academic papers.

        Args:
            query: Search query string
            limit: Maximum number of results (max 200)

        Returns:
            List of paper dictionaries with keys:
            - paper_id, title, authors, year, abstract,
              doi, url, journal, language, source
        """
        if not HAS_HTTPX:
            logger.warning("httpx not installed. Install: pip install httpx")
            return []

        if not self.appid:
            logger.error("CINII_APPID required for CiNii API access")
            return []

        url = f"{self.BASE_URL}/search"
        params = {
            "appid": self.appid,
            "q": query,
            "count": min(limit, 200),
            "format": "json",
        }

        try:
            response = self._client.get(url, params=params)  # type: ignore[union-attr]
            response.raise_for_status()
            data = response.json()

            results = []
            items = data.get("@graph", [])
            if isinstance(items, dict):
                items = items.get("items", [])
            elif isinstance(items, list) and len(items) > 0:
                items = items[0].get("items", []) if isinstance(items[0], dict) else []

            for item in items if isinstance(items, list) else []:
                if not isinstance(item, dict):
                    continue

                authors = []
                for author in item.get("dc:creator", []):
                    if isinstance(author, dict):
                        authors.append(author.get("@value", ""))
                    elif isinstance(author, str):
                        authors.append(author)

                title = ""
                titles = item.get("dc:title", [])
                if isinstance(titles, list) and len(titles) > 0:
                    t = titles[0]
                    if isinstance(t, dict):
                        title = t.get("@value", "")
                    elif isinstance(t, str):
                        title = t

                year = 0
                date = item.get("prism:publicationDate", "")
                if isinstance(date, str) and len(date) >= 4:
                    try:
                        year = int(date[:4])
                    except ValueError:
                        pass

                results.append(
                    {
                        "paper_id": item.get("@id", "").split("/")[-1],
                        "title": title,
                        "authors": authors,
                        "year": year,
                        "abstract": item.get("dc:description", "") or "",
                        "doi": item.get("prism:doi", "") or "",
                        "url": item.get("@id", "") or item.get("link", [{}])[0].get("@id", ""),
                        "journal": item.get("prism:publicationName", "") or "",
                        "language": "ja",
                        "source": "cinii",
                    }
                )
            return results

        except Exception as e:
            logger.warning("CiNii search error: %s", e)
            return []


class AsyncCiNiiClient:
    """
    Async CiNii API Client (Japanese academic database).
    """

    BASE_URL = "https://ci.nii.ac.jp/api"

    def __init__(self, appid: str = "") -> None:
        self.appid = appid or os.getenv("CINII_APPID", "")
        self._client: Any = None

    async def __aenter__(self) -> AsyncCiNiiClient:
        if HAS_HTTPX:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()

    async def search(self, query: str, limit: int = 50) -> list[dict]:
        """Async search CiNii for Japanese academic papers."""
        if not HAS_HTTPX:
            logger.warning("httpx not installed. Install: pip install httpx")
            return []

        if not self.appid:
            logger.error("CINII_APPID required for CiNii API access")
            return []

        url = f"{self.BASE_URL}/search"
        params = {
            "appid": self.appid,
            "q": query,
            "count": min(limit, 200),
            "format": "json",
        }

        try:
            response = await self._client.get(url, params=params)  # type: ignore[union-attr]
            response.raise_for_status()
            data = response.json()

            results = []
            items = data.get("@graph", [])
            if isinstance(items, dict):
                items = items.get("items", [])
            elif isinstance(items, list) and len(items) > 0:
                items = items[0].get("items", []) if isinstance(items[0], dict) else []

            for item in items if isinstance(items, list) else []:
                if not isinstance(item, dict):
                    continue

                authors = []
                for author in item.get("dc:creator", []):
                    if isinstance(author, dict):
                        authors.append(author.get("@value", ""))
                    elif isinstance(author, str):
                        authors.append(author)

                title = ""
                titles = item.get("dc:title", [])
                if isinstance(titles, list) and len(titles) > 0:
                    t = titles[0]
                    if isinstance(t, dict):
                        title = t.get("@value", "")
                    elif isinstance(t, str):
                        title = t

                year = 0
                date = item.get("prism:publicationDate", "")
                if isinstance(date, str) and len(date) >= 4:
                    try:
                        year = int(date[:4])
                    except ValueError:
                        pass

                results.append(
                    {
                        "paper_id": item.get("@id", "").split("/")[-1],
                        "title": title,
                        "authors": authors,
                        "year": year,
                        "abstract": item.get("dc:description", "") or "",
                        "doi": item.get("prism:doi", "") or "",
                        "url": item.get("@id", "") or item.get("link", [{}])[0].get("@id", ""),
                        "journal": item.get("prism:publicationName", "") or "",
                        "language": "ja",
                        "source": "cinii",
                    }
                )
            return results

        except Exception as e:
            logger.warning("CiNii search error: %s", e)
            return []
