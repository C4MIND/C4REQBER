"""
Tests for src/metamodels/impact.py
Covers ImpactEngine, ImpactAnalyzer, and all heuristic extractors.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from c4.engine import C4State
from metamodels.impact import (
    ImpactAnalyzer,
    ImpactEngine,
    ImpactPhase,
    ImpactResult,
    ImpactStep,
)


class TestImpactPhaseEnum:
    def test_all_six_phases(self):
        phases = list(ImpactPhase)
        assert len(phases) == 6
        assert ImpactPhase.IDENTIFY.value == "identify"
        assert ImpactPhase.MAP.value == "map"
        assert ImpactPhase.PREDICT.value == "predict"
        assert ImpactPhase.ANALYZE.value == "analyze"
        assert ImpactPhase.CREATE.value == "create"
        assert ImpactPhase.TEST.value == "test"


class TestImpactStepDefaults:
    def test_defaults(self):
        step = ImpactStep(phase=ImpactPhase.IDENTIFY, description="D")
        assert step.inputs == {}
        assert step.outputs == {}
        assert step.status == "pending"
        assert step.duration_seconds == 0.0
        assert step.notes == ""

    def test_with_outputs(self):
        step = ImpactStep(
            phase=ImpactPhase.MAP,
            description="Map phase",
            outputs={"entities": ["A", "B"]},
            status="completed",
        )
        assert step.outputs["entities"] == ["A", "B"]


class TestImpactResultDefaults:
    def test_defaults(self):
        result = ImpactResult(problem="P")
        assert result.steps == []
        assert result.final_solution is None
        assert result.total_duration == 0.0
        assert result.completed is False


class TestImpactEngineSolve:
    def test_solve_basic(self):
        engine = ImpactEngine()
        result = engine.solve("How to reduce traffic congestion?")
        assert result.problem == "How to reduce traffic congestion?"
        assert len(result.steps) == 6
        assert result.completed is True
        assert result.total_duration >= 0.0

    def test_solve_with_domain_hint(self):
        engine = ImpactEngine()
        result = engine.solve("Design a rocket", domain_hint="engineering")
        map_step = [s for s in result.steps if s.phase == ImpactPhase.MAP][0]
        assert "engineering" in map_step.outputs.get("domains", [])

    def test_phase_order(self):
        engine = ImpactEngine()
        result = engine.solve("Test")
        phases = [s.phase for s in result.steps]
        assert phases == ImpactEngine.PHASE_ORDER

    def test_all_steps_completed(self):
        engine = ImpactEngine()
        result = engine.solve("Test")
        for step in result.steps:
            assert step.status == "completed"
            assert step.duration_seconds >= 0.0

    def test_step_inputs_contain_problem(self):
        engine = ImpactEngine()
        result = engine.solve("Test problem")
        for step in result.steps:
            assert "problem" in step.inputs
            assert step.inputs["problem"] == "Test problem"

    def test_get_phase_prompt(self):
        engine = ImpactEngine()
        prompt = engine.get_phase_prompt(ImpactPhase.IDENTIFY)
        assert "Identify" in prompt


class TestImpactEngineHeuristicExtractors:
    """Test all heuristic extraction methods."""

    @pytest.fixture
    def engine(self):
        return ImpactEngine()

    def test_extract_stakeholders_users(self, engine):
        stakeholders = engine._extract_stakeholders(
            "How to improve user experience for customers"
        )
        assert "user" in stakeholders

    def test_extract_stakeholders_developers(self, engine):
        stakeholders = engine._extract_stakeholders(
            "How to help developers and programmers"
        )
        assert "developer" in stakeholders

    def test_extract_stakeholders_default(self, engine):
        stakeholders = engine._extract_stakeholders("xyz abc 123")
        assert stakeholders == ["user", "system"]

    def test_extract_success_criteria_fast(self, engine):
        criteria = engine._extract_success_criteria("Make it fast and quick", "general")
        assert "fast" in criteria

    def test_extract_success_criteria_scalable(self, engine):
        criteria = engine._extract_success_criteria("Must scale", "software")
        assert "scalable" in criteria

    def test_extract_success_criteria_domain_software(self, engine):
        criteria = engine._extract_success_criteria("Build app", "software")
        assert "maintainable" in criteria

    def test_extract_entities(self, engine):
        entities = engine._extract_entities("Design a neural network classifier")
        assert isinstance(entities, list)
        assert len(entities) <= 8

    def test_extract_entities_filters_stopwords(self, engine):
        entities = engine._extract_entities("that with from this")
        assert all(e.lower() not in {"that", "with", "from", "this"} for e in entities)

    def test_extract_relations(self, engine):
        relations = engine._extract_relations(
            "System depends on database", ["System", "Database"]
        )
        assert len(relations) > 0
        assert relations[0]["type"] == "depends_on"

    def test_extract_relations_too_few_entities(self, engine):
        relations = engine._extract_relations("text", ["Only"])
        assert relations == []

    def test_extract_constraints_budget(self, engine):
        constraints = engine._extract_constraints("Limited budget and funding")
        assert "budget_limit" in constraints

    def test_extract_constraints_time(self, engine):
        constraints = engine._extract_constraints("Tight deadline and schedule")
        assert "time_limit" in constraints

    def test_extract_constraints_empty(self, engine):
        constraints = engine._extract_constraints("hello world")
        assert constraints == []

    def test_generate_baseline_growth(self, engine):
        baseline = engine._generate_baseline("How to increase sales")
        assert "growth" in baseline.lower() or "continues" in baseline.lower()

    def test_generate_baseline_reduce(self, engine):
        baseline = engine._generate_baseline("How to reduce waste")
        assert "persists" in baseline.lower() or "worsens" in baseline.lower()

    def test_generate_baseline_optimize(self, engine):
        baseline = engine._generate_baseline("How to optimize process")
        assert "suboptimal" in baseline.lower()

    def test_generate_scenarios_basic(self, engine):
        scenarios = engine._generate_scenarios("Problem", "general")
        assert "optimistic" in scenarios
        assert "realistic" in scenarios
        assert "pessimistic" in scenarios

    def test_generate_scenarios_risk(self, engine):
        scenarios = engine._generate_scenarios("High risk uncertain", "general")
        assert "high_volatility" in scenarios

    def test_generate_scenarios_finance(self, engine):
        scenarios = engine._generate_scenarios("Invest", "finance")
        assert "market_crash" in scenarios

    def test_generate_scenarios_engineering(self, engine):
        scenarios = engine._generate_scenarios("Build system", "engineering")
        assert "technical_debt" in scenarios

    def test_extract_risk_keywords(self, engine):
        risks = engine._extract_risks("Potential failure and crash", "general")
        assert "execution_failure" in risks

    def test_extract_risks_domain_software(self, engine):
        risks = engine._extract_risks("Deploy app", "software")
        assert "security_breach" in risks

    def test_extract_risks_default(self, engine):
        risks = engine._extract_risks("hello", "general")
        assert risks == ["assumption_validity"]

    def test_extract_contradictions_fast_accurate(self, engine):
        contradictions = engine._extract_contradictions(
            "Need to be fast and accurate"
        )
        assert any(c["type"] == "speed_vs_precision" for c in contradictions)

    def test_extract_contradictions_cheap_quality(self, engine):
        contradictions = engine._extract_contradictions(
            "Must be cheap with high quality"
        )
        assert any(c["type"] == "cost_vs_quality" for c in contradictions)

    def test_extract_contradictions_none(self, engine):
        contradictions = engine._extract_contradictions("Simple text")
        assert contradictions == []

    def test_extract_bottlenecks_information(self, engine):
        bottlenecks = engine._extract_bottlenecks(
            "Data is unclear and unknown", "general"
        )
        assert "information_asymmetry" in bottlenecks

    def test_extract_bottlenecks_domain_software(self, engine):
        bottlenecks = engine._extract_bottlenecks("Optimize", "software")
        assert "io_bound" in bottlenecks or "cpu_bound" in bottlenecks

    def test_extract_bottlenecks_default(self, engine):
        bottlenecks = engine._extract_bottlenecks("hello", "general")
        assert bottlenecks == ["information_asymmetry"]

    def test_extract_leverage_points_feedback(self, engine):
        leverage = engine._extract_leverage_points(
            "Use feedback loops and iteration", "general"
        )
        assert "feedback_loop" in leverage

    def test_extract_leverage_points_domain_software(self, engine):
        leverage = engine._extract_leverage_points("Build API", "software")
        assert "api_abstraction" in leverage

    def test_extract_leverage_points_default(self, engine):
        leverage = engine._extract_leverage_points("hello", "general")
        assert leverage == ["feedback_loop"]

    def test_suggest_solutions_optimize(self, engine):
        solutions = engine._suggest_solutions("Optimize throughput", "general")
        assert "algorithmic_optimization" in solutions

    def test_suggest_solutions_design(self, engine):
        solutions = engine._suggest_solutions("Design architecture", "general")
        assert "modular_architecture" in solutions

    def test_suggest_solutions_default(self, engine):
        solutions = engine._suggest_solutions("hello world", "general")
        assert "iterative_refinement" in solutions

    def test_generate_validation_plan_software(self, engine):
        plan = engine._generate_validation_plan("Build app", "software")
        assert "unit_tests" in plan

    def test_generate_validation_plan_physics(self, engine):
        plan = engine._generate_validation_plan("Simulate", "physics")
        assert "numerical_simulation" in plan

    def test_generate_validation_plan_default(self, engine):
        plan = engine._generate_validation_plan("Solve", "general")
        assert "falsification" in plan

    def test_extract_edge_cases_scale(self, engine):
        cases = engine._extract_edge_cases("Scale the system", "general")
        assert "exponential_growth" in cases

    def test_extract_edge_cases_user(self, engine):
        cases = engine._extract_edge_cases("Handle user input", "general")
        assert "malicious_input" in cases

    def test_extract_edge_cases_software(self, engine):
        cases = engine._extract_edge_cases("Build app", "software")
        assert "race_condition" in cases

    def test_extract_edge_cases_finance(self, engine):
        cases = engine._extract_edge_cases("Trade", "finance")
        assert "market_crash" in cases


class TestImpactAnalyzer:
    """Test ImpactAnalyzer sub-engine."""

    @pytest.fixture
    def analyzer(self):
        return ImpactAnalyzer()

    def test_execute_phase_identify(self, analyzer):
        result = analyzer._execute_phase("IDENTIFY", {
            "problem": "Design rocket",
            "domain": "engineering",
        })
        assert "decomposition" in result
        assert "components" in result["decomposition"]
        assert result["estimated_complexity"] in {"LOW", "MEDIUM", "HIGH"}

    def test_execute_phase_measure(self, analyzer):
        result = analyzer._execute_phase("MEASURE", {
            "problem": "Test",
            "domain": "physics",
        })
        assert "metrics" in result
        assert "accuracy" in result["metrics"]

    def test_execute_phase_prototype(self, analyzer):
        result = analyzer._execute_phase("PROTOTYPE", {
            "problem": "Test",
            "domain": "general",
            "decomposition": {"components": [{"name": "A", "verb": "build"}]},
            "metrics": ["confidence"],
        })
        assert "hypotheses" in result
        assert "recommended_patterns" in result

    def test_execute_phase_assess(self, analyzer):
        result = analyzer._execute_phase("ASSESS", {
            "problem": "Test",
            "components": [1, 2, 3],
        })
        assert "confidence_interval" in result
        assert "risks" in result

    def test_execute_phase_communicate(self, analyzer):
        result = analyzer._execute_phase("COMMUNICATE", {
            "problem": "Test problem",
            "hypotheses": ["h1"],
        })
        assert "report" in result
        assert "executive_summary" in result["report"]

    def test_execute_phase_transform(self, analyzer):
        result = analyzer._execute_phase("TRANSFORM", {
            "problem": "Test",
            "domain": "physics",
            "components": [1, 2, 3, 4],
        })
        assert "transformation" in result
        assert "target_domains" in result["transformation"]

    def test_execute_phase_unknown(self, analyzer):
        result = analyzer._execute_phase("UNKNOWN", {"problem": "Test"})
        assert result["status"] == "completed"
        assert result["phase"] == "UNKNOWN"

    def test_phase_identify_empty_problem(self, analyzer):
        result = analyzer._phase_identify({"problem": "", "domain": "general"})
        assert "decomposition" in result

    def test_phase_measure_general_domain(self, analyzer):
        result = analyzer._phase_measure({"domain": "general"})
        assert "confidence" in result["metrics"]

    def test_phase_prototype_no_components(self, analyzer):
        result = analyzer._phase_prototype({"decomposition": {}})
        assert result["hypotheses"] == []

    def test_suggest_patterns_physics(self, analyzer):
        patterns = analyzer._suggest_patterns({"domain": "physics"})
        assert "monte_carlo" in patterns

    def test_suggest_patterns_biology(self, analyzer):
        patterns = analyzer._suggest_patterns({"domain": "biology"})
        assert "lotka_volterra" in patterns

    def test_suggest_patterns_unknown_domain(self, analyzer):
        patterns = analyzer._suggest_patterns({"domain": "cooking"})
        assert "monte_carlo" in patterns

    def test_cross_domain_map_physics(self, analyzer):
        domains = analyzer._cross_domain_map({"domain": "physics"})
        assert "engineering" in domains

    def test_cross_domain_map_unknown(self, analyzer):
        domains = analyzer._cross_domain_map({"domain": "cooking"})
        assert "general" in domains
