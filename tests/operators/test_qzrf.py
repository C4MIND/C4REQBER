"""Tests for QZRF meta-operators."""

from __future__ import annotations

import pytest

from src.c4.engine import C4State
from src.operators.qzrf import (
    Analogize,
    CognitiveFrame,
    Combine,
    ConstraintRelax,
    ConstraintTighten,
    Decompose,
    FirstPrinciples,
    Generalize,
    MetaReflect,
    PerspectiveShift,
    QZRFC4Rule,
    QZRFOperator,
    QZRFOpType,
    QZRFRegistry,
    Recursive,
    Reverse,
    Specify,
    Systemic,
    TemporalShift,
    apply_operator_sequence,
    get_operator_c4_transform,
    list_operators,
)


class TestQZRFC4Rule:
    def test_identity_rule(self) -> None:
        rule = QZRFC4Rule()
        state = C4State(T=1, S=1, A=1)
        result = rule.apply(state)
        assert result == state

    def test_single_axis_shift(self) -> None:
        rule = QZRFC4Rule(delta_t=1)
        state = C4State(T=0, S=0, A=0)
        result = rule.apply(state)
        assert result == C4State(T=1, S=0, A=0)

    def test_multi_axis_shift(self) -> None:
        rule = QZRFC4Rule(delta_t=1, delta_s=1, delta_a=1)
        state = C4State(T=0, S=0, A=0)
        result = rule.apply(state)
        assert result == C4State(T=1, S=1, A=1)

    def test_cyclic_wrap(self) -> None:
        rule = QZRFC4Rule(delta_t=1)
        state = C4State(T=2, S=1, A=1)
        result = rule.apply(state)
        assert result == C4State(T=0, S=1, A=1)


class TestCognitiveFrame:
    def test_basic_creation(self) -> None:
        frame = CognitiveFrame(c4_state=C4State(T=1, S=1, A=1))
        assert frame.c4_state == C4State(T=1, S=1, A=1)
        assert frame.content == {}

    def test_with_state(self) -> None:
        frame = CognitiveFrame(
            c4_state=C4State(T=0, S=0, A=0),
            content={"key": "value"},
        )
        new_frame = frame.with_state(C4State(T=1, S=1, A=1))
        assert new_frame.c4_state == C4State(T=1, S=1, A=1)
        assert new_frame.content == {"key": "value"}
        assert frame.c4_state == C4State(T=0, S=0, A=0)  # Original unchanged

    def test_with_content(self) -> None:
        frame = CognitiveFrame(c4_state=C4State(T=0, S=0, A=0))
        new_frame = frame.with_content(foo="bar", num=42)
        assert new_frame.content == {"foo": "bar", "num": 42}


class TestGeneralize:
    def test_c4_transform(self) -> None:
        op = Generalize()
        state = C4State(T=1, S=0, A=1)
        result = op.transform_c4(state)
        assert result == C4State(T=1, S=1, A=1)

    def test_semantic_transform(self) -> None:
        op = Generalize()
        frame = CognitiveFrame(
            c4_state=C4State(T=1, S=0, A=1),
            content={"instances": [{"a": 1, "b": 2}, {"a": 3, "b": 4}]},
        )
        result = op.transform(frame)
        assert result.c4_state == C4State(T=1, S=1, A=1)
        assert "pattern" in result.content
        assert result.content["abstraction_level"] == 1

    def test_extract_pattern(self) -> None:
        pattern = Generalize._extract_pattern([{"x": 1}, {"x": 2}])
        assert "structural_invariant" in pattern

    def test_op_type(self) -> None:
        op = Generalize()
        assert op.op_type == QZRFOpType.ABSTRACTION


class TestSpecify:
    def test_c4_transform(self) -> None:
        op = Specify()
        state = C4State(T=1, S=1, A=1)
        result = op.transform_c4(state)
        assert result == C4State(T=1, S=0, A=1)

    def test_semantic_transform(self) -> None:
        op = Specify()
        frame = CognitiveFrame(
            c4_state=C4State(T=1, S=1, A=1),
            content={"pattern": "some_pattern"},
        )
        result = op.transform(frame)
        assert result.content["instantiated"] is True
        assert result.content["concretization_level"] == 1


