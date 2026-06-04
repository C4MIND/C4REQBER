"""
Additional tests for src/c4/engine.py to reach 80%+ coverage.

Covers: all 27 states, transitions, shortest path, edge cases,
        C4Path, C4Transition, C4Space, predefined constants.
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
# Enums
# ═══════════════════════════════════════════════════════════════════


class TestTimeAxis:
    def test_values(self):
        assert TimeAxis.PAST == 0
        assert TimeAxis.PRESENT == 1
        assert TimeAxis.FUTURE == 2

    def test_all_values(self):
        assert list(TimeAxis) == [TimeAxis.PAST, TimeAxis.PRESENT, TimeAxis.FUTURE]


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
# C4State — Creation & Validation
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
                kwargs = {"T": 1, "S": 1, "A": 1, axis: 3}
                C4State(**kwargs)

    def test_all_27_states_valid(self):
        for t in range(3):
            for s in range(3):
                for a in range(3):
                    state = C4State(T=t, S=s, A=a)
                    assert state.T == t
                    assert state.S == s
                    assert state.A == a


# ═══════════════════════════════════════════════════════════════════
# C4State — Labels
# ═══════════════════════════════════════════════════════════════════


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

    def test_str_all_combinations(self):
        for state in C4State.all_states():
            s = str(state)
            assert state.time_label in s
            assert state.scale_label in s
            assert state.agency_label in s


# ═══════════════════════════════════════════════════════════════════
# C4State — Serialization
# ═══════════════════════════════════════════════════════════════════


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

    def test_all_states_cover_all_combinations(self):
        states = C4State.all_states()
        expected = {
            (t, s, a)
            for t in range(3)
            for s in range(3)
            for a in range(3)
        }
        actual = {st.to_tuple() for st in states}
        assert actual == expected


# ═══════════════════════════════════════════════════════════════════
# C4State — Shifts
# ═══════════════════════════════════════════════════════════════════


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

    def test_shift_scale_wrap(self):
        s = C4State(1, 2, 1)
        assert s.shift_scale(1).to_tuple() == (1, 0, 1)

    def test_shift_agency(self):
        s = C4State(1, 1, 0)
        assert s.shift_agency(1).to_tuple() == (1, 1, 1)

    def test_shift_agency_wrap(self):
        s = C4State(1, 1, 2)
        assert s.shift_agency(1).to_tuple() == (1, 1, 0)

    def test_shift_preserves_other_axes(self):
        s = C4State(1, 2, 0)
        shifted = s.shift_time(1)
        assert shifted.S == 2
        assert shifted.A == 0


# ═══════════════════════════════════════════════════════════════════
# C4State — Invert
# ═══════════════════════════════════════════════════════════════════


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

    def test_invert_all_states(self):
        for state in C4State.all_states():
            double = state.invert().invert()
            assert double == state


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

    def test_from_and_to_states(self):
        t = C4Transition("lambda+", C4State(0, 0, 0), C4State(0, 1, 0))
        assert t.from_state.to_tuple() == (0, 0, 0)
        assert t.to_state.to_tuple() == (0, 1, 0)


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

    def test_states_visited_empty(self):
        path = C4Path(start_state=C4State(0, 0, 0), end_state=C4State(0, 0, 0))
        assert path.states_visited() == []


# ═══════════════════════════════════════════════════════════════════
# C4Space — Initialization
# ═══════════════════════════════════════════════════════════════════


class TestC4SpaceInitialization:
    def test_has_27_states(self):
        space = C4Space()
        assert len(space.states) == 27

    def test_state_map_complete(self):
        space = C4Space()
        assert len(space.state_map) == 27
        for t in range(3):
            for s in range(3):
                for a in range(3):
                    assert (t, s, a) in space.state_map

    def test_operator_map(self):
        space = C4Space()
        expected_ops = {"tau+", "tau-", "lambda+", "lambda-", "kappa+", "kappa-", "iota"}
        assert set(space._ops.keys()) == expected_ops


# ═══════════════════════════════════════════════════════════════════
# C4Space — Hamming Distance
# ═══════════════════════════════════════════════════════════════════


class TestC4SpaceHammingDistance:
    def test_same_state(self):
        space = C4Space()
        s = C4State(1, 1, 1)
        assert space.hamming_distance(s, s) == 0

    def test_one_axis(self):
        space = C4Space()
        assert space.hamming_distance(C4State(0, 1, 1), C4State(1, 1, 1)) == 1

    def test_two_axes(self):
        space = C4Space()
        assert space.hamming_distance(C4State(0, 0, 1), C4State(1, 1, 1)) == 2

    def test_three_axes(self):
        space = C4Space()
        assert space.hamming_distance(C4State(0, 0, 0), C4State(1, 1, 1)) == 3

    def test_max_distance(self):
        space = C4Space()
        assert space.hamming_distance(C4State(0, 0, 0), C4State(2, 2, 2)) == 3

    def test_all_pairs(self):
        space = C4Space()
        states = C4State.all_states()
        for s1 in states:
            for s2 in states:
                h = space.hamming_distance(s1, s2)
                assert 0 <= h <= 3


# ═══════════════════════════════════════════════════════════════════
# C4Space — Shortest Path Length
# ═══════════════════════════════════════════════════════════════════


class TestC4SpaceShortestPathLength:
    def test_same_state(self):
        space = C4Space()
        s = C4State(1, 1, 1)
        assert space.shortest_path_length(s, s) == 0

    def test_one_axis(self):
        space = C4Space()
        assert space.shortest_path_length(C4State(0, 1, 1), C4State(1, 1, 1)) == 1

    def test_three_axes(self):
        space = C4Space()
        assert space.shortest_path_length(C4State(0, 0, 0), C4State(2, 2, 2)) == 3

    def test_theorem_11_maximum(self):
        space = C4Space()
        states = C4State.all_states()
        for s1 in states:
            for s2 in states:
                assert space.shortest_path_length(s1, s2) <= 6

    def test_equals_hamming(self):
        space = C4Space()
        states = C4State.all_states()
        for s1 in states:
            for s2 in states:
                assert space.shortest_path_length(s1, s2) == space.hamming_distance(s1, s2)


# ═══════════════════════════════════════════════════════════════════
# C4Space — Shortest Path
# ═══════════════════════════════════════════════════════════════════


class TestC4SpaceShortestPath:
    def test_same_state(self):
        space = C4Space()
        s = C4State(1, 1, 1)
        path = space.shortest_path(s, s)
        assert path.length == 0
        assert path.start_state == s
        assert path.end_state == s

    def test_one_axis_time(self):
        space = C4Space()
        path = space.shortest_path(C4State(0, 1, 1), C4State(1, 1, 1))
        assert path.length == 1
        assert path.transitions[0].operator in ["tau+", "tau-"]

    def test_one_axis_scale(self):
        space = C4Space()
        path = space.shortest_path(C4State(1, 0, 1), C4State(1, 1, 1))
        assert path.length == 1
        assert path.transitions[0].operator in ["lambda+", "lambda-"]

    def test_one_axis_agency(self):
        space = C4Space()
        path = space.shortest_path(C4State(1, 1, 0), C4State(1, 1, 1))
        assert path.length == 1
        assert path.transitions[0].operator in ["kappa+", "kappa-"]

    def test_two_axes(self):
        space = C4Space()
        path = space.shortest_path(C4State(0, 0, 1), C4State(1, 1, 1))
        assert path.length == 2
        assert path.transitions[-1].to_state.to_tuple() == (1, 1, 1)

    def test_three_axes(self):
        space = C4Space()
        path = space.shortest_path(C4State(0, 0, 0), C4State(2, 2, 2))
        assert path.length == 3
        assert path.transitions[-1].to_state.to_tuple() == (2, 2, 2)

    def test_wraparound(self):
        space = C4Space()
        path = space.shortest_path(C4State(2, 2, 2), C4State(0, 0, 0))
        assert path.length == 3
        assert path.transitions[-1].to_state.to_tuple() == (0, 0, 0)

    def test_path_continuity_all_pairs(self):
        space = C4Space()
        states = C4State.all_states()
        for start in states:
            for end in states:
                path = space.shortest_path(start, end)
                current = start
                for t in path.transitions:
                    assert t.from_state == current
                    current = t.to_state
                assert current.to_tuple() == end.to_tuple()

    def test_path_descriptions_present(self):
        space = C4Space()
        path = space.shortest_path(C4State(0, 0, 0), C4State(1, 1, 1))
        for t in path.transitions:
            assert len(t.description) > 0


# ═══════════════════════════════════════════════════════════════════
# C4Space — Find Path (alias)
# ═══════════════════════════════════════════════════════════════════


class TestC4SpaceFindPath:
    def test_returns_state_list(self):
        space = C4Space()
        start = C4State(0, 0, 0)
        end = C4State(1, 1, 1)
        states = space.find_path(start, end)
        assert states[0] == start
        assert states[-1].to_tuple() == end.to_tuple()
        assert len(states) == space.shortest_path(start, end).length + 1

    def test_same_state(self):
        space = C4Space()
        s = C4State(1, 1, 1)
        states = space.find_path(s, s)
        assert len(states) == 1
        assert states[0] == s


# ═══════════════════════════════════════════════════════════════════
# C4Space — Neighbors
# ═══════════════════════════════════════════════════════════════════


class TestC4SpaceNeighbors:
    def test_returns_tuples(self):
        space = C4Space()
        neighbors = space.neighbors(C4State(1, 1, 1))
        assert len(neighbors) == 7
        for name, state in neighbors:
            assert isinstance(name, str)
            assert isinstance(state, C4State)

    def test_neighbors_differ_by_one_op(self):
        space = C4Space()
        state = C4State(1, 1, 1)
        neighbors = space.neighbors(state)
        for _, n in neighbors:
            assert space.hamming_distance(state, n) <= 1 or n == state.invert()

    def test_neighbors_include_all_operators(self):
        space = C4Space()
        state = C4State(1, 1, 1)
        neighbors = space.neighbors(state)
        op_names = {name for name, _ in neighbors}
        expected = {"tau+", "tau-", "lambda+", "lambda-", "kappa+", "kappa-", "iota"}
        assert op_names == expected


# ═══════════════════════════════════════════════════════════════════
# C4Space — Get State
# ═══════════════════════════════════════════════════════════════════


class TestC4SpaceGetState:
    def test_by_coords(self):
        space = C4Space()
        assert space.get_state(0, 0, 0).to_tuple() == (0, 0, 0)
        assert space.get_state(2, 1, 0).to_tuple() == (2, 1, 0)

    def test_modulo(self):
        space = C4Space()
        assert space.get_state(3, 4, 5).to_tuple() == (0, 1, 2)

    def test_negative_modulo(self):
        space = C4Space()
        assert space.get_state(-1, -2, -3).to_tuple() == (2, 1, 0)


# ═══════════════════════════════════════════════════════════════════
# C4Space — State By Name
# ═══════════════════════════════════════════════════════════════════


class TestC4SpaceStateByName:
    def test_time_label(self):
        space = C4Space()
        s = space.state_by_name("Present")
        assert s is not None
        assert s.T == 1

    def test_scale_label(self):
        space = C4Space()
        s = space.state_by_name("Meta")
        assert s is not None
        assert s.S == 2

    def test_agency_label(self):
        space = C4Space()
        s = space.state_by_name("System")
        assert s is not None
        assert s.A == 2

    def test_not_found(self):
        space = C4Space()
        assert space.state_by_name("NonExistent") is None

    def test_case_insensitive(self):
        space = C4Space()
        s = space.state_by_name("present")
        assert s is not None
        assert s.T == 1


# ═══════════════════════════════════════════════════════════════════
# C4Space — All Paths
# ═══════════════════════════════════════════════════════════════════


class TestC4SpaceAllPaths:
    def test_finds_at_least_one(self):
        space = C4Space()
        paths = space.all_paths(C4State(0, 0, 0), C4State(1, 0, 0), max_length=3)
        assert len(paths) >= 1

    def test_respects_max_length(self):
        space = C4Space()
        paths = space.all_paths(C4State(0, 0, 0), C4State(2, 2, 2), max_length=6)
        for p in paths:
            assert p.length <= 6

    def test_paths_reach_target(self):
        space = C4Space()
        start = C4State(0, 0, 0)
        end = C4State(1, 1, 1)
        paths = space.all_paths(start, end, max_length=4)
        for p in paths:
            assert p.transitions[-1].to_state.to_tuple() == end.to_tuple()

    def test_shortest_path_found(self):
        space = C4Space()
        paths = space.all_paths(C4State(0, 0, 0), C4State(1, 0, 0), max_length=3)
        lengths = [p.length for p in paths]
        assert min(lengths) == 1  # direct path


# ═══════════════════════════════════════════════════════════════════
# Theorem 11 — Maximum 6 steps
# ═══════════════════════════════════════════════════════════════════


class TestTheorem11:
    def test_all_pairs_within_6(self):
        space = C4Space()
        states = C4State.all_states()
        for s1 in states:
            for s2 in states:
                path = space.shortest_path(s1, s2)
                assert path.length <= 3  # actual path uses 1 step per axis
                assert space.shortest_path_length(s1, s2) <= 6

    def test_hamming_bound(self):
        space = C4Space()
        states = C4State.all_states()
        for s1 in states:
            for s2 in states:
                h = space.hamming_distance(s1, s2)
                assert h <= 3
                assert space.shortest_path_length(s1, s2) == h

    def test_path_equals_hamming(self):
        space = C4Space()
        states = C4State.all_states()
        for s1 in states:
            for s2 in states:
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

    def test_all_predefined_in_all_states(self):
        all_states = C4State.all_states()
        assert C4_ORIGIN in all_states
        assert C4_PHI_ATTRACTOR in all_states
        assert C4_SYSTEMIC in all_states
        assert C4_FUTURE_META in all_states
        assert C4_PRESENT_ABSTRACT_SYSTEM in all_states


# ═══════════════════════════════════════════════════════════════════
# Operator Application
# ═══════════════════════════════════════════════════════════════════


class TestOperatorApplication:
    def test_tau_plus(self):
        space = C4Space()
        op = space._ops["tau+"]
        result = op(C4State(0, 0, 0))
        assert result.to_tuple() == (1, 0, 0)

    def test_tau_minus(self):
        space = C4Space()
        op = space._ops["tau-"]
        result = op(C4State(0, 0, 0))
        assert result.to_tuple() == (2, 0, 0)

    def test_lambda_plus(self):
        space = C4Space()
        op = space._ops["lambda+"]
        result = op(C4State(0, 0, 0))
        assert result.to_tuple() == (0, 1, 0)

    def test_lambda_minus(self):
        space = C4Space()
        op = space._ops["lambda-"]
        result = op(C4State(0, 0, 0))
        assert result.to_tuple() == (0, 2, 0)

    def test_kappa_plus(self):
        space = C4Space()
        op = space._ops["kappa+"]
        result = op(C4State(0, 0, 0))
        assert result.to_tuple() == (0, 0, 1)

    def test_kappa_minus(self):
        space = C4Space()
        op = space._ops["kappa-"]
        result = op(C4State(0, 0, 0))
        assert result.to_tuple() == (0, 0, 2)

    def test_iota(self):
        space = C4Space()
        op = space._ops["iota"]
        result = op(C4State(0, 0, 0))
        assert result.to_tuple() == (2, 2, 2)

    def test_operator_period_3(self):
        space = C4Space()
        for op_name in ["tau+", "lambda+", "kappa+"]:
            op = space._ops[op_name]
            state = C4State(0, 0, 0)
            s1 = op(state)
            s2 = op(s1)
            s3 = op(s2)
            assert s3 == state

    def test_all_operators_from_all_states(self):
        space = C4Space()
        states = C4State.all_states()
        for state in states:
            for op_name, op in space._ops.items():
                result = op(state)
                assert isinstance(result, C4State)
                assert 0 <= result.T <= 2
                assert 0 <= result.S <= 2
                assert 0 <= result.A <= 2
