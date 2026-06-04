"""Tests for src/bayesian/dst.py."""

from __future__ import annotations

import pytest

from src.bayesian.dst import (
    BasicBeliefAssignment,
    EvidenceSensor,
    FrameOfDiscernment,
    combine_multiple,
    compute_dst_result,
    dempster_combination,
)


class TestFrameOfDiscernment:
    def test_create(self):
        frame = FrameOfDiscernment(["A", "B", "C"])
        assert len(frame) == 3
        assert "A" in frame
        assert "D" not in frame

    def test_sorted_elements(self):
        frame = FrameOfDiscernment(["C", "A", "B"])
        assert frame.elements == ("A", "B", "C")

    def test_power_set(self):
        frame = FrameOfDiscernment(["A", "B"])
        ps = frame.power_set()
        assert len(ps) == 4
        assert frozenset() in ps
        assert frozenset({"A", "B"}) in ps

    def test_index_error(self):
        frame = FrameOfDiscernment(["A"])
        with pytest.raises(ValueError, match="not in frame"):
            frame.index("B")


class TestBasicBeliefAssignment:
    def test_assign_singleton(self):
        frame = FrameOfDiscernment(["A", "B"])
        bba = BasicBeliefAssignment(frame)
        bba.assign({"A"}, 0.7)
        assert bba.get_mass({"A"}) == 0.7

    def test_assign_string(self):
        frame = FrameOfDiscernment(["X", "Y"])
        bba = BasicBeliefAssignment(frame)
        bba.assign("X", 0.5)
        assert bba.get_mass({"X"}) == 0.5

    def test_assign_accumulates(self):
        frame = FrameOfDiscernment(["A"])
        bba = BasicBeliefAssignment(frame)
        bba.assign({"A"}, 0.3)
        bba.assign({"A"}, 0.2)
        assert bba.get_mass({"A"}) == pytest.approx(0.5)

    def test_normalize(self):
        frame = FrameOfDiscernment(["A", "B"])
        bba = BasicBeliefAssignment(frame)
        bba.assign({"A"}, 1.0)
        bba.assign({"B"}, 1.0)
        bba.normalize()
        assert bba.get_mass({"A"}) == pytest.approx(0.5)
        assert bba.get_mass({"B"}) == pytest.approx(0.5)

    def test_empty_normalize_raises(self):
        frame = FrameOfDiscernment(["A"])
        bba = BasicBeliefAssignment(frame)
        with pytest.raises(ValueError, match="Cannot normalize empty BBA"):
            bba.normalize()

    def test_negative_mass_raises(self):
        frame = FrameOfDiscernment(["A"])
        bba = BasicBeliefAssignment(frame)
        with pytest.raises(ValueError, match="Mass must be"):
            bba.assign({"A"}, -0.1)

    def test_mass_greater_than_one_raises(self):
        frame = FrameOfDiscernment(["A"])
        bba = BasicBeliefAssignment(frame)
        with pytest.raises(ValueError, match="Mass must be"):
            bba.assign({"A"}, 1.5)

    def test_subset_not_in_frame_raises(self):
        frame = FrameOfDiscernment(["A"])
        bba = BasicBeliefAssignment(frame)
        with pytest.raises(ValueError, match="Subset must be"):
            bba.assign({"B"}, 0.5)

    def test_belief(self):
        frame = FrameOfDiscernment(["A", "B", "C"])
        bba = BasicBeliefAssignment(frame)
        bba.assign({"A"}, 0.3)
        bba.assign({"A", "B"}, 0.4)
        bba.assign({"B", "C"}, 0.3)
        assert bba.belief({"A"}) == pytest.approx(0.3)
        assert bba.belief({"A", "B"}) == pytest.approx(0.7)

    def test_plausibility(self):
        frame = FrameOfDiscernment(["A", "B", "C"])
        bba = BasicBeliefAssignment(frame)
        bba.assign({"A"}, 0.3)
        bba.assign({"A", "B"}, 0.4)
        bba.assign({"C"}, 0.3)
        assert bba.plausibility({"A"}) == pytest.approx(0.7)
        assert bba.plausibility({"C"}) == pytest.approx(0.3)

    def test_focal_elements(self):
        frame = FrameOfDiscernment(["A", "B"])
        bba = BasicBeliefAssignment(frame)
        bba.assign({"A"}, 0.6)
        bba.assign({"A", "B"}, 0.4)
        focal = bba.focal_elements()
        assert frozenset({"A"}) in focal
        assert frozenset({"A", "B"}) in focal


class TestDempsterCombination:
    def test_combination(self):
        frame = FrameOfDiscernment(["A", "B"])
        bba1 = BasicBeliefAssignment(frame)
        bba1.assign({"A"}, 0.7)
        bba1.assign({"A", "B"}, 0.3)

        bba2 = BasicBeliefAssignment(frame)
        bba2.assign({"B"}, 0.6)
        bba2.assign({"A", "B"}, 0.4)

        combined, conflict = dempster_combination(bba1, bba2)
        assert 0.0 <= conflict < 1.0
        assert combined.belief({"A"}) >= 0.0
        assert combined.belief({"B"}) >= 0.0

    def test_frame_mismatch_raises(self):
        frame1 = FrameOfDiscernment(["A", "B"])
        frame2 = FrameOfDiscernment(["A", "C"])
        bba1 = BasicBeliefAssignment(frame1)
        bba2 = BasicBeliefAssignment(frame2)
        with pytest.raises(ValueError, match="same frame"):
            dempster_combination(bba1, bba2)

    def test_combine_multiple(self):
        frame = FrameOfDiscernment(["A", "B"])
        bba1 = BasicBeliefAssignment(frame)
        bba1.assign({"A"}, 0.8)
        bba1.assign({"A", "B"}, 0.2)

        bba2 = BasicBeliefAssignment(frame)
        bba2.assign({"A"}, 0.7)
        bba2.assign({"A", "B"}, 0.3)

        bba3 = BasicBeliefAssignment(frame)
        bba3.assign({"A"}, 0.9)
        bba3.assign({"B"}, 0.1)

        combined = combine_multiple(bba1, bba2, bba3)
        assert combined.belief({"A"}) > 0.5


class TestComputeDSTResult:
    def test_basic(self):
        frame = FrameOfDiscernment(["A", "B"])
        bba = BasicBeliefAssignment(frame)
        bba.assign({"A"}, 0.6)
        bba.assign({"B"}, 0.4)

        result = compute_dst_result(bba, ["A", "B"])
        assert "A" in result.belief
        assert "B" in result.belief
        assert "A" in result.plausibility
        assert "B" in result.plausibility
        assert result.conflict == 0.0


class TestEvidenceSensor:
    def test_from_likelihoods(self):
        frame = FrameOfDiscernment(["H1", "H2"])
        sensor = EvidenceSensor(frame)
        bba = sensor.from_likelihoods({"H1": 0.8, "H2": 0.2}, uncertainty=0.1)
        total = sum(bba.belief({e}) for e in frame.elements)
        assert total == pytest.approx(0.9, abs=0.01)

    def test_from_masses(self):
        frame = FrameOfDiscernment(["X", "Y"])
        sensor = EvidenceSensor(frame)
        bba = sensor.from_masses({frozenset({"X", "Y"}): 1.0})
        assert bba.get_mass({"X", "Y"}) == pytest.approx(1.0)
