"""Novelty Validator — checks hypothesis novelty using semantic embeddings."""
from __future__ import annotations

import json
import logging
import os
from difflib import SequenceMatcher
from typing import Any

import numpy as np


logger = logging.getLogger("c44tcdi.discovery.novelty_validator")

_SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer

    _SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning("sentence-transformers not available; using fallback similarity")


def _get_embedding_model() -> Any:
    """Lazy-load the sentence-transformer model (22MB)."""
    from src.di.container import get_container
    container = get_container()
    if not container.has("embedding_model") and _SENTENCE_TRANSFORMERS_AVAILABLE:
        try:
            container.register("embedding_model", SentenceTransformer("all-MiniLM-L6-v2"))
        except Exception as e:
            logger.error("Failed to load embedding model: %s", e)
            container.register("embedding_model", None)
    return container.resolve("embedding_model") if container.has("embedding_model") else None


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def _compute_semantic_similarity(
    hypothesis: str, paper_text: str, model: Any
) -> float:
    """Compute semantic similarity using sentence-transformer embeddings."""
    if model is None:
        return _compute_fallback_similarity(hypothesis, paper_text)
    try:
        emb_hyp = model.encode(hypothesis, convert_to_numpy=True, show_progress_bar=False)
        emb_pap = model.encode(paper_text, convert_to_numpy=True, show_progress_bar=False)
        return _cosine_similarity(emb_hyp, emb_pap)
    except Exception as e:
        logger.debug("Semantic similarity failed: %s", e)
        return _compute_fallback_similarity(hypothesis, paper_text)


def _compute_fallback_similarity(a: str, b: str) -> float:
    """Fallback: blend SequenceMatcher ratio with Jaccard token overlap."""
    a_clean = a.lower()[:500]
    b_clean = b.lower()[:500]
    if not a_clean or not b_clean:
        return 0.0
    sm = SequenceMatcher(None, a_clean, b_clean)
    ratio = sm.ratio()
    tokens_a = set(a_clean.split())
    tokens_b = set(b_clean.split())
    if not tokens_a or not tokens_b:
        return ratio
    jaccard = len(tokens_a & tokens_b) / len(tokens_a | tokens_b)
    return 0.6 * ratio + 0.4 * jaccard


# Back-compat alias used by tests
_compute_similarity = _compute_fallback_similarity


def _derive_novelty_score(max_similarity: float) -> float:
    """Convert max similarity to a 0–1 novelty score (higher = more novel)."""
    return round(1.0 - max_similarity, 4)


def _extract_keywords(text: str, max_len: int = 200) -> str:
    """Extract the most meaningful portion of text for querying."""
    return text.strip()[:max_len]


def _citation_overlap(
    hypothesis_citations: list[str], paper_citations: list[str]
) -> dict[str, Any]:
    """Compute citation network overlap between hypothesis and paper."""
    hyp_set = set(c.lower().strip() for c in hypothesis_citations)
    pap_set = set(c.lower().strip() for c in paper_citations)
    overlap = hyp_set & pap_set
    union = hyp_set | pap_set
    jaccard = len(overlap) / len(union) if union else 0.0
    return {
        "overlap_count": len(overlap),
        "union_count": len(union),
        "jaccard": round(jaccard, 4),
        "shared_citations": sorted(overlap)[:10],
    }


