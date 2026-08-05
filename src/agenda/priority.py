"""
c4reqber: Priority Scorer

Scores research questions by multi-criteria priority.
"""

from __future__ import annotations

from src.agenda.feasibility import FeasibilityResult
from src.agenda.generator import ResearchQuestion


class PriorityScorer:
    """Score research questions by priority."""

    def score(
        self,
        question: ResearchQuestion,
        feasibility: FeasibilityResult,
    ) -> float:
        """Compute priority score (0-1).

        Formula:
        - 30% novelty
        - 30% tractability
        - 20% impact potential
        - 20% user alignment
        """
        # Unchecked novelty (None) must not invent mid-range evidence — contribute 0
        novelty = 0.0 if question.novelty_score is None else float(question.novelty_score)
        return (
            0.30 * novelty
            + 0.30 * feasibility.tractability_score
            + 0.20 * question.impact_potential
            + 0.20 * question.user_alignment
        )

    def rank_questions(
        self,
        questions: list[ResearchQuestion],
        feasibilities: list[FeasibilityResult],
    ) -> list[tuple[ResearchQuestion, FeasibilityResult, float]]:
        """Rank questions by priority score.

        Returns:
            List of (question, feasibility, score) sorted by score descending.
        """
        scored = [(q, f, self.score(q, f)) for q, f in zip(questions, feasibilities, strict=False)]
        scored.sort(key=lambda x: x[2], reverse=True)
        return scored
