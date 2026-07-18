"""Discovery search endpoints."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any


logger = logging.getLogger(__name__)


async def search_knowledge(problem: str) -> list[dict[str, Any]]:
    """Search papers across registered sources.

    Resilience: a single slow/unreachable source must never abort the caller.
    Per-source timeouts are bounded in the orchestrator; this outer guard is
    only a last-resort safety net and is set ABOVE the largest per-source
    timeout so it never preempts the orchestrator's own graceful timeouts.
    On any failure we return an empty list (FLASH is a quick-answer mode that
    does not require papers) instead of raising into the discovery job.
    """
    start = time.perf_counter()
    try:
        from src.knowledge.orchestrator import MultiSourceSearcher

        searcher = MultiSourceSearcher()
        result = await asyncio.wait_for(
            searcher.search_all(problem, domain="general", max_per_source=8, include_web=False),
            timeout=90.0,
        )
        papers = result.get("papers", []) if isinstance(result, dict) else []
        elapsed = time.perf_counter() - start
        logger.info("Knowledge search found %d papers in %.2fs", len(papers), elapsed)
        return papers
    except (TimeoutError, asyncio.CancelledError, Exception) as e:
        logger.warning(
            "Knowledge search failed/timed out (%.1fs): %s", time.perf_counter() - start, e
        )
        return []
