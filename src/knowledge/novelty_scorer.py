"""
C4REQBER: Novelty Scorer

Computes an objective novelty score (0–1) for a proposed solution by comparing
its embedding to the embeddings of retrieved prior-art papers.

Inspired by SemNovel (BIDS-Xu-Lab/SemNovel) but simplified for CPU inference.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger("c4reqber.novelty_scorer")


class NoveltyScorer:
    """Score novelty of proposed solution vs prior art using embeddings."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self._model_name = model_name
        self._model: Any | None = None

    def _get_model(self) -> Any:
        """Lazy-load sentence-transformers model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self._model_name)
            except Exception as exc:
                logger.warning("sentence-transformers unavailable: %s", exc)
                raise
        return self._model

    def score(
        self,
        proposed_text: str,
        prior_art: list[dict[str, Any]],
    ) -> float:
        """Return novelty score 0.0 (identical to prior) → 1.0 (completely novel)."""
        if not prior_art:
            return 1.0  # No prior art = completely novel

        model = self._get_model()

        # Build corpus texts from prior art
        corpus_texts = []
        for p in prior_art:
            text = f"{p.get('title', '')} {p.get('abstract', '')}".strip()
            if text:
                corpus_texts.append(text)

        if not corpus_texts:
            return 1.0

        # Encode
        corpus_embeddings = model.encode(corpus_texts, convert_to_numpy=True)
        proposed_embedding = model.encode([proposed_text], convert_to_numpy=True)[0]

        # Cosine similarity
        corpus_norm = np.linalg.norm(corpus_embeddings, axis=1)
        proposed_norm = np.linalg.norm(proposed_embedding)
        if proposed_norm == 0 or np.any(corpus_norm == 0):
            return 1.0

        similarities = np.dot(corpus_embeddings, proposed_embedding) / (corpus_norm * proposed_norm)
        max_similarity = float(np.max(similarities))
        novelty = 1.0 - max_similarity

        # Clamp to [0, 1]
        return max(0.0, min(1.0, novelty))

    def flag(self, novelty_score: float) -> str:
        """Human-readable flag for a given novelty score."""
        if novelty_score < 0.2:
            return "HIGH_SIMILARITY_TO_PRIOR_ART"
        if novelty_score < 0.4:
            return "MODERATE_SIMILARITY"
        if novelty_score > 0.7:
            return "POTENTIALLY_NOVEL"
        return "NOVELTY_UNCERTAIN"
