"""
c4reqber: Prior Scorer

Scores hypotheses on prior plausibility before simulation.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np

from src.llm.embeddings import EmbeddingEngine

logger = logging.getLogger("c4reqber.discovery.ranking")


class PriorScorer:
    """Score hypotheses on prior plausibility."""

    def __init__(self) -> None:
        self._embedding = EmbeddingEngine()

    def score(
        self,
        hypothesis: dict[str, Any],
        literature: list[dict],
    ) -> dict[str, float]:
        """Compute prior scores for a hypothesis.

        Returns dict with keys: novelty, plausibility, formalizability, falsifiability.
        """
        return {
            "novelty": self._novelty(hypothesis, literature),
            "plausibility": self._plausibility(hypothesis, literature),
            "formalizability": self._formalizability(hypothesis),
            "falsifiability": self._falsifiability(hypothesis),
        }

    def _novelty(self, hypothesis: dict[str, Any], literature: list[dict]) -> float:
        """Novelty = distance from existing literature (0-1). Higher = more novel."""
        if not literature:
            return 1.0

        hyp_text = hypothesis.get("text", "")
        if not hyp_text:
            return 0.5

        try:
            hyp_emb = self._embedding.embed([hyp_text])[0]
            paper_texts = [p.get("title", "") + " " + p.get("abstract", "") for p in literature]
            paper_embs = [self._embedding.embed([t])[0] for t in paper_texts if t.strip()]
            if not paper_embs:
                return 1.0

            similarities = [self._cosine_sim(hyp_emb, pe) for pe in paper_embs]
            max_sim = max(similarities)
            # Novelty = 1 - max similarity, scaled
            novelty = 1.0 - max_sim
            return float(np.clip(novelty, 0.0, 1.0))
        except Exception as e:
            logger.warning("Novelty scoring error: %s", e)
            return 0.5

    def _plausibility(self, hypothesis: dict[str, Any], literature: list[dict]) -> float:
        """Plausibility = citation support / semantic similarity to evidence (0-1)."""
        if not literature:
            return 0.5

        hyp_text = hypothesis.get("text", "")
        if not hyp_text:
            return 0.5

        try:
            hyp_emb = self._embedding.embed(hyp_text)
            paper_texts = [p.get("title", "") + " " + p.get("abstract", "") for p in literature]
            paper_embs = [self._embedding.embed(t) for t in paper_texts if t.strip()]
            if not paper_embs:
                return 0.5

            similarities = [self._cosine_sim(hyp_emb, pe) for pe in paper_embs]
            mean_sim = np.mean(similarities)
            return float(np.clip(mean_sim, 0.0, 1.0))
        except Exception as e:
            logger.warning("Plausibility scoring error: %s", e)
            return 0.5

    def _formalizability(self, hypothesis: dict[str, Any]) -> float:
        """Quick check: can this hypothesis be formalized? (0-1)."""
        hyp_text = hypothesis.get("text", "")
        if not hyp_text:
            return 0.0

        # Heuristic: presence of mathematical/logical keywords
        math_keywords = [
            "forall", "exists", "implies", "if and only if", "theorem", "proof",
            "equal", "greater than", "less than", "function", "mapping",
            "converges", "diverges", "bounded", "continuous", "differentiable",
        ]
        text_lower = hyp_text.lower()
        score = sum(0.15 for kw in math_keywords if kw in text_lower)
        return float(min(score + 0.3, 1.0))  # baseline 0.3

    def _falsifiability(self, hypothesis: dict[str, Any]) -> float:
        """Can we test this hypothesis? (0-1)."""
        hyp_text = hypothesis.get("text", "")
        if not hyp_text:
            return 0.0

        # Heuristic: presence of testable claims
        testable_markers = [
            "increases", "decreases", "reduces", "enhances", "improves",
            "correlates", "causes", "affects", "inhibits", "promotes",
            "faster", "slower", "higher", "lower", "more", "less",
        ]
        text_lower = hyp_text.lower()
        score = sum(0.12 for m in testable_markers if m in text_lower)
        return float(min(score + 0.3, 1.0))  # baseline 0.3

    @staticmethod
    def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
        """Cosine similarity between two vectors."""
        norm = np.linalg.norm(a) * np.linalg.norm(b)
        if norm == 0:
            return 0.0
        return float(np.dot(a, b) / norm)
