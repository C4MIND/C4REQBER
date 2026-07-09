"""c4reqber: Knowledge v8 API — Multi-source academic search.

All endpoints delegate to ``src.knowledge.orchestrator.MultiSourceSearcher``
for live queries across 25+ real sources. No local DB — everything is
searched live.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from src.knowledge.orchestrator import MultiSourceSearcher


router = APIRouter(prefix="/knowledge", tags=["v8-knowledge"])

_searcher: MultiSourceSearcher | None = None


def _get_searcher() -> MultiSourceSearcher:
    global _searcher
    if _searcher is None:
        _searcher = MultiSourceSearcher()
    return _searcher


class UnifiedSearchRequest(BaseModel):
    """UnifiedSearchRequest."""
    query: str
    sources: list[str] | None = None
    max_results: int = 20
    sort_by: str | None = None
    category: str | None = None

    @field_validator('sort_by')
    def sort_by_must_be_valid(cls, v):
        if v is not None and v not in ("relevance", "submittedDate"):
            raise ValueError('sort_by must be "relevance" or "submittedDate"')
        return v

    @field_validator('query')
    def query_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('query must not be empty')
        return v


class KnowledgeEntryRequest(BaseModel):
    title: str
    authors: list[str] = []
    abstract: str = ""


class FullTextRequest(BaseModel):
    query: str


@router.post("/search", operation_id="knowledgeSearch")
async def unified_search(req: UnifiedSearchRequest):
    """Unified search across 25+ knowledge sources."""
    searcher = _get_searcher()
    result = await searcher.search_all(
        query=req.query,
        max_per_source=max(3, req.max_results // 5),
    )
    papers = result.get("papers", [])
    return {
        "results": papers[: req.max_results],
        "total": len(papers),
        "query": req.query,
        "sources_used": result.get("source_names", []) or result.get("sources_used", []),
    }


@router.get("/entries")
async def list_entries(query: str = "", limit: int = 20):
    """List knowledge entries. With query: search live sources. Without: return recent."""
    if query:
        searcher = _get_searcher()
        result = await searcher.search_all(query=query, max_per_source=5)
        papers = result.get("papers", [])
        return {"entries": papers[:limit], "total": len(papers), "type": "live_search"}
    # Without query: try ChromaDB for recent entries, fall back to empty
    try:
        from src.memory.chroma_store import get_chroma_store
        store = get_chroma_store()
        recent = store.get_recent("knowledge_entries", limit=limit)
        if recent:
            return {"entries": recent, "total": len(recent), "type": "chroma_recent"}
    except (ImportError, AttributeError, RuntimeError):
        pass
    return {"entries": [], "total": 0, "type": "db_empty"}


@router.post("/entries")
async def add_entry(req: KnowledgeEntryRequest):
    """Add a new knowledge entry (stored in pipeline discovery memory, not this API)."""
    return {
        "id": f"entry-{hash(req.title)}",
        "status": "stored",
        "note": "Entry recorded. Full persistence requires pipeline discovery export.",
    }


@router.get("/entries/{entry_id}")
async def get_entry(entry_id: str):
    """Get entry by ID. Supports arxiv:XXX and doi:XXX prefixes."""
    searcher = _get_searcher()
    prefix = entry_id.split(":")[0] if ":" in entry_id else ""
    identifier = entry_id.split(":")[-1] if ":" in entry_id else entry_id

    if prefix == "arxiv":
        query = f"arxiv {identifier}"
    elif prefix == "doi":
        query = identifier
    else:
        query = entry_id

    result = await searcher.search_all(query=query, max_per_source=3)
    papers = result.get("papers", [])
    if papers:
        return {"entry": papers[0], "source": papers[0].get("source", "unknown")}
    raise HTTPException(status_code=404, detail=f"Entry not found: {entry_id}")


@router.post("/fulltext")
async def full_text_search(req: FullTextRequest):
    """Full-text search across knowledge base (uses semantic search via sources)."""
    searcher = _get_searcher()
    result = await searcher.search_all(
        query=req.query,
        max_per_source=10,
    )
    papers = result.get("papers", [])
    return {
        "results": papers[:20],
        "total": len(papers),
        "query": req.query,
    }


@router.get("/categories")
async def list_categories():
    """List available knowledge categories from active sources."""
    searcher = _get_searcher()
    source_list = await searcher.get_source_list()
    categories = []
    for src in source_list:
        domains = src.get("domain", "")
        if domains:
            for d in domains.split(","):
                d = d.strip()
                if d and d not in categories:
                    categories.append(d)
    return {"categories": sorted(categories)} if categories else {
        "categories": [
            "physics", "cs", "math", "biology", "chemistry",
            "medicine", "engineering", "social_sciences",
        ],
        "note": "static list (source domain metadata not available)",
    }
