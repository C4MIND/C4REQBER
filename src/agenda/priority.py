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
        return (
            0.30 * question.novelty_score +
            0.30 * feasibility.tractability_score +
            0.20 * question.impact_potential +
            0.20 * question.user_alignment
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
        scored = [
            (q, f, self.score(q, f))
            for q, f in zip(questions, feasibilities)
        ]
        scored.sort(key=lambda x: x[2], reverse=True)
        return scored
