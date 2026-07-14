"""Tests for src/solver/core.py — OneShotResult, cost estimation, rendering."""
from __future__ import annotations

from datetime import datetime

from src.solver.core import OneShotResult, estimate_cost, render_summary


class TestOneShotResult:
    def test_default_construction(self):
        r = OneShotResult(problem="test", timestamp=datetime(2026, 1, 1), relevant_papers=[])
        assert r.problem == "test"
        assert r.total_api_calls == 0
        assert r.hypotheses == []

    def test_with_hypotheses(self):
        r = OneShotResult(
            problem="test",
            timestamp=datetime(2026, 1, 1),
            relevant_papers=[],
            hypotheses=[{"title": "H1", "validation_cost": 100.0}],
            total_api_calls=10,
        )
        assert len(r.hypotheses) == 1
        assert r.total_api_calls == 10

    def test_empty_recommendations(self):
        r = OneShotResult(problem="", timestamp=datetime.now(), relevant_papers=[])
        assert r.recommendations == []
        assert r.next_steps == []


class TestEstimateCost:
    def test_zero_calls(self):
        r = OneShotResult(problem="x", timestamp=datetime.now(), relevant_papers=[], total_api_calls=0)
        assert estimate_cost(r) == 0.0

    def test_with_calls(self):
        r = OneShotResult(problem="x", timestamp=datetime.now(), relevant_papers=[], total_api_calls=100)
        assert estimate_cost(r) == 1.0

    def test_with_validation_costs(self):
        r = OneShotResult(
            problem="x",
            timestamp=datetime.now(),
            relevant_papers=[],
            hypotheses=[
                {"validation_cost": 50.0},
                {"validation_cost": 30.0},
            ],
            total_api_calls=10,
        )
        cost = estimate_cost(r)
        assert cost == 80.1


class TestRenderSummary:
    def test_renders_without_error(self):
        r = OneShotResult(problem="test", timestamp=datetime(2026, 1, 1), relevant_papers=[])
        output = render_summary(r)
        assert "Discovery Cycle Complete" in output
        assert "Duration" in output

    def test_renders_with_papers(self):
        r = OneShotResult(
            problem="test",
            timestamp=datetime(2026, 1, 1),
            relevant_papers=[{"title": "Paper 1"}],
            consensus_analysis={"level": "strong", "confidence": 85.0},
        )
        output = render_summary(r)
        assert "1 papers found" in output
        assert "STRONG" in output
