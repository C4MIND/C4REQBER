"""
arXiv API Client — Async HTTP with Rate Limiting

License: ✅ Open Access (no restrictions)
Coverage: 2M+ preprints
API: export.arxiv.org/api (no key required)
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
import xml.etree.ElementTree as ET
from functools import lru_cache
from typing import Any


try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

logger = logging.getLogger("c4_cdi_turbo.knowledge.arxiv")

ARXIV_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
}


class AsyncArxivClient:
    """
    Async arXiv API Client.

    License: ✅ Open Access (no restrictions)
    Coverage: 2M+ preprints
    Rate Limit: ~3 requests/sec (polite usage)
    """

    BASE_URL = "https://export.arxiv.org/api/query"
    RATE_LIMIT = 3.0

    def __init__(self, timeout: float = 30.0) -> None:
        if not HAS_HTTPX:
            raise ImportError("httpx required: pip install httpx")
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._last_request: float = 0.0
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> AsyncArxivClient:
        self._client = httpx.AsyncClient(timeout=self._timeout)
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()

    async def _rate_limit(self) -> None:
        async with self._lock:
            now = time.monotonic()
            wait_time = self._last_request + (1.0 / self.RATE_LIMIT) - now
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self._last_request = time.monotonic()

    async def search(
        self,
        query: str,
        max_results: int = 20,
        sort_by: str = "relevance",
        sort_order: str = "descending",
    ) -> list[dict[str, Any]]:
        """
        Search arXiv for papers.

        Args:
            query: Search query (supports arXiv advanced search syntax)
            max_results: Maximum number of results
            sort_by: "relevance", "lastUpdatedDate", or "submittedDate"
            sort_order: "ascending" or "descending"

        Returns:
            List of paper dictionaries
        """
        await self._rate_limit()

        params: dict[str, str | int] = {
            "search_query": query,
            "start": 0,
            "max_results": min(max_results, 2000),
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }

        try:
            assert self._client is not None
            response = await self._client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return self._parse_feed(response.text)
        except Exception as e:
            logger.info("arXiv unavailable (429/timeout): %s", e)
            return []

    def _parse_feed(self, xml_text: str) -> list[dict[str, Any]]:
        results = []
        try:
            root = ET.fromstring(xml_text)
            entries = root.findall("atom:entry", ARXIV_NS)

            for entry in entries:
                arxiv_id = self._extract_arxiv_id(entry)
                title_elem = entry.find("atom:title", ARXIV_NS)
                title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""

                authors = []
                for author in entry.findall("atom:author", ARXIV_NS):
                    name_elem = author.find("atom:name", ARXIV_NS)
                    if name_elem is not None and name_elem.text:
                        authors.append(name_elem.text)

                summary_elem = entry.find("atom:summary", ARXIV_NS)
                abstract = summary_elem.text.strip() if summary_elem is not None and summary_elem.text else ""

                published_elem = entry.find("atom:published", ARXIV_NS)
                year = 0
                if published_elem is not None and published_elem.text:
                    year_match = re.search(r"(\d{4})", published_elem.text)
                    if year_match:
                        year = int(year_match.group(1))

                doi = ""
                doi_elem = entry.find("arxiv:doi", ARXIV_NS)
                if doi_elem is not None and doi_elem.text:
                    doi = doi_elem.text.strip()

                pdf_url = ""
                for link in entry.findall("atom:link", ARXIV_NS):
                    href = link.get("href", "")
                    if "pdf" in href:
                        pdf_url = href
                    link_title = link.get("title", "")
                    if link_title == "pdf":
                        pdf_url = href

                page_url = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else ""

                categories = []
                for cat in entry.findall("atom:category", ARXIV_NS):
                    term = cat.get("term")
                    if term:
                        categories.append(term)

                results.append(
                    {
                        "paper_id": arxiv_id,
                        "arxiv_id": arxiv_id,
                        "title": title,
                        "authors": authors,
                        "year": year,
                        "abstract": abstract,
                        "doi": doi,
                        "url": page_url,
                        "pdf_url": pdf_url,
                        "categories": categories,
                        "source": "arxiv",
                    }
                )

        except ET.ParseError as e:
            logger.warning("arXiv XML parse error: %s", e)

        return results

    def _extract_arxiv_id(self, entry: ET.Element) -> str:
        id_elem = entry.find("atom:id", ARXIV_NS)
        if id_elem is not None and id_elem.text:
            id_url = id_elem.text
            match = re.search(r"(\d{4}\.\d{4,5}(v\d+)?)$", id_url)
            if match:
                return match.group(1)
            match = re.search(r"([a-z-]+/\d+)$", id_url)
            if match:
                return match.group(1)
        return ""

    async def get_paper(self, arxiv_id: str) -> dict[str, Any] | None:
        """Get paper."""
        results = await self.search(f"id:{arxiv_id}", max_results=1)
        return results[0] if results else None

    async def get_by_author(self, author: str, max_results: int = 50) -> list[dict[str, Any]]:
        """
        Get papers by author name.

        Args:
            author: Author name (supports partial matching)
            max_results: Maximum number of results

        Returns:
            List of paper dictionaries
        """
        query = f"au:{author}"
        return await self.search(query, max_results=max_results)

    async def get_by_category(
        self, category: str, max_results: int = 50, sort_by: str = "submittedDate"
    ) -> list[dict[str, Any]]:
        """
        Get papers by arXiv category.

        Args:
            category: arXiv category (e.g., 'cs.AI', 'physics.comp-ph', 'math.CO')
            max_results: Maximum number of results
            sort_by: Sort field (default: submittedDate for recency)

        Returns:
            List of paper dictionaries
        """
        query = f"cat:{category}"
        return await self.search(query, max_results=max_results, sort_by=sort_by)

    @staticmethod
    @lru_cache(maxsize=256)
    def extract_id_from_url(url: str) -> str:
        """
        Extract arXiv ID from URL.

        Supports formats:
        - https://arxiv.org/abs/2301.12345
        - https://arxiv.org/pdf/2301.12345.pdf
        - https://arxiv.org/abs/cs/0701001
        - arxiv.org/abs/2301.12345v2

        Args:
            url: arXiv URL or arXiv ID

        Returns:
            arXiv ID string (empty if not found)
        """
        if not url:
            return ""

        url = url.strip()

        match = re.search(r"(\d{4}\.\d{4,5}(v\d+)?)", url)
        if match:
            return match.group(1)

        match = re.search(r"([a-z-]+/\d+)(v\d+)?$", url)
        if match:
            return match.group(1)

        return ""


class ArxivClient:
    """
    Sync arXiv API Client (backward compatibility).
    """

    BASE_URL = "https://export.arxiv.org/api/query"

    def __init__(self, timeout: float = 30.0) -> None:
        if not HAS_HTTPX:
            raise ImportError("httpx required: pip install httpx")
        self._timeout = timeout
        self._client: httpx.Client | None = None
        self.api_key = ""  # arXiv is open access, no API key required

    def __enter__(self) -> ArxivClient:
        self._client = httpx.Client(timeout=self._timeout)
        return self

    def __exit__(self, *args: Any) -> None:
        if self._client:
            self._client.close()

    def search(self, query: str, max_results: int = 20) -> list[dict[str, Any]]:
        """Search."""
        async def _search() -> list[dict[str, Any]]:
            async with AsyncArxivClient(self._timeout) as client:
                return await client.search(query, max_results)

        return asyncio.run(_search())

    def get_paper(self, arxiv_id: str) -> dict[str, Any] | None:
        """Get paper."""
        async def _get() -> dict[str, Any] | None:
            async with AsyncArxivClient(self._timeout) as client:
                return await client.get_paper(arxiv_id)

        return asyncio.run(_get())

    def get_full_text(self, arxiv_id: str) -> str:
        """Return the abstract for an arXiv paper as a proxy for full text."""
        paper = self.get_paper(arxiv_id)
        if paper is None:
            return ""
        return str(paper.get("abstract", ""))

    def get_by_author(self, author: str, max_results: int = 50) -> list[dict[str, Any]]:
        """Get by author."""
        async def _get() -> list[dict[str, Any]]:
            async with AsyncArxivClient(self._timeout) as client:
                return await client.get_by_author(author, max_results)

        return asyncio.run(_get())

    def get_by_category(self, category: str, max_results: int = 50) -> list[dict[str, Any]]:
        """Get by category."""
        async def _get() -> list[dict[str, Any]]:
            async with AsyncArxivClient(self._timeout) as client:
                return await client.get_by_category(category, max_results)

        return asyncio.run(_get())

    @staticmethod
    def extract_id_from_url(url: str) -> str:
        return AsyncArxivClient.extract_id_from_url(url)
