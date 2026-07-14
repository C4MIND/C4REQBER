from __future__ import annotations


"""
News Aggregator — extracts trending problems, recent discoveries, and patents
for the live ticker feed. Uses existing knowledge sources + LLM reformulation.
"""
import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from src.news.storage import NewsStorage


logger = logging.getLogger("c44tcdi.news.aggregator")

_LLM_REFORMULATE_PROMPT = """You are a science news editor. Given a list of research paper titles and abstracts,
produce a concise, engaging headline (max 120 chars) suitable for a scrolling news ticker.
Each headline should be a single line. Return ONLY the headlines, one per line, no numbering, no prefixes."""

_UNSOLVED_QUERIES = [
    "unsolved problem in physics OR astronomy OR cosmology",
    "open problem mathematics 2025 OR 2026",
    "unsolved challenge machine learning OR AI OR artificial intelligence",
    "major unsolved question in biology OR genetics OR evolution",
    "unsolved problem in chemistry OR materials science",
    "open question neuroscience OR cognitive science OR psychology",
    "unsolved problem in medicine OR immunology OR virology",
    "open problem climate science OR atmospheric physics OR oceanography",
    "unsolved problem in quantum computing OR quantum information",
    "open question economics OR game theory OR social science",
    "unsolved problem in linguistics OR philosophy of science",
    "open problem computer science OR cryptography OR algorithms",
    "unsolved problem in geology OR planetary science OR astrobiology",
    "open question robotics OR control theory OR dynamical systems",
    "unsolved problem in agriculture OR food science OR ecology",
    "open problem optics OR photonics OR electromagnetism",
    "unsolved problem in energy OR battery technology OR fusion",
    "open question nanotechnology OR molecular engineering",
]

