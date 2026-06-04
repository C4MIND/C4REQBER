"""Tests for agenda priority scoring."""
from __future__ import annotations

import pytest

from src.agenda.feasibility import FeasibilityResult
from src.agenda.generator import ResearchQuestion
from src.agenda.priority import PriorityScorer


class TestPriorityScorer:
    def test_score_computation(self) -> None:
        scorer = PriorityScorer()
        question = ResearchQuestion(
            text="Test",
            strategy="gap",
            novelty_score=1.0,
            impact_potential=0.5,
            user_alignment=0.5,
        )
        feasibility = FeasibilityResult(
            has_tools=True,
            estimated_cost_usd=10.0,
            estimated_time_minutes=300.0,
            tractability_score=0.8,
        )
        score = scorer.score(question, feasibility)
        expected = 0.30 * 1.0 + 0.30 * 0.8 + 0.20 * 0.5 + 0.20 * 0.5
        assert pytest.approx(score, abs=0.001) == expected

    def test_rank_questions(self) -> None:
        scorer = PriorityScorer()
        q1 = ResearchQuestion(text="Q1", strategy="gap", novelty_score=0.2, impact_potential=0.2, user_alignment=0.2)
        q2 = ResearchQuestion(text="Q2", strategy="extension", novelty_score=0.9, impact_potential=0.9, user_alignment=0.9)
        f = FeasibilityResult(
            has_tools=True,
            estimated_cost_usd=1.0,
            estimated_time_minutes=60.0,
            tractability_score=0.5,
        )
        ranked = scorer.rank_questions([q1, q2], [f, f])
        assert len(ranked) == 2
        assert ranked[0][0].text == "Q2"  # higher score first
        assert ranked[1][0].text == "Q1"
