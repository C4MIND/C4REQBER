"""
c4reqber: Surprise-Driven Question Generator

Generates research questions that maximize distance from existing knowledge.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np

from src.llm.embeddings import EmbeddingEngine
from src.llm.router import ProviderRouter


logger = logging.getLogger("c4reqber.exploration")


class SurpriseDrivenQuestionGenerator:
    """Generate surprising research questions."""

    def __init__(self) -> None:
        self._embedding = EmbeddingEngine()
        self._router = ProviderRouter()

    async def generate(
        self,
        existing_questions: list[str],
        topic: str,
        n_candidates: int = 50,
        top_k: int = 5,
    ) -> list[str]:
        """Generate surprising research questions.

        Args:
            existing_questions: Already known/asked questions.
            topic: Research topic.
            n_candidates: Number of candidate questions to generate.
            top_k: Number of top questions to return.

        Returns:
            List of top-k surprising questions.
        """
        try:
            candidates = await self._generate_candidates(topic, n_candidates)
        except Exception as e:
            logger.warning("Question generation failed: %s", e)
            return []

        if not existing_questions:
            return candidates[:top_k]

        try:
            existing_embs = self._embedding.embed(existing_questions)
            scores = []
            for c in candidates:
                c_emb = self._embedding.embed([c])[0]
                # Distance to nearest existing question
                sims = [self._cosine_sim(c_emb, e) for e in existing_embs]
                min_sim = min(sims) if sims else 1.0
                scores.append(1.0 - min_sim)  # Higher = more surprising

            # Sort by surprise score
            indexed = list(enumerate(scores))
            indexed.sort(key=lambda x: x[1], reverse=True)
            return [candidates[i] for i, _ in indexed[:top_k]]
        except Exception as e:
            logger.warning("Question scoring failed: %s", e)
            return candidates[:top_k]

    async def _generate_candidates(self, topic: str, n: int) -> list[str]:
        """Generate candidate questions via LLM."""
        prompt = f"""Generate {n} novel, surprising research questions about the topic: {topic}.

Requirements:
- Each question should explore an unexpected angle or connection
- Avoid questions that are already commonly studied
- Make them specific and investigable

Return one question per line, no numbering, no extra text."""

        response = await self._router.generate(
            stage_name="question_generation",
            prompt=prompt,
            system_prompt="You are a creative research strategist.",
        )
        content = response.content if hasattr(response, "content") else str(response)
        lines = [line.strip() for line in content.split("\n") if line.strip() and "?" in line]
        return lines[:n]

    @staticmethod
    def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
        norm = np.linalg.norm(a) * np.linalg.norm(b)
        if norm == 0:
            return 0.0
        return float(np.dot(a, b) / norm)
