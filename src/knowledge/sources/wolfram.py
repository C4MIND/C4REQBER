# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""Wolfram Alpha integration — 29th knowledge source.

Wolfram Alpha API provides computational answers to factual queries.
API: https://api.wolframalpha.com/v1/result (Short Answers)
     https://api.wolframalpha.com/v2/query (Full Results)
"""
from __future__ import annotations

import logging
import os
from typing import Any

import httpx


logger = logging.getLogger(__name__)

WOLFRAM_APP_ID = os.environ.get("WOLFRAM_APP_ID", "")
WOLFRAM_SHORT_URL = "https://api.wolframalpha.com/v1/result"
WOLFRAM_FULL_URL = "https://api.wolframalpha.com/v2/query"


def is_available() -> bool:
    return bool(WOLFRAM_APP_ID)


async def query_short(question: str) -> dict[str, Any]:
    """Quick factual answer from Wolfram Alpha."""
    if not WOLFRAM_APP_ID:
        return {"status": "unavailable", "error": "WOLFRAM_APP_ID not set"}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(
                WOLFRAM_SHORT_URL,
                params={"appid": WOLFRAM_APP_ID, "i": question, "units": "metric"},
            )
            if r.status_code == 200:
                return {"status": "ok", "result": r.text.strip(), "source": "wolfram_alpha"}
            return {"status": "error", "error": f"HTTP {r.status_code}", "source": "wolfram_alpha"}
    except Exception as e:
        logger.debug("Wolfram query failed: %s", e)
        return {"status": "error", "error": str(e), "source": "wolfram_alpha"}


async def search_sources(topic: str, max_results: int = 5) -> list[dict[str, Any]]:
    """Search Wolfram Alpha as a knowledge source (orchestrator-compatible)."""
    result = await query_short(topic)
    if result["status"] != "ok":
        return []

    return [{
        "title": f"Wolfram: {topic[:60]}",
        "snippet": result.get("result", "")[:500],
        "authors": "Wolfram Alpha",
        "year": "",
        "venue": "wolfram_alpha",
        "url": f"https://www.wolframalpha.com/input?i={topic.replace(' ', '+')}",
        "source": "wolfram_alpha",
    }]
