from __future__ import annotations

import json


"""Novelty validator — checks hypothesis overlap against CrossRef papers."""
import logging
from difflib import SequenceMatcher
from typing import Any


logger = logging.getLogger("c44tcdi.novelty.validator")

try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


class NoveltyValidator:
    """NoveltyValidator."""
    def __init__(self) -> None:
        self.crossref_base = "https://api.crossref.org/works"
        self._client: Any = None
        if HAS_HTTPX:
            self._client = httpx.AsyncClient(timeout=30.0)

    async def check_novelty(self, hypothesis: str, domain: str = "") -> dict[str, Any]:
        """Check if hypothesis overlaps with existing papers."""
        if not HAS_HTTPX:
            return {
                "status": "unchecked",
                "reason": "httpx not installed",
                "novel": None,
            }

        keywords = hypothesis[:200]
        try:
            async with httpx.AsyncClient(timeout=30.0) as c:
                r = await c.get(f"{self.crossref_base}?query={keywords}&rows=10")
                if r.status_code != 200:
                    return {"status": "unchecked", "reason": f"API returned {r.status_code}"}

                papers = r.json().get("message", {}).get("items", [])
                similarities: list[dict[str, Any]] = []
                for paper in papers[:10]:
                    title = paper.get("title", [""])[0] if paper.get("title") else ""
                    sim = SequenceMatcher(None, hypothesis[:200].lower(), title.lower()).ratio()
                    similarities.append({"title": title[:120], "similarity": round(sim, 3)})

                max_sim = max((s["similarity"] for s in similarities), default=0)
                closest = [s for s in similarities if s["similarity"] == max_sim][:1]

                return {
                    "status": "checked",
                    "novel": max_sim < 0.3,
                    "max_similarity": max_sim,
                    "closest_paper": closest,
                    "papers_checked": len(similarities),
                }
        except TimeoutError:
            logger.warning("Novelty check timed out")
            return {"status": "unchecked", "reason": "timeout", "novel": None}
        except (IndexError, KeyError, TypeError, httpx.HTTPError, json.JSONDecodeError) as e:
            logger.error("Novelty check error: %s", e)
            return {"status": "unchecked", "reason": str(e), "novel": None}

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()

    async def __aenter__(self) -> NoveltyValidator:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