class TestAnalogize:
    def test_c4_transform(self) -> None:
        op = Analogize()
        state = C4State(T=1, S=1, A=0)
        result = op.transform_c4(state)
        assert result == C4State(T=1, S=1, A=1)

    def test_semantic_transform(self) -> None:
        op = Analogize()
        frame = CognitiveFrame(
            c4_state=C4State(T=1, S=1, A=0),
            content={"domain": "physics"},
        )
        result = op.transform(frame)
        assert result.content["analogy_source"] == "physics"
        assert result.content["perspective_shift"] is True


class TestReverse:
    def test_c4_transform(self) -> None:
        op = Reverse()
        state = C4State(T=0, S=0, A=0)
        result = op.transform_c4(state)
        assert result == C4State(T=1, S=1, A=1)

    def test_negation(self) -> None:
        negated = Reverse._negate("all systems are go")
        assert "NOT" in negated

    def test_semantic_transform(self) -> None:
        op = Reverse()
        frame = CognitiveFrame(
            c4_state=C4State(T=0, S=0, A=0),
            content={"proposition": "all birds can fly"},
        )
        result = op.transform(frame)
        assert "negated_proposition" in result.content
        assert result.content["inverted"] is True


class TestCombine:
    def test_c4_transform(self) -> None:
        op = Combine()
        state = C4State(T=1, S=0, A=0)
        result = op.transform_c4(state)
        assert result == C4State(T=1, S=1, A=0)

    def test_merge_frames(self) -> None:
        f1 = CognitiveFrame(c4_state=C4State(T=0, S=0, A=0), content={"a": 1})
        f2 = CognitiveFrame(c4_state=C4State(T=1, S=1, A=1), content={"b": 2})
        merged = Combine.merge([f1, f2])
        assert merged.c4_state.S == 1  # max scale
        assert merged.content["a"] == 1
        assert merged.content["b"] == 2
        assert merged.content["merged_from"] == 2

    def test_merge_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            Combine.merge([])


class TestDecompose:
    def test_c4_transform(self) -> None:
        op = Decompose()
        state = C4State(T=1, S=1, A=1)
        result = op.transform_c4(state)
        assert result == C4State(T=1, S=0, A=1)


class TestTemporalShift:
    def test_forward(self) -> None:
        op = TemporalShift(direction=1)
        state = C4State(T=0, S=1, A=1)
        result = op.transform_c4(state)
        assert result == C4State(T=1, S=1, A=1)

    def test_backward(self) -> None:
        op = TemporalShift(direction=-1)
        state = C4State(T=1, S=1, A=1)
        result = op.transform_c4(state)
        assert result == C4State(T=0, S=1, A=1)

    def test_semantic(self) -> None:
        op = TemporalShift(direction=1)
        frame = CognitiveFrame(c4_state=C4State(T=0, S=1, A=1))
        result = op.transform(frame)
        assert result.content["temporal_context"] == "Present"
        assert result.content["time_shifted"] is True


class TestPerspectiveShift:
    def test_c4_transform(self) -> None:
        op = PerspectiveShift()
        state = C4State(T=1, S=1, A=0)
        result = op.transform_c4(state)
        assert result == C4State(T=1, S=1, A=1)

    def test_semantic(self) -> None:
        op = PerspectiveShift()
        frame = CognitiveFrame(c4_state=C4State(T=1, S=1, A=0))
        result = op.transform(frame)
        assert result.content["viewpoint"] == "Other"


class TestFirstPrinciples:
    def test_c4_transform(self) -> None:
        op = FirstPrinciples()
        state = C4State(T=1, S=0, A=1)
        result = op.transform_c4(state)
        assert result == C4State(T=1, S=2, A=1)

    def test_strips_content(self) -> None:
        op = FirstPrinciples()
        frame = CognitiveFrame(
            c4_state=C4State(T=1, S=0, A=1),
            content={
                "axioms": ["a1", "a2"],
                "constraints": ["c1"],
                "assumptions": ["assume_x"],
                "noise": "should_be_removed",
            },
        )
        result = op.transform(frame)
        assert "axioms" in result.content
        assert "noise" not in result.content
        assert result.content["first_principles_applied"] is True


class TestSystemic:
    def test_c4_transform(self) -> None:
        op = Systemic()
        state = C4State(T=1, S=1, A=0)
        result = op.transform_c4(state)
        assert result == C4State(T=1, S=1, A=2)


