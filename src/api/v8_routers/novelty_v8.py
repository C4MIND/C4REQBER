from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/novelty", tags=["v8-novelty"])


class NoveltyCheckRequest(BaseModel):
    """NoveltyCheckRequest."""
    hypothesis: str
    domain: str = "general"
    keywords: list[str] = []
    existing_papers: list[dict[str, Any]] = []


class NoveltyPass(BaseModel):
    """NoveltyPass."""
    pass_name: str
    papers_checked: int
    closest_match: dict[str, Any] | None = None
    closest_similarity: float = 0.0
    overlap_detected: bool = False
    overlap_details: list[str] = []
    time_seconds: float = 0.0


class NoveltyCheckResponse(BaseModel):
    """NoveltyCheckResponse."""
    status: str
    overall_novelty_score: float
    passes: list[dict[str, Any]]
    closest_papers: list[dict[str, Any]]
    recommendation: str
    total_time_seconds: float
    errors: list[str]


class ThreePassNoveltyValidator:
    """3-pass novelty validation: broad → deep → context. REAL APIs only."""

    def __init__(self) -> None:
        self.client_timeout = 20.0
        self.min_similarity_threshold = 0.3
        self.pass_threshold = 0.5

    async def validate(self, hypothesis: str, domain: str,
                       keywords: list[str]) -> dict[str, Any]:
        """Validate."""
        errors: list[str] = []
        passes: list[dict[str, Any]] = []

        t1 = time.perf_counter()
        p1 = await self._pass1_broad_scan(hypothesis, keywords)
        p1["time_seconds"] = round(time.perf_counter() - t1, 3)
        passes.append({
            "pass_name": "broad_scan",
            "papers_checked": p1["papers_checked"],
            "overlap_detected": p1["overlap_detected"],
            "closest_similarity": p1["max_similarity"],
            "time_seconds": p1["time_seconds"],
        })

        candidates = p1.get("potential_overlaps", [])[:5]

        t2 = time.perf_counter()
        p2 = await self._pass2_deep_dive(hypothesis, candidates)
        p2["time_seconds"] = round(time.perf_counter() - t2, 3)
        passes.append({
            "pass_name": "deep_dive",
            "papers_checked": p2["papers_analyzed"],
            "overlap_detected": p2["overlap_detected"],
            "closest_similarity": p2.get("overall_overlap_score", 0.0),
            "time_seconds": p2["time_seconds"],
        })

        overlapping = p2.get("overlapping_claims", [])

        t3 = time.perf_counter()
        p3 = await self._pass3_citation_context(overlapping)
        p3["time_seconds"] = round(time.perf_counter() - t3, 3)
        passes.append({
            "pass_name": "citation_context",
            "papers_checked": p3["papers_analyzed"],
            "overlap_detected": p3["is_established_paradigm"],
            "closest_similarity": 0.0,
            "time_seconds": p3["time_seconds"],
        })

        score = self._compute_overall_score(passes)
        recommendation = self._generate_recommendation(passes, score)

        return {
            "status": "OVERLAP_DETECTED" if score < 0.8 else "PASS",
            "overall_novelty_score": score,
            "passes": passes,
            "closest_papers": candidates[:10],
            "recommendation": recommendation,
            "total_time_seconds": 0,
            "errors": errors,
        }

    async def _pass1_broad_scan(self, hypothesis: str, keywords: list[str]) -> dict[str, Any]:
        phrases = hypothesis.lower().split()
        query = " ".join(phrases[:20])
        if keywords:
            query += " " + " ".join(keywords[:10])

        async def search_s2() -> list[dict[str, Any]]:
            """Search s2."""
            url = "https://api.semanticscholar.org/graph/v1/paper/search"
            params: dict[str, Any] = {"query": query[:300], "limit": 50,
                      "fields": "title,abstract,year,authors,citationCount"}
            async with httpx.AsyncClient(timeout=self.client_timeout) as c:
                r = await c.get(url, params=params)
                if r.status_code == 200:
                    return r.json().get("data", [])
                return []

        async def search_openalex() -> list[dict[str, Any]]:
            """Search openalex."""
            url = "https://api.openalex.org/works"
            params: dict[str, Any] = {"search": query[:300], "per_page": 50, "sort": "cited_by_count:desc"}
            async with httpx.AsyncClient(timeout=self.client_timeout) as c:
                r = await c.get(url, params=params)
                if r.status_code == 200:
                    results = r.json().get("results", [])
                    return [{"title": w.get("title", ""),
                             "year": w.get("publication_year"),
                             "doi": w.get("doi", ""),
                             "cited_by": w.get("cited_by_count", 0)}
                            for w in results]
                return []

        s2_results, oa_results = await asyncio.gather(search_s2(), search_openalex())

        all_papers = s2_results + oa_results
        overlaps: list[dict[str, Any]] = []

        for p in all_papers:
            title = (p.get("title") or "").lower()
            abstract = (p.get("abstract") or "").lower()
            text = title + " " + abstract

            hypo_words = set(hypothesis.lower().split()[:30])
            text_words = set(text.split())
            overlap = len(hypo_words & text_words) / max(len(hypo_words), 1)

            if overlap > self.min_similarity_threshold:
                overlaps.append({
                    "title": p.get("title", ""),
                    "year": p.get("year", ""),
                    "similarity": round(overlap, 3),
                    "source": "s2" if "paperId" in p else "openalex",
                    "citation_count": p.get("citationCount") or p.get("cited_by", 0),
                })

        overlaps.sort(key=lambda x: x["similarity"], reverse=True)

        return {
            "papers_checked": len(all_papers),
            "potential_overlaps": overlaps[:10],
            "max_similarity": overlaps[0]["similarity"] if overlaps else 0,
            "overlap_detected": bool(overlaps),
            "time_seconds": 0,
        }

    async def _pass2_deep_dive(self, hypothesis: str, candidate_papers: list[dict[str, Any]]) -> dict[str, Any]:
        overlapping_claims: list[dict[str, Any]] = []
        analyzed = 0
        claims_compared = 0

        paper_ids: list[str] = []
        for cp in candidate_papers:
            pid = cp.get("paperId")
            if pid:
                paper_ids.append(pid)

        sem_abstracts: dict[str, str] = {}

        async def fetch_s2_abstract(pid: str) -> tuple[str, str]:
            """Fetch s2 abstract."""
            url = f"https://api.semanticscholar.org/graph/v1/paper/{pid}"
            params = {"fields": "title,abstract"}
            async with httpx.AsyncClient(timeout=self.client_timeout) as c:
                r = await c.get(url, params=params)
                if r.status_code == 200:
                    data = r.json()
                    abs_text = data.get("abstract", "") or ""
                    return pid, abs_text
            return pid, ""

        if paper_ids:
            fetched = await asyncio.gather(*[fetch_s2_abstract(pid) for pid in paper_ids[:5]])
            sem_abstracts = dict(fetched)

        for cp in candidate_papers:
            analyzed += 1
            title = cp.get("title", "")
            abstract = sem_abstracts.get(cp.get("paperId", ""), "")
            text = f"{title}. {abstract}"

            sentences = [s.strip() for s in text.replace("\n", " ").split(".") if len(s.strip()) > 20]
            hypo_sentences = [s.strip() for s in hypothesis.replace("\n", " ").split(".") if len(s.strip()) > 10]

            for hs in hypo_sentences[:5]:
                for sent in sentences[:10]:
                    claims_compared += 1
                    hs_words = set(hs.lower().split())
                    sent_words = set(sent.lower().split())
                    if not hs_words:
                        continue
                    overlap = len(hs_words & sent_words) / len(hs_words)
                    if overlap > self.pass_threshold:
                        overlapping_claims.append({
                            "paper": title[:100],
                            "claim": sent[:200],
                            "overlap": round(overlap, 3),
                        })

        overall = sum(c["overlap"] for c in overlapping_claims) / max(len(overlapping_claims), 1) if overlapping_claims else 0.0

        return {
            "papers_analyzed": analyzed,
            "claims_compared": claims_compared,
            "overlapping_claims": overlapping_claims[:10],
            "overall_overlap_score": round(overall, 3),
            "overlap_detected": len(overlapping_claims) > 0,
            "time_seconds": 0,
        }

    async def _pass3_citation_context(self, overlapping_claims: list[dict[str, Any]]) -> dict[str, Any]:
        if not overlapping_claims:
            return {
                "papers_analyzed": 0,
                "citations_found": 0,
                "consensus": {"supports": 0, "refutes": 0, "extends": 0, "replicates": 0},
                "dominant_sentiment": "unclear",
                "is_established_paradigm": False,
                "time_seconds": 0,
            }

        paper_titles = list({c["paper"] for c in overlapping_claims[:3]})
        citations_found = 0
        consensus = {"supports": 0, "refutes": 0, "extends": 0, "replicates": 0}

        async def search_citations(title: str) -> list[dict[str, Any]]:
            """Search citations."""
            nonlocal citations_found
            url = "https://api.semanticscholar.org/graph/v1/paper/search"
            params: dict[str, Any] = {"query": title[:200], "limit": 5,
                      "fields": "title,citations.title,citations.abstract"}
            async with httpx.AsyncClient(timeout=self.client_timeout) as c:
                r = await c.get(url, params=params)
                if r.status_code == 200:
                    data = r.json().get("data", [])
                    if data:
                        citations = data[0].get("citations", [])
                        return citations
                return []

        sentiment_keywords = {
            "supports": ["support", "confirm", "validate", "agree", "consistent", "demonstrat", "show"],
            "refutes": ["refute", "contradict", "fail", "challenge", "disagree", "inconsistent",
                        "cannot", "does not", "no evidence"],
            "extends": ["extend", "build", "further", "advance", "generalize", "beyond",
                        "improve", "develop"],
            "replicates": ["replicat", "reproduc", "repeat", "same result", "confirm findings"],
        }

        for title in paper_titles:
            citing_papers = await search_citations(title)
            for cp in citing_papers:
                citations_found += 1
                text = (cp.get("title", "") + " " + (cp.get("abstract", "") or "")).lower()

                best_sentiment = "unclear"
                best_count = 0
                for sentiment, keywords_list in sentiment_keywords.items():
                    count = sum(1 for kw in keywords_list if kw in text)
                    if count > best_count:
                        best_count = count
                        best_sentiment = sentiment

                if best_sentiment in consensus:
                    consensus[best_sentiment] += 1

        total = sum(consensus.values())
        if total == 0:
            dominant = "unclear"
        elif consensus["supports"] + consensus["replicates"] > consensus["refutes"] + consensus["extends"]:
            dominant = "accepted"
        elif consensus["refutes"] > consensus["supports"]:
            dominant = "contested"
        else:
            dominant = "unclear"

        paradigm = (consensus["supports"] + consensus["replicates"]) >= total * 0.6 if total > 0 else False

        return {
            "papers_analyzed": len(paper_titles),
            "citations_found": citations_found,
            "consensus": consensus,
            "dominant_sentiment": dominant,
            "is_established_paradigm": paradigm,
            "time_seconds": 0,
        }

    def _compute_overall_score(self, passes: list[dict[str, Any]]) -> float:
        p1_score = 1.0 - min(passes[0].get("closest_similarity", 0) * 1.5, 1.0) if len(passes) > 0 else 1.0
        p2_score = 1.0 - min(passes[1].get("closest_similarity", 0) * 2.0, 1.0) if len(passes) > 1 else 1.0
        p3_penalty = 0.25 if len(passes) > 2 and passes[2].get("overlap_detected", False) else 0.0

        raw = (p1_score * 0.3 + p2_score * 0.5) - p3_penalty
        return round(max(0.0, min(1.0, raw)), 4)

    def _generate_recommendation(self, passes: list[dict[str, Any]], score: float) -> str:
        if score >= 0.9:
            return "STRONG NOVELTY — hypothesis appears genuinely novel. Proceed with discovery pipeline."
        elif score >= 0.7:
            return "MODERATE NOVELTY — some overlaps detected but hypothesis has unique elements. Consider refining claims to differentiate."
        elif score >= 0.4:
            return "LOW NOVELTY — significant overlap with existing literature. Reformulate hypothesis to emphasize unique contributions."
        else:
            return "INSUFFICIENT NOVELTY — hypothesis substantially overlaps with established work. Significant reformulation required."


