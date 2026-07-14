"""
Tests for CDI Engine (core/cdi_engine.py)
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


class TestPhysicalContradiction:
    def test_contradiction_str(self):
        pc = PhysicalContradiction(
            parameter="Speed",
            value_a="fast",
            value_not_a="slow",
            requirement_y="performance",
            requirement_z="safety",
            contradiction_type=ContradictionType.TRADE_OFF,
        )
        result = str(pc)
        assert "Speed" in result
        assert "fast" in result
        assert "slow" in result

    def test_all_contradiction_types(self):
        types = [
            ContradictionType.TRADE_OFF,
            ContradictionType.DUAL_REQUIREMENT,
            ContradictionType.CONFLICTING_GOALS,
            ContradictionType.TEMPORAL,
            ContradictionType.SCALE,
            ContradictionType.PERSPECTIVE,
        ]
        for ct in types:
            pc = PhysicalContradiction(
                parameter="P", value_a="A", value_not_a="B",
                requirement_y="Y", requirement_z="Z",
                contradiction_type=ct,
            )
            assert pc.contradiction_type == ct


class TestCDISolution:
    def test_solution_creation(self):
        pc = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.TRADE_OFF,
        )
        solution = CDISolution(
            hypothesis="Test hypothesis",
            c4_path=[],
            steps_taken=3,
            contradiction=pc,
            confidence_score=0.85,
        )
        assert solution.steps_taken == 3
        assert solution.confidence_score == 0.85

    def test_theorem_11_enforced(self):
        pc = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.TRADE_OFF,
        )
        with pytest.raises(AssertionError):
            CDISolution(
                hypothesis="Test",
                c4_path=[],
                steps_taken=7,
                contradiction=pc,
                confidence_score=0.5,
            )


class TestCDIEngine:
    def test_engine_initialization(self):
        engine = CDIEngine()
        assert engine.c4_space is not None
        assert engine.operators is not None

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

    def test_solve_with_custom_state(self):
        engine = CDIEngine()
        contradiction = PhysicalContradiction(
            parameter="Cost",
            value_a="low",
            value_not_a="high",
            requirement_y="affordability",
            requirement_z="quality",
            contradiction_type=ContradictionType.DUAL_REQUIREMENT,
        )
        start_state = C4State(T=0, S=0, A=0)
        solution = engine.solve(contradiction, start_state)
        assert solution.steps_taken <= 6
        assert solution.c4_path[0].from_state == start_state

    def test_fingerprint_mapping(self):
        engine = CDIEngine()
        contradiction = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.CONFLICTING_GOALS,
        )
        state = engine._fingerprint_contradiction(contradiction)
        assert state.T == 2
        assert state.S == 2
        assert state.A == 2

    def test_predict_solution_region(self):
        engine = CDIEngine()
        contradiction = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.TEMPORAL,
        )
        target = engine._predict_solution_region(contradiction)
        assert target.T == 2
        assert target.S == 2
        assert target.A == 2

    def test_compute_route(self):
        engine = CDIEngine()
        start = C4State(T=0, S=0, A=0)
        end = C4State(T=2, S=2, A=2)
        path = engine._compute_route(start, end)
        assert len(path) <= 6
        assert path[-1].to_state.to_tuple() == end.to_tuple()

    def test_calculate_confidence(self):
        engine = CDIEngine()
        path = [
            C4Transition("tau+", C4State(0, 0, 0), C4State(1, 0, 0)),
            C4Transition("lambda+", C4State(1, 0, 0), C4State(1, 1, 0)),
        ]
        contradiction = PhysicalContradiction(
            parameter="P", value_a="A", value_not_a="B",
            requirement_y="Y", requirement_z="Z",
            contradiction_type=ContradictionType.TRADE_OFF,
        )
        confidence = engine._calculate_confidence(path, contradiction)
        assert 0.0 <= confidence <= 1.0
        assert confidence == round(confidence, 2)

    def test_synthesize_hypothesis(self):
        engine = CDIEngine()
        contradiction = PhysicalContradiction(
            parameter="Size",
            value_a="big",
            value_not_a="small",
            requirement_y="capacity",
            requirement_z="portability",
            contradiction_type=ContradictionType.SCALE,
        )
        final_state = C4State(T=2, S=2, A=2)
        path = [
            C4Transition("tau+", C4State(1, 0, 2), C4State(2, 0, 2)),
        ]
        hypothesis = engine._synthesize_hypothesis(contradiction, final_state, path)
        assert "Size" in hypothesis
        assert "tau+" in hypothesis


class TestEinsteinValidator:
    def test_str_validation(self):
        engine = CDIEngine()
        validator = EinsteinValidator(engine)
        solution = validator.validate_str()
        assert solution.steps_taken <= 4
        assert "speed" in solution.hypothesis.lower() or "light" in solution.hypothesis.lower()

    def test_gtr_validation(self):
        engine = CDIEngine()
        validator = EinsteinValidator(engine)
        solution = validator.validate_gtr()
        assert solution.steps_taken <= 6
        assert "gravity" in solution.hypothesis.lower()

    def test_str_contradiction_type(self):
        engine = CDIEngine()
        validator = EinsteinValidator(engine)
        solution = validator.validate_str()
        assert solution.contradiction.contradiction_type == ContradictionType.CONFLICTING_GOALS

    def test_gtr_start_state(self):
        engine = CDIEngine()
        validator = EinsteinValidator(engine)
        solution = validator.validate_gtr()
        assert solution.c4_path[0].from_state.to_tuple() == (1, 1, 2)
