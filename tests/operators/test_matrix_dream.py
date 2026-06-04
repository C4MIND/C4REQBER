"""Tests for Matrix Dream 72 patterns."""

from __future__ import annotations

import pytest

from src.c4.engine import C4State
from src.operators.matrix_dream import (
    ALL_PATTERNS,
    C4Transform,
    DreamPattern,
    MatrixDreamRegistry,
    PatternCategory,
    apply_pattern_sequence,
    find_patterns_for_c4_transition,
    get_category_distribution,
)
from src.operators.qzrf import CognitiveFrame


class TestC4Transform:
    def test_identity(self) -> None:
        t = C4Transform()
        state = C4State(T=1, S=1, A=1)
        assert t.apply(state) == state

    def test_single_axis(self) -> None:
        t = C4Transform(delta_t=1)
        state = C4State(T=0, S=0, A=0)
        assert t.apply(state) == C4State(T=1, S=0, A=0)

    def test_multi_axis(self) -> None:
        t = C4Transform(delta_t=1, delta_s=-1, delta_a=2)
        state = C4State(T=1, S=1, A=1)
        result = t.apply(state)
        assert result == C4State(T=2, S=0, A=0)

    def test_cyclic(self) -> None:
        t = C4Transform(delta_t=2, delta_s=2, delta_a=2)
        state = C4State(T=1, S=1, A=1)
        result = t.apply(state)
        assert result == C4State(T=0, S=0, A=0)


class TestDreamPattern:
    def test_apply_basic(self) -> None:
        pattern = DreamPattern(
            id=999,
            name="TestPattern",
            description="Test",
            category=PatternCategory.ABSTRACTION,
            c4_transform=C4Transform(delta_s=1),
        )
        frame = CognitiveFrame(c4_state=C4State(T=0, S=0, A=0))
        result = pattern.apply(frame)
        assert result.c4_state == C4State(T=0, S=1, A=0)
        assert result.metadata["applied_pattern"] == "TestPattern"

    def test_apply_with_semantic(self) -> None:
        pattern = DreamPattern(
            id=999,
            name="TestPattern",
            description="Test",
            category=PatternCategory.ABSTRACTION,
            c4_transform=C4Transform(delta_s=1),
            semantic_transform=lambda c: {**c, "test_key": "test_value"},
        )
        frame = CognitiveFrame(c4_state=C4State(T=0, S=0, A=0))
        result = pattern.apply(frame)
        assert result.content["test_key"] == "test_value"


class TestPatternRegistry:
    def test_all_72_loaded(self) -> None:
        patterns = MatrixDreamRegistry.all()
        assert len(patterns) == 72

    def test_ids_unique(self) -> None:
        patterns = MatrixDreamRegistry.all()
        ids = [p.id for p in patterns]
        assert len(ids) == len(set(ids))

    def test_names_unique(self) -> None:
        patterns = MatrixDreamRegistry.all()
        names = [p.name for p in patterns]
        assert len(names) == len(set(names))

    def test_get_by_id(self) -> None:
        p = MatrixDreamRegistry.get(1)
        assert p.id == 1
        assert p.name == "Lift_Instance_To_Class"

    def test_get_by_name(self) -> None:
        p = MatrixDreamRegistry.get_by_name("Extract_Invariant")
        assert p.id == 2

    def test_get_unknown_id_raises(self) -> None:
        with pytest.raises(KeyError):
            MatrixDreamRegistry.get(9999)

    def test_get_unknown_name_raises(self) -> None:
        with pytest.raises(KeyError):
            MatrixDreamRegistry.get_by_name("NonExistent")

    def test_categories_complete(self) -> None:
        cats = MatrixDreamRegistry.categories()
        assert len(cats) == 9

    def test_by_category_counts(self) -> None:
        for cat in PatternCategory:
            patterns = MatrixDreamRegistry.by_category(cat)
            assert len(patterns) == 8, f"Category {cat.name} should have 8 patterns"

    def test_all_patterns_have_descriptions(self) -> None:
        for p in MatrixDreamRegistry.all():
            assert p.description
            assert len(p.description) > 3