@router.post("/check")
async def check_novelty(request: NoveltyCheckRequest) -> dict[str, Any]:
    """
    3-pass novelty validation.

    Pass 1: Broad scan across SemanticScholar + OpenAlex
    Pass 2: Deep analysis of 5 closest papers — claim extraction + comparison
    Pass 3: Citation context — is the overlapping claim established or contested?

    Returns NoveltyCheckResponse with detailed report.
    """
    t0 = time.perf_counter()
    errors: list[str] = []
    validator = ThreePassNoveltyValidator()

    try:
        result = await validator.validate(
            hypothesis=request.hypothesis,
            domain=request.domain,
            keywords=request.keywords,
        )
        elapsed = time.perf_counter() - t0
        result["total_time_seconds"] = round(elapsed, 3)
        result["status"] = "OVERLAP_DETECTED" if result.get("overall_novelty_score", 1.0) < 0.8 else "PASS"
        return result
    except (ImportError, AttributeError, RuntimeError) as e:
        logger.warning("novelty validator failed: %s", e)
        errors.append(str(e))
        return {
            "status": "ERROR",
            "overall_novelty_score": 0.0,
            "passes": [],
            "recommendation": f"Validation failed: {e}",
            "total_time_seconds": round(time.perf_counter() - t0, 3),
            "errors": errors,
        }


