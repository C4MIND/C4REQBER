"""
PubMed/NCBI API Client — Async HTTP with Rate Limiting

License: ✅ Open Access (no restrictions)
Coverage: 35M+ biomedical citations
API: eutils.ncbi.nlm.nih.gov (API key recommended for higher limits)
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any


try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

logger = logging.getLogger("c4_cdi_turbo.knowledge.pubmed")


class AsyncPubMedClient:
    """
    Async PubMed/NCBI E-utilities API Client.

    License: ✅ Open Access (no restrictions)
    Coverage: 35M+ biomedical citations
    Rate Limit: 3/sec without API key, 10/sec with key
    """

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    RATE_LIMIT_NO_KEY = 3.0
    RATE_LIMIT_WITH_KEY = 10.0

    def __init__(
        self,
        api_key: str | None = None,
        email: str | None = None,
        tool: str = "c4reqber",
        timeout: float = 30.0,
    ) -> None:
        if not HAS_HTTPX:
            raise ImportError("httpx required: pip install httpx")

        self.api_key = api_key or os.getenv("NCBI_API_KEY", "")
        self.email = email or os.getenv("NCBI_EMAIL", "")
        self.tool = tool
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._last_request: float = 0.0
        self._lock = asyncio.Lock()

        self._rate_limit_per_sec = (
            self.RATE_LIMIT_WITH_KEY if self.api_key else self.RATE_LIMIT_NO_KEY
        )

    async def __aenter__(self) -> AsyncPubMedClient:
        self._client = httpx.AsyncClient(timeout=self._timeout)
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()

    async def _rate_limit(self) -> None:
        async with self._lock:
            now = time.monotonic()
            wait_time = self._last_request + (1.0 / self._rate_limit_per_sec) - now
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self._last_request = time.monotonic()

    async def search(
        self,
        query: str,
        max_results: int = 50,
        date_range: tuple[str, str] | None = None,
    ) -> list[str]:
        """
        Search PubMed, return PMIDs.

        Args:
            query: PubMed search query
            max_results: Maximum number of results
            date_range: Optional tuple of (start_date, end_date) in YYYY/MM/DD format

        Returns:
            List of PMID strings
        """
        await self._rate_limit()

        params: dict[str, Any] = {
            "db": "pubmed",
            "term": query,
            "retmax": min(max_results, 10000),
            "retmode": "json",
            "usehistory": "y",
        }

        if self.api_key:
            params["api_key"] = self.api_key
        if self.email:
            params["email"] = self.email
        if self.tool:
            params["tool"] = self.tool
        if date_range:
            params["mindate"] = date_range[0]
            params["maxdate"] = date_range[1]

        try:
            assert self._client is not None
            response = await self._client.get(
                f"{self.BASE_URL}/esearch.fcgi", params=params
            )
            response.raise_for_status()
            data = response.json()
            return data.get("esearchresult", {}).get("idlist", [])

        except Exception as e:
            logger.warning("PubMed search error: %s", e)
            return []

    async def fetch_papers(self, pmids: list[str]) -> list[dict[str, Any]]:
        """Fetch paper details by PMIDs.

        Returns:
            List of dicts with: pmid, title, authors, abstract, doi, journal, date
        """
        return await self._fetch_details(pmids)

    async def get_by_author(self, author: str, max_results: int = 50) -> list[dict[str, Any]]:
        """Get papers by author name."""
        pmids = await self.search(f"{author}[Author]", max_results=max_results)
        if not pmids:
            return []
        return await self.fetch_papers(pmids)

    async def _fetch_details(self, pmids: list[str]) -> list[dict[str, Any]]:
        if not pmids:
            return []

        await self._rate_limit()

        params: dict[str, Any] = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
        }

        if self.api_key:
            params["api_key"] = self.api_key
        if self.email:
            params["email"] = self.email
        if self.tool:
            params["tool"] = self.tool

        try:
            assert self._client is not None
            response = await self._client.get(
                f"{self.BASE_URL}/efetch.fcgi", params=params
            )
            response.raise_for_status()
            return self._parse_pubmed_xml(response.text)

        except Exception as e:
            logger.warning("PubMed fetch error: %s", e)
            return []

    def _parse_pubmed_xml(self, xml_text: str) -> list[dict[str, Any]]:
        import xml.etree.ElementTree as ET

        results = []
        try:
            root = ET.fromstring(xml_text)

            for article in root.findall(".//PubmedArticle"):
                pmid_elem = article.find(".//PMID")
                pmid = pmid_elem.text if pmid_elem is not None else ""

                title_elem = article.find(".//ArticleTitle")
                title = title_elem.text if title_elem is not None and title_elem.text else ""

                authors = []
                for author in article.findall(".//Author"):
                    lastname = author.find("LastName")
                    forename = author.find("ForeName")
                    if lastname is not None and lastname.text:
                        name = lastname.text
                        if forename is not None and forename.text:
                            name = f"{forename.text} {name}"
                        authors.append(name)

                abstract_parts = []
                for abstract_text in article.findall(".//AbstractText"):
                    if abstract_text.text:
                        abstract_parts.append(abstract_text.text)
                abstract = " ".join(abstract_parts)

                year = 0
                date_str = ""
                pub_date = article.find(".//PubDate/Year")
                if pub_date is not None and pub_date.text:
                    try:
                        year = int(pub_date.text)
                        date_str = pub_date.text
                    except ValueError:
                        pass
                medline_date = article.find(".//PubDate/MedlineDate")
                if medline_date is not None and medline_date.text:
                    date_str = medline_date.text

                doi = ""
                for article_id in article.findall(".//ArticleId"):
                    if article_id.get("IdType") == "doi" and article_id.text:
                        doi = article_id.text
                        break

                journal_elem = article.find(".//Journal/Title")
                journal = journal_elem.text if journal_elem is not None and journal_elem.text else ""

                keywords = []
                for keyword in article.findall(".//Keyword"):
                    if keyword.text:
                        keywords.append(keyword.text)

                results.append(
                    {
                        "paper_id": pmid,
                        "pmid": pmid,
                        "title": title,
                        "authors": authors,
                        "year": year,
                        "date": date_str,
                        "abstract": abstract,
                        "doi": doi,
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        "journal": journal,
                        "keywords": keywords,
                        "source": "pubmed",
                    }
                )

        except ET.ParseError as e:
            logger.warning("PubMed XML parse error: %s", e)

        return results

    async def get_paper(self, pmid: str) -> dict[str, Any] | None:
        """Get paper."""
        results = await self._fetch_details([pmid])
        return results[0] if results else None

    async def get_citations(self, pmid: str, max_results: int = 50) -> list[str]:
        """Get citations."""
        await self._rate_limit()

        params: dict[str, Any] = {
            "dbfrom": "pubmed",
            "db": "pubmed",
            "linkname": "pubmed_pubmed_citedin",
            "id": pmid,
            "retmode": "json",
        }

        if self.api_key:
            params["api_key"] = self.api_key

        try:
            assert self._client is not None
            response = await self._client.get(
                f"{self.BASE_URL}/elink.fcgi", params=params
            )
            response.raise_for_status()
            data = response.json()

            linksets = data.get("linksets", [])
            if linksets:
                return linksets[0].get("linksetdbs", [{}])[0].get("links", [])[:max_results]
            return []

        except Exception as e:
            logger.warning("PubMed citations error: %s", e)
            return []


class PubMedClient:
    """
    Sync PubMed API Client.

    Usage:
        with PubMedClient() as client:
            pmids = client.search("machine learning", max_results=10)
            papers = client.fetch_papers(pmids)
    """

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(
        self,
        api_key: str | None = None,
        email: str | None = None,
        tool: str = "c4reqber",
        timeout: float = 30.0,
    ) -> None:
        self._async_client = AsyncPubMedClient(api_key, email, tool, timeout)

    def __enter__(self) -> PubMedClient:
        return self

    def __exit__(self, *args: Any) -> None:
        pass

    def search(self, query: str, max_results: int = 50) -> list[str]:
        """Search."""
        async def _search() -> list[str]:
            async with AsyncPubMedClient(
                self._async_client.api_key,
                self._async_client.email,
                self._async_client.tool,
                self._async_client._timeout,
            ) as client:
                return await client.search(query, max_results)

        return asyncio.run(_search())

    def fetch_papers(self, pmids: list[str]) -> list[dict[str, Any]]:
        """Fetch papers."""
        async def _fetch() -> list[dict[str, Any]]:
            async with AsyncPubMedClient(
                self._async_client.api_key,
                self._async_client.email,
                self._async_client.tool,
                self._async_client._timeout,
            ) as client:
                return await client.fetch_papers(pmids)

        return asyncio.run(_fetch())

    def get_paper(self, pmid: str) -> dict[str, Any] | None:
        """Get paper."""
        async def _get() -> dict[str, Any] | None:
            async with AsyncPubMedClient(
                self._async_client.api_key,
                self._async_client.email,
                self._async_client.tool,
                self._async_client._timeout,
            ) as client:
                return await client.get_paper(pmid)

        return asyncio.run(_get())

    def get_by_author(self, author: str, max_results: int = 50) -> list[dict[str, Any]]:
        """Get by author."""
        async def _get() -> list[dict[str, Any]]:
            async with AsyncPubMedClient(
                self._async_client.api_key,
                self._async_client.email,
                self._async_client.tool,
                self._async_client._timeout,
            ) as client:
                return await client.get_by_author(author, max_results)

        return asyncio.run(_get())

    def get_citations(self, pmid: str, max_results: int = 50) -> list[str]:
        """Get citations."""
        async def _get() -> list[str]:
            async with AsyncPubMedClient(
                self._async_client.api_key,
                self._async_client.email,
                self._async_client.tool,
                self._async_client._timeout,
            ) as client:
                return await client.get_citations(pmid, max_results)

        return asyncio.run(_get())