class NoveltyValidator:
    """Validates hypothesis novelty using semantic embeddings and citation analysis."""

    def __init__(self, mailto: str | None = None, timeout: float = 30.0) -> None:
        self._mailto = mailto
        self._timeout = timeout
        self._model = _get_embedding_model()

    async def check(
        self, hypothesis: str, domain: str = "general"
    ) -> dict[str, Any]:
        """Check novelty of a hypothesis against existing literature.

        Returns:
            dict with keys:
                - novelty_score: float 0-1 (higher = more novel)
                - max_similarity: float 0-1 (highest overlap found)
                - most_similar_paper: dict | None
                - citation_overlap: dict
                - closest_papers: list of {title, similarity, doi, year, source}
                - papers_checked: int
                - status: 'checked' | 'unchecked'
        """
        try:
            from src.knowledge.crossref_client import CrossRefClient

            keywords = _extract_keywords(hypothesis)
            domain_keywords = (
                f"{domain} {keywords}" if domain and domain != "general" else keywords
            )

            closest_papers: list[dict[str, Any]] = []
            all_similarities: list[float] = []

            async with CrossRefClient(
                mailto=self._mailto, timeout=self._timeout
            ) as client:
                queries = [keywords[:200], domain_keywords[:200]]
                seen_titles: set[str] = set()

                for query in queries:
                    try:
                        results = await client.search(query, max_results=10)
                        for paper in results:
                            title = paper.get("title", "")
                            if not title or title in seen_titles:
                                continue
                            seen_titles.add(title)

                            abstract = paper.get("abstract", "")
                            paper_text = f"{title} {abstract}"[:1000]
                            similarity = _compute_semantic_similarity(
                                hypothesis, paper_text, self._model
                            )
                            all_similarities.append(similarity)

                            # Extract citation lists if available
                            hyp_citations = paper.get("hypothesis_citations", [])
                            paper_citations = paper.get("references", [])
                            cit_overlap = _citation_overlap(
                                hyp_citations, paper_citations
                            )

                            closest_papers.append({
                                "title": title[:200],
                                "similarity": round(similarity, 4),
                                "doi": paper.get("doi", ""),
                                "year": paper.get("year", 0),
                                "source": "crossref",
                                "citation_overlap": cit_overlap,
                            })
                    except (TimeoutError, TypeError) as e:
                        logger.warning(
                            "CrossRef search error for query '%s': %s",
                            query[:60],
                            e,
                        )
                        continue

            max_similarity = max(all_similarities) if all_similarities else 0.0
            novelty_score = _derive_novelty_score(max_similarity)
            closest_papers.sort(key=lambda p: p["similarity"], reverse=True)

            most_similar = closest_papers[0] if closest_papers else None
            aggregate_citation_overlap = (
                most_similar["citation_overlap"]
                if most_similar
                else {"overlap_count": 0, "union_count": 0, "jaccard": 0.0, "shared_citations": []}
            )

            return {
                "status": "checked",
                "novelty_score": novelty_score,
                "max_similarity": round(max_similarity, 4),
                "most_similar_paper": most_similar,
                "citation_overlap": aggregate_citation_overlap,
                "closest_papers": closest_papers[:5],
                "papers_checked": len(closest_papers),
            }

        except ImportError:
            logger.warning("CrossRefClient not available, falling back to raw httpx")
            return await self._fallback_check(hypothesis, domain)
        except (TimeoutError, IndexError, KeyError, TypeError) as e:
            logger.error("Novelty check error: %s", e)
            return {
                "status": "unchecked",
                "novelty_score": 0.5,
                "max_similarity": 0.0,
                "most_similar_paper": None,
                "citation_overlap": {
                    "overlap_count": 0,
                    "union_count": 0,
                    "jaccard": 0.0,
                    "shared_citations": [],
                },
                "closest_papers": [],
                "papers_checked": 0,
                "error": str(e)[:200],
            }

    async def check_semantic(
        self, hypothesis: str, domain: str
    ) -> dict[str, Any]:
        """Real semantic novelty check via LLM (kept for backward compatibility)."""
        or_key = get_key("openrouter") or os.getenv("OPENROUTER_API_KEY", "")
        if not or_key:
            return await self.check(hypothesis, domain)

        import httpx

        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {or_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek/deepseek-chat",
                    "temperature": 0.3,
                    "max_tokens": 500,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a scientific novelty validator. Rate the hypothesis novelty 0-1. "
                                "Check against known literature. Output JSON: "
                                "{novelty_score: float, reasoning: str, closest_known_work: str}."
                            ),
                        },
                        {
                            "role": "user",
                            "content": f"Hypothesis: {hypothesis[:1000]}. Domain: {domain}. Is this genuinely novel?",
                        },
                    ],
                },
            )
            try:
                result = json.loads(
                    r.json()["choices"][0]["message"]["content"]
                )
                return {
                    "semantic_novelty": result.get("novelty_score", 0.5),
                    "reasoning": result.get("reasoning", ""),
                    "closest_work": result.get("closest_known_work", ""),
                }
            except (
                AttributeError,
                ImportError,
                IndexError,
                KeyError,
                TypeError,
                httpx.HTTPError,
            ):
                return {"semantic_novelty": 0.5}

    async def _fallback_check(
        self, hypothesis: str, domain: str
    ) -> dict[str, Any]:
        """Fallback: use raw httpx to search CrossRef directly."""
        try:
            import httpx

            keywords = _extract_keywords(hypothesis)

            async with httpx.AsyncClient(timeout=self._timeout) as client:
                r = await client.get(
                    "https://api.crossref.org/works",
                    params={"query": keywords, "rows": 10},
                    headers={
                        "User-Agent": "c44tcdi (mailto:c44tcdi@example.com)"
                    },
                )
                if r.status_code != 200:
                    return {
                        "status": "unchecked",
                        "novelty_score": 0.5,
                        "max_similarity": 0.0,
                        "most_similar_paper": None,
                        "citation_overlap": {
                            "overlap_count": 0,
                            "union_count": 0,
                            "jaccard": 0.0,
                            "shared_citations": [],
                        },
                        "closest_papers": [],
                        "papers_checked": 0,
                        "reason": f"CrossRef returned {r.status_code}",
                    }

                items = r.json().get("message", {}).get("items", [])
                closest_papers: list[dict[str, Any]] = []
                similarities: list[float] = []

                for paper in items[:10]:
                    title = ""
                    title_list = paper.get("title", [])
                    if title_list:
                        title = (
                            title_list[0]
                            if isinstance(title_list, list)
                            else str(title_list)
                        )
                    if not title:
                        continue

                    paper_text = f"{title} {paper.get('abstract', '')}"[:1000]
                    similarity = _compute_semantic_similarity(
                        hypothesis, paper_text, self._model
                    )
                    similarities.append(similarity)
                    closest_papers.append({
                        "title": title[:200],
                        "similarity": round(similarity, 4),
                        "doi": paper.get("DOI", ""),
                        "year": 0,
                        "source": "crossref",
                        "citation_overlap": {
                            "overlap_count": 0,
                            "union_count": 0,
                            "jaccard": 0.0,
                            "shared_citations": [],
                        },
                    })

                max_similarity = max(similarities) if similarities else 0.0
                closest_papers.sort(key=lambda p: p["similarity"], reverse=True)
                most_similar = closest_papers[0] if closest_papers else None

                return {
                    "status": "checked",
                    "novelty_score": _derive_novelty_score(max_similarity),
                    "max_similarity": round(max_similarity, 4),
                    "most_similar_paper": most_similar,
                    "citation_overlap": most_similar["citation_overlap"]
                    if most_similar
                    else {
                        "overlap_count": 0,
                        "union_count": 0,
                        "jaccard": 0.0,
                        "shared_citations": [],
                    },
                    "closest_papers": closest_papers[:5],
                    "papers_checked": len(closest_papers),
                }
        except ImportError:
            return {
                "status": "unchecked",
                "novelty_score": 0.5,
                "max_similarity": 0.0,
                "most_similar_paper": None,
                "citation_overlap": {
                    "overlap_count": 0,
                    "union_count": 0,
                    "jaccard": 0.0,
                    "shared_citations": [],
                },
                "closest_papers": [],
                "papers_checked": 0,
                "reason": "httpx not installed",
            }
        except (TimeoutError, IndexError, KeyError, TypeError, ValueError, httpx.HTTPError, json.JSONDecodeError) as e:
            logger.error("Novelty fallback check error: %s", e)
            return {
                "status": "unchecked",
                "novelty_score": 0.5,
                "max_similarity": 0.0,
                "most_similar_paper": None,
                "citation_overlap": {
                    "overlap_count": 0,
                    "union_count": 0,
                    "jaccard": 0.0,
                    "shared_citations": [],
                },
                "closest_papers": [],
                "papers_checked": 0,
                "error": str(e)[:200],
            }

    async def close(self) -> None:
        pass

    async def __aenter__(self) -> NoveltyValidator:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
