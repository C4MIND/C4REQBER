"""Tests for agenda module."""

from __future__ import annotations

from unittest.mock import AsyncMock

import networkx as nx
import pytest

from src.agenda.feasibility import FeasibilityChecker, FeasibilityResult
from src.agenda.generator import AgendaGenerator, ResearchQuestion
from src.agenda.priority import PriorityScorer
from src.agenda.progress import ProgressTracker
from src.api.v8_routers.agenda import approve_question, generate_agenda


class TestResearchQuestion:
    def test_to_dict(self) -> None:
        q = ResearchQuestion("Test?", "gap", 0.8, 0.7)
        d = q.to_dict()
        assert d["text"] == "Test?"
        assert d["strategy"] == "gap"


class TestAgendaGenerator:
    def test_generate_empty_graph(self) -> None:
        gen = AgendaGenerator()
        graph = nx.Graph()
        questions = gen.generate(graph, [], n_questions=3)
        assert isinstance(questions, list)

    def test_gap_driven(self) -> None:
        gen = AgendaGenerator()
        graph = nx.Graph()
        graph.add_nodes_from(["A", "B", "C", "D"])
        graph.add_edge("A", "B")
        questions = gen.generate(graph, [], n_questions=5)
        assert len(questions) > 0
        gap_qs = [q for q in questions if q.strategy == "gap"]
        assert len(gap_qs) > 0

    def test_extension_driven(self) -> None:
        gen = AgendaGenerator()
        graph = nx.Graph()
        recent = [{"hypothesis": {"text": "H1"}}]
        questions = gen.generate(graph, recent, n_questions=3)
        ext_qs = [q for q in questions if q.strategy == "extension"]
        assert len(ext_qs) > 0

    def test_sorted_by_score(self) -> None:
        gen = AgendaGenerator()
        graph = nx.Graph()
        graph.add_nodes_from(["A", "B", "C"])
        questions = gen.generate(graph, [], n_questions=3)
        scores = [q.novelty_score * 0.4 + q.impact_potential * 0.4 for q in questions]
        assert scores == sorted(scores, reverse=True)


class TestFeasibilityChecker:
    def test_detects_tools(self) -> None:
        checker = FeasibilityChecker()
        q = ResearchQuestion("Simulate wave dynamics", "gap", 0.5, 0.5)
        result = checker.check(q)
        assert result.has_tools is True
        assert result.tractability_score > 0.0

    def test_estimates_cost(self) -> None:
        checker = FeasibilityChecker()
        q = ResearchQuestion("Simple question", "gap", 0.5, 0.5)
        result = checker.check(q)
        assert result.estimated_cost_usd > 0.0
        assert result.estimated_time_minutes > 0.0


class TestPriorityScorer:
    def test_score_range(self) -> None:
        scorer = PriorityScorer()
        q = ResearchQuestion("Q", "gap", 0.5, 0.5)
        f = FeasibilityResult(True, 1.0, 10.0, 0.5)
        score = scorer.score(q, f)
        assert 0.0 <= score <= 1.0

    def test_ranking(self) -> None:
        scorer = PriorityScorer()
        q1 = ResearchQuestion("Q1", "gap", 0.9, 0.9)
        q2 = ResearchQuestion("Q2", "gap", 0.1, 0.1)
        f = FeasibilityResult(True, 1.0, 10.0, 0.5)
        ranked = scorer.rank_questions([q1, q2], [f, f])
        assert ranked[0][0] == q1
        assert ranked[1][0] == q2


class TestProgressTracker:
    def test_update_and_retrieve(self) -> None:
        tracker = ProgressTracker()
        tracker.update({"hypothesis": {"text": "Sleep affects memory"}, "gaps": ["mechanism"]})
        assert "sleep affects memory" in tracker.get_covered_topics()
        assert tracker.get_open_gaps() == ["mechanism"]

    def test_dedup_gaps(self) -> None:
        tracker = ProgressTracker()
        tracker.update({"gaps": ["a", "b"]})
        tracker.update({"gaps": ["a", "c"]})
        assert tracker.get_open_gaps() == ["a", "b", "c"]


class TestAgendaAPI:
    @pytest.mark.anyio(backend="asyncio")
    async def test_generate_agenda(self) -> None:
        req = AsyncMock()
        req.knowledge_graph = {"nodes": ["A", "B", "C"], "edges": [["A", "B"]]}
        req.recent_results = [{"hypothesis": {"text": "H1"}}]
        req.n_questions = 3

        result = await generate_agenda(req)
        assert "questions" in result
        assert result["count"] <= 3

    @pytest.mark.anyio(backend="asyncio")
    async def test_approve_question(self) -> None:
        req = AsyncMock()
        req.question_text = "Q1"
        req.action = "approve"
        req.modified_text = None

        result = await approve_question(req)
        assert result["status"] == "approved"

    @pytest.mark.anyio(backend="asyncio")
    async def test_reject_question(self) -> None:
        req = AsyncMock()
        req.question_text = "Q1"
        req.action = "reject"
        req.modified_text = None

        result = await approve_question(req)
        assert result["status"] == "rejected"

    @pytest.mark.anyio(backend="asyncio")
    async def test_modify_question(self) -> None:
        req = AsyncMock()
        req.question_text = "Q1"
        req.action = "modify"
        req.modified_text = "Q1 refined"

        result = await approve_question(req)
        assert result["status"] == "modified"
        assert result["modified"] == "Q1 refined"
