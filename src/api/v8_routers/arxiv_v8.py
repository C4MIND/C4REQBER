from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/arxiv", tags=["v8-arxiv"])

class ArxivSearchRequest(BaseModel):
    """ArxivSearchRequest."""
    query: str
    max_results: int = 20

@router.get("/search")
async def search_papers(q: str, max_results: int = 20) -> dict[str, Any]:
    """Search arXiv papers (free, no quota)."""
    from src.knowledge.arxiv_client import ArxivClient
    client = ArxivClient()
    results = client.search(q, max_results)
    return {"papers": results, "total": len(results)}

@router.get("/paper/{arxiv_id}")
async def get_paper(arxiv_id: str) -> dict[str, Any]:
    """Get paper metadata + TOC."""
    from src.knowledge.arxiv_client import ArxivClient
    client = ArxivClient()
    paper = client.get_paper(arxiv_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper

@router.get("/paper/{arxiv_id}/fulltext")
async def get_full_text(arxiv_id: str) -> dict[str, Any]:
    """Get full text (uses quota)."""
    from src.knowledge.arxiv_client import ArxivClient
    client = ArxivClient()

    if not client.api_key:
        raise HTTPException(status_code=501, detail="API key required for full text. Set ARXIV_API_KEY")

    text = client.get_full_text(arxiv_id)
    return {"text": text}
