"""
C4REQBER API: Search Router

Federated search across 15+ academic APIs via MultiSourceSearcher.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from src.api.dependencies import check_rate_limit_ip
from src.api.models import SearchRequest, SearchResponse


router = APIRouter(prefix="/api/v1/search", tags=["search"])


@router.post("/papers", response_model=SearchResponse)
async def search_papers(
    request: SearchRequest,
    _rate_limit: bool = Depends(check_rate_limit_ip),
) -> SearchResponse:
    """Federated paper search across OpenAlex, CrossRef, PubMed, arXiv, and more."""
    from src.knowledge.orchestrator import MultiSourceSearcher

    ms = MultiSourceSearcher(max_concurrent=8)
    result = await ms.search_all(
        request.query,
        domain="general",
        max_per_source=request.limit or 10,
    )
    papers = result.get("papers", [])

    return SearchResponse(
        query=request.query,
        total=len(papers),
        papers=[
            {
                "title": p.get("title", ""),
                "authors": p.get("authors", []),
                "year": p.get("year", 0) or 0,
                "citation_count": p.get("citation_count", 0),
                "abstract": (p.get("abstract", "")[:200] + "...")
                if p.get("abstract") and len(p.get("abstract", "")) > 200
                else (p.get("abstract") or ""),
                "source": p.get("source", ""),
                "doi": p.get("doi", ""),
                "url": p.get("url", ""),
            }
            for p in papers
        ],
    )


@router.get("/papers")
async def search_papers_get(
    query: str = Query(..., min_length=3, max_length=500),
    limit: int = Query(10, ge=1, le=100),
    _rate_limit: bool = Depends(check_rate_limit_ip),
) -> SearchResponse:
    """GET wrapper for federated paper search."""
    return await search_papers(
        SearchRequest(query=query, limit=limit),
        _rate_limit,
    )
