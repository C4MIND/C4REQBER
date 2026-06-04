"""
Comprehensive tests for src/core/cdi_engine.py

Covers: CDIEngine initialization, solve pipeline, state management,
        PhysicalContradiction, CDISolution, C4Transition, EinsteinValidator
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
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def engine():
    """Fresh CDIEngine instance."""
    return CDIEngine()


@pytest.fixture
def sample_contradiction():
    """A generic physical contradiction for testing."""
    return PhysicalContradiction(
        parameter="Weight",
        value_a="light",
        value_not_a="heavy",
        requirement_y="portability",
        requirement_z="durability",
        contradiction_type=ContradictionType.TRADE_OFF,
    )


@pytest.fixture
def all_contradiction_types():
    """All contradiction types with expected fingerprint mappings."""
    return [
        (ContradictionType.TRADE_OFF, (1, 1, 2)),
        (ContradictionType.DUAL_REQUIREMENT, (1, 0, 1)),
        (ContradictionType.CONFLICTING_GOALS, (2, 2, 2)),
        (ContradictionType.TEMPORAL, (0, 1, 2)),
        (ContradictionType.SCALE, (1, 0, 2)),
        (ContradictionType.PERSPECTIVE, (1, 1, 0)),
    ]


# ═══════════════════════════════════════════════════════════════════
# PhysicalContradiction
# ═══════════════════════════════════════════════════════════════════


class TestPhysicalContradiction:
    def test_creation(self):
        pc = PhysicalContradiction(
            parameter="Speed",
            value_a="fast",
            value_not_a="slow",
            requirement_y="performance",
            requirement_z="safety",
            contradiction_type=ContradictionType.TRADE_OFF,
        )
        assert pc.parameter == "Speed"
        assert pc.value_a == "fast"
        assert pc.value_not_a == "slow"
        assert pc.requirement_y == "performance"
        assert pc.requirement_z == "safety"
        assert pc.contradiction_type == ContradictionType.TRADE_OFF

    def test_str_representation(self):
        pc = PhysicalContradiction(
            parameter="Size",
            value_a="big",
            value_not_a="small",
            requirement_y="capacity",
            requirement_z="portability",
            contradiction_type=ContradictionType.SCALE,
        )
        result = str(pc)
        assert "Size" in result
        assert "big" in result
        assert "small" in result
        assert "capacity" in result
        assert "portability" in result

    def test_all_types_exist(self):
        types = list(ContradictionType)
        assert len(types) == 6
        assert ContradictionType.TRADE_OFF in types
        assert ContradictionType.PERSPECTIVE in types


# ═══════════════════════════════════════════════════════════════════
# CDISolution
# ═══════════════════════════════════════════════════════════════════


class TestCDISolution:
    def test_creation_valid(self, sample_contradiction):
        solution = CDISolution(
            hypothesis="Test hypothesis",
            c4_path=[],
            steps_taken=3,
            contradiction=sample_contradiction,
            confidence_score=0.85,
        )
        assert solution.hypothesis == "Test hypothesis"
        assert solution.steps_taken == 3
        assert solution.confidence_score == 0.85
        assert solution.c4_path == []

    def test_theorem_11_violation_raises(self, sample_contradiction):
        with pytest.raises(AssertionError, match="Theorem 11 violated"):
            CDISolution(
                hypothesis="Test",
                c4_path=[],
                steps_taken=7,
                contradiction=sample_contradiction,
                confidence_score=0.5,
            )

    def test_theorem_11_boundary_ok(self, sample_contradiction):
        for steps in [0, 1, 3, 6]:
            sol = CDISolution(
                hypothesis="Test",
                c4_path=[],
                steps_taken=steps,
                contradiction=sample_contradiction,
                confidence_score=0.5,
            )
            assert sol.steps_taken == steps

    def test_steps_taken_zero(self, sample_contradiction):
        sol = CDISolution(
            hypothesis="No steps needed",
            c4_path=[],
            steps_taken=0,
            contradiction=sample_contradiction,
            confidence_score=1.0,
        )
        assert sol.steps_taken == 0


# ═══════════════════════════════════════════════════════════════════
# C4Transition
# ═══════════════════════════════════════════════════════════════════


class TestC4Transition:
    def test_creation(self):
        t = C4Transition(
            operator="tau+",
            from_state=C4State(0, 0, 0),
            to_state=C4State(1, 0, 0),
            description="Time forward",
        )
        assert t.operator == "tau+"
        assert t.from_state.to_tuple() == (0, 0, 0)
        assert t.to_state.to_tuple() == (1, 0, 0)
        assert t.description == "Time forward"

    def test_default_description(self):
        t = C4Transition("lambda+", C4State(0, 0, 0), C4State(0, 1, 0))
        assert t.description == ""


# ═══════════════════════════════════════════════════════════════════
# CDIEngine — Initialization
# ═══════════════════════════════════════════════════════════════════


class TestCDIEngineInitialization:
    def test_init_creates_components(self, engine):
        assert engine.c4_space is not None
        assert engine.operators is not None

    def test_init_fresh_instances(self):
        e1 = CDIEngine()
        e2 = CDIEngine()
        assert e1 is not e2
        assert e1.c4_space is not e2.c4_space


# ═══════════════════════════════════════════════════════════════════
# CDIEngine — Fingerprinting
# ═══════════════════════════════════════════════════════════════════


class TestCDIEngineFingerprinting:
    def test_fingerprint_all_types(self, engine, all_contradiction_types):
        for ct_type, expected_coords in all_contradiction_types:
            pc = PhysicalContradiction(
                parameter="P", value_a="A", value_not_a="B",
                requirement_y="Y", requirement_z="Z",
                contradiction_type=ct_type,
            )
            state = engine._fingerprint_contradiction(pc)
            assert state.to_tuple() == expected_coords, f"Failed for {ct_type}"

    def test_fingerprint_default_for_unknown(self, engine):
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
# CDIEngine — Solution Region Prediction
# ═══════════════════════════════════════════════════════════════════


class TestCDIEnginePredictSolutionRegion:
    def test_always_returns_future_meta_system(self, engine):
        for ct in ContradictionType:
            pc = PhysicalContradiction(
                parameter="P", value_a="A", value_not_a="B",
                requirement_y="Y", requirement_z="Z",
                contradiction_type=ct,
            )
            target = engine._predict_solution_region(pc)
            assert target.to_tuple() == (2, 2, 2)


# ═══════════════════════════════════════════════════════════════════
# CDIEngine — Route Computation
# ═══════════════════════════════════════════════════════════════════


class TestCDIEngineComputeRoute:
    def test_same_start_end(self, engine):
        start = C4State(1, 1, 1)
        end = C4State(1, 1, 1)
        path = engine._compute_route(start, end)
        assert len(path) == 0

    def test_one_axis_diff(self, engine):
        start = C4State(0, 1, 1)
        end = C4State(1, 1, 1)
        path = engine._compute_route(start, end)
        assert len(path) == 1
        assert path[0].operator == "tau+"
        assert path[0].to_state.to_tuple() == (1, 1, 1)

    def test_two_axes_diff(self, engine):
        start = C4State(0, 0, 1)
        end = C4State(1, 1, 1)
        path = engine._compute_route(start, end)
        assert len(path) == 2
        assert path[-1].to_state.to_tuple() == (1, 1, 1)

    def test_three_axes_diff(self, engine):
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


# ═══════════════════════════════════════════════════════════════════
# CDIEngine — Path Execution
# ═══════════════════════════════════════════════════════════════════


class TestCDIEngineExecutePath:
    def test_empty_path_returns_start(self, engine):
        start = C4State(1, 1, 1)
        result = engine._execute_path(start, [])
        assert result == start

    def test_path_returns_final_state(self, engine):
        start = C4State(0, 0, 0)
        path = [
            C4Transition("tau+", C4State(0, 0, 0), C4State(1, 0, 0)),
            C4Transition("lambda+", C4State(1, 0, 0), C4State(1, 1, 0)),
        ]
        result = engine._execute_path(start, path)
        assert result.to_tuple() == (1, 1, 0)


# ═══════════════════════════════════════════════════════════════════
# CDIEngine — Hypothesis Synthesis
# ═══════════════════════════════════════════════════════════════════


class TestCDIEngineSynthesizeHypothesis:
    def test_includes_parameter(self, engine):
        pc = PhysicalContradiction(
            parameter="Length", value_a="long", value_not_a="short",
            requirement_y="reach", requirement_z="compactness",
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


# ═══════════════════════════════════════════════════════════════════
# CDIEngine — Confidence Calculation
# ═══════════════════════════════════════════════════════════════════


class TestCDIEngineCalculateConfidence:
    def test_empty_path(self, engine, sample_contradiction):
        confidence = engine._calculate_confidence([], sample_contradiction)
        assert confidence == pytest.approx(1.0, 0.01)

    def test_full_path(self, engine, sample_contradiction):
        path = [
            C4Transition("tau+", C4State(0, 0, 0), C4State(1, 0, 0)),
            C4Transition("lambda+", C4State(1, 0, 0), C4State(1, 1, 0)),
            C4Transition("kappa+", C4State(1, 1, 0), C4State(1, 1, 1)),
        ]
        confidence = engine._calculate_confidence(path, sample_contradiction)
        assert 0.0 <= confidence <= 1.0
        assert confidence == pytest.approx(0.75, 0.01)

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


# ═══════════════════════════════════════════════════════════════════
# CDIEngine — Full Solve Pipeline
# ═══════════════════════════════════════════════════════════════════


class TestCDIEngineSolve:
    def test_solve_returns_solution(self, engine, sample_contradiction):
        solution = engine.solve(sample_contradiction)
        assert isinstance(solution, CDISolution)
        assert solution.steps_taken <= 6
        assert 0.0 <= solution.confidence_score <= 1.0
        assert len(solution.hypothesis) > 0

    def test_solve_with_custom_state(self, engine, sample_contradiction):
        start = C4State(0, 0, 0)
        solution = engine.solve(sample_contradiction, start)
        assert solution.steps_taken <= 6
        if solution.c4_path:
            assert solution.c4_path[0].from_state == start

    def test_solve_no_state_uses_fingerprint(self, engine):
        pc = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.CONFLICTING_GOALS,
        )
        solution = engine.solve(pc)
        assert solution.steps_taken <= 6

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


# ═══════════════════════════════════════════════════════════════════
# EinsteinValidator
# ═══════════════════════════════════════════════════════════════════


class TestEinsteinValidator:
    def test_str_validation(self, engine):
        validator = EinsteinValidator(engine)
        solution = validator.validate_str()
        assert solution.steps_taken <= 4
        assert "speed" in solution.hypothesis.lower() or "light" in solution.hypothesis.lower()
        assert solution.contradiction.contradiction_type == ContradictionType.CONFLICTING_GOALS

    def test_gtr_validation(self, engine):
        validator = EinsteinValidator(engine)
        solution = validator.validate_gtr()
        assert solution.steps_taken <= 6
        assert "gravity" in solution.hypothesis.lower()
        assert solution.contradiction.contradiction_type == ContradictionType.CONFLICTING_GOALS

    def test_str_start_state(self, engine):
        validator = EinsteinValidator(engine)
        solution = validator.validate_str()
        assert solution.c4_path[0].from_state.to_tuple() == (0, 0, 2)

    def test_gtr_start_state(self, engine):
        validator = EinsteinValidator(engine)
        solution = validator.validate_gtr()
        assert solution.c4_path[0].from_state.to_tuple() == (1, 1, 2)

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
