"""Agent literature search — shared by blast agent_search tool (no stub theatre)."""

from __future__ import annotations

import json
from typing import Any


async def run_agent_search(query: str, max_results: int = 10) -> dict[str, Any]:
    """Gather + partition verified sources. Never invent success for empty/failed search."""
    from src.knowledge.flash_contract import source_cards_from_papers
    from src.knowledge.flash_sources import gather_flash_sources

    q = (query or "").strip()
    if not q:
        return {
            "status": "error",
            "message": "Search query cannot be empty.",
            "sources": [],
            "verified_count": 0,
            "found_count": 0,
        }

    limit = max(1, min(int(max_results), 25))
    try:
        papers, _context, search_meta = await gather_flash_sources(
            q,
            deep=limit > 5,
            include_web=True,
        )
    except Exception as exc:
        return {
            "status": "error",
            "message": f"Literature search unavailable: {exc}",
            "sources": [],
            "verified_count": 0,
            "found_count": 0,
            "search_meta": {"errors": {"gather": str(exc)[:200]}},
        }

    papers = papers[:limit]
    partitioned = source_cards_from_papers(papers, sanitize=False, limit=limit)
    verified_count = int(partitioned["verified_count"])
    found_count = int(partitioned["found_count"])
    errors = search_meta.get("errors") or {}

    if found_count == 0 and errors:
        return {
            "status": "error",
            "message": "Literature search unavailable — all configured sources failed.",
            "sources": [],
            "unverified_hits": [],
            "verified_count": 0,
            "found_count": 0,
            "search_meta": search_meta,
        }

    status = "success" if verified_count > 0 else "partial"
    if found_count == 0:
        status = "partial"

    return {
        "status": status,
        "query": q,
        "sources": partitioned["sources"],
        "unverified_hits": partitioned["unverified_hits"],
        "verified_count": verified_count,
        "found_count": found_count,
        "search_meta": search_meta,
    }


async def run_agent_search_json(query: str, max_results: int = 10) -> str:
    """JSON string form for MCP/agent tool surfaces."""
    return json.dumps(await run_agent_search(query, max_results), ensure_ascii=False)
