"""
Extended tests for CDI Engine (src/core/cdi_engine.py)

Targets: initialization, contradiction resolution, C4 navigation,
hypothesis generation, confidence calculation.
Goal: 85%+ coverage.
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
# Initialization
# ═══════════════════════════════════════════════════════════════════


class TestCDIEngineInitialization:
    def test_engine_creates_c4_space(self):
        engine = CDIEngine()
        assert engine.c4_space is not None
        assert len(engine.c4_space.states) == 27

    def test_engine_creates_operators(self):
        engine = CDIEngine()
        assert engine.operators is not None
        assert len(engine.operators.all) >= 27


# ═══════════════════════════════════════════════════════════════════
# Contradiction Resolution
# ═══════════════════════════════════════════════════════════════════


class TestContradictionResolution:
    def test_solve_trade_off(self):
        engine = CDIEngine()
        contradiction = PhysicalContradiction(
            parameter="Weight",
            value_a="light",
            value_not_a="heavy",
            requirement_y="portability",
            requirement_z="durability",
            contradiction_type=ContradictionType.TRADE_OFF,
        )
        solution = engine.solve(contradiction)
        assert isinstance(solution, CDISolution)
        assert solution.steps_taken <= 6
        assert 0.0 <= solution.confidence_score <= 1.0
        assert len(solution.hypothesis) > 0
        assert solution.contradiction == contradiction

    def test_solve_dual_requirement(self):
        engine = CDIEngine()
        contradiction = PhysicalContradiction(
            parameter="Cost",
            value_a="low",
            value_not_a="high",
            requirement_y="affordability",
            requirement_z="quality",
            contradiction_type=ContradictionType.DUAL_REQUIREMENT,
        )
        solution = engine.solve(contradiction)
        assert solution.steps_taken <= 6
        assert solution.confidence_score > 0.0

    def test_solve_conflicting_goals(self):
        engine = CDIEngine()
        contradiction = PhysicalContradiction(
            parameter="Speed",
            value_a="fast",
            value_not_a="slow",
            requirement_y="performance",
            requirement_z="safety",
            contradiction_type=ContradictionType.CONFLICTING_GOALS,
        )
        solution = engine.solve(contradiction)
        assert solution.steps_taken <= 6

    def test_solve_temporal(self):
        engine = CDIEngine()
        contradiction = PhysicalContradiction(
            parameter="Timing",
            value_a="now",
            value_not_a="later",
            requirement_y="urgency",
            requirement_z="quality",
            contradiction_type=ContradictionType.TEMPORAL,
        )
        solution = engine.solve(contradiction)
        assert solution.steps_taken <= 6

    def test_solve_scale(self):
        engine = CDIEngine()
        contradiction = PhysicalContradiction(
            parameter="Size",
            value_a="big",
            value_not_a="small",
            requirement_y="capacity",
            requirement_z="portability",
            contradiction_type=ContradictionType.SCALE,
        )
        solution = engine.solve(contradiction)
        assert solution.steps_taken <= 6

    def test_solve_perspective(self):
        engine = CDIEngine()
        contradiction = PhysicalContradiction(
            parameter="Viewpoint",
            value_a="user",
            value_not_a="developer",
            requirement_y="usability",
            requirement_z="maintainability",
            contradiction_type=ContradictionType.PERSPECTIVE,
        )
        solution = engine.solve(contradiction)
        assert solution.steps_taken <= 6

    def test_solve_default_fingerprint(self):
        """When no state provided, engine fingerprints from contradiction type."""
        engine = CDIEngine()
        contradiction = PhysicalContradiction(
            parameter="P",
            value_a="A",
            value_not_a="B",
            requirement_y="Y",
            requirement_z="Z",
            contradiction_type=ContradictionType.TRADE_OFF,
        )
        solution = engine.solve(contradiction)
        # TRADE_OFF maps to C4State(T=1, S=1, A=2)
        assert solution.c4_path[0].from_state.to_tuple() == (1, 1, 2)


# ═══════════════════════════════════════════════════════════════════
# C4 Navigation
# ═══════════════════════════════════════════════════════════════════


class TestC4Navigation:
    def test_compute_route_zero_steps(self):
        engine = CDIEngine()
        start = C4State(T=2, S=2, A=2)
        end = C4State(T=2, S=2, A=2)
        path = engine._compute_route(start, end)
        assert len(path) == 0

    def test_compute_route_one_axis(self):
        engine = CDIEngine()
        start = C4State(T=0, S=2, A=2)
        end = C4State(T=2, S=2, A=2)
        path = engine._compute_route(start, end)
        assert len(path) == 1
        assert path[0].operator in ("tau+", "tau-")
        assert path[0].to_state.to_tuple() == end.to_tuple()

    def test_compute_route_two_axes(self):
        engine = CDIEngine()
        start = C4State(T=0, S=0, A=2)
        end = C4State(T=2, S=2, A=2)
        path = engine._compute_route(start, end)
        assert len(path) == 2
        assert path[-1].to_state.to_tuple() == end.to_tuple()

    def test_compute_route_all_axes(self):
        engine = CDIEngine()
        start = C4State(T=0, S=0, A=0)
        end = C4State(T=2, S=2, A=2)
        path = engine._compute_route(start, end)
        assert len(path) == 3
        assert path[-1].to_state.to_tuple() == end.to_tuple()

    def test_compute_route_wrap_tau_minus(self):
        """T diff = 2 means tau- (backward) is shorter."""
        engine = CDIEngine()
        start = C4State(T=0, S=1, A=1)
        end = C4State(T=2, S=1, A=1)
        path = engine._compute_route(start, end)
        assert len(path) == 1
        assert path[0].operator == "tau-"

    def test_compute_route_wrap_lambda_minus(self):
        engine = CDIEngine()
        start = C4State(T=1, S=0, A=1)
        end = C4State(T=1, S=2, A=1)
        path = engine._compute_route(start, end)
        assert len(path) == 1
        assert path[0].operator == "lambda-"

    def test_compute_route_wrap_kappa_minus(self):
        engine = CDIEngine()
        start = C4State(T=1, S=1, A=0)
        end = C4State(T=1, S=1, A=2)
        path = engine._compute_route(start, end)
        assert len(path) == 1
        assert path[0].operator == "kappa-"

    def test_execute_path_empty(self):
        engine = CDIEngine()
        start = C4State(T=1, S=1, A=1)
        result = engine._execute_path(start, [])
        assert result == start

    def test_execute_path_nonempty(self):
        engine = CDIEngine()
        start = C4State(T=0, S=0, A=0)
        path = [
            C4Transition("tau+", C4State(0, 0, 0), C4State(1, 0, 0)),
            C4Transition("lambda+", C4State(1, 0, 0), C4State(1, 1, 0)),
        ]
        result = engine._execute_path(start, path)
        assert result.to_tuple() == (1, 1, 0)


# ═══════════════════════════════════════════════════════════════════
# Hypothesis Generation
# ═══════════════════════════════════════════════════════════════════


class TestHypothesisGeneration:
    def test_synthesize_empty_path(self):
        engine = CDIEngine()
        contradiction = PhysicalContradiction(
            parameter="X",
            value_a="A",
            value_not_a="B",
            requirement_y="Y",
            requirement_z="Z",
            contradiction_type=ContradictionType.TRADE_OFF,
        )
        final_state = C4State(T=2, S=2, A=2)
        hypothesis = engine._synthesize_hypothesis(contradiction, final_state, [])
        assert "X" in hypothesis
        assert "Final perspective" in hypothesis

    def test_synthesize_with_operators(self):
        engine = CDIEngine()
        contradiction = PhysicalContradiction(
            parameter="Speed",
            value_a="fast",
            value_not_a="slow",
            requirement_y="perf",
            requirement_z="safe",
            contradiction_type=ContradictionType.TRADE_OFF,
        )
        final_state = C4State(T=2, S=2, A=2)
        path = [
            C4Transition("tau+", C4State(1, 1, 2), C4State(2, 1, 2)),
            C4Transition("lambda+", C4State(2, 1, 2), C4State(2, 2, 2)),
        ]
        hypothesis = engine._synthesize_hypothesis(contradiction, final_state, path)
        assert "tau+" in hypothesis
        assert "lambda+" in hypothesis
        assert "Speed" in hypothesis


# ═══════════════════════════════════════════════════════════════════
# Confidence Calculation
# ═══════════════════════════════════════════════════════════════════


class TestConfidenceCalculation:
    def test_confidence_zero_steps(self):
        engine = CDIEngine()
        path = []
        contradiction = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.TRADE_OFF,
        )
        confidence = engine._calculate_confidence(path, contradiction)
        assert confidence == 1.0

    def test_confidence_three_steps(self):
        engine = CDIEngine()
        path = [
            C4Transition("tau+", C4State(0, 0, 0), C4State(1, 0, 0)),
            C4Transition("lambda+", C4State(1, 0, 0), C4State(1, 1, 0)),
            C4Transition("kappa+", C4State(1, 1, 0), C4State(1, 1, 1)),
        ]
        contradiction = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.TRADE_OFF,
        )
        confidence = engine._calculate_confidence(path, contradiction)
        assert confidence == round(0.5 + 0.5 * (1 - 3 / 6), 2)

    def test_confidence_six_steps(self):
        engine = CDIEngine()
        path = [
            C4Transition("tau+", C4State(0, 0, 0), C4State(1, 0, 0)),
            C4Transition("tau+", C4State(1, 0, 0), C4State(2, 0, 0)),
            C4Transition("lambda+", C4State(2, 0, 0), C4State(2, 1, 0)),
            C4Transition("lambda+", C4State(2, 1, 0), C4State(2, 2, 0)),
            C4Transition("kappa+", C4State(2, 2, 0), C4State(2, 2, 1)),
            C4Transition("kappa+", C4State(2, 2, 1), C4State(2, 2, 2)),
        ]
        contradiction = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.TRADE_OFF,
        )
        confidence = engine._calculate_confidence(path, contradiction)
        assert confidence == round(0.5 + 0.5 * 0.0, 2)

    def test_confidence_rounded_to_two_decimals(self):
        engine = CDIEngine()
        path = [C4Transition("tau+", C4State(0, 0, 0), C4State(1, 0, 0))]
        contradiction = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.TRADE_OFF,
        )
        confidence = engine._calculate_confidence(path, contradiction)
        assert confidence == round(confidence, 2)


# ═══════════════════════════════════════════════════════════════════
# Einstein Validator
# ═══════════════════════════════════════════════════════════════════


class TestEinsteinValidatorExtended:
    def test_str_steps_bound(self):
        engine = CDIEngine()
        validator = EinsteinValidator(engine)
        solution = validator.validate_str()
        assert solution.steps_taken <= 4

    def test_gtr_steps_bound(self):
        engine = CDIEngine()
        validator = EinsteinValidator(engine)
        solution = validator.validate_gtr()
        assert solution.steps_taken <= 6

    def test_str_hypothesis_content(self):
        engine = CDIEngine()
        validator = EinsteinValidator(engine)
        solution = validator.validate_str()
        assert "speed" in solution.hypothesis.lower() or "light" in solution.hypothesis.lower()

    def test_gtr_hypothesis_content(self):
        engine = CDIEngine()
        validator = EinsteinValidator(engine)
        solution = validator.validate_gtr()
        assert "gravity" in solution.hypothesis.lower()

    def test_str_start_state_tuple(self):
        engine = CDIEngine()
        validator = EinsteinValidator(engine)
        solution = validator.validate_str()
        assert solution.c4_path[0].from_state.to_tuple() == (0, 0, 2)

    def test_gtr_start_state_tuple(self):
        engine = CDIEngine()
        validator = EinsteinValidator(engine)
        solution = validator.validate_gtr()
        assert solution.c4_path[0].from_state.to_tuple() == (1, 1, 2)

    def test_str_contradiction_fields(self):
        engine = CDIEngine()
        validator = EinsteinValidator(engine)
        solution = validator.validate_str()
        assert solution.contradiction.parameter == "Speed of light"
        assert "relative" in solution.contradiction.value_a.lower()
        assert "constant" in solution.contradiction.value_not_a.lower()

    def test_gtr_contradiction_fields(self):
        engine = CDIEngine()
        validator = EinsteinValidator(engine)
        solution = validator.validate_gtr()
        assert solution.contradiction.parameter == "Gravity"
        assert "instantaneous" in solution.contradiction.value_a.lower()
        assert "geometric" in solution.contradiction.value_not_a.lower()


# ═══════════════════════════════════════════════════════════════════
# Fingerprint Mapping
# ═══════════════════════════════════════════════════════════════════


class TestFingerprintMapping:
    def test_trade_off_mapping(self):
        engine = CDIEngine()
        pc = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.TRADE_OFF,
        )
        state = engine._fingerprint_contradiction(pc)
        assert state.to_tuple() == (1, 1, 2)

    def test_dual_requirement_mapping(self):
        engine = CDIEngine()
        pc = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.DUAL_REQUIREMENT,
        )
        state = engine._fingerprint_contradiction(pc)
        assert state.to_tuple() == (1, 0, 1)

    def test_conflicting_goals_mapping(self):
        engine = CDIEngine()
        pc = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.CONFLICTING_GOALS,
        )
        state = engine._fingerprint_contradiction(pc)
        assert state.to_tuple() == (2, 2, 2)

    def test_temporal_mapping(self):
        engine = CDIEngine()
        pc = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.TEMPORAL,
        )
        state = engine._fingerprint_contradiction(pc)
        assert state.to_tuple() == (0, 1, 2)

    def test_scale_mapping(self):
        engine = CDIEngine()
        pc = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.SCALE,
        )
        state = engine._fingerprint_contradiction(pc)
        assert state.to_tuple() == (1, 0, 2)

    def test_perspective_mapping(self):
        engine = CDIEngine()
        pc = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.PERSPECTIVE,
        )
        state = engine._fingerprint_contradiction(pc)
        assert state.to_tuple() == (1, 1, 0)

    def test_unknown_type_defaults(self):
        engine = CDIEngine()
        # Create a contradiction with an unknown type by bypassing enum
        pc = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=None,  # type: ignore[arg-type]
        )
        state = engine._fingerprint_contradiction(pc)
        assert state.to_tuple() == (1, 1, 2)


# ═══════════════════════════════════════════════════════════════════
# Predict Solution Region
# ═══════════════════════════════════════════════════════════════════


class TestPredictSolutionRegion:
    def test_always_returns_future_meta_system(self):
        engine = CDIEngine()
        for ct in ContradictionType:
            pc = PhysicalContradiction(
                parameter="P", value_a="A", value_not_a="B",
                requirement_y="Y", requirement_z="Z",
                contradiction_type=ct,
            )
            target = engine._predict_solution_region(pc)
            assert target.to_tuple() == (2, 2, 2)


# ═══════════════════════════════════════════════════════════════════
# CDISolution Post-Init
# ═══════════════════════════════════════════════════════════════════


class TestCDISolutionPostInit:
    def test_valid_steps_accepted(self):
        pc = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.TRADE_OFF,
        )
        for steps in range(7):
            solution = CDISolution(
                hypothesis="H", c4_path=[], steps_taken=steps,
                contradiction=pc, confidence_score=0.5,
            )
            assert solution.steps_taken == steps

    def test_invalid_steps_rejected(self):
        pc = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.TRADE_OFF,
        )
        with pytest.raises(AssertionError):
            CDISolution(
                hypothesis="H", c4_path=[], steps_taken=7,
                contradiction=pc, confidence_score=0.5,
            )

    def test_boundary_steps_six_accepted(self):
        pc = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.TRADE_OFF,
        )
        solution = CDISolution(
            hypothesis="H", c4_path=[], steps_taken=6,
            contradiction=pc, confidence_score=0.5,
        )
        assert solution.steps_taken == 6


# ═══════════════════════════════════════════════════════════════════
# PhysicalContradiction
# ═══════════════════════════════════════════════════════════════════


class TestPhysicalContradictionStr:
    def test_str_format(self):
        pc = PhysicalContradiction(
            parameter="Temperature",
            value_a="hot",
            value_not_a="cold",
            requirement_y="comfort",
            requirement_z="preservation",
            contradiction_type=ContradictionType.TRADE_OFF,
        )
        s = str(pc)
        assert "Temperature" in s
        assert "hot" in s
        assert "cold" in s
        assert "comfort" in s
        assert "preservation" in s

    def test_all_types_have_values(self):
        for ct in ContradictionType:
            assert ct.value is not None
            assert isinstance(ct.value, str)


# ═══════════════════════════════════════════════════════════════════
# End-to-End
# ═══════════════════════════════════════════════════════════════════


class TestCDIEndToEnd:
    def test_full_pipeline_all_contradiction_types(self):
        engine = CDIEngine()
        for ct in ContradictionType:
            contradiction = PhysicalContradiction(
                parameter="TestParam",
                value_a="A",
                value_not_a="not-A",
                requirement_y="ReqY",
                requirement_z="ReqZ",
                contradiction_type=ct,
            )
            solution = engine.solve(contradiction)
            assert isinstance(solution, CDISolution)
            assert solution.steps_taken <= 6
            assert 0.0 <= solution.confidence_score <= 1.0
            assert solution.hypothesis != ""
            assert solution.contradiction == contradiction

    def test_path_continuity(self):
        engine = CDIEngine()
        contradiction = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.CONFLICTING_GOALS,
        )
        solution = engine.solve(contradiction)
        for i, transition in enumerate(solution.c4_path):
            if i > 0:
                assert transition.from_state.to_tuple() == solution.c4_path[i - 1].to_state.to_tuple()

    def test_custom_start_state_reaches_target(self):
        engine = CDIEngine()
        contradiction = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.TRADE_OFF,
        )
        start = C4State(T=0, S=0, A=0)
        solution = engine.solve(contradiction, start)
        if solution.c4_path:
            assert solution.c4_path[-1].to_state.to_tuple() == (2, 2, 2)
