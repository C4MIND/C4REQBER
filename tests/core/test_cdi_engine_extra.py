"""
Additional tests for src/core/cdi_engine.py to reach 80%+ coverage.

Covers: CDIEngine edge cases, EinsteinValidator edge cases,
        all private methods, error paths.
"""
from __future__ import annotations

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
# PhysicalContradiction
# ═══════════════════════════════════════════════════════════════════


class TestPhysicalContradictionEdgeCases:
    def test_str_format(self):
        pc = PhysicalContradiction(
            parameter="Length",
            value_a="long",
            value_not_a="short",
            requirement_y="reach",
            requirement_z="portability",
            contradiction_type=ContradictionType.SCALE,
        )
        s = str(pc)
        assert "Length" in s
        assert "long" in s
        assert "short" in s
        assert "reach" in s
        assert "portability" in s

    def test_all_types(self):
        for ct in ContradictionType:
            pc = PhysicalContradiction(
                parameter="P", value_a="A", value_not_a="B",
                requirement_y="Y", requirement_z="Z",
                contradiction_type=ct,
            )
            assert pc.contradiction_type == ct


# ═══════════════════════════════════════════════════════════════════
# CDISolution
# ═══════════════════════════════════════════════════════════════════


class TestCDISolutionEdgeCases:
    def test_boundary_steps_6(self):
        pc = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.TRADE_OFF,
        )
        sol = CDISolution(
            hypothesis="Test", c4_path=[], steps_taken=6,
            contradiction=pc, confidence_score=0.5,
        )
        assert sol.steps_taken == 6

    def test_zero_steps(self):
        pc = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.TRADE_OFF,
        )
        sol = CDISolution(
            hypothesis="Test", c4_path=[], steps_taken=0,
            contradiction=pc, confidence_score=1.0,
        )
        assert sol.steps_taken == 0
        assert sol.confidence_score == 1.0


# ═══════════════════════════════════════════════════════════════════
# CDIEngine — Fingerprinting
# ═══════════════════════════════════════════════════════════════════


class TestCDIEngineFingerprintingEdgeCases:
    def test_all_type_mappings(self, engine):
        expected = {
            ContradictionType.TRADE_OFF: (1, 1, 2),
            ContradictionType.DUAL_REQUIREMENT: (1, 0, 1),
            ContradictionType.CONFLICTING_GOALS: (2, 2, 2),
            ContradictionType.TEMPORAL: (0, 1, 2),
            ContradictionType.SCALE: (1, 0, 2),
            ContradictionType.PERSPECTIVE: (1, 1, 0),
        }
        for ct, coords in expected.items():
            pc = PhysicalContradiction(
                parameter="P", value_a="A", value_not_a="B",
                requirement_y="Y", requirement_z="Z",
                contradiction_type=ct,
            )
            state = engine._fingerprint_contradiction(pc)
            assert state.to_tuple() == coords

    def test_fingerprint_default_unknown_type(self, engine):
        class FakeType:
            pass

        pc = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=FakeType(),  # type: ignore[arg-type]
        )
        state = engine._fingerprint_contradiction(pc)
        assert state.to_tuple() == (1, 1, 2)


# ═══════════════════════════════════════════════════════════════════
# CDIEngine — Route Computation
# ═══════════════════════════════════════════════════════════════════


class TestCDIEngineRouteComputation:
    def test_same_start_end(self, engine):
        start = C4State(1, 1, 1)
        end = C4State(1, 1, 1)
        path = engine._compute_route(start, end)
        assert len(path) == 0

    def test_one_axis_forward(self, engine):
        start = C4State(0, 1, 1)
        end = C4State(1, 1, 1)
        path = engine._compute_route(start, end)
        assert len(path) == 1
        assert path[0].operator == "tau+"

    def test_one_axis_backward(self, engine):
        start = C4State(1, 1, 1)
        end = C4State(0, 1, 1)
        path = engine._compute_route(start, end)
        assert len(path) == 1
        assert path[0].operator == "tau-"

    def test_two_axes(self, engine):
        start = C4State(0, 0, 1)
        end = C4State(1, 1, 1)
        path = engine._compute_route(start, end)
        assert len(path) == 2
        assert path[-1].to_state.to_tuple() == end.to_tuple()

    def test_three_axes(self, engine):
        start = C4State(0, 0, 0)
        end = C4State(2, 2, 2)
        path = engine._compute_route(start, end)
        assert len(path) == 3
        assert path[-1].to_state.to_tuple() == (2, 2, 2)

    def test_wraparound_backward(self, engine):
        start = C4State(2, 2, 2)
        end = C4State(0, 0, 0)
        path = engine._compute_route(start, end)
        assert len(path) == 3
        assert path[-1].to_state.to_tuple() == (0, 0, 0)

    def test_wraparound_mixed(self, engine):
        start = C4State(2, 0, 1)
        end = C4State(0, 2, 0)
        path = engine._compute_route(start, end)
        assert len(path) == 3
        assert path[-1].to_state.to_tuple() == (0, 2, 0)

    def test_path_validity(self, engine):
        start = C4State(0, 0, 0)
        end = C4State(2, 2, 2)
        path = engine._compute_route(start, end)
        current = start
        for transition in path:
            assert transition.from_state == current
            current = transition.to_state
        assert current == end

    def test_path_operators_valid(self, engine):
        start = C4State(0, 0, 0)
        end = C4State(2, 2, 2)
        path = engine._compute_route(start, end)
        valid_ops = {"tau+", "tau-", "lambda+", "lambda-", "kappa+", "kappa-"}
        for t in path:
            assert t.operator in valid_ops


