"""
Zenodo/Figshare Dataset API Clients.
License: Open datasets (CC-BY, CC0)
"""

from __future__ import annotations

import logging
from typing import Any


try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

logger = logging.getLogger("c4_cdi_turbo.knowledge.dataset")


class ZenodoClient:
    """
    Zenodo Dataset API Client.

    License: Open datasets
    Coverage: 3M+ records
    API: zenodo.org/api (no API key required for search)
    """

    BASE_URL = "https://zenodo.org/api"

    def __init__(self, token: str = "") -> None:
        self.token = token
        self._client: Any = None
        if HAS_HTTPX:
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            self._client = httpx.AsyncClient(timeout=30.0, headers=headers)

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()

    async def __aenter__(self) -> ZenodoClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def search(self, query: str, max_results: int = 50) -> list[dict]:
        """
        Search Zenodo for datasets.

        Args:
            query: Search query string
            max_results: Maximum number of results

        Returns:
            List of dataset dictionaries with keys:
            - record_id, title, authors, abstract, doi, url, license, year
        """
        if not HAS_HTTPX:
            logger.warning("httpx not installed. Install: pip install httpx")
            return []

        url = f"{self.BASE_URL}/records"
        params = {"q": query, "size": min(max_results, 100), "sort": "mostrecent"}

        try:
            response = await self._client.get(url, params=params)  # type: ignore[union-attr]
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("hits", {}).get("hits", []):
                metadata = item.get("metadata", {})
                results.append(
                    {
                        "record_id": str(item.get("id", "")),
                        "title": metadata.get("title", ""),
                        "authors": [
                            a.get("name", "")
                            for a in metadata.get("creators", [])
                            if a.get("name")
                        ],
                        "abstract": metadata.get("description", "") or "",
                        "doi": metadata.get("doi", "") or "",
                        "url": f"https://zenodo.org/record/{item.get('id', '')}",
                        "license": (metadata.get("license") or {}).get("id", ""),
                        "year": metadata.get("publication_date", "")[:4]
                        if metadata.get("publication_date")
                        else "",
                        "keywords": metadata.get("keywords", []),
                        "type": metadata.get("resource_type", {}).get("title", ""),
                        "source": "zenodo",
                    }
                )
            return results

        except Exception as e:
            logger.warning("Zenodo search error: %s", e)
            return []

    async def get_record(self, record_id: str) -> dict:
        """
        Get dataset record by ID.

        Args:
            record_id: Zenodo record ID

        Returns:
            Record dictionary or empty dict if not found
        """
        if not HAS_HTTPX:
            return {}

        url = f"{self.BASE_URL}/records/{record_id}"

        try:
            response = await self._client.get(url)  # type: ignore[union-attr]
            response.raise_for_status()
            data = response.json()
            metadata = data.get("metadata", {})

            return {
                "record_id": str(data.get("id", "")),
                "title": metadata.get("title", ""),
                "authors": [
                    a.get("name", "")
                    for a in metadata.get("creators", [])
                    if a.get("name")
                ],
                "abstract": metadata.get("description", "") or "",
                "doi": metadata.get("doi", "") or "",
                "url": f"https://zenodo.org/record/{record_id}",
                "license": (metadata.get("license") or {}).get("id", ""),
                "year": metadata.get("publication_date", "")[:4]
                if metadata.get("publication_date")
                else "",
                "keywords": metadata.get("keywords", []),
                "type": metadata.get("resource_type", {}).get("title", ""),
                "files": data.get("files", []),
                "source": "zenodo",
            }

        except Exception as e:
            logger.warning("Zenodo get_record error: %s", e)
            return {}


class FigshareClient:
    """
    Figshare Dataset API Client.

    License: Open datasets
    Coverage: 500K+ datasets
    API: api.figshare.com (no API key required for search)
    """

    BASE_URL = "https://api.figshare.com/v2"

    def __init__(self, token: str = "") -> None:
        self.token = token
        self._client: Any = None
        if HAS_HTTPX:
            headers = {}
            if self.token:
                headers["Authorization"] = f"token {self.token}"
            self._client = httpx.AsyncClient(timeout=30.0, headers=headers)

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()

    async def __aenter__(self) -> FigshareClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def search(self, query: str, max_results: int = 50) -> list[dict]:
        """
        Search Figshare for datasets.

        Args:
            query: Search query string
            max_results: Maximum number of results

        Returns:
            List of dataset dictionaries with keys:
            - record_id, title, authors, abstract, doi, url, license, year
        """
        if not HAS_HTTPX:
            logger.warning("httpx not installed. Install: pip install httpx")
            return []

        url = f"{self.BASE_URL}/articles/search"
        payload = {"search_for": query, "page_size": min(max_results, 100)}

        try:
            response = await self._client.post(url, json=payload)  # type: ignore[union-attr]
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data:
                results.append(
                    {
                        "record_id": str(item.get("id", "")),
                        "title": item.get("title", ""),
                        "authors": [
                            a.get("full_name", "")
                            for a in item.get("authors", [])
                            if a.get("full_name")
                        ],
                        "abstract": item.get("description", "") or "",
                        "doi": item.get("doi", "") or "",
                        "url": item.get("url_public_api", "")
                        or f"https://figshare.com/articles/{item.get('id', '')}",
                        "license": (item.get("license") or {}).get("name", ""),
                        "year": str(item.get("published_date", ""))[:4]
                        if item.get("published_date")
                        else "",
                        "keywords": item.get("tags", []),
                        "type": item.get("defined_type_name", ""),
                        "source": "figshare",
                    }
                )
            return results

        except Exception as e:
            logger.warning("Figshare search error: %s", e)
            return []

    async def get_record(self, record_id: str) -> dict:
        """
        Get dataset record by ID.

        Args:
            record_id: Figshare article ID

        Returns:
            Record dictionary or empty dict if not found
        """
        if not HAS_HTTPX:
            return {}

        url = f"{self.BASE_URL}/articles/{record_id}"

        try:
            response = await self._client.get(url)  # type: ignore[union-attr]
            response.raise_for_status()
            data = response.json()

            return {
                "record_id": str(data.get("id", "")),
                "title": data.get("title", ""),
                "authors": [
                    a.get("full_name", "")
                    for a in data.get("authors", [])
                    if a.get("full_name")
                ],
                "abstract": data.get("description", "") or "",
                "doi": data.get("doi", "") or "",
                "url": data.get("url_public_api", "")
                or f"https://figshare.com/articles/{record_id}",
                "license": (data.get("license") or {}).get("name", ""),
                "year": str(data.get("published_date", ""))[:4]
                if data.get("published_date")
                else "",
                "keywords": data.get("tags", []),
                "type": data.get("defined_type_name", ""),
                "files": data.get("files", []),
                "source": "figshare",
            }

        except Exception as e:
            logger.warning("Figshare get_record error: %s", e)
            return {}
