from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

import httpx


logger = logging.getLogger(__name__)

NEW_PARADIGM_MARKERS: list[str] = [
    "active",
    "adaptive",
    "inhibitory",
    "reconsolidation",
    "motivated",
    "directed",
    "retrieval-induced",
    "suppression",
    "control",
    "mechanism",
    "process",
    "function",
    "regulation",
    "modulation",
    "plasticity",
    "synaptic",
    "molecular",
    "network",
    "circuit",
    "encoding",
    "consolidation",
    "executive",
    "prefrontal",
]

OLD_PARADIGM_MARKERS: list[str] = [
    "decay",
    "passive",
    "trace",
    "spontaneous",
    "loss",
    "degradation",
    "storage failure",
    "forgetting curve",
    "disintegration",
    "extinction",
    "erasure",
    "deterioration",
    "weakening",
]


class AlreadyShiftedDetector:
    """AlreadyShiftedDetector."""
    SEMINAL_AGE_THRESHOLD: int = 5
    CONSENSUS_THRESHOLD: float = 0.6
    REVIEW_THRESHOLD: int = 3
    CITATION_VELOCITY_THRESHOLD: float = 1.5

    def _adaptive_review_threshold(self, paper_count: int) -> int:
        return min(self.REVIEW_THRESHOLD, max(0, (paper_count - 5) // 5))

    async def check(
        self,
        hypothesis: str,
        papers: list[dict[str, Any]],
        citation_timeline: list[dict[str, Any]] | None = None,
        domain: str = "general",
    ) -> dict[str, Any]:
        """Check."""
        now_year = datetime.now(timezone.utc).year  # noqa: UP017
        keywords = self._extract_paradigm_keywords(hypothesis)
        keywords.get("domain", domain) if domain == "general" else domain

        seminal = self._find_seminal_papers(papers, now_year)
        consensus = self._compute_consensus(papers, keywords, now_year)
        timeline = self._build_timeline(papers, keywords, now_year, citation_timeline)
        citation_velocity = self._compute_citation_velocity(timeline)
        plateau_detected = self._detect_plateau(timeline)

        first_old = self._last_old_paradigm_year(papers, keywords, now_year)

        review_count = 0
        for t in timeline:
            review_count += t.get("reviews", 0)

        review_threshold = self._adaptive_review_threshold(len(papers))

        shift_year: int | None = None
        for t in timeline:
            if t["new_papers"] > 0 and t["old_papers"] == 0 and t["reviews"] > 0 and shift_year is None:
                shift_year = t["year"]
            elif t["new_papers"] > t["old_papers"] * 2 and t["reviews"] >= 1 and shift_year is None:
                shift_year = t["year"]

        oldest_seminal_year = min((s["year"] for s in seminal), default=now_year)
        seminal_age = now_year - oldest_seminal_year if seminal else 0

        confidence = 0.0
        if seminal:
            confidence += 0.20
        confidence += min(consensus, 0.30)
        confidence += min(citation_velocity / 5.0, 0.15)
        if review_threshold > 0:
            confidence += min(review_count / review_threshold, 1.0) * 0.15
        if plateau_detected:
            confidence += 0.10
        if first_old is not None and now_year - first_old >= 2:
            confidence += 0.10
        # Subtractive terms — prevents overconfidence from weak evidence
        if not seminal:
            confidence -= 0.10
        if consensus < 0.3:
            confidence -= 0.10
        if review_count == 0:
            confidence -= 0.05
        if citation_velocity < 0.5:
            confidence -= 0.05
        confidence = max(0.0, min(confidence, 1.0))

        already_shifted = (
            seminal_age >= self.SEMINAL_AGE_THRESHOLD
            and consensus >= self.CONSENSUS_THRESHOLD
            and review_count >= review_threshold
        )

        verdict = self._generate_verdict(
            seminal_age=seminal_age,
            consensus=consensus,
            review_count=review_count,
            review_threshold=review_threshold,
            citation_velocity=citation_velocity,
            plateau_detected=plateau_detected,
            first_old=first_old,
            now_year=now_year,
        )

        explanation_parts: list[str] = []
        if seminal:
            explanation_parts.append(
                f"Seminal paper from {oldest_seminal_year} ({seminal_age} years ago)"
            )
        else:
            explanation_parts.append("No seminal papers older than 5 years found")
        explanation_parts.append(f"Consensus: {consensus:.0%}")
        if review_count > 0:
            explanation_parts.append(f"{review_count} review papers")
        if plateau_detected:
            explanation_parts.append("Adoption has plateaued")
        if first_old is not None:
            explanation_parts.append(
                f"No old-paradigm papers since {first_old}"
            )

        return {
            "already_shifted": already_shifted,
            "confidence": round(confidence, 3),
            "shift_year": shift_year,
            "seminal_papers": seminal,
            "consensus_level": round(consensus, 3),
            "citation_velocity": round(citation_velocity, 3),
            "review_count": review_count,
            "first_old_paradigm_paper": first_old or 0,
            "timeline": timeline,
            "verdict": verdict,
            "explanation": " | ".join(explanation_parts),
        }

    def _find_seminal_papers(
        self, papers: list[dict[str, Any]], now_year: int
    ) -> list[dict[str, Any]]:
        cutoff = now_year - self.SEMINAL_AGE_THRESHOLD
        old = [p for p in papers if (p.get("year") or 9999) <= cutoff]
        old.sort(key=lambda p: -(p.get("citationCount") or 0))
        return [
            {"title": p.get("title", ""), "year": p.get("year", 0), "citations": p.get("citationCount", 0)}
            for p in old[:5]
        ]

    def _compute_consensus(
        self,
        papers: list[dict[str, Any]],
        keywords: dict[str, list[str]],
        now_year: int,
    ) -> float:
        recent_cutoff = now_year - 3
        recent = [p for p in papers if (p.get("year") or 0) >= recent_cutoff]
        if not recent:
            recent = papers

        new_kw = [k.lower() for k in keywords.get("new", [])]
        old_kw = [k.lower() for k in keywords.get("old", [])]

        new_count = 0
        old_count = 0

        for p in recent:
            text = f"{p.get('title', '')} {p.get('abstract', '')}".lower()
            if any(kw in text for kw in new_kw):
                new_count += 1
            elif any(kw in text for kw in old_kw):
                old_count += 1

        total = new_count + old_count
        return new_count / total if total > 0 else 0.0

    def _extract_paradigm_keywords(self, hypothesis: str) -> dict[str, Any]:
        new_kw: list[str] = []
        old_kw: list[str] = []

        shift_markers = [
            r"from\s+(.+?)\s+to\s+(.+)",
            r"shift\s+from\s+(.+?)\s+to\s+(.+)",
            r"transition\s+from\s+(.+?)\s+to\s+(.+)",
            r"refram(?:e|ing)\s+(.+?)\s+as\s+(.+)",
        ]

        for pattern in shift_markers:
            m = re.search(pattern, hypothesis, re.IGNORECASE)
            if m:
                old_phrase = m.group(1).strip(" ,;.")
                new_phrase = m.group(2).strip(" ,;.")
                old_kw = [
                    w.strip(" ,;.\"'")
                    for w in re.split(r"\s+(?:and|or|,)\s*|[\s]+", old_phrase)
                    if len(w.strip(" ,;.\"'")) > 2 and w.lower() not in {"the", "a", "an", "is", "was"}
                ]
                new_kw = [
                    w.strip(" ,;.\"'")
                    for w in re.split(r"\s+(?:and|or|,)\s*|[\s]+", new_phrase)
                    if len(w.strip(" ,;.\"'")) > 2 and w.lower() not in {"the", "a", "an", "is", "was"}
                ]
                break

        if ":" in hypothesis:
            before, after = hypothesis.split(":", 1)
            for phrase in [before, after]:
                words = [w.strip(" ,;.\"'") for w in phrase.split() if len(w.strip(" ,;.\"'")) > 2]
                for w in words:
                    wl = w.lower()
                    if any(m in wl for m in ["activ", "adaptiv", "inhibitor", "control", "mechanis"]):
                        if wl not in [k.lower() for k in new_kw]:
                            new_kw.append(w)
                    if any(m in wl for m in ["decay", "passiv", "trace", "loss", "spontan"]):
                        if wl not in [k.lower() for k in old_kw]:
                            old_kw.append(w)

        if not new_kw and not old_kw:
            return {"new": [], "old": [], "domain": "", "domain_keywords_missing": True}

        domain_words: list[str] = []
        for word in hypothesis.lower().replace(":", " ").replace(",", " ").split():
            clean = word.strip(" ,;.\"'")
            if len(clean) > 3 and clean not in {
                "from", "this", "that", "with", "have", "been", "into",
                "over", "more", "than", "some", "such", "these", "those",
                "about", "their", "would", "could", "shall", "should",
                "there", "which", "being", "reframing", "paradigm",
                "shift", "model", "framework", "view",
            }:
                domain_words.append(clean)

        return {
            "new": new_kw,
            "old": old_kw,
            "domain": " ".join(sorted(set(domain_words))),
        }

    def _build_timeline(
        self,
        papers: list[dict[str, Any]],
        keywords: dict[str, list[str]],
        now_year: int,
        citation_timeline: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        new_kw = [k.lower() for k in keywords.get("new", [])]
        old_kw = [k.lower() for k in keywords.get("old", [])]

        years_present: set[int] = {p.get("year", now_year) for p in papers if p.get("year")}
        if citation_timeline:
            years_present |= {c.get("year", now_year) for c in citation_timeline if c.get("year")}

        if not years_present:
            return []

        min_year = min(years_present)
        max_year = max(years_present)
        years = list(range(min_year, max_year + 1))

        timeline: list[dict[str, Any]] = []
        for year in years:
            year_papers = [p for p in papers if p.get("year") == year]
            new_count = 0
            old_count = 0
            reviews = 0

            for p in year_papers:
                text = f"{p.get('title', '')} {p.get('abstract', '')}".lower()
                if any(r in text for r in ["review", "annual review", "meta-analysis", "survey", "state of the art"]):
                    reviews += 1
                if any(kw in text for kw in new_kw):
                    new_count += 1
                elif any(kw in text for kw in old_kw):
                    old_count += 1

            total_citations = sum(p.get("citationCount", 0) for p in year_papers)
            if citation_timeline:
                year_citations = [c for c in citation_timeline if c.get("year") == year]
                total_citations += sum(c.get("count", 0) for c in year_citations)

            timeline.append({
                "year": year,
                "new_papers": new_count,
                "old_papers": old_count,
                "reviews": reviews,
                "total_citations": total_citations,
            })

        return timeline

    def _compute_citation_velocity(self, timeline: list[dict[str, Any]]) -> float:
        if len(timeline) < 2:
            return 0.0

        citations_per_year = [t["total_citations"] for t in timeline if t["total_citations"] > 0]
        if len(citations_per_year) < 2:
            return 0.0

        growth_rates: list[float] = []
        for i in range(1, len(citations_per_year)):
            if citations_per_year[i - 1] > 0:
                rate = citations_per_year[i] / citations_per_year[i - 1]
                growth_rates.append(rate)

        return sum(growth_rates) / len(growth_rates) if growth_rates else 0.0

    def _detect_plateau(self, timeline: list[dict[str, Any]]) -> bool:
        if len(timeline) < 4:
            return False

        adoption = [t["new_papers"] for t in timeline]

        early = adoption[: len(adoption) // 2]
        late = adoption[len(adoption) // 2 :]

        early_avg = sum(early) / len(early) if early else 0
        late_avg = sum(late) / len(late) if late else 0

        early_rates = [
            (early[i] - early[i - 1]) / max(early[i - 1], 1)
            for i in range(1, len(early))
        ]
        late_rates = [
            (late[i] - late[i - 1]) / max(late[i - 1], 1)
            for i in range(1, len(late))
        ]

        early_rate = sum(early_rates) / len(early_rates) if early_rates else 0
        late_rate = sum(late_rates) / len(late_rates) if late_rates else 0

        return late_rate < early_rate and late_rate >= 0 and late_avg > early_avg

    def _last_old_paradigm_year(
        self,
        papers: list[dict[str, Any]],
        keywords: dict[str, list[str]],
        now_year: int,
    ) -> int | None:
        old_kw = [k.lower() for k in (keywords.get("old") or OLD_PARADIGM_MARKERS[:6])]
        last = None
        for p in papers:
            text = f"{p.get('title', '')} {p.get('abstract', '')}".lower()
            if any(kw in text for kw in old_kw):
                year = p.get("year")
                if year and (last is None or year > last):
                    last = year
        return last

    def _generate_verdict(
        self,
        seminal_age: int,
        consensus: float,
        review_count: int,
        review_threshold: int,
        citation_velocity: float,
        plateau_detected: bool,
        first_old: int | None,
        now_year: int,
    ) -> str:
        already = (
            seminal_age >= self.SEMINAL_AGE_THRESHOLD
            and consensus >= self.CONSENSUS_THRESHOLD
            and review_count >= review_threshold
        )

        if already:
            return "ALREADY_SHIFTED"

        shifting = (
            citation_velocity > 1.0
            and consensus > 0.3
            and not already
        )
        if shifting:
            return "SHIFTING"

        not_shifted = (
            citation_velocity <= 1.0
            and consensus <= 0.3
        )
        if not_shifted:
            return "NOT_SHIFTED"

        return "UNCLEAR"

    async def _search_for_reviews(
        self, domain: str, keywords: list[str]
    ) -> list[dict[str, Any]]:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        query = f"{domain} {' '.join(keywords[:5])} review"
        params: dict[str, Any] = {
            "query": query,
            "limit": 50,
            "fields": "title,authors,year,abstract,citationCount,publicationVenue",
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                reviews = [
                    p
                    for p in data.get("data", [])
                    if any(
                        k in (p.get("title", "") + p.get("abstract", "")).lower()
                        for k in [
                            "review",
                            "annual review",
                            "meta-analysis",
                            "survey",
                            "state of the art",
                        ]
                    )
                ]
                return reviews
        except (TimeoutError, TypeError, httpx.HTTPError, json.JSONDecodeError):
            logger.debug("SemanticScholar review search failed, returning empty", exc_info=True)
            return []