class TestCategoryPatterns:
    def test_abstraction_patterns(self) -> None:
        patterns = MatrixDreamRegistry.by_category(PatternCategory.ABSTRACTION)
        assert len(patterns) == 8
        assert patterns[0].id == 1
        assert patterns[-1].id == 8

    def test_concretization_patterns(self) -> None:
        patterns = MatrixDreamRegistry.by_category(PatternCategory.CONCRETIZATION)
        assert len(patterns) == 8
        assert patterns[0].id == 9
        assert patterns[-1].id == 16

    def test_temporal_patterns(self) -> None:
        patterns = MatrixDreamRegistry.by_category(PatternCategory.TEMPORAL)
        assert len(patterns) == 8
        assert patterns[0].id == 17
        assert patterns[-1].id == 24

    def test_perspective_patterns(self) -> None:
        patterns = MatrixDreamRegistry.by_category(PatternCategory.PERSPECTIVE)
        assert len(patterns) == 8
        assert patterns[0].id == 25
        assert patterns[-1].id == 32

    def test_composition_patterns(self) -> None:
        patterns = MatrixDreamRegistry.by_category(PatternCategory.COMPOSITION)
        assert len(patterns) == 8
        assert patterns[0].id == 33
        assert patterns[-1].id == 40

    def test_decomposition_patterns(self) -> None:
        patterns = MatrixDreamRegistry.by_category(PatternCategory.DECOMPOSITION)
        assert len(patterns) == 8
        assert patterns[0].id == 41
        assert patterns[-1].id == 48

    def test_inversion_patterns(self) -> None:
        patterns = MatrixDreamRegistry.by_category(PatternCategory.INVERSION)
        assert len(patterns) == 8
        assert patterns[0].id == 49
        assert patterns[-1].id == 56

    def test_constraint_patterns(self) -> None:
        patterns = MatrixDreamRegistry.by_category(PatternCategory.CONSTRAINT)
        assert len(patterns) == 8
        assert patterns[0].id == 57
        assert patterns[-1].id == 64

    def test_meta_patterns(self) -> None:
        patterns = MatrixDreamRegistry.by_category(PatternCategory.META)
        assert len(patterns) == 8
        assert patterns[0].id == 65
        assert patterns[-1].id == 72


class TestPatternApplication:
    def test_pattern_1_lift_instance(self) -> None:
        p = MatrixDreamRegistry.get(1)
        frame = CognitiveFrame(
            c4_state=C4State(T=1, S=0, A=0),
            content={"instance": "bird"},
        )
        result = p.apply(frame)
        assert result.c4_state.S == 1
        assert result.content["abstraction"] == "class"
        assert result.content["generalized_from"] == "bird"

    def test_pattern_17_retrospective(self) -> None:
        p = MatrixDreamRegistry.get(17)
        frame = CognitiveFrame(c4_state=C4State(T=1, S=1, A=1))
        result = p.apply(frame)
        assert result.c4_state.T == 0
        assert result.content["temporal_focus"] == "past"

    def test_pattern_27_system_overview(self) -> None:
        p = MatrixDreamRegistry.get(27)
        frame = CognitiveFrame(c4_state=C4State(T=1, S=1, A=0))
        result = p.apply(frame)
        assert result.c4_state.A == 2
        assert result.content["perspective"] == "system"

    def test_pattern_49_assumption_negation(self) -> None:
        p = MatrixDreamRegistry.get(49)
        frame = CognitiveFrame(
            c4_state=C4State(T=0, S=0, A=0),
            content={"core_assumptions": ["a1", "a2"]},
        )
        result = p.apply(frame)
        assert result.content["negation_count"] == 2

    def test_pattern_65_process_reflection(self) -> None:
        p = MatrixDreamRegistry.get(65)
        frame = CognitiveFrame(
            c4_state=C4State(T=0, S=0, A=0),
            content={"trace": ["step1", "step2"]},
        )
        result = p.apply(frame)
        assert result.c4_state.S == 2
        assert result.content["process_reflection"] is True


class TestPatternSequence:
    def test_sequence(self) -> None:
        frame = CognitiveFrame(c4_state=C4State(T=0, S=0, A=0))
        result = apply_pattern_sequence(frame, [1, 9])  # Generalize then Specify
        # Should return to original S
        assert result.c4_state.S == 0

    def test_empty_sequence(self) -> None:
        frame = CognitiveFrame(c4_state=C4State(T=1, S=1, A=1))
        result = apply_pattern_sequence(frame, [])
        assert result.c4_state == C4State(T=1, S=1, A=1)


class TestFindPatternsForC4Transition:
    def test_find_matching(self) -> None:
        from_state = C4State(T=0, S=0, A=0)
        to_state = C4State(T=0, S=1, A=0)
        matching = find_patterns_for_c4_transition(from_state, to_state)
        assert len(matching) > 0
        for p in matching:
            assert p.c4_transform.delta_s == 1

    def test_no_match(self) -> None:
        from_state = C4State(T=0, S=0, A=0)
        to_state = C4State(T=0, S=0, A=0)
        matching = find_patterns_for_c4_transition(from_state, to_state)
        # Patterns with all-zero transform
        assert all(p.c4_transform.delta_t == 0 for p in matching)
        assert all(p.c4_transform.delta_s == 0 for p in matching)
        assert all(p.c4_transform.delta_a == 0 for p in matching)


class TestCategoryDistribution:
    def test_distribution(self) -> None:
        dist = get_category_distribution()
        assert len(dist) == 9
        for cat_name, count in dist.items():
            assert count == 8, f"Category {cat_name} should have 8 patterns"


class TestAllPatternsConstant:
    def test_total_count(self) -> None:
        assert len(ALL_PATTERNS) == 72

    def test_id_range(self) -> None:
        ids = [p.id for p in ALL_PATTERNS]
        assert min(ids) == 1
        assert max(ids) == 72

    def test_all_categories_present(self) -> None:
        categories = {p.category for p in ALL_PATTERNS}
        assert len(categories) == 9
        assert all(cat in categories for cat in PatternCategory)
