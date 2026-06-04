# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""Live Intelligence Feed — global news + scientific publications + anomaly detection.

Sources:
- Reddit (r/MachineLearning, r/science, r/LocalLLaMA)
- HackerNews (top stories)
- NewsAPI.org (80K worldwide news sources — requires NEWSAPI_KEY)
- arXiv API (latest papers in cs.AI, stat.ML, physics, q-bio)
- Semantic Scholar (trending papers, citation bursts)

Caching: 1-hour TTL, disk cache at ~/.c4reqber/feed_cache.json
Offline mode: serves cached data, no network calls
Force refresh: Ctrl+R in TUI or feed.force_refresh()
"""
from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from collections import Counter, deque
from dataclasses import dataclass, field
from pathlib import Path

import httpx


logger = logging.getLogger(__name__)

FEED_CACHE_PATH = Path.home() / ".c4reqber" / "feed_cache.json"
FEED_TTL = 3600  # 1 hour
MAX_FEED_ITEMS = 50
MAX_CACHE_AGE = 24 * 3600  # Show cached data up to 24h in offline mode


@dataclass
class Problem:
    """Problem."""
    id: str
    title: str
    source: str  # "reddit", "hackernews", "x", "arxiv"
    url: str
    severity: float  # 0.0-1.0 based on upvotes/reposts
    discovered_at: float = field(default_factory=time.time)

    @property
    def age_minutes(self) -> float:
        return (time.time() - self.discovered_at) / 60


@dataclass
class Hypothesis:
    """Hypothesis."""
    id: str
    title: str
    source_problems: list[str]  # problem IDs this hypothesis addresses
    confidence: float  # 0.0-1.0
    domain: str
    generated_at: float = field(default_factory=time.time)


class LiveFeed:
    """Background collector + problem detector + hypothesis generator."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._problems: deque[Problem] = deque(maxlen=MAX_FEED_ITEMS)
        self._hypotheses: deque[Hypothesis] = deque(maxlen=MAX_FEED_ITEMS)
        self._last_collect = 0.0
        self._running = False
        self._thread: threading.Thread | None = None
        self._offline = not self._check_network()
        if self._offline:
            self._load_cache()
            logger.info("LiveFeed: offline mode — serving cached data")

    def _check_network(self) -> bool:
        try:
            with httpx.Client(timeout=3.0) as client:
                client.get("https://www.reddit.com/r/MachineLearning/new.json?limit=1")
                return True
        except Exception:
            return False

    def _load_cache(self) -> None:
        try:
            if FEED_CACHE_PATH.exists():
                data = json.loads(FEED_CACHE_PATH.read_text())
                for p in data.get("problems", []):
                    self._problems.append(Problem(**p))
                for h in data.get("hypotheses", []):
                    self._hypotheses.append(Hypothesis(**h))
                logger.info("Loaded %d problems + %d hypotheses from cache", len(self._problems), len(self._hypotheses))
        except Exception:
            logger.debug("Feed source failed", exc_info=True)

            pass

    def _save_cache(self) -> None:
        try:
            FEED_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with self._lock:
                data = {
                    "problems": [{"id": p.id, "title": p.title, "source": p.source, "url": p.url, "severity": p.severity, "discovered_at": p.discovered_at} for p in list(self._problems)[:30]],
                    "hypotheses": [{"id": h.id, "title": h.title, "source_problems": h.source_problems, "confidence": h.confidence, "domain": h.domain, "generated_at": h.generated_at} for h in list(self._hypotheses)[:30]],
                    "updated_at": time.time(),
                }
            FEED_CACHE_PATH.write_text(json.dumps(data, indent=2))
        except Exception:
            logger.debug("Feed source failed", exc_info=True)

            pass

    def force_refresh(self) -> None:
        """Immediate refresh of all sources."""
        logger.info("LiveFeed: force refresh")
        self._collect_all()
        self._save_cache()

    def start(self) -> None:
        """Start."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._collect_loop, daemon=True)
        self._thread.start()
        logger.info("LiveFeed started")

    def stop(self) -> None:
        self._running = False

    @property
    def problems(self) -> list[Problem]:
        with self._lock:
            return list(self._problems)

    @property
    def hypotheses(self) -> list[Hypothesis]:
        with self._lock:
            return list(self._hypotheses)

    def _collect_loop(self) -> None:
        while self._running:
            try:
                self._collect_all()
                self._save_cache()
            except Exception as e:
                logger.debug("Feed collection error: %s", e)
            time.sleep(300)  # Every 5 minutes

    def _collect_all(self) -> None:
        if self._offline:
            return
        self._collect_reddit()
        self._collect_hackernews()
        self._collect_newsapi()
        self._collect_arxiv()
        self._collect_semantic_scholar()
        self._detect_anomalies()
        self._generate_hypotheses()

    def _collect_reddit(self) -> None:
        subs = ["MachineLearning", "science", "programming", "artificial", "LocalLLaMA"]
        for sub in subs:
            try:
                with httpx.Client(timeout=10.0) as client:
                    r = client.get(
                        f"https://www.reddit.com/r/{sub}/new.json?limit=10",
                        headers={"User-Agent": "c4reqber/5.3.7"},
                    )
                    if r.status_code != 200:
                        continue
                    posts = r.json().get("data", {}).get("children", [])
                    for p in posts:
                        data = p["data"]
                        title = data.get("title", "")
                        score = data.get("score", 0)
                        if score < 5 or self._is_tutorial(title):
                            continue
                        self._add_problem(
                            title=title,
                            source=f"reddit/r/{sub}",
                            url=f"https://reddit.com{data.get('permalink', '')}",
                            severity=min(1.0, score / 100),
                        )
            except Exception:
                logger.debug("Feed source failed", exc_info=True)

                pass

    def _collect_hackernews(self) -> None:
        try:
            with httpx.Client(timeout=10.0) as client:
                r = client.get(
                    "https://hacker-news.firebaseio.com/v0/topstories.json",
                )
                if r.status_code != 200:
                    return
                ids = r.json()[:10]
                for hid in ids:
                    item_r = client.get(
                        f"https://hacker-news.firebaseio.com/v0/item/{hid}.json",
                    )
                    if item_r.status_code != 200:
                        continue
                    item = item_r.json()
                    title = item.get("title", "")
                    score = item.get("score", 0)
                    if score < 10 or self._is_show_hn(title):
                        continue
                    self._add_problem(
                        title=title,
                        source="hackernews",
                        url=f"https://news.ycombinator.com/item?id={hid}",
                        severity=min(1.0, score / 200),
                    )
        except Exception:
            logger.debug("Feed source failed", exc_info=True)

            pass

    def _add_problem(self, title: str, source: str, url: str, severity: float) -> None:
        pid = f"{source}:{hash(title) % 1000000:06d}"
        with self._lock:
            if any(p.id == pid for p in self._problems):
                return
            self._problems.appendleft(Problem(id=pid, title=title, source=source, url=url, severity=severity))

    def _detect_anomalies(self) -> None:
        """Detect anomalies: repeated keywords, sentiment shifts, topic bursts."""
        with self._lock:
            recent = list(self._problems)[:20]
        if len(recent) < 5:
            return

        words: Counter[str] = Counter()
        for p in recent:
            for w in p.title.lower().split():
                if len(w) > 3 and w not in {"that", "this", "with", "from", "your", "what", "when", "there", "which", "have", "they", "about", "will"}:
                    words[w] += 1

        for word, count in words.most_common(10):
            if count >= 3:
                pid = f"anomaly:{hash(word) % 1000000:06d}"
                self._add_problem(
                    title=f"Trending: '{word}' ({count} mentions in {len(recent)} posts)",
                    source="anomaly_detector",
                    url="",
                    severity=min(1.0, count / 10),
                )

    def _generate_hypotheses(self) -> None:
        with self._lock:
            recent = list(self._problems)[:10]
        if not recent:
            return

        clusters: dict[str, list[str]] = {}
        for p in recent:
            words = set(w for w in p.title.lower().split() if len(w) > 5)
            for w in words:
                clusters.setdefault(w, []).append(p.id)

        for keyword, problem_ids in clusters.items():
            if len(problem_ids) < 2:
                continue
            self._add_hypothesis(
                title=f"Investigate the role of {keyword} in {' and '.join(p.title[:40] for p in recent[:2])}",
                source_problems=problem_ids,
                confidence=min(1.0, len(problem_ids) * 0.2),
                domain=keyword,
            )

    def _add_hypothesis(self, title: str, source_problems: list[str], confidence: float, domain: str) -> None:
        hid = f"hyp:{hash(title) % 1000000:06d}"
        with self._lock:
            if any(h.id == hid for h in self._hypotheses):
                return
            self._hypotheses.appendleft(Hypothesis(
                id=hid, title=title, source_problems=source_problems,
                confidence=confidence, domain=domain,
            ))

    @staticmethod
    def _is_tutorial(title: str) -> bool:
        lower = title.lower()
        return any(w in lower for w in {"tutorial", "how to", "guide", "introduction to", "101", "course"})

    @staticmethod
    def _is_show_hn(title: str) -> bool:
        return title.lower().startswith("show hn")

    def _collect_newsapi(self) -> None:
        """Collect from NewsAPI.org — 80K worldwide sources."""
        news_key = os.environ.get("NEWSAPI_KEY", "")
        if not news_key:
            return
        try:
            with httpx.Client(timeout=10.0) as client:
                r = client.get(
                    "https://newsapi.org/v2/top-headlines",
                    params={"apiKey": news_key, "language": "en", "pageSize": 20, "category": "science"},
                )
                if r.status_code != 200:
                    return
                articles = r.json().get("articles", [])
                for a in articles:
                    title = a.get("title", "")
                    desc = a.get("description", "") or ""
                    if not title or self._is_tutorial(title):
                        continue
                    self._add_problem(
                        title=f"{title} — {desc[:60]}" if desc else title,
                        source=f"news/{a.get('source', {}).get('name', 'unknown')}",
                        url=a.get("url", ""),
                        severity=0.6,
                    )
        except Exception:
            logger.debug("Feed source failed", exc_info=True)

            pass

    def _collect_arxiv(self) -> None:
        """Collect latest papers from arXiv (cs.AI, stat.ML, physics, q-bio)."""
        categories = ["cs.AI", "stat.ML", "physics.soc-ph", "q-bio.NC"]
        for cat in categories:
            try:
                with httpx.Client(timeout=10.0) as client:
                    r = client.get(
                        f"http://export.arxiv.org/api/query?search_query=cat:{cat}&sortBy=submittedDate&sortOrder=descending&max_results=5",
                    )
                    if r.status_code != 200:
                        continue
                    # Parse XML titles
                    titles = re.findall(r"<title>(.*?)</title>", r.text)
                    authors = re.findall(r"<name>(.*?)</name>", r.text)
                    for i, title in enumerate(titles[1:]):  # Skip first (query title)
                        author = authors[i][:40] if i < len(authors) else ""
                        self._add_problem(
                            title=f"[arXiv:{cat}] {title.strip()} ({author})",
                            source="arxiv",
                            url=f"https://arxiv.org/search/?query={title.strip()[:50].replace(' ', '+')}",
                            severity=0.7,
                        )
            except Exception:
                logger.debug("Feed source failed", exc_info=True)

                pass

    def _collect_semantic_scholar(self) -> None:
        """Collect trending papers from Semantic Scholar."""
        ss_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "")
        if not ss_key:
            return
        try:
            with httpx.Client(timeout=10.0) as client:
                r = client.get(
                    "https://api.semanticscholar.org/graph/v1/paper/search",
                    params={"query": "novel method framework model", "limit": 5, "fieldsOfStudy": "Computer Science,Physics,Biology"},
                    headers={"x-api-key": ss_key},
                )
                if r.status_code != 200:
                    return
                papers = r.json().get("data", [])
                for p in papers:
                    title = p.get("title", "")
                    citations = p.get("citationCount", 0)
                    if not title:
                        continue
                    source_problems = [f"semantic_scholar:{p.get('paperId', '')}"]
                    self._add_hypothesis(
                        title=f"Explore: {title} (cited {citations}×)",
                        source_problems=source_problems,
                        confidence=min(1.0, citations / 100),
                        domain="semantic_scholar",
                    )
        except Exception:
            logger.debug("Feed source failed", exc_info=True)

            pass


# Singleton
_feed: LiveFeed | None = None


def get_live_feed() -> LiveFeed:
    """Get live feed."""
    global _feed
    if _feed is None:
        _feed = LiveFeed()
        _feed.start()
    return _feed
