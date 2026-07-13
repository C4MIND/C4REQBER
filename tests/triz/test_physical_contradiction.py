"""
Tests for TRIZ Physical Contradictions.
Verifies detection, resolution, and C4 mapping on classic examples.
"""

import pytest

from src.triz.physical_contradiction import (
    CLASSIC_PHYSICAL_CONTRADICTIONS,
    COMMON_OPPOSITES,
    SEPARATION_STRATEGIES,
    PhysicalContradiction,
    PhysicalContradictionAnalyzer,
    SeparationType,
    detect_physical_contradiction,
    get_classic_examples,
    resolve_physical_contradiction,
)


# =============================================================================
# DETECTION TESTS
# =============================================================================


class TestDetection:
    def test_detect_explicit_pattern_both(self):
        text = "The door must be both open and closed at the same time."
        results = detect_physical_contradiction(text)
        assert len(results) >= 1
        assert any(r.object_name == "door" for r in results)

    def test_detect_explicit_pattern_must_be(self):
        text = "The wing must be large and small simultaneously."
        results = detect_physical_contradiction(text)
        assert len(results) >= 1
        assert any(r.property == "large" for r in results)

    def test_detect_by_opposites(self):
        text = "The container is hot in summer and cold in winter."
        results = detect_physical_contradiction(text)
        # Should detect hot/cold pair
        assert any(r.property == "hot" and r.opposite == "cold" for r in results)

    def test_detect_no_contradiction(self):
        text = "The sky is blue and the grass is green."
        results = detect_physical_contradiction(text)
        assert len(results) == 0

    def test_common_opposites_coverage(self):
        assert "hot" in COMMON_OPPOSITES
        assert COMMON_OPPOSITES["hot"] == "cold"
        assert COMMON_OPPOSITES["fast"] == "slow"
        assert COMMON_OPPOSITES["rigid"] == "flexible"

    def test_detect_multiple_in_same_text(self):
        text = (
            "The cup must be hot to keep coffee warm. The cup must be cold to avoid burning hands."
        )
        analyzer = PhysicalContradictionAnalyzer()
        results = analyzer.detect(text)
        # Should find at least one contradiction
        assert len(results) >= 1


# =============================================================================
# RESOLUTION TESTS
# =============================================================================


class TestResolution:
    def test_resolve_in_time(self):
        pc = PhysicalContradiction(
            object_name="umbrella",
            property="open",
            opposite="closed",
            context="Umbrella must be open in rain and closed when stored.",
        )
        result = resolve_physical_contradiction(pc)
        assert "recommendations" in result
        assert len(result["recommendations"]) == 4
        best = result["best_strategy"]
        assert best is not None
        assert "separation_type" in best

    def test_resolve_with_hint(self):
        pc = PhysicalContradiction(
            object_name="diving suit",
            property="thick",
            opposite="thin",
            context="Thick for warmth, thin for flexibility.",
        )
        result = resolve_physical_contradiction(pc, SeparationType.IN_SPACE)
        best = result["best_strategy"]
        assert best["separation_type"] == "IN_SPACE"

    def test_all_separation_strategies_exist(self):
        for sep_type in SeparationType:
            assert sep_type in SEPARATION_STRATEGIES

    def test_c4_trajectories_present(self):
        for _sep_type, strategy in SEPARATION_STRATEGIES.items():
            assert len(strategy.c4_trajectory) >= 2
            for t, s, a in strategy.c4_trajectory:
                assert 0 <= t <= 2
                assert 0 <= s <= 2
                assert 0 <= a <= 2


# =============================================================================
# C4 MAPPING TESTS
# =============================================================================


class TestC4Mapping:
    def test_map_to_c4_transition(self):
        pc = PhysicalContradiction(
            object_name="spring",
            property="rigid",
            opposite="flexible",
            context="Spring must support and absorb shock.",
        )
        analyzer = PhysicalContradictionAnalyzer()
        mapping = analyzer.map_to_c4_transition(pc, SeparationType.PARTS_WHOLE)
        assert mapping["separation_type"] == "PARTS_WHOLE"
        assert mapping["c4_shift"] == "agency_shift"
        assert "c4_trajectory" in mapping
        assert "observer_transition" in mapping

    def test_observer_transition_label(self):
        analyzer = PhysicalContradictionAnalyzer()
        from c4.types import C4State

        s1 = C4State(T=1, S=0, A=0)
        s2 = C4State(T=2, S=0, A=0)
        label = analyzer._observer_transition_label([s1, s2])
        assert "O0" in label or "O1" in label


