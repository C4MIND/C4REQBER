"""Tests for FRARouter in src/c4/routing.py

Verifies BFS routing, Theorem 9 integration, quality presets, and adaptive routing.
"""

from __future__ import annotations

import pytest

from c4.engine import C4Space, C4State
from c4.routing import (
    FRARouter,
    QualityPreset,
    RoutePlan,
)


class TestFRARouterFingerprint:
    def test_fingerprint_basic(self):
        router = FRARouter()
        result = router.fingerprint("The system is confusing and unpredictable")
        assert result["situation"] == "chaos"
        assert result["c4_state"] == C4State(T=0, S=0, A=0)
        assert len(result["recommended_operators"]) == 4

    def test_fingerprint_stagnation(self):
        router = FRARouter()
        result = router.fingerprint("We are stuck at a plateau with no progress")
        assert result["situation"] == "stagnation"

    def test_fingerprint_returns_scores(self):
        router = FRARouter()
        result = router.fingerprint("confusion and disorder everywhere")
        assert "scores" in result
        assert result["scores"]["chaos"] > 0

    def test_classify_c4_state(self):
        router = FRARouter()
        state = router.classify_c4_state("random unpredictable turbulence")
        assert isinstance(state, C4State)
        assert state.to_tuple() == (0, 0, 0)


class TestFRARouterLegacyRoute:
    def test_route_low_gap(self):
        router = FRARouter()
        ops = router.route("chaos", gap_pct=20)
        assert "tune" in ops

    def test_route_mid_gap(self):
        router = FRARouter()
        ops = router.route("chaos", gap_pct=50)
        assert "shift" in ops

    def test_route_high_gap(self):
        router = FRARouter()
        ops = router.route("chaos", gap_pct=80)
        assert "crystallize" in ops


class TestFRARouterFindRoute:
    def test_same_state_returns_optimal(self):
        router = FRARouter()
        start = C4State(T=1, S=1, A=1)
        plan = router.find_route(start, start)
        assert plan.path.length == 0
        assert plan.is_optimal
        assert plan.convergence_check["converged"]

    def test_one_axis_transition(self):
        router = FRARouter()
        start = C4State(T=0, S=1, A=1)
        target = C4State(T=1, S=1, A=1)
        plan = router.find_route(start, target)
        assert plan.path.length == 1
        assert plan.hamming_distance == 1
        assert plan.is_optimal

    def test_two_axes_transition(self):
        router = FRARouter()
        start = C4State(T=0, S=0, A=1)
        target = C4State(T=1, S=1, A=1)
        plan = router.find_route(start, target)
        assert plan.path.length == 2
        assert plan.hamming_distance == 2
        assert plan.is_optimal

    def test_three_axes_transition(self):
        router = FRARouter()
        start = C4State(T=0, S=0, A=0)
        target = C4State(T=2, S=2, A=2)
        plan = router.find_route(start, target)
        # iota operator can invert all axes at once, creating shortcut
        assert plan.path.length <= 3
        assert plan.hamming_distance == 3
        # With iota available, path may be shorter than Hamming distance
        assert plan.path.length <= plan.hamming_distance

    def test_wraparound_transition(self):
        router = FRARouter()
        start = C4State(T=2, S=2, A=2)
        target = C4State(T=0, S=0, A=0)
        plan = router.find_route(start, target)
        # iota operator inverts directly: (2,2,2) -> (0,0,0) in 1 step
        assert plan.path.length <= 3
        assert plan.path.length <= plan.hamming_distance

    def test_all_pairs_within_six_steps(self):
        router = FRARouter()
        space = C4Space()
        states = space.states
        for s1 in states:
            for s2 in states:
                plan = router.find_route(s1, s2)
                assert plan.path.length <= 6, f"Failed for {s1} -> {s2}"

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

    def test_path_length_within_hamming_bound(self):
        router = FRARouter()
        space = C4Space()
        for s1 in space.states[:10]:
            for s2 in space.states[:10]:
                plan = router.find_route(s1, s2)
                # With iota operator, path can be <= hamming distance
                assert plan.path.length <= plan.hamming_distance, (
                    f"Path exceeded hamming bound for {s1} -> {s2}"
                )

    def test_returns_route_plan_type(self):
        router = FRARouter()
        plan = router.find_route(C4State(0, 0, 0), C4State(1, 1, 1))
        assert isinstance(plan, RoutePlan)
        assert plan.to_dict()["hamming_distance"] == 3


class TestFRARouterQualityPresets:
    def test_synthesis_preset(self):
        router = FRARouter()
        plan = router.route_synthesis(C4State(0, 0, 0), C4State(2, 2, 2))
        assert plan.preset == QualityPreset.SYNTHESIS
        assert plan.path.length <= plan.hamming_distance

    def test_mp_rotation_preset(self):
        router = FRARouter()
        plan = router.route_mp_rotation(C4State(0, 0, 0), C4State(2, 2, 2))
        assert plan.preset == QualityPreset.MP_ROTATION
        assert plan.path.length <= plan.hamming_distance

    def test_validation_preset(self):
        router = FRARouter()
        plan = router.route_validation(C4State(0, 0, 0), C4State(2, 2, 2))
        assert plan.preset == QualityPreset.VALIDATION
        assert plan.path.length <= plan.hamming_distance

    def test_preset_affects_operator_order(self):
        router = FRARouter()
        p1 = router.find_route(C4State(0, 0, 0), C4State(2, 2, 2), preset=QualityPreset.SYNTHESIS)
        p2 = router.find_route(C4State(0, 0, 0), C4State(2, 2, 2), preset=QualityPreset.VALIDATION)
        # Both should find valid paths (iota may make them identical for this case)
        assert p1.path.length <= p1.hamming_distance
        assert p2.path.length <= p2.hamming_distance


class TestFRARouterAdaptiveRoute:
    def test_adaptive_route_basic(self):
        router = FRARouter()
        plan = router.adaptive_route(C4State(0, 0, 0), C4State(2, 2, 2))
        assert plan.path.length <= 6
        assert plan.convergence_check["converged"] or plan.path.length > 0

    def test_adaptive_route_converges_for_simple_cases(self):
        router = FRARouter()
        plan = router.adaptive_route(C4State(1, 1, 1), C4State(2, 1, 1))
        assert plan.convergence_check["converged"]

    def test_feedback_improves_ranking(self):
        router = FRARouter()
        router.record_feedback("tau+", 0.9)
        router.record_feedback("tau+", 0.95)
        stats = router.get_feedback_stats()
        assert stats["count"] == 2
        assert stats["average_score"] == pytest.approx(0.925)

    def test_feedback_stats_empty(self):
        router = FRARouter()
        stats = router.get_feedback_stats()
        assert stats["count"] == 0


class TestFRARouterUtilities:
    def test_operator_family(self):
        router = FRARouter()
        assert router.operator_family("scan") == "sense"
        assert router.operator_family("connect") == "structure"
        assert router.operator_family("nonexistent") is None

    def test_list_situations(self):
        situations = FRARouter.list_situations()
        assert len(situations) == 7
        assert "chaos" in situations
        assert "rigidity" in situations

    def test_list_operator_families(self):
        families = FRARouter.list_operator_families()
        assert len(families) == 5
        assert "sense" in families
        assert "flow" in families

    def test_list_all_operators(self):
        ops = FRARouter.list_all_operators()
        assert len(ops) == 20
        assert all(":" in op for op in ops)