@router.get("/quick")
async def quick_novelty_check(hypothesis: str, domain: str = "general") -> dict[str, Any]:
    """
    Fast novelty check — just Pass 1 broad scan across Semantic Scholar + OpenAlex.
    Returns within 5-10 seconds. Shows if ANY paper overlaps with the hypothesis.

    Query: GET /api/v8/novelty/quick?hypothesis=<text>&domain=general
    """
    t0 = time.perf_counter()
    validator = ThreePassNoveltyValidator()
    try:
        p1 = await validator._pass1_broad_scan(hypothesis, [h.strip() for h in hypothesis.split()[:10]])
        elapsed = round(time.perf_counter() - t0, 3)

        overlaps = p1.get("potential_overlaps", [])
        max_sim = p1.get("max_similarity", 0)

        return {
            "hypothesis": hypothesis[:200],
            "domain": domain,
            "papers_checked": p1.get("papers_checked", 0),
            "overlaps_found": len(overlaps),
            "max_similarity": round(max_sim, 3),
            "likely_novel": max_sim < 0.3,
            "novelty_score": round(1.0 - max_sim, 3) if max_sim < 1.0 else 0.0,
            "top_overlaps": overlaps[:5],
            "time_seconds": elapsed,
            "recommendation": (
                "FRESH — pursue this idea" if max_sim < 0.1 else
                "LIKELY NOVEL — verify with deep search" if max_sim < 0.3 else
                "POTENTIAL OVERLAP — need deeper check" if max_sim < 0.5 else
                "OVERLAP DETECTED — similar ideas exist" if max_sim < 0.8 else
                "NOT NOVEL — this has been published"
            ),
        }
    except (ImportError, AttributeError, RuntimeError) as e:
        logger.warning("novelty check failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Novelty check failed: {e}") from e