# =============================================================================
# CLASSIC EXAMPLES TESTS
# =============================================================================


class TestClassicExamples:
    def test_all_10_classic_examples_present(self):
        assert len(CLASSIC_PHYSICAL_CONTRADICTIONS) == 10
        examples = get_classic_examples()
        assert len(examples) == 10

    def test_classic_coffee_cup(self):
        examples = get_classic_examples()
        cup = next(e for e in examples if e.object_name == "coffee cup")
        result = resolve_physical_contradiction(cup)
        assert result["best_strategy"] is not None

    def test_classic_airplane_wing(self):
        examples = get_classic_examples()
        wing = next(e for e in examples if e.object_name == "airplane wing")
        result = resolve_physical_contradiction(wing)
        assert result["best_strategy"] is not None
        # Large/small spatial contradiction → likely IN_SPACE
        assert any(r["separation_type"] == "IN_SPACE" for r in result["recommendations"])

    def test_classic_knife_blade(self):
        examples = get_classic_examples()
        knife = next(e for e in examples if e.object_name == "knife blade")
        result = resolve_physical_contradiction(knife)
        assert result["best_strategy"] is not None

    def test_classic_door(self):
        examples = get_classic_examples()
        door = next(e for e in examples if e.object_name == "door")
        result = resolve_physical_contradiction(door)
        # Open/closed → likely IN_TIME
        assert any(r["separation_type"] == "IN_TIME" for r in result["recommendations"])

    def test_classic_spring(self):
        examples = get_classic_examples()
        spring = next(e for e in examples if e.object_name == "spring")
        result = resolve_physical_contradiction(spring)
        # Rigid/flexible → likely PARTS_WHOLE
        assert any(r["separation_type"] == "PARTS_WHOLE" for r in result["recommendations"])

    def test_classic_information(self):
        examples = get_classic_examples()
        info = next(e for e in examples if e.object_name == "information")
        result = resolve_physical_contradiction(info)
        # Visible/invisible → likely UNDER_CONDITIONS or IN_SPACE
        assert result["best_strategy"] is not None

    def test_classic_vehicle(self):
        examples = get_classic_examples()
        vehicle = next(e for e in examples if e.object_name == "vehicle")
        result = resolve_physical_contradiction(vehicle)
        # Fast/slow → likely IN_TIME
        assert any(r["separation_type"] == "IN_TIME" for r in result["recommendations"])

    def test_classic_container(self):
        examples = get_classic_examples()
        container = next(e for e in examples if e.object_name == "container")
        result = resolve_physical_contradiction(container)
        # Porous/dense → likely IN_SPACE or UNDER_CONDITIONS
        assert result["best_strategy"] is not None

    def test_classic_diving_suit(self):
        examples = get_classic_examples()
        suit = next(e for e in examples if e.object_name == "diving suit")
        result = resolve_physical_contradiction(suit)
        # Thick/thin → likely IN_SPACE
        assert any(r["separation_type"] == "IN_SPACE" for r in result["recommendations"])

    def test_classic_tire(self):
        examples = get_classic_examples()
        tire = next(e for e in examples if e.object_name == "tire")
        result = resolve_physical_contradiction(tire)
        # Wide/narrow → likely IN_TIME or IN_SPACE
        assert result["best_strategy"] is not None


# =============================================================================
# BATCH ANALYSIS TESTS
# =============================================================================


class TestBatchAnalysis:
    def test_analyze_text(self):
        text = "The diving suit must be thick for thermal insulation but thin for flexibility."
        analyzer = PhysicalContradictionAnalyzer()
        report = analyzer.analyze_text(text)
        assert report["contradictions_found"] >= 1
        assert len(report["contradictions"]) >= 1
        assert len(report["resolutions"]) >= 1

    def test_analyze_text_no_contradiction(self):
        text = "The weather is nice today with a gentle breeze."
        analyzer = PhysicalContradictionAnalyzer()
        report = analyzer.analyze_text(text)
        assert report["contradictions_found"] == 0
