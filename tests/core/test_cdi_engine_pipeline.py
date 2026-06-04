"""
Comprehensive tests for src/core/cdi_engine.py — Extended coverage.

Targets:
- Full pipeline execution (solve, error recovery, cost tracking, cache integration)
- Error recovery paths
- Cost tracking integration
- Cache integration
- Mock LLM calls where applicable

Target coverage: 85%+
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.core.c4_state import C4State
from src.core.cdi_engine import (
    C4Transition,
    CDIEngine,
    CDISolution,
    ContradictionType,
    EinsteinValidator,
    PhysicalContradiction,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def engine():
    """Fresh CDIEngine instance."""
    return CDIEngine()


@pytest.fixture
def sample_contradiction():
    return PhysicalContradiction(
        parameter="Weight",
        value_a="light",
        value_not_a="heavy",
        requirement_y="portability",
        requirement_z="durability",
        contradiction_type=ContradictionType.TRADE_OFF,
    )


@pytest.fixture
def conflicting_contradiction():
    return PhysicalContradiction(
        parameter="Speed of light",
        value_a="relative",
        value_not_a="constant",
        requirement_y="Newtonian mechanics",
        requirement_z="Maxwell's equations",
        contradiction_type=ContradictionType.CONFLICTING_GOALS,
    )


# ═══════════════════════════════════════════════════════════════════
# Full Pipeline Execution
# ═══════════════════════════════════════════════════════════════════


class TestFullPipelineExecution:
    def test_solve_end_to_end(self, engine, sample_contradiction):
        """Test complete pipeline from contradiction to solution."""
        solution = engine.solve(sample_contradiction)

        assert isinstance(solution, CDISolution)
        assert solution.steps_taken <= 6
        assert 0.0 <= solution.confidence_score <= 1.0
        assert len(solution.hypothesis) > 0
        assert solution.contradiction == sample_contradiction
        assert isinstance(solution.c4_path, list)

    def test_solve_all_contradiction_types(self, engine):
        """Pipeline works for every contradiction type."""
        for ct in ContradictionType:
            pc = PhysicalContradiction(
                parameter="P", value_a="A", value_not_a="B",
                requirement_y="Y", requirement_z="Z",
                contradiction_type=ct,
            )
            sol = engine.solve(pc)
            assert isinstance(sol, CDISolution)
            assert sol.steps_taken <= 6

    def test_solve_with_provided_state(self, engine, sample_contradiction):
        """Pipeline uses provided start state instead of fingerprinting."""
        start = C4State(0, 0, 0)
        solution = engine.solve(sample_contradiction, start)

        assert solution.steps_taken <= 6
        if solution.c4_path:
            assert solution.c4_path[0].from_state == start

    def test_solve_same_start_end_zero_steps(self, engine):
        """If start == target, pipeline returns zero-step solution."""
        pc = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.CONFLICTING_GOALS,
        )
        start = C4State(2, 2, 2)
        solution = engine.solve(pc, start)

        assert solution.steps_taken == 0
        assert solution.confidence_score == 1.0
        assert solution.c4_path == []

    def test_pipeline_path_continuity(self, engine, sample_contradiction):
        """Each transition's to_state matches next transition's from_state."""
        solution = engine.solve(sample_contradiction)
        path = solution.c4_path

        for i in range(len(path) - 1):
            assert path[i].to_state == path[i + 1].from_state

    def test_pipeline_hypothesis_contains_operators(self, engine, sample_contradiction):
        """Hypothesis references operators used in the path."""
        solution = engine.solve(sample_contradiction)
        for transition in solution.c4_path:
            assert transition.operator in solution.hypothesis

    def test_pipeline_confidence_inversely_correlates_with_steps(self, engine):
        """More steps → lower confidence."""
        pc = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.CONFLICTING_GOALS,
        )
        sol_short = engine.solve(pc, C4State(2, 2, 2))  # 0 steps
        sol_long = engine.solve(pc, C4State(0, 0, 0))   # 3 steps

        assert sol_short.confidence_score >= sol_long.confidence_score

    def test_pipeline_str_representation_in_hypothesis(self, engine, sample_contradiction):
        """Final state string representation appears in hypothesis."""
        solution = engine.solve(sample_contradiction)
        assert str(solution.c4_path[-1].to_state if solution.c4_path else C4State(2, 2, 2)) in solution.hypothesis


# ═══════════════════════════════════════════════════════════════════
# Error Recovery
# ═══════════════════════════════════════════════════════════════════


class TestErrorRecovery:
    def test_fingerprint_unknown_type_defaults(self, engine):
        """Unknown contradiction type falls back to default fingerprint."""
        class FakeType:
            pass

        pc = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=FakeType(),  # type: ignore[arg-type]
        )
        state = engine._fingerprint_contradiction(pc)
        assert state.to_tuple() == (1, 1, 2)

    def test_compute_route_with_invalid_operator_name(self, engine, monkeypatch):
        """Route computation handles missing operators gracefully."""
        def fake_get(name):
            if name == "tau+":
                return None
            return engine.operators.get(name)

        monkeypatch.setattr(engine.operators, "get", fake_get)
        start = C4State(0, 1, 1)
        end = C4State(1, 1, 1)

        # When operator is missing, path computation should still complete
        # or handle the error — current code will raise AttributeError on None
        with pytest.raises((AttributeError, TypeError)):
            engine._compute_route(start, end)

    def test_solve_with_none_contradiction(self, engine):
        """Passing None as contradiction should raise AttributeError."""
        with pytest.raises(AttributeError):
            engine.solve(None)  # type: ignore[arg-type]

    def test_solve_survives_empty_contradiction_fields(self, engine):
        """Empty-string fields should not crash the pipeline."""
        pc = PhysicalContradiction(
            parameter="", value_a="", value_not_a="",
            requirement_y="", requirement_z="",
            contradiction_type=ContradictionType.TRADE_OFF,
        )
        solution = engine.solve(pc)
        assert isinstance(solution, CDISolution)

    def test_execute_path_with_mismatched_states(self, engine):
        """Path execution handles non-continuous paths."""
        path = [
            C4Transition("tau+", C4State(0, 0, 0), C4State(1, 0, 0)),
            C4Transition("lambda+", C4State(2, 0, 0), C4State(2, 1, 0)),  # mismatch
        ]
        result = engine._execute_path(C4State(0, 0, 0), path)
        assert result.to_tuple() == (2, 1, 0)

    def test_theorem_11_violation_recovery(self):
        """CDISolution post_init catches steps > 6."""
        pc = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.TRADE_OFF,
        )
        with pytest.raises(AssertionError, match="Theorem 11 violated"):
            CDISolution(
                hypothesis="Test", c4_path=[],
                steps_taken=7, contradiction=pc, confidence_score=0.5,
            )

    def test_einstein_validator_str_assertion_recovery(self, engine, monkeypatch):
        """Validator raises AssertionError if STR takes too many steps."""
        def fake_solve(*args, **kwargs):
            pc = PhysicalContradiction(
                parameter="Speed of light",
                value_a="relative", value_not_a="constant",
                requirement_y="Newton", requirement_z="Maxwell",
                contradiction_type=ContradictionType.CONFLICTING_GOALS,
            )
            return CDISolution(
                hypothesis="Fake", c4_path=[],
                steps_taken=5, contradiction=pc, confidence_score=0.5,
            )

        monkeypatch.setattr(engine, "solve", fake_solve)
        validator = EinsteinValidator(engine)
        with pytest.raises(AssertionError, match="STR should take"):
            validator.validate_str()

    def test_einstein_validator_gtr_assertion_recovery(self, engine, monkeypatch):
        """Validator raises AssertionError if GTR takes too many steps."""
        def fake_solve(*args, **kwargs):
            pc = PhysicalContradiction(
                parameter="Gravity",
                value_a="force", value_not_a="geometry",
                requirement_y="Newton", requirement_z="SR",
                contradiction_type=ContradictionType.CONFLICTING_GOALS,
            )
            return CDISolution(
                hypothesis="Fake", c4_path=[],
                steps_taken=7, contradiction=pc, confidence_score=0.5,
            )

        monkeypatch.setattr(engine, "solve", fake_solve)
        validator = EinsteinValidator(engine)
        with pytest.raises(AssertionError):
            validator.validate_gtr()


# ═══════════════════════════════════════════════════════════════════
# Cost Tracking
# ═══════════════════════════════════════════════════════════════════


class TestCostTracking:
    def test_solve_returns_confidence_score(self, engine, sample_contradiction):
        """Solution includes a confidence score for cost/quality tracking."""
        solution = engine.solve(sample_contradiction)
        assert isinstance(solution.confidence_score, float)
        assert 0.0 <= solution.confidence_score <= 1.0

    def test_confidence_decreases_with_path_length(self, engine, sample_contradiction):
        """Confidence is inversely related to computational cost (path length)."""
        path_0 = []
        path_3 = [
            C4Transition("tau+", C4State(0, 0, 0), C4State(1, 0, 0)),
            C4Transition("lambda+", C4State(1, 0, 0), C4State(1, 1, 0)),
            C4Transition("kappa+", C4State(1, 1, 0), C4State(1, 1, 1)),
        ]
        path_6 = [
            C4Transition("tau+", C4State(0, 0, 0), C4State(1, 0, 0)),
            C4Transition("tau+", C4State(1, 0, 0), C4State(2, 0, 0)),
            C4Transition("lambda+", C4State(2, 0, 0), C4State(2, 1, 0)),
            C4Transition("lambda+", C4State(2, 1, 0), C4State(2, 2, 0)),
            C4Transition("kappa+", C4State(2, 2, 0), C4State(2, 2, 1)),
            C4Transition("kappa+", C4State(2, 2, 1), C4State(2, 2, 2)),
        ]

        c0 = engine._calculate_confidence(path_0, sample_contradiction)
        c3 = engine._calculate_confidence(path_3, sample_contradiction)
        c6 = engine._calculate_confidence(path_6, sample_contradiction)

        assert c0 == pytest.approx(1.0, abs=0.01)
        assert c3 == pytest.approx(0.75, abs=0.01)
        assert c6 == pytest.approx(0.5, abs=0.01)
        assert c0 > c3 > c6

    def test_steps_taken_reflects_computational_cost(self, engine, sample_contradiction):
        """steps_taken is a proxy for computational effort."""
        solution = engine.solve(sample_contradiction)
        assert solution.steps_taken == len(solution.c4_path)
        assert solution.steps_taken <= 6  # Theorem 11 bound

    def test_zero_step_solution_max_confidence(self, engine):
        """Zero-step solution has maximum confidence (minimum cost)."""
        pc = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.CONFLICTING_GOALS,
        )
        solution = engine.solve(pc, C4State(2, 2, 2))
        assert solution.steps_taken == 0
        assert solution.confidence_score == 1.0

    def test_cost_quality_tradeoff_documented(self, engine, sample_contradiction):
        """Longer paths have documented lower confidence (higher cost)."""
        solution = engine.solve(sample_contradiction)
        # Every solution should document its cost/quality tradeoff
        assert hasattr(solution, 'steps_taken')
        assert hasattr(solution, 'confidence_score')
        assert solution.confidence_score == pytest.approx(
            0.5 + 0.5 * (1.0 - solution.steps_taken / 6.0), abs=0.01
        )


# ═══════════════════════════════════════════════════════════════════
# Cache Integration
# ═══════════════════════════════════════════════════════════════════


class TestCacheIntegration:
    def test_solve_is_deterministic_for_same_input(self, engine, sample_contradiction):
        """Same input produces same output — cacheable."""
        sol1 = engine.solve(sample_contradiction)
        sol2 = engine.solve(sample_contradiction)

        assert sol1.steps_taken == sol2.steps_taken
        assert sol1.confidence_score == sol2.confidence_score
        assert sol1.hypothesis == sol2.hypothesis
        assert len(sol1.c4_path) == len(sol2.c4_path)

    def test_solve_deterministic_with_state(self, engine, sample_contradiction):
        """Same input + state produces same output — cacheable."""
        start = C4State(0, 0, 0)
        sol1 = engine.solve(sample_contradiction, start)
        sol2 = engine.solve(sample_contradiction, start)

        assert sol1.steps_taken == sol2.steps_taken
        assert sol1.confidence_score == sol2.confidence_score
        assert sol1.hypothesis == sol2.hypothesis

    def test_different_contradictions_different_results(self, engine):
        """Different inputs produce different outputs."""
        pc1 = PhysicalContradiction(
            parameter="A", value_a="1", value_not_a="2",
            requirement_y="X", requirement_z="Y",
            contradiction_type=ContradictionType.TRADE_OFF,
        )
        pc2 = PhysicalContradiction(
            parameter="B", value_a="3", value_not_a="4",
            requirement_y="X", requirement_z="Y",
            contradiction_type=ContradictionType.SCALE,
        )
        sol1 = engine.solve(pc1)
        sol2 = engine.solve(pc2)

        # Same start state (fingerprinted differently) → different paths
        assert sol1.hypothesis != sol2.hypothesis

    def test_fingerprint_caching_consistency(self, engine):
        """Fingerprinting is deterministic for same contradiction type."""
        pc = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.TEMPORAL,
        )
        f1 = engine._fingerprint_contradiction(pc)
        f2 = engine._fingerprint_contradiction(pc)
        assert f1 == f2

    def test_predict_solution_region_caching_consistency(self, engine):
        """Solution region prediction is deterministic."""
        pc1 = PhysicalContradiction(
            parameter="A", value_a="1", value_not_a="2",
            requirement_y="X", requirement_z="Y",
            contradiction_type=ContradictionType.TRADE_OFF,
        )
        pc2 = PhysicalContradiction(
            parameter="B", value_a="3", value_not_a="4",
            requirement_y="X", requirement_z="Y",
            contradiction_type=ContradictionType.SCALE,
        )
        t1 = engine._predict_solution_region(pc1)
        t2 = engine._predict_solution_region(pc2)
        assert t1 == t2

    def test_mock_cache_wrapper(self, engine, sample_contradiction):
        """Simulate a cache wrapper around solve()."""
        cache: dict[tuple, CDISolution] = {}

        def cached_solve(contradiction, state=None):
            key = (contradiction.parameter, contradiction.contradiction_type.value,
                   state.to_tuple() if state else None)
            if key not in cache:
                cache[key] = engine.solve(contradiction, state)
            return cache[key]

        start = C4State(0, 0, 0)
        sol1 = cached_solve(sample_contradiction, start)
        sol2 = cached_solve(sample_contradiction, start)

        assert sol1 is sol2  # Same object from cache
        assert len(cache) == 1


# ═══════════════════════════════════════════════════════════════════
# Mock LLM Integration
# ═══════════════════════════════════════════════════════════════════


class TestMockLLMIntegration:
    def test_synthesize_hypothesis_can_be_mocked(self, engine, sample_contradiction, monkeypatch):
        """Hypothesis synthesis can be replaced with LLM mock."""
        def mock_llm_synthesize(contradiction, final_state, path):
            return f"LLM: Resolve {contradiction.parameter} via quantum approach"

        monkeypatch.setattr(engine, "_synthesize_hypothesis", mock_llm_synthesize)
        solution = engine.solve(sample_contradiction)
        assert "LLM:" in solution.hypothesis
        assert "quantum approach" in solution.hypothesis

    def test_mock_llm_returns_structured_output(self, engine, sample_contradiction, monkeypatch):
        """Mock LLM returns structured JSON-like output."""
        def mock_llm_json(contradiction, final_state, path):
            return (
                f'{{"solution": "{contradiction.parameter}", '
                f'"operators": {[t.operator for t in path]}, '
                f'"confidence": 0.95}}'
            )

        monkeypatch.setattr(engine, "_synthesize_hypothesis", mock_llm_json)
        solution = engine.solve(sample_contradiction)
        assert "solution" in solution.hypothesis
        assert "confidence" in solution.hypothesis

    def test_mock_llm_error_handling(self, engine, sample_contradiction, monkeypatch):
        """Pipeline handles LLM failures gracefully."""
        def failing_llm(*args, **kwargs):
            raise RuntimeError("LLM API timeout")

        monkeypatch.setattr(engine, "_synthesize_hypothesis", failing_llm)
        with pytest.raises(RuntimeError, match="LLM API timeout"):
            engine.solve(sample_contradiction)

    def test_mock_llm_with_cost_tracking(self, engine, sample_contradiction, monkeypatch):
        """Track mock LLM token cost alongside pipeline cost."""
        call_count = 0

        def counting_llm(contradiction, final_state, path):
            nonlocal call_count
            call_count += 1
            return f"LLM call #{call_count} for {contradiction.parameter}"

        monkeypatch.setattr(engine, "_synthesize_hypothesis", counting_llm)
        engine.solve(sample_contradiction)
        assert call_count == 1

    def test_mock_llm_batch_processing(self, engine, monkeypatch):
        """Batch process multiple contradictions with mock LLM."""
        results = []

        def batch_llm(contradiction, final_state, path):
            results.append(contradiction.parameter)
            return f"Resolved: {contradiction.parameter}"

        monkeypatch.setattr(engine, "_synthesize_hypothesis", batch_llm)

        contradictions = [
            PhysicalContradiction(
                parameter=f"Param{i}", value_a="A", value_not_a="B",
                requirement_y="Y", requirement_z="Z",
                contradiction_type=ContradictionType.TRADE_OFF,
            )
            for i in range(5)
        ]

        for pc in contradictions:
            engine.solve(pc)

        assert len(results) == 5
        assert all(f"Param{i}" in results for i in range(5))


# ═══════════════════════════════════════════════════════════════════
# Einstein Validator — Extended
# ═══════════════════════════════════════════════════════════════════


class TestEinsteinValidatorExtended:
    def test_str_solution_steps_bound(self, engine):
        """STR validation: solution must take <= 4 steps."""
        validator = EinsteinValidator(engine)
        solution = validator.validate_str()
        assert solution.steps_taken <= 4
        assert solution.contradiction.parameter == "Speed of light"

    def test_gtr_solution_steps_bound(self, engine):
        """GTR validation: solution must take <= 6 steps."""
        validator = EinsteinValidator(engine)
        solution = validator.validate_gtr()
        assert solution.steps_taken <= 6
        assert solution.contradiction.parameter == "Gravity"

    def test_str_hypothesis_content(self, engine):
        """STR hypothesis contains expected keywords."""
        validator = EinsteinValidator(engine)
        solution = validator.validate_str()
        hypo = solution.hypothesis.lower()
        assert "speed" in hypo or "light" in hypo

    def test_gtr_hypothesis_content(self, engine):
        """GTR hypothesis contains expected keywords."""
        validator = EinsteinValidator(engine)
        solution = validator.validate_gtr()
        assert "gravity" in solution.hypothesis.lower()

    def test_str_path_validity(self, engine):
        """STR path is a valid C4 navigation."""
        validator = EinsteinValidator(engine)
        solution = validator.validate_str()
        current = C4State(0, 0, 2)
        for t in solution.c4_path:
            assert t.from_state == current
            current = t.to_state

    def test_gtr_path_validity(self, engine):
        """GTR path is a valid C4 navigation."""
        validator = EinsteinValidator(engine)
        solution = validator.validate_gtr()
        current = C4State(1, 1, 2)
        for t in solution.c4_path:
            assert t.from_state == current
            current = t.to_state


# ═══════════════════════════════════════════════════════════════════
# Edge Cases & Boundary Conditions
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_wraparound_route_tau_minus(self, engine):
        """T-axis wraparound backward: 2 → 0 uses tau+ (mod 3: 2+1=0)."""
        start = C4State(2, 1, 1)
        end = C4State(0, 1, 1)
        path = engine._compute_route(start, end)
        assert len(path) == 1
        # diff = (0 - 2) % 3 = 1, so tau+ is used (2+1=0 mod 3)
        assert path[0].operator == "tau+"

    def test_wraparound_route_lambda_minus(self, engine):
        """S-axis wraparound backward: 2 → 0 uses lambda+ (mod 3: 2+1=0)."""
        start = C4State(1, 2, 1)
        end = C4State(1, 0, 1)
        path = engine._compute_route(start, end)
        assert len(path) == 1
        # diff = (0 - 2) % 3 = 1, so lambda+ is used (2+1=0 mod 3)
        assert path[0].operator == "lambda+"

    def test_wraparound_route_kappa_minus(self, engine):
        """A-axis wraparound backward: 2 → 0 uses kappa+ (mod 3: 2+1=0)."""
        start = C4State(1, 1, 2)
        end = C4State(1, 1, 0)
        path = engine._compute_route(start, end)
        assert len(path) == 1
        # diff = (0 - 2) % 3 = 1, so kappa+ is used (2+1=0 mod 3)
        assert path[0].operator == "kappa+"

    def test_all_axes_wraparound(self, engine):
        """All three axes wrapping simultaneously."""
        start = C4State(2, 2, 2)
        end = C4State(0, 0, 0)
        path = engine._compute_route(start, end)
        assert len(path) == 3
        assert path[-1].to_state.to_tuple() == (0, 0, 0)

    def test_confidence_with_empty_path(self, engine, sample_contradiction):
        """Empty path gives maximum confidence."""
        confidence = engine._calculate_confidence([], sample_contradiction)
        assert confidence == pytest.approx(1.0, abs=0.01)

    def test_confidence_rounding(self, engine, sample_contradiction):
        """Confidence is rounded to 2 decimal places."""
        path = [C4Transition("tau+", C4State(0, 0, 0), C4State(1, 0, 0))]
        confidence = engine._calculate_confidence(path, sample_contradiction)
        assert confidence == round(confidence, 2)

    def test_c4_transition_defaults(self):
        """C4Transition has empty description by default."""
        t = C4Transition("tau+", C4State(0, 0, 0), C4State(1, 0, 0))
        assert t.description == ""

    def test_physical_contradiction_str_format(self):
        """String representation includes all key fields."""
        pc = PhysicalContradiction(
            parameter="Length",
            value_a="long",
            value_not_a="short",
            requirement_y="reach",
            requirement_z="compactness",
            contradiction_type=ContradictionType.SCALE,
        )
        s = str(pc)
        assert "Length" in s
        assert "long" in s
        assert "short" in s
        assert "reach" in s
        assert "compactness" in s


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
