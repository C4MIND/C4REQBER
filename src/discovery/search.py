"""Discovery search endpoints."""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any


logger = logging.getLogger(__name__)


async def search_knowledge(problem: str) -> list[dict[str, Any]]:
    """Search papers across registered sources."""
    try:
        from src.knowledge.orchestrator import MultiSourceSearcher

        searcher = MultiSourceSearcher()
        start = time.perf_counter()
        result = await asyncio.wait_for(
            searcher.search_all(problem, domain="general", max_per_source=8, include_web=False),
            timeout=12.0,
        )
        papers = result.get("papers", []) if isinstance(result, dict) else []
        elapsed = time.perf_counter() - start
        logger.info("Knowledge search found %d papers in %.2fs", len(papers), elapsed)
        return papers
    except TimeoutError:
        logger.warning("Knowledge search timed out")
        raise
    except Exception as e:
        logger.error("Knowledge search error: %s", e)
        raise
