"""
Tests for canonical C4State in src/c4/types.py.

Verifies:
- All 27 states exist and are valid
- Modular arithmetic wrap-around
- Distance symmetry and triangle inequality
- Backward-compatible methods
"""
from __future__ import annotations

import pytest

from c4.types import Agency, C4State, Scale, Time, all_27_states


class TestEnums:
    def test_time_values(self):
        assert Time.PAST == 0
        assert Time.PRESENT == 1
        assert Time.FUTURE == 2

    def test_scale_values(self):
        assert Scale.CONCRETE == 0
        assert Scale.ABSTRACT == 1
        assert Scale.META == 2

    def test_agency_values(self):
        assert Agency.SELF == 0
        assert Agency.OTHER == 1
        assert Agency.SYSTEM == 2


class TestAll27States:
    def test_count(self):
        states = all_27_states()
        assert len(states) == 27

    def test_uniqueness(self):
        states = all_27_states()
        assert len(set(states)) == 27

    def test_all_valid(self):
        for s in all_27_states():
            assert 0 <= s.t <= 2
            assert 0 <= s.s <= 2
            assert 0 <= s.a <= 2

    def test_state_names_complete(self):
        for s in all_27_states():
            assert s.name is not None
            assert len(s.name) > 0


class TestConstruction:
    def test_positional(self):
        s = C4State(1, 2, 0)
        assert s.t == 1
        assert s.s == 2
        assert s.a == 0

    def test_keyword_tsa(self):
        s = C4State(t=1, s=2, a=0)
        assert s.to_tuple() == (1, 2, 0)

    def test_keyword_TSA(self):
        s = C4State(T=1, S=2, A=0)
        assert s.to_tuple() == (1, 2, 0)

    def test_mixed_kwargs(self):
        s = C4State(t=1, S=2, a=0)
        assert s.to_tuple() == (1, 2, 0)

    def test_modulo_wrap(self):
        s = C4State.from_coords(3, 4, 5)
        assert s.t == 0
        assert s.s == 1
        assert s.a == 2

    def test_negative_modulo(self):
        s = C4State.from_coords(-1, -2, -3)
        assert s.t == 2  # -1 % 3 = 2
        assert s.s == 1  # -2 % 3 = 1
        assert s.a == 0  # -3 % 3 = 0

    def test_validation_upper(self):
        with pytest.raises(ValueError):
            C4State(t=3, s=0, a=0)

    def test_validation_lower(self):
        with pytest.raises(ValueError):
            C4State(t=-1, s=0, a=0)

    def test_immutable(self):
        s = C4State(1, 1, 1)
        with pytest.raises(AttributeError):
            s.t = 2  # type: ignore[misc]

    def test_property_aliases(self):
        s = C4State(1, 2, 0)
        assert s.T == s.t
        assert s.S == s.s
        assert s.A == s.a


class TestShiftOperators:
    def test_shift_time_forward(self):
        s = C4State(0, 1, 1)
        assert s.shift_time(1).to_tuple() == (1, 1, 1)

    def test_shift_time_backward(self):
        s = C4State(0, 1, 1)
        assert s.shift_time(-1).to_tuple() == (2, 1, 1)

    def test_shift_time_wrap(self):
        s = C4State(2, 1, 1)
        assert s.shift_time(1).to_tuple() == (0, 1, 1)

    def test_shift_scale(self):
        s = C4State(1, 0, 1)
        assert s.shift_scale(1).to_tuple() == (1, 1, 1)

    def test_shift_agency(self):
        s = C4State(1, 1, 0)
        assert s.shift_agency(1).to_tuple() == (1, 1, 1)

    def test_shift_preserves_other_axes(self):
        s = C4State(1, 2, 0)
        shifted = s.shift_time(1)
        assert shifted.s == 2
        assert shifted.a == 0


class TestInvert:
    def test_origin(self):
        s = C4State(0, 0, 0)
        assert s.invert().to_tuple() == (2, 2, 2)

    def test_max(self):
        s = C4State(2, 2, 2)
        assert s.invert().to_tuple() == (0, 0, 0)

    def test_middle(self):
        s = C4State(1, 1, 1)
        assert s.invert().to_tuple() == (1, 1, 1)

    def test_double_invert_identity(self):
        for state in all_27_states():
            assert state.invert().invert() == state

    def test_period_2(self):
        """Invert applied twice must return identity for all states."""
        for s in all_27_states():
            assert s.invert().invert() == s


class TestSymmetricDistance:
    def test_distance_to_self_is_zero(self):
        for s in all_27_states():
            assert s.distance(s) == 0

    def test_symmetry(self):
        states = all_27_states()
        for a in states:
            for b in states:
                assert a.distance(b) == b.distance(a)

    def test_triangle_inequality(self):
        states = all_27_states()
        for a in states:
            for b in states:
                for c in states:
                    assert a.distance(c) <= a.distance(b) + b.distance(c)

    def test_diameter_is_3(self):
        max_dist = max(
            a.distance(b) for a in all_27_states() for b in all_27_states()
        )
        assert max_dist == 3

    def test_antipodal_distance(self):
        origin = C4State(0, 0, 0)
        antipode = C4State(2, 2, 2)
        assert origin.distance(antipode) == 3

    def test_known_distances(self):
        s00 = C4State(0, 0, 0)
        s12 = C4State(1, 2, 0)
        # t: min(|0-1|, 2) = 1, s: min(|0-2|, 1) = 1, a: 0
        assert s00.distance(s12) == 2

        s22 = C4State(2, 2, 2)
        # Each axis: min(|0-2|, 1) = 1, total = 3
        assert s00.distance(s22) == 3


