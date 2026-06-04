"""
C4REQBER: Semantic Scholar Integration
Search 200M+ papers from Semantic Scholar API
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


@dataclass
class SemanticPaper:
    """A paper from Semantic Scholar."""

    paper_id: str
    title: str
    authors: list[str]
    year: int
    abstract: str
    citation_count: int
    reference_count: int
    fields_of_study: list[str]
    publication_types: list[str]
    open_access_pdf: str | None = None
    venue: str = ""
    tldr: str = ""  # AI-generated TL;DR


class SemanticScholarClient:
    """
    Client for Semantic Scholar API.

    Free tier: 100 requests per 5 minutes
    Docs: https://api.semanticscholar.org/api-docs/
    """

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
        self.client = None
        self._last_request: float = 0.0
        self._rate_limit = 1.0 / 3.5  # ~3.5 sec between requests for free tier safety
        if HAS_HTTPX:
            headers = {}
            if self.api_key:
                headers["x-api-key"] = self.api_key
            self.client = httpx.AsyncClient(headers=headers, timeout=30.0)

    async def _rate_limit_wait(self) -> None:
        import time
        import asyncio
        now = time.monotonic()
        wait = self._last_request + (1.0 / self._rate_limit) - now
        if wait > 0:
            await asyncio.sleep(wait)
        self._last_request = time.monotonic()

    async def __aenter__(self) -> Any:
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self.client:
            await self.client.aclose()

    async def search_papers(
        self,
        query: str,
        limit: int = 10,
        fields: list[str] | None = None,
        year_start: int | None = None,
        year_end: int | None = None,
        open_access_only: bool = False,
    ) -> list[SemanticPaper]:
        """
        Search for papers on Semantic Scholar.

        Args:
            query: Search query
            limit: Number of results (max 100)
            fields: Fields to return (default: all)
            year_start: Filter by year start
            year_end: Filter by year end
            open_access_only: Only return open access papers
        """
        if not HAS_HTTPX:
            raise ImportError(
                "httpx required for Semantic Scholar. Install: pip install httpx"
            )

        if fields is None:
            fields = [
                "paperId",
                "title",
                "authors",
                "year",
                "abstract",
                "citationCount",
                "referenceCount",
                "fieldsOfStudy",
                "publicationTypes",
                "openAccessPdf",
                "venue",
                "tldr",
            ]

        url = f"{self.BASE_URL}/paper/search"
        params = {
            "query": query,
            "limit": min(limit, 100),
            "fields": ",".join(fields),
        }

        if year_start:
            params["publicationDateOrYear"] = f"{year_start}:"
        if year_end:
            params["publicationDateOrYear"] = f":{year_end}"
        if year_start and year_end:
            params["publicationDateOrYear"] = f"{year_start}:{year_end}"
        if open_access_only:
            params["openAccessPdf"] = "true"

        await self._rate_limit_wait()
        response = await self.client.get(url, params=params)  # type: ignore[arg-type, union-attr]
        if response.status_code == 429:
            import asyncio
            await asyncio.sleep(5)
            await self._rate_limit_wait()
        response = await self.client.get(url, params=params)  # type: ignore[arg-type, union-attr]
        if response.status_code == 429:
            import asyncio
            await asyncio.sleep(5)
            response = await self.client.get(url, params=params)  # type: ignore[arg-type, union-attr]
        response.raise_for_status()

        data = response.json()
        papers = []

        for item in data.get("data", []):
            authors = []
            for author in item.get("authors", []):
                if isinstance(author, dict):
                    authors.append(author.get("name", ""))
                else:
                    authors.append(str(author))

            tldr = ""
            if item.get("tldr"):
                if isinstance(item["tldr"], dict):
                    tldr = item["tldr"].get("text", "")
                else:
                    tldr = str(item["tldr"])

            paper = SemanticPaper(
                paper_id=item.get("paperId", ""),
                title=item.get("title", "Untitled"),
                authors=authors,
                year=item.get("year", 0),
                abstract=item.get("abstract", "") or "",
                citation_count=item.get("citationCount", 0) or 0,
                reference_count=item.get("referenceCount", 0) or 0,
                fields_of_study=item.get("fieldsOfStudy") or [],
                publication_types=item.get("publicationTypes") or [],
                open_access_pdf=item.get("openAccessPdf", {}).get("url")
                if isinstance(item.get("openAccessPdf"), dict)
                else None,
                venue=item.get("venue", "") or "",
                tldr=tldr,
            )
            papers.append(paper)

        return papers

    async def get_paper_details(self, paper_id: str) -> SemanticPaper | None:
        """Get detailed information about a specific paper."""
        if not HAS_HTTPX:
            raise ImportError("httpx required for Semantic Scholar")

        url = f"{self.BASE_URL}/paper/{paper_id}"
        params = {
            "fields": "paperId,title,authors,year,abstract,citationCount,referenceCount,fieldsOfStudy,publicationTypes,openAccessPdf,venue,tldr"
        }

        await self._rate_limit_wait()
        response = await self.client.get(url, params=params)  # type: ignore[union-attr]
        if response.status_code == 404:
            return None
        if response.status_code == 429:
            import asyncio
            await asyncio.sleep(5)
            response = await self.client.get(url, params=params)  # type: ignore[union-attr]

        response.raise_for_status()
        item = response.json()

        authors = []
        for author in item.get("authors", []):
            if isinstance(author, dict):
                authors.append(author.get("name", ""))
            else:
                authors.append(str(author))

        tldr = ""
        if item.get("tldr"):
            if isinstance(item["tldr"], dict):
                tldr = item["tldr"].get("text", "")
            else:
                tldr = str(item["tldr"])

        return SemanticPaper(
            paper_id=item.get("paperId", ""),
            title=item.get("title", "Untitled"),
            authors=authors,
            year=item.get("year", 0),
            abstract=item.get("abstract", "") or "",
            citation_count=item.get("citationCount", 0) or 0,
            reference_count=item.get("referenceCount", 0) or 0,
            fields_of_study=item.get("fieldsOfStudy") or [],
            publication_types=item.get("publicationTypes") or [],
            open_access_pdf=item.get("openAccessPdf", {}).get("url")
            if isinstance(item.get("openAccessPdf"), dict)
            else None,
            venue=item.get("venue", "") or "",
            tldr=tldr,
        )

    async def get_citations(
        self, paper_id: str, limit: int = 10
    ) -> list[SemanticPaper]:
        """Get papers that cite the given paper."""
        if not HAS_HTTPX:
            raise ImportError("httpx required for Semantic Scholar")

        url = f"{self.BASE_URL}/paper/{paper_id}/citations"
        params = {
            "limit": min(limit, 100),
            "fields": "paperId,title,authors,year,abstract,citationCount,venue",
        }

        response = await self.client.get(url, params=params)  # type: ignore[arg-type, union-attr]
        response.raise_for_status()

        data = response.json()
        papers = []

        for item in data.get("data", []):
            citing_paper = item.get("citingPaper", {})
            authors = []
            for author in citing_paper.get("authors", []):
                if isinstance(author, dict):
                    authors.append(author.get("name", ""))
                else:
                    authors.append(str(author))

            paper = SemanticPaper(
                paper_id=citing_paper.get("paperId", ""),
                title=citing_paper.get("title", "Untitled"),
                authors=authors,
                year=citing_paper.get("year", 0),
                abstract=citing_paper.get("abstract", "") or "",
                citation_count=citing_paper.get("citationCount", 0) or 0,
                reference_count=0,
                fields_of_study=[],
                publication_types=[],
                venue=citing_paper.get("venue", "") or "",
            )
            papers.append(paper)

        return papers

    async def find_related_hypotheses(
        self, problem: str, top_k: int = 5
    ) -> list[dict[str, Any]]:
        """
        Find papers related to a research problem.
        Returns papers with relevance scores.
        """
        papers = await self.search_papers(problem, limit=top_k * 2)

        # Score by relevance (simple heuristic)
        results = []
        for paper in papers[:top_k]:
            score = 0.5  # Base score

            # Boost by citation count (log scale)
            if paper.citation_count > 0:
                import math

                score += min(math.log10(paper.citation_count) / 10, 0.3)

            # Boost for recent papers
            if paper.year >= 2020:
                score += 0.1

            # Boost for open access
            if paper.open_access_pdf:
                score += 0.1

            results.append(
                {
                    "paper": paper,
                    "relevance_score": min(score, 1.0),
                }
            )

        # Sort by score
        results.sort(key=lambda x: x["relevance_score"], reverse=True)  # type: ignore[arg-type, return-value]
        return results


def get_semantic_scholar_client() -> SemanticScholarClient:
    """Get singleton Semantic Scholar client (backed by DI container)."""
    from src.di.container import get_container
    return get_container().get_or_register("semantic_scholar_client", SemanticScholarClient)