class NewsAggregator:
    """Aggregates news, patents, and discoveries for the live ticker."""

    def __init__(self, storage: NewsStorage | None = None) -> None:
        self._storage = storage or NewsStorage()

    async def _search_knowledge(self, query: str, max_results: int = 8) -> list[dict[str, Any]]:
        try:
            from src.knowledge.mega_db import MegaDatabase
            db = MegaDatabase()
            grouped = await db.search_all(query, max_per_source=max_results)
            flat: list[dict[str, Any]] = []
            for source_key, papers in grouped.items():
                for paper in papers:
                    paper["_source"] = source_key
                    flat.append(paper)
            return flat
        except ImportError as e:
            logger.warning("MegaDatabase not available for news aggregation: %s", e)
            raise
        except (TimeoutError, KeyError, TypeError) as e:
            logger.error("Knowledge search error: %s", e)
            raise

    async def _search_arxiv(self, query: str, max_results: int = 8) -> list[dict[str, Any]]:
        try:
            from src.knowledge.arxiv_client import AsyncArxivClient
            async with AsyncArxivClient() as client:
                results = await client.search(query, max_results=max_results)
                return results if isinstance(results, list) else []
        except ImportError as e:
            logger.warning("arXiv client not available: %s", e)
            raise
        except (TimeoutError, TypeError) as e:
            logger.error("arXiv search error: %s", e)
            raise

    async def _search_pubmed(self, query: str, max_results: int = 8) -> list[dict[str, Any]]:
        try:
            from src.knowledge.pubmed_client import AsyncPubMedClient
            client = AsyncPubMedClient()
            results = await client.search(query, max_results=max_results)
            return results if isinstance(results, list) else []  # type: ignore[return-value]
        except ImportError as e:
            logger.warning("PubMed client not available: %s", e)
            raise
        except (TimeoutError, TypeError) as e:
            logger.error("PubMed search error: %s", e)
            raise

    async def _reformulate_titles(self, titles: list[str]) -> list[str]:
        """Use LLM to rewrite technical titles into ticker-friendly headlines.
        Falls back to original titles if LLM unavailable."""
        if not titles:
            return []
        try:
            from src.llm.multi_provider import async_generate
            joined = "\n".join(f"- {t}" for t in titles[:20])
            prompt = f"{_LLM_REFORMULATE_PROMPT}\n\nPapers:\n{joined}"
            response = await async_generate(prompt, max_tokens=300)
            lines = [line.strip(" -•") for line in response.content.split("\n") if line.strip()]
            return lines[:len(titles) + 5]
        except Exception:
            return [t[:120] for t in titles]

    async def fetch_trending_problems(self) -> list[dict[str, Any]]:
        """Search for unsolved/open problems across 18 science domains."""
        all_results: list[dict[str, Any]] = []
        tasks = [self._search_knowledge(q, max_results=3) for q in _UNSOLVED_QUERIES]
        batches = await asyncio.gather(*tasks, return_exceptions=True)
        for batch in batches:
            if isinstance(batch, list):
                all_results.extend(batch)

        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for item in all_results:
            title = item.get("title", "")
            if title and title not in seen and not _is_noise(title):
                seen.add(title)
                unique.append(item)
        return unique[:30]

    async def fetch_recent_discoveries(self) -> list[dict[str, Any]]:
        """Fetch meaningful scientific breakthroughs, not challenge reports."""
        _results = await asyncio.gather(
            self._search_arxiv(
                "novel method OR significant advance OR new paradigm 2025 2026", max_results=15
            ),
            self._search_pubmed(
                "novel therapeutic OR breakthrough treatment OR new mechanism", max_results=10
            ),
            return_exceptions=True,
        )
        arxiv_results: list[dict[str, Any]] | BaseException = _results[0]
        pubmed_results: list[dict[str, Any]] | BaseException = _results[1]

        combined: list[dict[str, Any]] = []
        seen: set[str] = set()

        for batch in (arxiv_results, pubmed_results):
            if not isinstance(batch, list):
                continue
            for item in batch:
                title = item.get("title", "")
                if not title or title in seen:
                    continue
                if _is_noise(title):
                    continue
                seen.add(title)
                combined.append(item)

        return combined[:20]

    async def fetch_recent_patents(self) -> list[dict[str, Any]]:
        """Fetch recent patents (USPTO not yet integrated — graceful fallback)."""
        logger.warning(
            "USPTO patent feed not yet integrated — coming in v8.2. "
            "Requires USPTO API key + rate-limit handling."
        )
        return []

    async def get_ticker_feed(self, limit: int = 50) -> list[dict[str, Any]]:
        """Combined feed for the live ticker. Merges problems + discoveries,
        deduplicates, reformulates via LLM, and stores in local DB."""
        problems = await self.fetch_trending_problems()
        discoveries = await self.fetch_recent_discoveries()

        all_titles: list[str] = []
        all_items: list[dict[str, Any]] = []

        for item in problems + discoveries:
            title = item.get("title", "")
            if title:
                all_titles.append(title)
                all_items.append(item)

        if not all_titles:
            return []

        headlines = await self._reformulate_titles(all_titles)

        feed: list[dict[str, Any]] = []
        now_iso = datetime.now(UTC).isoformat()

        for i, item in enumerate(all_items):
            display_title = headlines[i] if i < len(headlines) else item.get("title", "")
            category = "problem" if i < len(problems) else "discovery"

            self._storage.upsert(
                title=display_title,
                body=item.get("abstract", item.get("summary", "")),
                source=item.get("source", item.get("_source", "")),
                url=item.get("url", ""),
                category=category,
                published_at=now_iso,
            )

            feed.append({
                "title": display_title,
                "body": item.get("abstract", item.get("summary", "")),
                "source": item.get("source", item.get("_source", "")),
                "url": item.get("url", ""),
                "category": category,
                "published_at": now_iso,
            })

        return feed[:limit]


_NOISE_WORDS = {
    "challenge", "benchmark", "survey", "proceedings", "workshop",
    "competition", "shared task", "overview of", "NTIRE", "VQualA",
    "challenge report", "challenge on", "summary of",
}


def _is_noise(title: str) -> bool:
    t = title.lower()
    return any(w in t for w in _NOISE_WORDS)
