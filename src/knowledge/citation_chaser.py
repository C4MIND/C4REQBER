from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import defaultdict
from typing import Any

import httpx


logger = logging.getLogger(__name__)


class CitationChaser:
    """Recursive citation graph crawler. Depth-based expansion of paper network."""

    MAX_DEPTH = 3
    MAX_PAPERS_PER_DEPTH = 50
    CITATION_GROWTH_WINDOW_YEARS = 5
    SEMINAL_PAPER_CITATION_THRESHOLD = 50
    MAX_CONCURRENT = 8
    RATE_LIMIT_INTERVAL = 0.35

    def __init__(
        self,
        max_depth: int = MAX_DEPTH,
        max_papers_per_depth: int = MAX_PAPERS_PER_DEPTH,
        seminal_threshold: int = SEMINAL_PAPER_CITATION_THRESHOLD,
        timeout: float = 15.0,
    ) -> None:
        self.max_depth = max_depth
        self.max_papers_per_depth = max_papers_per_depth
        self.seminal_threshold = seminal_threshold
        self.timeout = timeout
        self._semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)
        self._rate_lock: asyncio.Lock | None = asyncio.Lock()
        self._last_request: float = 0.0

    async def chase(
        self,
        seed_papers: list[dict[str, Any]],
        query: str,
    ) -> dict[str, Any]:
        """Chase."""
        start_time = time.monotonic()
        self._last_request = time.monotonic()

        depth_papers: dict[int, list[dict[str, Any]]] = {}
        visited_ids: set[str] = set()
        citation_graph: dict[str, list[str]] = {}
        crawl_timing: dict[int, float] = {}

        depth_papers[0] = list(seed_papers)
        for paper in seed_papers:
            pid = self._extract_id(paper)
            if pid:
                visited_ids.add(pid)

        for depth in range(0, self.max_depth):
            current_papers = depth_papers.get(depth, [])
            if not current_papers:
                break

            depth_start = time.monotonic()
            next_papers: list[dict[str, Any]] = []

            for paper in current_papers[: self.max_papers_per_depth]:
                pid = self._extract_id(paper)
                if not pid:
                    continue

                citations, references = await asyncio.gather(
                    self._get_citations(pid),
                    self._get_references(pid),
                )

                citation_graph[pid] = [self._extract_id(r) for r in references if self._extract_id(r)]

                for cited_paper in citations + references:
                    cid = self._extract_id(cited_paper)
                    if cid and cid not in visited_ids:
                        visited_ids.add(cid)
                        next_papers.append(cited_paper)

            depth_papers[depth + 1] = next_papers[: self.max_papers_per_depth]
            crawl_timing[depth] = round(time.monotonic() - depth_start, 3)

        all_papers = self._deduplicate_by_id(
            [p for papers in depth_papers.values() for p in papers]
        )

        seminal_papers = self._find_seminal_papers(all_papers)
        citation_velocity = self._compute_citation_velocity(all_papers)
        first_year = self._find_first_publication(all_papers)
        paradigm_timeline = self._build_paradigm_timeline(all_papers, query)

        growth_rate, r_squared = self._linear_regression_slope(all_papers)
        is_field_growing = growth_rate > 0.05 and r_squared > 0.5
        has_plateaued = abs(growth_rate) < 0.02

        total_time = round(time.monotonic() - start_time, 3)

        result: dict[str, Any] = {
            **{f"depth_{d}": depth_papers.get(d, []) for d in range(self.max_depth + 1)},
            "all_papers": all_papers,
            "citation_graph": citation_graph,
            "seminal_papers": seminal_papers,
            "citation_velocity": citation_velocity,
            "first_publication_year": first_year,
            "total_unique_papers": len(all_papers),
            "crawl_timing": crawl_timing,
            "paradigm_timeline": paradigm_timeline,
            "is_field_growing": is_field_growing,
            "growth_rate": round(growth_rate, 4),
            "has_plateaued": has_plateaued,
            "r_squared": round(r_squared, 4),
            "total_time": total_time,
        }
        return result

    async def _rate_limit(self) -> None:
        if self._rate_lock is None:
            self._rate_lock = asyncio.Lock()
        async with self._rate_lock:
            now = time.monotonic()
            wait = self._last_request + self.RATE_LIMIT_INTERVAL - now
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request = time.monotonic()

    async def _get_citations(
        self,
        paper_id: str,
        source: str = "semantic_scholar",
    ) -> list[dict[str, Any]]:
        if source == "semantic_scholar":
            return await self._get_citations_from_s2(paper_id, limit=self.max_papers_per_depth)
        if source == "opencitations":
            return await self._get_citations_from_oc(paper_id)
        return []

    async def _get_references(
        self,
        paper_id: str,
        source: str = "semantic_scholar",
    ) -> list[dict[str, Any]]:
        if source == "semantic_scholar":
            return await self._get_references_from_s2(paper_id, limit=self.max_papers_per_depth)
        if source == "opencitations":
            return await self._get_references_from_oc(paper_id)
        return []

    @staticmethod
    def _validate_paper_id(paper_id: str) -> str:
        import re
        if not re.fullmatch(r"[A-Za-z0-9_-]+", paper_id):
            raise ValueError(f"Invalid paper_id format: {paper_id}")
        return paper_id

    async def _get_citations_from_s2(
        self,
        paper_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        paper_id = self._validate_paper_id(paper_id)
        url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/citations"
        params: dict[str, Any] = {
            "limit": limit,
            "fields": "title,authors,year,abstract,citationCount,externalIds,publicationVenue,publicationDate",
        }
        for attempt in range(3):
            try:
                await self._rate_limit()
                async with self._semaphore:
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        resp = await client.get(url, params=params)
                if resp.status_code == 404:
                    return []
                if resp.status_code == 429:
                    wait = 2 ** attempt
                    logger.debug("S2 citations 429, retry %d/%d after %ds", attempt + 1, 3, wait)
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                data = resp.json()
                return [
                    {
                        "title": c.get("citingPaper", {}).get("title", ""),
                        "paper_id": c.get("citingPaper", {}).get("paperId", ""),
                        "s2_id": c.get("citingPaper", {}).get("paperId", ""),
                        "year": c.get("citingPaper", {}).get("year"),
                        "citation_count": c.get("citingPaper", {}).get("citationCount", 0),
                        "authors": [a.get("name") for a in c.get("citingPaper", {}).get("authors", [])],
                        "doi": (c.get("citingPaper", {}).get("externalIds") or {}).get("DOI", ""),
                        "abstract": c.get("citingPaper", {}).get("abstract", ""),
                        "publication_date": c.get("citingPaper", {}).get("publicationDate", ""),
                        "source": "semantic_scholar_citations",
                    }
                    for c in data.get("data", [])
                ]
            except (TimeoutError, httpx.TimeoutException, httpx.HTTPError, json.JSONDecodeError) as e:
                logger.debug("S2 citations error for %s: %s", paper_id, e)
                if attempt < 2:
                    await asyncio.sleep(1.0)
        return []

    async def _get_references_from_s2(
        self,
        paper_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        paper_id = self._validate_paper_id(paper_id)
        url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/references"
        params: dict[str, Any] = {
            "limit": limit,
            "fields": "title,authors,year,abstract,citationCount,externalIds,publicationVenue,publicationDate",
        }
        for attempt in range(3):
            try:
                await self._rate_limit()
                async with self._semaphore:
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        resp = await client.get(url, params=params)
                if resp.status_code == 404:
                    return []
                if resp.status_code == 429:
                    wait = 2 ** attempt
                    logger.debug("S2 references 429, retry %d/%d after %ds", attempt + 1, 3, wait)
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                data = resp.json()
                return [
                    {
                        "title": r.get("citedPaper", {}).get("title", ""),
                        "paper_id": r.get("citedPaper", {}).get("paperId", ""),
                        "s2_id": r.get("citedPaper", {}).get("paperId", ""),
                        "year": r.get("citedPaper", {}).get("year"),
                        "citation_count": r.get("citedPaper", {}).get("citationCount", 0),
                        "authors": [a.get("name") for a in r.get("citedPaper", {}).get("authors", [])],
                        "doi": (r.get("citedPaper", {}).get("externalIds") or {}).get("DOI", ""),
                        "abstract": r.get("citedPaper", {}).get("abstract", ""),
                        "publication_date": r.get("citedPaper", {}).get("publicationDate", ""),
                        "source": "semantic_scholar_references",
                    }
                    for r in data.get("data", [])
                    if r.get("citedPaper")
                ]
            except (TimeoutError, httpx.TimeoutException, httpx.HTTPError, json.JSONDecodeError) as e:
                logger.debug("S2 references error for %s: %s", paper_id, e)
                if attempt < 2:
                    await asyncio.sleep(1.0)
        return []

    async def _get_citations_from_oc(
        self,
        paper_id: str,
    ) -> list[dict[str, Any]]:
        doi = paper_id if "/" in paper_id else ""
        if not doi:
            return []
        url = f"https://opencitations.net/index/api/v2/citations/{doi}"
        try:
            await self._rate_limit()
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url)
                if resp.status_code == 404:
                    return []
                resp.raise_for_status()
                data = resp.json()
            return [
                {
                    "paper_id": c.get("citing", ""),
                    "title": "",
                    "year": None,
                    "citation_count": 0,
                    "authors": [],
                    "doi": c.get("citing", ""),
                    "source": "opencitations",
                }
                for c in data
            ]
        except (TimeoutError, httpx.TimeoutException, httpx.HTTPError, json.JSONDecodeError) as e:
            logger.debug("OpenCitations citations error for %s: %s", paper_id, e)
            return []

    async def _get_references_from_oc(
        self,
        paper_id: str,
    ) -> list[dict[str, Any]]:
        doi = paper_id if "/" in paper_id else ""
        if not doi:
            return []
        url = f"https://opencitations.net/index/api/v2/references/{doi}"
        try:
            await self._rate_limit()
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url)
                if resp.status_code == 404:
                    return []
                resp.raise_for_status()
                data = resp.json()
            return [
                {
                    "paper_id": c.get("cited", ""),
                    "title": "",
                    "year": None,
                    "citation_count": 0,
                    "authors": [],
                    "doi": c.get("cited", ""),
                    "source": "opencitations",
                }
                for c in data
            ]
        except (TimeoutError, httpx.TimeoutException, httpx.HTTPError, json.JSONDecodeError) as e:
            logger.debug("OpenCitations references error for %s: %s", paper_id, e)
            return []

    def _compute_citation_velocity(self, papers: list[dict[str, Any]]) -> float:
        import datetime
        current_year = datetime.datetime.now().year
        year_citations: dict[int, int] = defaultdict(int)
        year_counts: dict[int, int] = defaultdict(int)

        for paper in papers:
            year = paper.get("year")
            if not isinstance(year, int) or year is None or year <= 0:
                continue
            cc = paper.get("citation_count", 0)
            if not isinstance(cc, (int, float)):
                cc = 0
            year_citations[year] += int(cc)
            year_counts[year] += 1

        recent_years = range(current_year - self.CITATION_GROWTH_WINDOW_YEARS, current_year + 1)
        early_start = min((y for y, _ in year_citations.items()), default=2000)
        early_years = range(early_start, early_start + min(self.CITATION_GROWTH_WINDOW_YEARS, 5))

        recent_total = sum(year_citations.get(y, 0) for y in recent_years)
        early_total = sum(year_citations.get(y, 0) for y in early_years)

        if early_total > 0:
            return round(recent_total / max(early_total, 1), 4)
        return round(float(recent_total), 4)

    def _find_seminal_papers(self, papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        candidates = [p for p in papers if p.get("citation_count", 0) >= self.seminal_threshold]
        candidates.sort(key=lambda p: (p.get("year") or 9999, -p.get("citation_count", 0)))
        return candidates[:20]

    def _find_first_publication(self, papers: list[dict[str, Any]]) -> int:
        years: list[int] = []
        for p in papers:
            year = p.get("year")
            if isinstance(year, int) and year > 0:
                years.append(year)
        return min(years) if years else 2000

    def _deduplicate_by_id(self, papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: dict[str, dict[str, Any]] = {}
        import hashlib
        for paper in papers:
            pid = self._extract_id(paper)
            if not pid:
                # Use content hash instead of object identity
                content = json.dumps(paper, sort_keys=True, default=str)
                pid = "content_" + hashlib.sha256(content.encode()).hexdigest()[:16]
            if pid not in seen:
                seen[pid] = paper
            else:
                existing = seen[pid]
                if (paper.get("citation_count") or 0) > (existing.get("citation_count") or 0):
                    seen[pid] = paper
                elif not existing.get("abstract") and paper.get("abstract"):
                    seen[pid] = {**existing, "abstract": paper["abstract"]}
        return list(seen.values())

    def _linear_regression_slope(self, papers: list[dict[str, Any]]) -> tuple[float, float]:
        year_citations: dict[int, int] = defaultdict(int)
        year_counts: dict[int, int] = defaultdict(int)

        for paper in papers:
            year = paper.get("year")
            if not isinstance(year, int) or year is None or year <= 0:
                continue
            cc = paper.get("citation_count", 0)
            if not isinstance(cc, (int, float)):
                cc = 0
            year_citations[year] += int(cc)
            year_counts[year] += 1

        if len(year_citations) < 2:
            return (0.0, 0.0)

        sorted_items = sorted(year_citations.items())
        x_raw = [float(y) for y, _ in sorted_items]
        y_vals = [float(c) for _, c in sorted_items]
        n = len(x_raw)

        # Normalize x to [0, 1] so slope is scale-invariant
        x_min, x_max = min(x_raw), max(x_raw)
        x_range = x_max - x_min if x_max != x_min else 1.0
        x_vals = [(x - x_min) / x_range for x in x_raw]

        mean_x = sum(x_vals) / n
        mean_y = sum(y_vals) / n

        num = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_vals, y_vals, strict=False))
        den = sum((x - mean_x) ** 2 for x in x_vals)

        if den == 0:
            return (0.0, 0.0)

        slope = num / den
        intercept = mean_y - slope * mean_x

        y_pred = [slope * x + intercept for x in x_vals]
        ss_res = sum((y - yp) ** 2 for y, yp in zip(y_vals, y_pred, strict=False))
        ss_tot = sum((y - mean_y) ** 2 for y in y_vals)

        r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        return (slope, r_squared)

    def _build_paradigm_timeline(
        self,
        papers: list[dict[str, Any]],
        query: str,
    ) -> list[dict[str, Any]]:
        year_events: dict[int, list[dict[str, str]]] = defaultdict(list)

        for paper in papers:
            year = paper.get("year")
            if not isinstance(year, int) or year is None or year <= 0:
                continue
            title = paper.get("title", "Untitled")
            authors = paper.get("authors", [])
            first_author = authors[0] if authors else "Unknown"
            cc = paper.get("citation_count", 0)
            is_seminal = cc >= self.seminal_threshold

            year_events[year].append({
                "title": title,
                "first_author": first_author,
                "citation_count": cc,
                "is_seminal": is_seminal,
            })

        timeline: list[dict[str, Any]] = []
        for year in sorted(year_events.keys()):
            events = year_events[year]
            events.sort(key=lambda e: e["citation_count"], reverse=True)
            descriptions: list[str] = []
            for e in events[:3]:
                suffix = " [SEMINAL]" if e["is_seminal"] else ""
                descriptions.append(
                    f"{e['first_author']} et al. '{e['title'][:80]}' ({e['citation_count']} citations){suffix}"
                )
            timeline.append({
                "year": year,
                "events": descriptions,
                "paper_count": len(events),
                "total_citations": sum(e["citation_count"] for e in events),
            })

        return timeline

    @staticmethod
    def _extract_id(paper: dict[str, Any]) -> str:
        candidates = [
            paper.get("paper_id"),
            paper.get("s2_id"),
            paper.get("doi"),
            paper.get("arxiv_id"),
        ]
        for c in candidates:
            if c and isinstance(c, str) and c.strip():
                return c.strip()
        return ""