# ═══════════════════════════════════════════════════════════════════
# CDIEngine — Path Execution
# ═══════════════════════════════════════════════════════════════════


class TestCDIEngineExecutePath:
    def test_empty_path(self, engine):
        start = C4State(1, 1, 1)
        result = engine._execute_path(start, [])
        assert result == start

    def test_single_transition(self, engine):
        start = C4State(0, 0, 0)
        path = [C4Transition("tau+", start, C4State(1, 0, 0))]
        result = engine._execute_path(start, path)
        assert result.to_tuple() == (1, 0, 0)

    def test_multiple_transitions(self, engine):
        start = C4State(0, 0, 0)
        path = [
            C4Transition("tau+", C4State(0, 0, 0), C4State(1, 0, 0)),
            C4Transition("lambda+", C4State(1, 0, 0), C4State(1, 1, 0)),
            C4Transition("kappa+", C4State(1, 1, 0), C4State(1, 1, 1)),
        ]
        result = engine._execute_path(start, path)
        assert result.to_tuple() == (1, 1, 1)


# ═══════════════════════════════════════════════════════════════════
# CDIEngine — Hypothesis Synthesis
# ═══════════════════════════════════════════════════════════════════


class TestCDIEngineSynthesizeHypothesis:
    def test_includes_parameter(self, engine):
        pc = PhysicalContradiction(
            parameter="Length", value_a="long", value_not_a="short",
            requirement_y="reach", requirement_z="portability",
            contradiction_type=ContradictionType.TRADE_OFF,
        )
        final = C4State(2, 2, 2)
        path = [C4Transition("tau+", C4State(1, 1, 2), C4State(2, 1, 2))]
        hypo = engine._synthesize_hypothesis(pc, final, path)
        assert "Length" in hypo
        assert "tau+" in hypo
        assert str(final) in hypo

    def test_empty_path(self, engine):
        pc = PhysicalContradiction(
            parameter="X", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.TRADE_OFF,
        )
        final = C4State(1, 1, 2)
        hypo = engine._synthesize_hypothesis(pc, final, [])
        assert "X" in hypo
        assert "Final perspective" in hypo

    def test_multiple_operators(self, engine):
        pc = PhysicalContradiction(
            parameter="Weight", value_a="light", value_not_a="heavy",
            requirement_y="portability", requirement_z="durability",
            contradiction_type=ContradictionType.TRADE_OFF,
        )
        final = C4State(2, 2, 2)
        path = [
            C4Transition("tau+", C4State(1, 1, 2), C4State(2, 1, 2)),
            C4Transition("lambda+", C4State(2, 1, 2), C4State(2, 2, 2)),
        ]
        hypo = engine._synthesize_hypothesis(pc, final, path)
        assert "tau+, lambda+" in hypo


# ═══════════════════════════════════════════════════════════════════
# CDIEngine — Confidence Calculation
# ═══════════════════════════════════════════════════════════════════