@router.post("/quick")
async def quick_novelty_check_post(request: NoveltyCheckRequest) -> dict[str, Any]:
    """
    Same as GET /quick but POST with JSON body.
    """
    t0 = time.perf_counter()
    validator = ThreePassNoveltyValidator()
    try:
        p1 = await validator._pass1_broad_scan(
            request.hypothesis,
            request.keywords or [w for w in request.hypothesis.split()[:10]],
        )
        elapsed = round(time.perf_counter() - t0, 3)

        overlaps = p1.get("potential_overlaps", [])
        max_sim = p1.get("max_similarity", 0)

        return {
            "hypothesis": request.hypothesis[:200],
            "domain": request.domain,
            "papers_checked": p1.get("papers_checked", 0),
            "overlaps_found": len(overlaps),
            "max_similarity": round(max_sim, 3),
            "likely_novel": max_sim < 0.3,
            "novelty_score": round(1.0 - max_sim, 3) if max_sim < 1.0 else 0.0,
            "top_overlaps": overlaps[:5],
            "time_seconds": elapsed,
            "recommendation": (
                "FRESH — pursue this idea" if max_sim < 0.1 else
                "LIKELY NOVEL — verify with deep search" if max_sim < 0.3 else
                "POTENTIAL OVERLAP — need deeper check" if max_sim < 0.5 else
                "OVERLAP DETECTED — similar ideas exist" if max_sim < 0.8 else
                "NOT NOVEL — this has been published"
            ),
        }
    except (ImportError, AttributeError, RuntimeError) as e:
        logger.warning("novelty check failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Novelty check failed: {e}") from e

@router.get("/already-published")
async def check_already_published(hypothesis: str, domain: str = "general") -> dict[str, Any]:
    """
    Checks if a hypothesis has already been published in the literature.
    More direct than the 3-pass — just binary "is this already known?"
    """
    validator = ThreePassNoveltyValidator()
    try:
        p1 = await validator._pass1_broad_scan(hypothesis, [])
        overlaps = p1.get("potential_overlaps", [])
        if overlaps:
            return {
                "already_published": True,
                "best_match": overlaps[0],
                "total_overlaps": len(overlaps),
                "max_similarity": p1.get("max_similarity", 0),
            }
        return {"already_published": False, "total_overlaps": 0, "max_similarity": 0}
    except (ImportError, AttributeError, RuntimeError) as e:
        logger.warning("already-published check failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


__all__ = ["ThreePassNoveltyValidator", "router"]
