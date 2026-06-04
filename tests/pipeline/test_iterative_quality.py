"""Tests for IterativeQualityLoop — auto-improve pipeline results on failed gates.

Tests src/pipeline/iterative_quality.py.
"""
from __future__ import annotations

import pytest

from src.pipeline.config import PipelineConfig
from src.pipeline.iterative_quality import (
    ImprovementPlan,
    IterativeQualityLoop,
)
from src.pipeline.quality import GateResult, QualityGates, QualityReport


@pytest.fixture
def config():
    cfg = PipelineConfig(name="test")
    cfg.min_quality_score = 60
    cfg.min_sources = 3
    cfg.min_gaps = 1
    cfg.min_hypotheses = 1
    cfg.min_dissertation_words = 600
    cfg.llm_temperature = 0.8
    cfg.max_sources = 50
    cfg.max_llm_tokens_per_section = 800
    cfg.hypothesis_ambition = "novel"
    return cfg


@pytest.fixture
def quality_loop(config):
    return IterativeQualityLoop(config=config)


@pytest.fixture
def passing_report():
    gates = [
        GateResult(step="sources", passed=True, score=0.9, message="OK"),
        GateResult(step="gaps", passed=True, score=0.85, message="OK"),
        GateResult(step="hypotheses", passed=True, score=0.9, message="OK"),
        GateResult(step="bibliography", passed=True, score=0.8, message="OK"),
        GateResult(step="dissertation", passed=True, score=0.85, message="OK"),
    ]
    return QualityReport(
        overall_score=85,
        grade="A",
        gates=gates,
        passed_all=True,
        recommendations=[],
    )


@pytest.fixture
def failing_report():
    gates = [
        GateResult(step="sources", passed=False, score=0.2, message="too few"),
        GateResult(step="gaps", passed=False, score=0.1, message="too few"),
        GateResult(step="hypotheses", passed=False, score=0.3, message="unambitious"),
        GateResult(step="bibliography", passed=False, score=0.1, message="no refs"),
        GateResult(step="dissertation", passed=False, score=0.25, message="too short"),
    ]
    return QualityReport(
        overall_score=30,
        grade="F",
        gates=gates,
        passed_all=False,
        recommendations=["Need deeper research"],
    )


@pytest.fixture
def borderline_report():
    gates = [
        GateResult(step="sources", passed=True, score=0.7, message="minimal"),
        GateResult(step="gaps", passed=True, score=0.65, message="few gaps"),
        GateResult(step="hypotheses", passed=False, score=0.5, message="unambitious"),
        GateResult(step="bibliography", passed=True, score=0.7, message="OK"),
        GateResult(step="dissertation", passed=True, score=0.7, message="minimal"),
    ]
    return QualityReport(
        overall_score=50,
        grade="C",
        gates=gates,
        passed_all=False,
        recommendations=["More ambitious hypotheses needed"],
    )