class TestCDIEngineCalculateConfidence:
    def test_empty_path(self, engine, sample_contradiction):
        confidence = engine._calculate_confidence([], sample_contradiction)
        assert confidence == pytest.approx(1.0, abs=0.01)

    def test_full_path(self, engine, sample_contradiction):
        path = [
            C4Transition("tau+", C4State(0, 0, 0), C4State(1, 0, 0)),
            C4Transition("lambda+", C4State(1, 0, 0), C4State(1, 1, 0)),
            C4Transition("kappa+", C4State(1, 1, 0), C4State(1, 1, 1)),
        ]
        confidence = engine._calculate_confidence(path, sample_contradiction)
        assert 0.0 <= confidence <= 1.0
        assert confidence == pytest.approx(0.75, abs=0.01)

    def test_rounded_to_two_decimals(self, engine, sample_contradiction):
        path = [C4Transition("tau+", C4State(0, 0, 0), C4State(1, 0, 0))]
        confidence = engine._calculate_confidence(path, sample_contradiction)
        assert confidence == round(confidence, 2)

    def test_shorter_path_higher_confidence(self, engine, sample_contradiction):
        short_path = [C4Transition("tau+", C4State(0, 0, 0), C4State(1, 0, 0))]
        long_path = [
            C4Transition("tau+", C4State(0, 0, 0), C4State(1, 0, 0)),
            C4Transition("lambda+", C4State(1, 0, 0), C4State(1, 1, 0)),
        ]
        c_short = engine._calculate_confidence(short_path, sample_contradiction)
        c_long = engine._calculate_confidence(long_path, sample_contradiction)
        assert c_short > c_long

    def test_six_step_path(self, engine, sample_contradiction):
        path = [
            C4Transition("tau+", C4State(0, 0, 0), C4State(1, 0, 0)),
            C4Transition("tau+", C4State(1, 0, 0), C4State(2, 0, 0)),
            C4Transition("lambda+", C4State(2, 0, 0), C4State(2, 1, 0)),
            C4Transition("lambda+", C4State(2, 1, 0), C4State(2, 2, 0)),
            C4Transition("kappa+", C4State(2, 2, 0), C4State(2, 2, 1)),
            C4Transition("kappa+", C4State(2, 2, 1), C4State(2, 2, 2)),
        ]
        confidence = engine._calculate_confidence(path, sample_contradiction)
        assert confidence == pytest.approx(0.5, abs=0.01)


# ═══════════════════════════════════════════════════════════════════
# CDIEngine — Full Solve Pipeline
# ═══════════════════════════════════════════════════════════════════


class TestCDIEngineSolveEdgeCases:
    def test_solve_all_contradiction_types(self, engine):
        for ct in ContradictionType:
            pc = PhysicalContradiction(
                parameter="P", value_a="A", value_not_a="B",
                requirement_y="Y", requirement_z="Z",
                contradiction_type=ct,
            )
            solution = engine.solve(pc)
            assert isinstance(solution, CDISolution)
            assert solution.steps_taken <= 6
            assert 0.0 <= solution.confidence_score <= 1.0

    def test_solve_same_start_end(self, engine):
        pc = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.CONFLICTING_GOALS,
        )
        start = C4State(2, 2, 2)
        solution = engine.solve(pc, start)
        assert solution.steps_taken == 0
        assert solution.confidence_score == 1.0

    def test_solve_returns_path(self, engine, sample_contradiction):
        solution = engine.solve(sample_contradiction)
        assert isinstance(solution.c4_path, list)
        for transition in solution.c4_path:
            assert isinstance(transition, C4Transition)

    def test_solve_hypothesis_non_empty(self, engine, sample_contradiction):
        solution = engine.solve(sample_contradiction)
        assert len(solution.hypothesis) > 0

    def test_solve_with_custom_state(self, engine):
        pc = PhysicalContradiction(
            parameter="Cost", value_a="low", value_not_a="high",
            requirement_y="affordability", requirement_z="quality",
            contradiction_type=ContradictionType.DUAL_REQUIREMENT,
        )
        start = C4State(0, 0, 0)
        solution = engine.solve(pc, start)
        assert solution.steps_taken <= 6
        if solution.c4_path:
            assert solution.c4_path[0].from_state == start


# ═══════════════════════════════════════════════════════════════════
# EinsteinValidator
# ═══════════════════════════════════════════════════════════════════


class TestEinsteinValidatorEdgeCases:
    def test_str_start_state(self, engine):
        validator = EinsteinValidator(engine)
        solution = validator.validate_str()
        assert solution.c4_path[0].from_state.to_tuple() == (0, 0, 2)

    def test_gtr_start_state(self, engine):
        validator = EinsteinValidator(engine)
        solution = validator.validate_gtr()
        assert solution.c4_path[0].from_state.to_tuple() == (1, 1, 2)

    def test_str_contradiction_type(self, engine):
        validator = EinsteinValidator(engine)
        solution = validator.validate_str()
        assert solution.contradiction.contradiction_type == ContradictionType.CONFLICTING_GOALS

    def test_gtr_contradiction_type(self, engine):
        validator = EinsteinValidator(engine)
        solution = validator.validate_gtr()
        assert solution.contradiction.contradiction_type == ContradictionType.CONFLICTING_GOALS

    def test_str_hypothesis_contains_speed(self, engine):
        validator = EinsteinValidator(engine)
        solution = validator.validate_str()
        hypo_lower = solution.hypothesis.lower()
        assert "speed" in hypo_lower or "light" in hypo_lower

    def test_gtr_hypothesis_contains_gravity(self, engine):
        validator = EinsteinValidator(engine)
        solution = validator.validate_gtr()
        assert "gravity" in solution.hypothesis.lower()

    def test_str_assertion_fails_if_too_long(self, engine, monkeypatch):
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

    def test_gtr_assertion_fails_if_too_long(self, engine, monkeypatch):
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
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def engine():
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
