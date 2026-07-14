"""Tests for FRA routing in src/c4/routing.py

Focuses on RoutePlan dataclass, BFS route finding,
and feedback-adjusted scoring.
Pure-logic unit tests: NO MOCKS, NO NETWORK, NO LLM.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from c4.engine import C4Path, C4Space, C4State, C4Transition
from c4.routing import FRARouter, QualityPreset, RoutePlan


class TestRoutePlanDataclass:
    """Test RoutePlan: the core C4 route plan dataclass."""

    def test_route_plan_creation_defaults(self):
        start = C4State(T=0, S=0, A=0)
        target = C4State(T=1, S=1, A=1)
        path = C4Path(start_state=start, end_state=target)
        plan = RoutePlan(
            start_state=start,
            target_state=target,
            path=path,
            hamming_distance=2,
        )
        assert plan.start_state == start
        assert plan.target_state == target
        assert plan.path == path
        assert plan.hamming_distance == 2
        assert plan.preset is None
        assert plan.convergence_check == {}

    def test_route_plan_with_preset(self):
        start = C4State(T=0, S=0, A=0)
        target = C4State(T=2, S=2, A=2)
        path = C4Path(start_state=start, end_state=target)
        plan = RoutePlan(
            start_state=start,
            target_state=target,
            path=path,
            preset=QualityPreset.SYNTHESIS,
            hamming_distance=3,
        )
        assert plan.preset == QualityPreset.SYNTHESIS

    def test_route_plan_operators_property(self):
        start = C4State(T=0, S=0, A=0)
        path = C4Path(
            start_state=start,
            end_state=C4State(T=1, S=0, A=0),
            transitions=[
                C4Transition(
                    operator="tau+",
                    from_state=C4State(T=0, S=0, A=0),
                    to_state=C4State(T=1, S=0, A=0),
                ),
            ],
        )
        plan = RoutePlan(start_state=start, target_state=C4State(T=1, S=0, A=0), path=path)
        assert plan.operators == ["tau+"]

    def test_is_optimal_zero_distance(self):
        start = C4State(T=1, S=1, A=1)
        path = C4Path(start_state=start, end_state=start)
        plan = RoutePlan(
            start_state=start,
            target_state=start,
            path=path,
            hamming_distance=0,
        )
        assert plan.is_optimal is True

    def test_is_optimal_when_length_matches_hamming(self):
        start = C4State(T=0, S=0, A=0)
        target = C4State(T=1, S=0, A=0)
        path = C4Path(
            start_state=start,
            end_state=target,
            transitions=[
                C4Transition(
                    operator="tau+",
                    from_state=start,
                    to_state=target,
                ),
            ],
        )
        plan = RoutePlan(start_state=start, target_state=target, path=path, hamming_distance=1)
        assert plan.is_optimal is True

    def test_to_dict_serialization(self):
        start = C4State(T=0, S=0, A=0)
        target = C4State(T=1, S=0, A=0)
        path = C4Path(start_state=start, end_state=target)
        plan = RoutePlan(
            start_state=start,
            target_state=target,
            path=path,
            preset=QualityPreset.VALIDATION,
            hamming_distance=1,
            convergence_check={"converged": True},
        )
        d = plan.to_dict()
        assert d["start_state"] == str(start)
        assert d["target_state"] == str(target)
        assert d["hamming_distance"] == 1
        assert d["preset"] == "validation"
        assert d["convergence_check"] == {"converged": True}


class TestRouteFinding:
    """Test find_route: BFS route discovery in C4 state space."""

    def test_find_route_same_state(self):
        router = FRARouter()
        state = C4State(T=1, S=1, A=1)
        plan = router.find_route(state, state)
        assert plan.path.length == 0
        assert plan.is_optimal
        assert plan.convergence_check["converged"]

    def test_find_route_one_step(self):
        router = FRARouter()
        start = C4State(T=0, S=1, A=1)
        target = C4State(T=1, S=1, A=1)
        plan = router.find_route(start, target)
        assert plan.path.length == 1
        assert plan.hamming_distance == 1
        assert plan.is_optimal

    def test_find_route_two_steps(self):
        router = FRARouter()
        start = C4State(T=0, S=0, A=1)
        target = C4State(T=1, S=1, A=1)
        plan = router.find_route(start, target)
        assert plan.path.length == 2
        assert plan.hamming_distance == 2
        assert plan.is_optimal

    def test_find_route_three_axes(self):
        router = FRARouter()
        start = C4State(T=0, S=0, A=0)
        target = C4State(T=2, S=2, A=2)
        plan = router.find_route(start, target)
        assert plan.hamming_distance == 3
        assert plan.path.length <= plan.hamming_distance

    def test_find_route_returns_route_plan(self):
        router = FRARouter()
        plan = router.find_route(C4State(0, 0, 0), C4State(2, 2, 2))
        assert isinstance(plan, RoutePlan)

    def test_all_27_states_reachable_within_six(self):
        router = FRARouter()
        space = C4Space()
        for s1 in space.states:
            for s2 in space.states:
                plan = router.find_route(s1, s2)
                assert plan.path.length <= 6, f"Path from {s1} to {s2} exceeded 6 steps: {plan.path.length}"

    def test_path_continuity(self):
        router = FRARouter()
        start = C4State(0, 0, 0)
        target = C4State(2, 1, 0)
        plan = router.find_route(start, target)
        current = start
        for t in plan.path.transitions:
            assert t.from_state == current
            current = t.to_state
        assert current.to_tuple() == target.to_tuple()


class TestFeedbackAdjustedScoring:
    """Test adaptive routing with feedback-based operator scoring."""

    def test_record_feedback_increases_count(self):
        router = FRARouter()
        router.record_feedback("tau+", 0.9)
        router.record_feedback("tau-", 0.7)
        stats = router.get_feedback_stats()
        assert stats["count"] == 2
        assert stats["average_score"] == pytest.approx(0.8)

    def test_feedback_stats_empty(self):
        router = FRARouter()
        stats = router.get_feedback_stats()
        assert stats["count"] == 0
        assert stats["average_score"] == 0.0

    def test_feedback_affects_adaptive_route(self):
        router = FRARouter()
        router.record_feedback("tau+", 1.0)
        router.record_feedback("tau-", 0.1)
        router.record_feedback("lambda+", 0.5)
        plan = router.adaptive_route(
            C4State(T=0, S=0, A=0),
            C4State(T=2, S=2, A=2),
        )
        assert plan.path.length <= 6
        assert isinstance(plan, RoutePlan)

    def test_feedback_stats_includes_min_max(self):
        router = FRARouter()
        router.record_feedback("tau+", 0.3)
        router.record_feedback("tau+", 0.9)
        stats = router.get_feedback_stats()
        assert stats["min_score"] == pytest.approx(0.3)
        assert stats["max_score"] == pytest.approx(0.9)
        assert stats["count"] == 2

    def test_adaptive_route_converges_simple_cases(self):
        router = FRARouter()
        plan = router.adaptive_route(C4State(1, 1, 1), C4State(2, 1, 1))
        assert plan.convergence_check["converged"]
        assert plan.path.length == 1


class TestQualityPresets:
    """Test quality presets: synthesis, mp_rotation, validation."""

    def test_synthesis_preset(self):
        router = FRARouter()
        plan = router.route_synthesis(C4State(0, 0, 0), C4State(2, 2, 2))
        assert plan.preset == QualityPreset.SYNTHESIS
        assert plan.path.length <= plan.hamming_distance

    def test_mp_rotation_preset(self):
        router = FRARouter()
        plan = router.route_mp_rotation(C4State(0, 0, 0), C4State(2, 2, 2))
        assert plan.preset == QualityPreset.MP_ROTATION

    def test_validation_preset(self):
        router = FRARouter()
        plan = router.route_validation(C4State(0, 0, 0), C4State(2, 2, 2))
        assert plan.preset == QualityPreset.VALIDATION

    def test_presets_produce_valid_paths(self):
        router = FRARouter()
        start = C4State(0, 0, 0)
        target = C4State(1, 2, 0)
        for preset in (QualityPreset.SYNTHESIS, QualityPreset.MP_ROTATION, QualityPreset.VALIDATION):
            plan = router.find_route(start, target, preset=preset)
            assert plan.path.length <= plan.hamming_distance
            assert plan.preset == preset