class TestIterativeQuality:
    """Tests for IterativeQualityLoop control flow and improvement logic."""

    def test_should_improve_false_when_passing(self, quality_loop, passing_report):
        """should_improve returns False when overall_score >= threshold."""
        assert quality_loop.should_improve(passing_report) is False

    def test_should_improve_false_when_passed_all(self, quality_loop):
        """should_improve returns False when passed_all is True, even with low score."""
        gates = [
            GateResult(step="sources", passed=True, score=0.3, message="low but passed"),
        ]
        report = QualityReport(
            overall_score=30,
            grade="F",
            gates=gates,
            passed_all=True,
            recommendations=[],
        )
        assert quality_loop.should_improve(report) is False

    def test_should_improve_true_when_failing_improvable(self, quality_loop, failing_report):
        """should_improve returns True when failed gates are improvable types."""
        assert quality_loop.should_improve(failing_report) is True

    def test_should_improve_false_non_improvable_gate(self, quality_loop, config):
        """Non-improvable gate failures cannot be auto-improved."""
        gates = [
            GateResult(step="simulation", passed=False, score=0.0, message="crashed"),
        ]
        report = QualityReport(
            overall_score=20,
            grade="F",
            gates=gates,
            passed_all=False,
            recommendations=[],
        )
        assert quality_loop.should_improve(report) is False

    def test_create_improvement_plan_generates_actions(self, quality_loop, failing_report):
        """create_improvement_plan generates actionable steps for failed gates."""
        plan = quality_loop.create_improvement_plan(failing_report, iteration=1)
        assert isinstance(plan, ImprovementPlan)
        assert plan.iteration == 1
        assert len(plan.actions) > 0
        assert len(plan.failed_gates) > 0
        assert "sources" in plan.failed_gates
        assert plan.parameter_changes

    def test_create_improvement_plan_sources_action(self, quality_loop, config):
        """Failed sources gate triggers expand_source_search action."""
        gates = [
            GateResult(step="sources", passed=False, score=0.2, message="too few"),
        ]
        report = QualityReport(
            overall_score=20, grade="F", gates=gates,
            passed_all=False, recommendations=[],
        )
        plan = quality_loop.create_improvement_plan(report, iteration=1)
        assert any(a["action"] == "expand_source_search" for a in plan.actions)
        assert plan.parameter_changes.get("min_sources") == config.min_sources + 5

    def test_create_improvement_plan_gaps_action(self, quality_loop):
        """Failed gaps gate triggers deepen_gap_analysis action."""
        gates = [
            GateResult(step="gaps", passed=False, score=0.1, message="no gaps"),
        ]
        report = QualityReport(
            overall_score=20, grade="F", gates=gates,
            passed_all=False, recommendations=[],
        )
        plan = quality_loop.create_improvement_plan(report, iteration=1)
        assert any(a["action"] == "deepen_gap_analysis" for a in plan.actions)
        assert plan.parameter_changes.get("min_gaps", 0) >= 3

    def test_create_improvement_plan_dissertation_action(self, quality_loop):
        """Failed dissertation gate triggers regenerate_dissertation action."""
        gates = [
            GateResult(step="dissertation", passed=False, score=0.2, message="too short"),
        ]
        report = QualityReport(
            overall_score=20, grade="F", gates=gates,
            passed_all=False, recommendations=[],
        )
        plan = quality_loop.create_improvement_plan(report, iteration=1)
        assert any(a["action"] == "regenerate_dissertation" for a in plan.actions)
        assert plan.parameter_changes.get("min_dissertation_words") == 600 + 300

    def test_apply_parameter_changes_modifies_config(self, quality_loop, config, failing_report):
        """apply_parameter_changes creates updated config with improved parameters."""
        plan = quality_loop.create_improvement_plan(failing_report, iteration=1)
        new_config = quality_loop.apply_parameter_changes(config, plan)
        assert new_config is not config
        assert new_config.min_sources == config.min_sources + 5
        assert new_config.max_sources == config.max_sources + 10

    def test_apply_parameter_changes_preserves_unrelated(self, quality_loop, config, failing_report):
        """Unrelated config fields are preserved after applying changes."""
        original_verification = config.require_verification
        plan = quality_loop.create_improvement_plan(failing_report, iteration=1)
        new_config = quality_loop.apply_parameter_changes(config, plan)
        assert new_config.require_verification == original_verification

    def test_max_iterations_hardcoded(self, quality_loop):
        """max_iterations is 3 by default."""
        assert quality_loop.max_iterations == 3

    def test_quality_threshold_from_config(self, config):
        """quality_threshold is read from config.min_quality_score."""
        loop = IterativeQualityLoop(config=config)
        assert loop.quality_threshold == config.min_quality_score

    def test_improvement_plan_all_failed_gates(self, quality_loop, failing_report):
        """All failed gate steps appear in the plan."""
        plan = quality_loop.create_improvement_plan(failing_report, iteration=1)
        for gate in failing_report.gates:
            if not gate.passed:
                assert gate.step in plan.failed_gates

    def test_improvement_plan_no_failed_gates(self, quality_loop, passing_report):
        """No failed gates produces empty plan."""
        plan = quality_loop.create_improvement_plan(passing_report, iteration=1)
        assert len(plan.failed_gates) == 0
        assert len(plan.actions) == 0

    def test_create_improvement_plan_hypotheses_action(self, quality_loop, config):
        """Failed hypotheses gate triggers regenerate_hypotheses and diversify_prompting."""
        gates = [
            GateResult(step="hypotheses", passed=False, score=0.3, message="unambitious"),
        ]
        report = QualityReport(
            overall_score=20, grade="F", gates=gates,
            passed_all=False, recommendations=[],
        )
        plan = quality_loop.create_improvement_plan(report, iteration=1)
        actions_names = [a["action"] for a in plan.actions]
        assert "regenerate_hypotheses" in actions_names
        assert "diversify_prompting" in actions_names
        assert plan.parameter_changes.get("min_hypotheses") == config.min_hypotheses + 2
        assert plan.parameter_changes.get("llm_temperature") <= 0.5

    def test_create_improvement_plan_bibliography_action(self, quality_loop, config):
        """Failed bibliography gate triggers expand_bibliography action."""
        gates = [
            GateResult(step="bibliography", passed=False, score=0.1, message="no refs"),
        ]
        report = QualityReport(
            overall_score=20, grade="F", gates=gates,
            passed_all=False, recommendations=[],
        )
        plan = quality_loop.create_improvement_plan(report, iteration=1)
        assert any(a["action"] == "expand_bibliography" for a in plan.actions)
        assert plan.parameter_changes.get("max_sources") == config.max_sources + 10

    def test_llm_temperature_clamped(self, quality_loop, config):
        """LLM temperature increase is clamped to max 0.5."""
        config.llm_temperature = 0.49
        gates = [
            GateResult(step="hypotheses", passed=False, score=0.3, message="unambitious"),
        ]
        report = QualityReport(
            overall_score=20, grade="F", gates=gates,
            passed_all=False, recommendations=[],
        )
        plan = quality_loop.create_improvement_plan(report, iteration=1)
        assert plan.parameter_changes.get("llm_temperature") <= 0.5
