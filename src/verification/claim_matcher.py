"""Claim-to-Source Verification — extract claims and match against retrieved papers."""

from __future__ import annotations

import logging
import re
import threading
from dataclasses import dataclass, field
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    dot = float(np.dot(a, b))
    na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
    return dot / (na * nb) if na and nb else 0.0


@dataclass
class ClaimMatch:
    """Result of matching a single claim against sources."""

    claim: str
    support_score: float  # 0-1
    best_source_title: str
    best_source_similarity: float
    matched: bool  # support_score >= threshold
    excerpts: list[str] = field(default_factory=list)


@dataclass
class ClaimVerificationResult:
    """Full verification result for a piece of text."""

    claims: list[ClaimMatch]
    overall_coverage: float  # % of claims with support
    unsupported_claims: list[str]
    pass_threshold: float
    passed: bool  # overall_coverage >= pass_threshold


class ClaimMatcher:
    """Extract atomic claims from text and verify against paper sources.

    Uses a module-level singleton for the embedding model to avoid
    reloading ~80MB on every call.
    """

    DEFAULT_SUPPORT_THRESHOLD = 0.35
    DEFAULT_PASS_THRESHOLD = 0.50
    _GLOBAL_MODEL: Any = None
    _GLOBAL_MODEL_LOCK: Any = None

    def __init__(
        self,
        support_threshold: float = DEFAULT_SUPPORT_THRESHOLD,
        pass_threshold: float = DEFAULT_PASS_THRESHOLD,
    ) -> None:
        self.support_threshold = support_threshold
        self.pass_threshold = pass_threshold
        self._embedding_model: Any = None

    @classmethod
    def _get_global_model(cls) -> Any:
        if cls._GLOBAL_MODEL_LOCK is None:
            import threading
            cls._GLOBAL_MODEL_LOCK = threading.Lock()
        model = cls._GLOBAL_MODEL
        if model is not None:
            return model
        with cls._GLOBAL_MODEL_LOCK:
            # Double-checked locking
            model = cls._GLOBAL_MODEL
            if model is not None:
                return model
            try:
                from sentence_transformers import SentenceTransformer

                cls._GLOBAL_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("ClaimMatcher: embedding model loaded (singleton)")
            except Exception as e:
                logger.warning("ClaimMatcher: sentence-transformers unavailable: %s", e)
                cls._GLOBAL_MODEL = None
        return cls._GLOBAL_MODEL

    def _ensure_model(self) -> Any:
        if self._embedding_model is not None:
            return self._embedding_model
        self._embedding_model = self._get_global_model()
        return self._embedding_model

    def _embed(self, texts: list[str]) -> np.ndarray | None:
        model = self._ensure_model()
        if model is None:
            return None
        try:
            return model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        except Exception as e:
            logger.warning("ClaimMatcher: embedding failed: %s", e)
            return None

    def extract_claims(self, text: str) -> list[str]:
        """Extract atomic factual claims from text.

        Uses a lightweight heuristic + optional LLM fallback.
        """
        # Heuristic: sentences containing numbers, percentages, causal language
        # Improved sentence splitting that avoids abbreviations and decimals
        abbrev_re = re.compile(r'\b(?:e\.g|i\.e|etc|Dr|Mr|Mrs|Ms|Jr|Sr|vs|vol|no|fig|al)\b', re.IGNORECASE)
        decimal_re = re.compile(r'\d\.\d')
        # Temporarily protect abbreviations and decimals
        protected: list[str] = []
        def _protect(m: re.Match) -> str:
            protected.append(m.group(0))
            return f"§PROT{len(protected)-1}§"
        temp = abbrev_re.sub(_protect, text)
        temp = decimal_re.sub(_protect, temp)
        sentences = [s.strip() for s in re.split(r'[.!?]\s+', temp) if len(s.strip()) > 20]
        # Restore protected strings
        restored = []
        for s in sentences:
            for i, p in enumerate(protected):
                s = s.replace(f"§PROT{i}§", p)
            restored.append(s)
        sentences = restored
        claims = []
        for s in sentences:
            # Filter for factual claims (contain numbers, measurements, or causal verbs)
            if re.search(r'\d+(?:\.\d+)?(?:\s*%|\s*(?:MPa|nm|μm|°C|K|fold|x|times|orders))', s):
                claims.append(s)
            elif any(kw in s.lower() for kw in ("increases", "decreases", "reduces", "enhances", "improves", "causes", "leads to", "results in", "significantly", "demonstrated", "showed")):
                claims.append(s)
        # If heuristic finds too few, take all substantive sentences
        if len(claims) < 3:
            claims = sentences[:10]
        return claims[:15]

    def verify(
        self,
        text: str,
        sources: list[dict[str, Any]],
    ) -> ClaimVerificationResult:
        """Verify claims in text against paper sources.

        Args:
            text: Text to verify (solution, hypothesis, dissertation).
            sources: Retrieved paper sources with 'title' and 'abstract' fields.

        Returns:
            ClaimVerificationResult with per-claim scores and overall coverage.
        """
        claims = self.extract_claims(text)
        if not claims or not sources:
            return ClaimVerificationResult(
                claims=[],
                overall_coverage=0.0,
                unsupported_claims=[],
                pass_threshold=self.pass_threshold,
                passed=False,
            )

        # Prepare source texts
        source_texts = []
        valid_sources = []
        for s in sources:
            title = s.get("title", "")
            abstract = s.get("abstract", s.get("snippet", ""))
            if title or abstract:
                source_texts.append(f"{title}. {abstract}")
                valid_sources.append(s)

        if not source_texts:
            return ClaimVerificationResult(
                claims=[ClaimMatch(c, 0.0, "", 0.0, False) for c in claims],
                overall_coverage=0.0,
                unsupported_claims=claims,
                pass_threshold=self.pass_threshold,
                passed=False,
            )

        # Embed claims and sources
        claim_vecs = self._embed(claims)
        source_vecs = self._embed(source_texts)

        if claim_vecs is None or source_vecs is None:
            # Fallback: keyword overlap
            return self._verify_keyword_fallback(claims, valid_sources)

        # Compute similarities
        claim_matches: list[ClaimMatch] = []
        unsupported: list[str] = []

        for i, claim in enumerate(claims):
            best_idx = 0
            best_sim = 0.0
            for j in range(len(valid_sources)):
                sim = _cosine(claim_vecs[i], source_vecs[j])
                if sim > best_sim:
                    best_sim = sim
                    best_idx = j

            matched = best_sim >= self.support_threshold
            if not matched:
                unsupported.append(claim)

            claim_matches.append(
                ClaimMatch(
                    claim=claim,
                    support_score=round(best_sim, 3),
                    best_source_title=valid_sources[best_idx].get("title", "")[:80],
                    best_source_similarity=round(best_sim, 3),
                    matched=matched,
                    excerpts=[source_texts[best_idx][:200]] if matched else [],
                )
            )

        coverage = sum(1 for cm in claim_matches if cm.matched) / len(claim_matches) if claim_matches else 0.0

        return ClaimVerificationResult(
            claims=claim_matches,
            overall_coverage=round(coverage, 3),
            unsupported_claims=unsupported,
            pass_threshold=self.pass_threshold,
            passed=coverage >= self.pass_threshold,
        )

    def _verify_keyword_fallback(
        self, claims: list[str], sources: list[dict[str, Any]]
    ) -> ClaimVerificationResult:
        """Fallback verification using keyword overlap when embeddings unavailable."""
        claim_matches: list[ClaimMatch] = []
        unsupported: list[str] = []

        for claim in claims:
            claim_words = set(claim.lower().split())
            best_sim = 0.0
            best_idx = 0
            for j, s in enumerate(sources):
                text = f"{s.get('title', '')} {s.get('abstract', s.get('snippet', ''))}"
                text_words = set(text.lower().split())
                overlap = len(claim_words & text_words)
                union = len(claim_words | text_words)
                sim = overlap / union if union else 0.0
                if sim > best_sim:
                    best_sim = sim
                    best_idx = j

            matched = best_sim >= self.support_threshold
            if not matched:
                unsupported.append(claim)

            claim_matches.append(
                ClaimMatch(
                    claim=claim,
                    support_score=round(best_sim, 3),
                    best_source_title=sources[best_idx].get("title", "")[:80],
                    best_source_similarity=round(best_sim, 3),
                    matched=matched,
                )
            )

        coverage = sum(1 for cm in claim_matches if cm.matched) / len(claim_matches) if claim_matches else 0.0
        return ClaimVerificationResult(
            claims=claim_matches,
            overall_coverage=round(coverage, 3),
            unsupported_claims=unsupported,
            pass_threshold=self.pass_threshold,
            passed=coverage >= self.pass_threshold,
        )


# Convenience functions


# Module-level singleton to avoid reloading the model on every call
_claim_matcher_singleton: ClaimMatcher | None = None
_claim_matcher_lock = threading.Lock()


def _get_matcher() -> ClaimMatcher:
    global _claim_matcher_singleton
    if _claim_matcher_singleton is None:
        with _claim_matcher_lock:
            if _claim_matcher_singleton is None:
                _claim_matcher_singleton = ClaimMatcher()
    return _claim_matcher_singleton


def verify_claims(text: str, sources: list[dict[str, Any]]) -> ClaimVerificationResult:
    """One-shot claim verification."""
    return _get_matcher().verify(text, sources)


def verify_solution(solution: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
    """Verify a solution and return a serializable dict."""
    result = verify_claims(solution, sources)
    return {
        "overall_coverage": result.overall_coverage,
        "passed": result.passed,
        "pass_threshold": result.pass_threshold,
        "unsupported_claims": result.unsupported_claims,
        "claim_count": len(result.claims),
        "supported_count": sum(1 for c in result.claims if c.matched),
        "details": [
            {
                "claim": c.claim[:200],
                "support_score": c.support_score,
                "matched": c.matched,
                "source": c.best_source_title,
            }
            for c in result.claims
        ],
    }
