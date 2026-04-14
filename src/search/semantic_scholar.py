"""
TURBO-CDI: Semantic Scholar Integration
Search 200M+ papers from Semantic Scholar API
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import asyncio

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
    authors: List[str]
    year: int
    abstract: str
    citation_count: int
    reference_count: int
    fields_of_study: List[str]
    publication_types: List[str]
    open_access_pdf: Optional[str] = None
    venue: str = ""
    tldr: str = ""  # AI-generated TL;DR


class SemanticScholarClient:
    """
    Client for Semantic Scholar API.

    Free tier: 100 requests per 5 minutes
    Docs: https://api.semanticscholar.org/api-docs/
    """

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
        self.client = None
        if HAS_HTTPX:
            headers = {}
            if self.api_key:
                headers["x-api-key"] = self.api_key
            self.client = httpx.AsyncClient(headers=headers, timeout=30.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        if self.client:
            await self.client.aclose()

    async def search_papers(
        self,
        query: str,
        limit: int = 10,
        fields: Optional[List[str]] = None,
        year_start: Optional[int] = None,
        year_end: Optional[int] = None,
        open_access_only: bool = False,
    ) -> List[SemanticPaper]:
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

        response = await self.client.get(url, params=params)
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

    async def get_paper_details(self, paper_id: str) -> Optional[SemanticPaper]:
        """Get detailed information about a specific paper."""
        if not HAS_HTTPX:
            raise ImportError("httpx required for Semantic Scholar")

        url = f"{self.BASE_URL}/paper/{paper_id}"
        params = {
            "fields": "paperId,title,authors,year,abstract,citationCount,referenceCount,fieldsOfStudy,publicationTypes,openAccessPdf,venue,tldr"
        }

        response = await self.client.get(url, params=params)
        if response.status_code == 404:
            return None

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
    ) -> List[SemanticPaper]:
        """Get papers that cite the given paper."""
        if not HAS_HTTPX:
            raise ImportError("httpx required for Semantic Scholar")

        url = f"{self.BASE_URL}/paper/{paper_id}/citations"
        params = {
            "limit": min(limit, 100),
            "fields": "paperId,title,authors,year,abstract,citationCount,venue",
        }

        response = await self.client.get(url, params=params)
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
    ) -> List[Dict[str, Any]]:
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
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results


# Singleton instance
_client: Optional[SemanticScholarClient] = None


def get_semantic_scholar_client() -> SemanticScholarClient:
    """Get singleton Semantic Scholar client."""
    global _client
    if _client is None:
        _client = SemanticScholarClient()
    return _client
