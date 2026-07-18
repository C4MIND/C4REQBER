"""Shared flash-mode literature/web context (CLI + MCP)."""

from __future__ import annotations

import logging
from typing import Any


logger = logging.getLogger(__name__)


async def gather_flash_sources(
    question: str,
    *,
    deep: bool = False,
    include_web: bool = True,
) -> tuple[list[dict[str, Any]], str]:
    """Search MultiSourceSearcher for flash context.

    Returns (papers, context_block). Never invents example.com URLs.
    """
    from src.knowledge.orchestrator import MultiSourceSearcher

    searcher = MultiSourceSearcher()
    try:
        result = await searcher.search_all(question, include_web=include_web)
    except Exception as exc:
        logger.warning("flash sources search failed: %s", exc)
        return [], ""

    limit = 5 if deep else 3
    papers = result.get("papers", [])[:limit]
    context = "\n".join(
        [
            f"- {p.get('title', '')} ({p.get('_source', 'unknown')}): "
            f"{p.get('snippet', p.get('abstract', ''))[:250]}"
            for p in papers
        ]
    )
    return papers, context