class TestDirectedDistance:
    def test_directed_to_self_is_zero(self):
        for s in all_27_states():
            assert s.directed_distance(s) == 0

    def test_asymmetry(self):
        s00 = C4State(0, 0, 0)
        s01 = C4State(0, 0, 1)
        assert s00.directed_distance(s01) == 1
        assert s01.directed_distance(s00) == 2

    def test_directed_triangle_inequality(self):
        states = all_27_states()
        for a in states:
            for b in states:
                for c in states:
                    assert (
                        a.directed_distance(c)
                        <= a.directed_distance(b) + b.directed_distance(c)
                    )

    def test_diameter_is_6(self):
        max_dist = max(
            a.directed_distance(b)
            for a in all_27_states()
            for b in all_27_states()
        )
        assert max_dist == 6

    def test_antipodal_directed_distance(self):
        origin = C4State(0, 0, 0)
        antipode = C4State(2, 2, 2)
        assert origin.directed_distance(antipode) == 6


class TestNeighbors:
    def test_count_is_6(self):
        for s in all_27_states():
            assert len(s.neighbors()) == 6

    def test_wraparound_time(self):
        s = C4State(0, 1, 1)
        neighbors = s.neighbors()
        # shift_time(-1) wraps to 2
        assert C4State(2, 1, 1) in neighbors
        # shift_time(1) goes to 1
        assert C4State(1, 1, 1) in neighbors

    def test_wraparound_scale(self):
        s = C4State(1, 0, 1)
        neighbors = s.neighbors()
        assert C4State(1, 2, 1) in neighbors  # wrap backward
        assert C4State(1, 1, 1) in neighbors

    def test_wraparound_agency(self):
        s = C4State(1, 1, 0)
        neighbors = s.neighbors()
        assert C4State(1, 1, 2) in neighbors  # wrap backward
        assert C4State(1, 1, 1) in neighbors

    def test_neighbors_are_distinct(self):
        for s in all_27_states():
            nbrs = s.neighbors()
            assert len(nbrs) == len(set(nbrs))


class TestShortestPath:
    def test_same_state_empty(self):
        s = C4State(1, 1, 1)
        assert s.shortest_path(s) == []

    def test_adjacent_one_step(self):
        s = C4State(0, 0, 0)
        target = C4State(1, 0, 0)
        path = s.shortest_path(target)
        assert len(path) == 1
        assert path[0] == target

    def test_wraparound_path(self):
        s = C4State(0, 0, 0)
        target = C4State(2, 0, 0)
        # shortest symmetric path: 0 -> 2 is distance 1 (wrap)
        path = s.shortest_path(target)
        assert len(path) == 1
        assert path[0] == target

    def test_path_reaches_target(self):
        states = all_27_states()
        for start in states:
            for end in states:
                path = start.shortest_path(end)
                if path:
                    assert path[-1] == end
                else:
                    assert start == end

    def test_path_length_matches_distance(self):
        states = all_27_states()
        for start in states[:10]:
            for end in states[:10]:
                path = start.shortest_path(end)
                assert len(path) == start.distance(end)


class TestBackwardCompat:
    def test_apply_T(self):
        s = C4State(0, 1, 2)
        assert s.apply_T() == C4State(1, 1, 2)
        assert s.apply_T().apply_T() == C4State(2, 1, 2)
        assert s.apply_T().apply_T().apply_T() == s

    def test_apply_S(self):
        s = C4State(0, 1, 2)
        assert s.apply_S() == C4State(0, 2, 2)
        assert s.apply_S().apply_S() == C4State(0, 0, 2)
        assert s.apply_S().apply_S().apply_S() == s

    def test_apply_A(self):
        s = C4State(0, 1, 2)
        assert s.apply_A() == C4State(0, 1, 0)
        assert s.apply_A().apply_A() == C4State(0, 1, 1)
        assert s.apply_A().apply_A().apply_A() == s

    def test_cyclic_distance(self):
        assert C4State.cyclic_distance(0, 0) == 0
        assert C4State.cyclic_distance(0, 1) == 1
        assert C4State.cyclic_distance(0, 2) == 2
        assert C4State.cyclic_distance(1, 0) == 2
        assert C4State.cyclic_distance(2, 0) == 1

    def test_hamming_distance_alias(self):
        s00 = C4State(0, 0, 0)
        s22 = C4State(2, 2, 2)
        assert s00.hamming_distance(s22) == 6  # directed_distance alias

    def test_is_antipode(self):
        s00 = C4State(0, 0, 0)
        s22 = C4State(2, 2, 2)
        assert s00.is_antipode(s22)

    def test_canonical_path(self):
        s00 = C4State(0, 0, 0)
        s22 = C4State(2, 2, 2)
        path = s00.canonical_path(s22)
        assert s00.apply_path(path) == s22
