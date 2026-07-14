"""
Comprehensive tests for src/c4/engine.py

Covers: C4 states, transitions, shortest path, Theorem 11,
        C4Space operations, C4Path, predefined constants
"""
from __future__ import annotations

import pytest

from src.c4.engine import (
    C4_FUTURE_META,
    C4_ORIGIN,
    C4_PHI_ATTRACTOR,
    C4_PRESENT_ABSTRACT_SYSTEM,
    C4_SYSTEMIC,
    AgencyAxis,
    C4Path,
    C4Space,
    C4State,
    C4Transition,
    ScaleAxis,
    TimeAxis,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def space():
    """Fresh C4Space instance."""
    return C4Space()


@pytest.fixture
def all_states():
    """All 27 C4 states."""
    return C4State.all_states()


# ═══════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════


class TestTimeAxis:
    def test_values(self):
        assert TimeAxis.PAST == 0
        assert TimeAxis.PRESENT == 1
        assert TimeAxis.FUTURE == 2


class TestScaleAxis:
    def test_values(self):
        assert ScaleAxis.CONCRETE == 0
        assert ScaleAxis.ABSTRACT == 1
        assert ScaleAxis.META == 2


class TestAgencyAxis:
    def test_values(self):
        assert AgencyAxis.SELF == 0
        assert AgencyAxis.OTHER == 1
        assert AgencyAxis.SYSTEM == 2


# ═══════════════════════════════════════════════════════════════════
# C4State
# ═══════════════════════════════════════════════════════════════════


class TestC4StateCreation:
    def test_basic(self):
        state = C4State(T=1, S=0, A=2)
        assert state.T == 1
        assert state.S == 0
        assert state.A == 2

    def test_immutable(self):
        state = C4State(T=1, S=0, A=2)
        with pytest.raises(AttributeError):
            state.T = 2  # type: ignore[misc]

    def test_validation_upper_bound(self):
        with pytest.raises(ValueError, match="must be in"):
            C4State(T=3, S=0, A=0)

    def test_validation_lower_bound(self):
        with pytest.raises(ValueError, match="must be in"):
            C4State(T=-1, S=0, A=0)

    def test_validation_all_axes(self):
        for axis in ["T", "S", "A"]:
            with pytest.raises(ValueError):
                C4State(**{"T": 1, "S": 1, "A": 1, axis: 3})


class TestC4StateLabels:
    def test_time_labels(self):
        assert C4State(0, 0, 0).time_label == "Past"
        assert C4State(1, 0, 0).time_label == "Present"
        assert C4State(2, 0, 0).time_label == "Future"

    def test_scale_labels(self):
        assert C4State(0, 0, 0).scale_label == "Concrete"
        assert C4State(0, 1, 0).scale_label == "Abstract"
        assert C4State(0, 2, 0).scale_label == "Meta"

    def test_agency_labels(self):
        assert C4State(0, 0, 0).agency_label == "Self"
        assert C4State(0, 0, 1).agency_label == "Other"
        assert C4State(0, 0, 2).agency_label == "System"

    def test_str_format(self):
        state = C4State(1, 1, 1)
        s = str(state)
        assert "Present" in s
        assert "Abstract" in s
        assert "Other" in s
        assert "F⟨" in s


class TestC4StateSerialization:
    def test_to_tuple(self):
        assert C4State(1, 0, 2).to_tuple() == (1, 0, 2)

    def test_from_coords_modulo(self):
        state = C4State.from_coords(3, 4, 5)
        assert state.T == 0
        assert state.S == 1
        assert state.A == 2

    def test_from_coords_negative(self):
        state = C4State.from_coords(-1, -2, -3)
        assert state.T == 2  # -1 % 3 = 2
        assert state.S == 1  # -2 % 3 = 1
        assert state.A == 0  # -3 % 3 = 0

    def test_all_states_count(self):
        states = C4State.all_states()
        assert len(states) == 27

    def test_all_states_unique(self):
        states = C4State.all_states()
        tuples = [s.to_tuple() for s in states]
        assert len(set(tuples)) == 27


class TestC4StateShifts:
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
        assert shifted.S == 2
        assert shifted.A == 0


class TestC4StateInvert:
    def test_origin_inverts_to_max(self):
        s = C4State(0, 0, 0)
        assert s.invert().to_tuple() == (2, 2, 2)

    def test_max_inverts_to_origin(self):
        s = C4State(2, 2, 2)
        assert s.invert().to_tuple() == (0, 0, 0)

    def test_middle_stays(self):
        s = C4State(1, 1, 1)
        assert s.invert().to_tuple() == (1, 1, 1)

    def test_double_invert_identity(self):
        s = C4State(0, 1, 2)
        assert s.invert().invert() == s


# ═══════════════════════════════════════════════════════════════════
# C4Transition
# ═══════════════════════════════════════════════════════════════════


class TestC4Transition:
    def test_creation(self):
        t = C4Transition("tau+", C4State(0, 0, 0), C4State(1, 0, 0), "Time forward")
        assert t.operator == "tau+"
        assert t.description == "Time forward"

    def test_default_description(self):
        t = C4Transition("tau+", C4State(0, 0, 0), C4State(1, 0, 0))
        assert t.description == ""


# ═══════════════════════════════════════════════════════════════════
# C4Path
# ═══════════════════════════════════════════════════════════════════


class TestC4Path:
    def test_empty(self):
        path = C4Path()
        assert path.length == 0
        assert path.operators == []
        assert path.states_visited() == []
        assert path.start_state is None
        assert path.end_state is None

    def test_with_transitions(self):
        t1 = C4Transition("tau+", C4State(0, 0, 0), C4State(1, 0, 0))
        t2 = C4Transition("lambda+", C4State(1, 0, 0), C4State(1, 1, 0))
        path = C4Path(transitions=[t1, t2], start_state=C4State(0, 0, 0), end_state=C4State(1, 1, 0))
        assert path.length == 2
        assert path.operators == ["tau+", "lambda+"]

    def test_states_visited(self):
        t1 = C4Transition("tau+", C4State(0, 0, 0), C4State(1, 0, 0))
        path = C4Path(transitions=[t1], start_state=C4State(0, 0, 0), end_state=C4State(1, 0, 0))
        states = path.states_visited()
        assert len(states) == 2
        assert states[0].to_tuple() == (0, 0, 0)
        assert states[1].to_tuple() == (1, 0, 0)


# ═══════════════════════════════════════════════════════════════════
# C4Space
# ═══════════════════════════════════════════════════════════════════


class TestC4SpaceInitialization:
    def test_has_27_states(self, space):
        assert len(space.states) == 27

    def test_state_map_complete(self, space):
        assert len(space.state_map) == 27
        for t in range(3):
            for s in range(3):
                for a in range(3):
                    assert (t, s, a) in space.state_map

    def test_operator_map(self, space):
        expected_ops = {"tau+", "tau-", "lambda+", "lambda-", "kappa+", "kappa-", "iota"}
        assert set(space._ops.keys()) == expected_ops


class TestC4SpaceHammingDistance:
    def test_same_state(self, space):
        s = C4State(1, 1, 1)
        assert space.hamming_distance(s, s) == 0

    def test_one_axis(self, space):
        assert space.hamming_distance(C4State(0, 1, 1), C4State(1, 1, 1)) == 1

    def test_two_axes(self, space):
        assert space.hamming_distance(C4State(0, 0, 1), C4State(1, 1, 1)) == 2

    def test_three_axes(self, space):
        assert space.hamming_distance(C4State(0, 0, 0), C4State(1, 1, 1)) == 3

    def test_max_distance(self, space):
        assert space.hamming_distance(C4State(0, 0, 0), C4State(2, 2, 2)) == 3


class TestC4SpaceShortestPathLength:
    def test_same_state(self, space):
        s = C4State(1, 1, 1)
        assert space.shortest_path_length(s, s) == 0

    def test_one_axis(self, space):
        assert space.shortest_path_length(C4State(0, 1, 1), C4State(1, 1, 1)) == 1

    def test_three_axes(self, space):
        assert space.shortest_path_length(C4State(0, 0, 0), C4State(2, 2, 2)) == 3

    def test_theorem_11_maximum(self, space, all_states):
        for s1 in all_states:
            for s2 in all_states:
                assert space.shortest_path_length(s1, s2) <= 6


class TestC4SpaceShortestPath:
    def test_same_state(self, space):
        s = C4State(1, 1, 1)
        path = space.shortest_path(s, s)
        assert path.length == 0
        assert path.start_state == s
        assert path.end_state == s

    def test_one_axis_time(self, space):
        path = space.shortest_path(C4State(0, 1, 1), C4State(1, 1, 1))
        assert path.length == 1
        assert path.transitions[0].operator in ["tau+", "tau-"]

    def test_one_axis_scale(self, space):
        path = space.shortest_path(C4State(1, 0, 1), C4State(1, 1, 1))
        assert path.length == 1
        assert path.transitions[0].operator in ["lambda+", "lambda-"]

    def test_one_axis_agency(self, space):
        path = space.shortest_path(C4State(1, 1, 0), C4State(1, 1, 1))
        assert path.length == 1
        assert path.transitions[0].operator in ["kappa+", "kappa-"]

    def test_two_axes(self, space):
        path = space.shortest_path(C4State(0, 0, 1), C4State(1, 1, 1))
        assert path.length == 2
        assert path.transitions[-1].to_state.to_tuple() == (1, 1, 1)

    def test_three_axes(self, space):
        path = space.shortest_path(C4State(0, 0, 0), C4State(2, 2, 2))
        assert path.length == 3
        assert path.transitions[-1].to_state.to_tuple() == (2, 2, 2)

    def test_wraparound(self, space):
        path = space.shortest_path(C4State(2, 2, 2), C4State(0, 0, 0))
        assert path.length == 3
        assert path.transitions[-1].to_state.to_tuple() == (0, 0, 0)

    def test_path_continuity(self, space, all_states):
        for start in all_states[:10]:
            for end in all_states[:10]:
                path = space.shortest_path(start, end)
                current = start
                for t in path.transitions:
                    assert t.from_state == current
                    current = t.to_state
                assert current.to_tuple() == end.to_tuple()


class TestC4SpaceFindPath:
    def test_returns_state_list(self, space):
        start = C4State(0, 0, 0)
        end = C4State(1, 1, 1)
        states = space.find_path(start, end)
        assert states[0] == start
        assert states[-1].to_tuple() == end.to_tuple()
        assert len(states) == space.shortest_path(start, end).length + 1

    def test_same_state(self, space):
        s = C4State(1, 1, 1)
        states = space.find_path(s, s)
        assert len(states) == 1
        assert states[0] == s


class TestC4SpaceNeighbors:
    def test_returns_tuples(self, space):
        neighbors = space.neighbors(C4State(1, 1, 1))
        assert len(neighbors) == 7
        for name, state in neighbors:
            assert isinstance(name, str)
            assert isinstance(state, C4State)

    def test_neighbors_differ_by_one_op(self, space):
        state = C4State(1, 1, 1)
        neighbors = space.neighbors(state)
        for _, n in neighbors:
            assert space.hamming_distance(state, n) <= 1 or n == state.invert()


class TestC4SpaceGetState:
    def test_by_coords(self, space):
        assert space.get_state(0, 0, 0).to_tuple() == (0, 0, 0)
        assert space.get_state(2, 1, 0).to_tuple() == (2, 1, 0)

    def test_modulo(self, space):
        assert space.get_state(3, 4, 5).to_tuple() == (0, 1, 2)


class TestC4SpaceStateByName:
    def test_time_label(self, space):
        s = space.state_by_name("Present")
        assert s is not None
        assert s.T == 1

    def test_scale_label(self, space):
        s = space.state_by_name("Meta")
        assert s is not None
        assert s.S == 2

    def test_agency_label(self, space):
        s = space.state_by_name("System")
        assert s is not None
        assert s.A == 2

    def test_not_found(self, space):
        assert space.state_by_name("NonExistent") is None

    def test_case_insensitive(self, space):
        s = space.state_by_name("present")
        assert s is not None
        assert s.T == 1


class TestC4SpaceAllPaths:
    def test_finds_at_least_one(self, space):
        paths = space.all_paths(C4State(0, 0, 0), C4State(1, 0, 0), max_length=3)
        assert len(paths) >= 1

    def test_respects_max_length(self, space):
        paths = space.all_paths(C4State(0, 0, 0), C4State(2, 2, 2), max_length=6)
        for p in paths:
            assert p.length <= 6

    def test_paths_reach_target(self, space):
        start = C4State(0, 0, 0)
        end = C4State(1, 1, 1)
        paths = space.all_paths(start, end, max_length=4)
        for p in paths:
            assert p.transitions[-1].to_state.to_tuple() == end.to_tuple()


# ═══════════════════════════════════════════════════════════════════
# Theorem 11 — Maximum 6 steps
# ═══════════════════════════════════════════════════════════════════


class TestTheorem11:
    def test_all_pairs_within_6(self, space, all_states):
        for s1 in all_states:
            for s2 in all_states:
                path = space.shortest_path(s1, s2)
                assert path.length <= 3  # actual path uses 1 step per axis
                assert space.shortest_path_length(s1, s2) <= 6

    def test_hamming_bound(self, space, all_states):
        for s1 in all_states:
            for s2 in all_states:
                h = space.hamming_distance(s1, s2)
                assert h <= 3
                assert space.shortest_path_length(s1, s2) == h

    def test_path_equals_hamming(self, space, all_states):
        for s1 in all_states[:9]:
            for s2 in all_states[:9]:
                path = space.shortest_path(s1, s2)
                h = space.hamming_distance(s1, s2)
                assert path.length == h


# ═══════════════════════════════════════════════════════════════════
# Predefined Constants
# ═══════════════════════════════════════════════════════════════════


class TestPredefinedStates:
    def test_origin(self):
        assert C4_ORIGIN.to_tuple() == (0, 0, 0)

    def test_phi_attractor(self):
        assert C4_PHI_ATTRACTOR.to_tuple() == (1, 0, 1)

    def test_systemic(self):
        assert C4_SYSTEMIC.to_tuple() == (1, 2, 2)

    def test_future_meta(self):
        assert C4_FUTURE_META.to_tuple() == (2, 2, 2)

    def test_present_abstract_system(self):
        assert C4_PRESENT_ABSTRACT_SYSTEM.to_tuple() == (1, 1, 2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
