"""
C4REQBER API: v8 SciMatic Router
Endpoints for SciMatic integration (optional, proprietary).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.knowledge.scimatic_client import SciMaticClient


router = APIRouter(prefix="/scimatic", tags=["v8-scimatic"])


class SciMaticSearchResponse(BaseModel):
    """SciMaticSearchResponse."""
    papers: list[dict] = []
    total: int = 0
    error: str | None = None


class SciMaticExportRequest(BaseModel):
    """SciMaticExportRequest."""
    paper_ids: list[str]


@router.get("/search", response_model=SciMaticSearchResponse)
async def search_scimatic(
    q: str = Query(..., min_length=1, description="Search query"),
    sources: str | None = Query(None, description="Comma-separated sources"),
) -> SciMaticSearchResponse:
    """Multi-source search via SciMatic API."""
    client = SciMaticClient()
    if not client.api_key:
        raise HTTPException(
            status_code=501,
            detail="SciMatic API key required — user must provide own API key. "
            "Set SCIMATIC_API_KEY environment variable.",
        )

    source_list = sources.split(",") if sources else None
    result = client.search(q, source_list)

    if "error" in result:
        raise HTTPException(
            status_code=result.get("status", 500),
            detail=result["error"],
        )

    return SciMaticSearchResponse(
        papers=result.get("papers", []),
        total=result.get("total", 0),
    )


@router.post("/export")
async def export_bibtex(req: SciMaticExportRequest) -> dict[str, str]:
    """Export papers as BibTeX via SciMatic API."""
    client = SciMaticClient()
    if not client.api_key:
        raise HTTPException(
            status_code=501,
            detail="SciMatic API key required — user must provide own API key. "
            "Set SCIMATIC_API_KEY environment variable.",
        )

    bibtex = client.export_bibtex(req.paper_ids)
    if not bibtex:
        raise HTTPException(status_code=503, detail="Failed to export BibTeX")

    return {"bibtex": bibtex}