class TestRecursive:
    def test_identity_c4(self) -> None:
        op = Recursive(depth=3)
        state = C4State(T=1, S=1, A=1)
        result = op.transform_c4(state)
        assert result == state

    def test_depth_tracking(self) -> None:
        op = Recursive(depth=3)
        frame = CognitiveFrame(c4_state=C4State(T=1, S=1, A=1))
        result = op.transform(frame)
        assert result.content["recursive_depth"] == 3
        assert result.content["self_similar"] is True


class TestConstraintRelax:
    def test_c4_transform(self) -> None:
        op = ConstraintRelax()
        state = C4State(T=0, S=0, A=0)
        result = op.transform_c4(state)
        assert result == C4State(T=1, S=1, A=0)


class TestConstraintTighten:
    def test_c4_transform(self) -> None:
        op = ConstraintTighten()
        state = C4State(T=1, S=1, A=1)
        result = op.transform_c4(state)
        assert result == C4State(T=0, S=0, A=1)


class TestMetaReflect:
    def test_c4_transform(self) -> None:
        op = MetaReflect()
        state = C4State(T=0, S=0, A=0)
        result = op.transform_c4(state)
        assert result == C4State(T=1, S=2, A=0)

    def test_meta_level_increment(self) -> None:
        op = MetaReflect()
        frame = CognitiveFrame(
            c4_state=C4State(T=0, S=0, A=0),
            content={"meta_level": 2},
        )
        result = op.transform(frame)
        assert result.content["meta_level"] == 3
        assert result.content["reflective_mode"] is True


class TestQZRFRegistry:
    def test_all_14_operators_registered(self) -> None:
        operators = QZRFRegistry.all()
        assert len(operators) == 14

    def test_get_by_name(self) -> None:
        op = QZRFRegistry.get("Generalize")
        assert isinstance(op, Generalize)

    def test_get_unknown_raises(self) -> None:
        with pytest.raises(KeyError):
            QZRFRegistry.get("NonExistent")

    def test_names(self) -> None:
        names = QZRFRegistry.names()
        expected = [
            "Generalize", "Specify", "Analogize", "Reverse", "Combine",
            "Decompose", "TemporalShift", "PerspectiveShift", "FirstPrinciples",
            "Systemic", "Recursive", "ConstraintRelax", "ConstraintTighten",
            "MetaReflect",
        ]
        assert sorted(names) == sorted(expected)

    def test_by_type(self) -> None:
        abstraction_ops = QZRFRegistry.by_type(QZRFOpType.ABSTRACTION)
        assert len(abstraction_ops) >= 3
        for op in abstraction_ops:
            assert op.op_type == QZRFOpType.ABSTRACTION


class TestOperatorSequence:
    def test_sequence_application(self) -> None:
        frame = CognitiveFrame(c4_state=C4State(T=0, S=0, A=0))
        ops = [Generalize(), TemporalShift(direction=1)]
        result = apply_operator_sequence(frame, ops)
        # Generalize: S=0→1, TemporalShift: T=0→1
        assert result.c4_state == C4State(T=1, S=1, A=0)

    def test_empty_sequence(self) -> None:
        frame = CognitiveFrame(c4_state=C4State(T=1, S=1, A=1))
        result = apply_operator_sequence(frame, [])
        assert result.c4_state == C4State(T=1, S=1, A=1)


class TestGetOperatorC4Transform:
    def test_named_transform(self) -> None:
        state = C4State(T=0, S=0, A=0)
        result = get_operator_c4_transform("Generalize", state)
        assert result == C4State(T=0, S=1, A=0)


class TestListOperators:
    def test_returns_14(self) -> None:
        names = list_operators()
        assert len(names) == 14


class TestOperatorProperties:
    def test_all_have_descriptions(self) -> None:
        for op in QZRFRegistry.all():
            assert op.description
            assert len(op.description) > 5

    def test_all_transform_c4(self) -> None:
        test_state = C4State(T=1, S=1, A=1)
        for op in QZRFRegistry.all():
            result = op.transform_c4(test_state)
            assert isinstance(result, C4State)
            assert all(0 <= v <= 2 for v in result.to_tuple())
