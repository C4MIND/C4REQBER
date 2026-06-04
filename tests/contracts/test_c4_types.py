"""Tests for src/contracts/c4_types.py — contract C4State, C4Space protocol."""
from __future__ import annotations

from src.contracts.c4_types import AgencyAxis, C4Path, C4Space, C4State, ScaleAxis, TimeAxis


class TestEnums:
    def test_time_axis(self):
        assert TimeAxis.PAST == 0
        assert TimeAxis.PRESENT == 1
        assert TimeAxis.FUTURE == 2

    def test_scale_axis(self):
        assert ScaleAxis.CONCRETE == 0
        assert ScaleAxis.META == 2

    def test_agency_axis(self):
        assert AgencyAxis.SELF == 0
        assert AgencyAxis.OTHER == 1
        assert AgencyAxis.SYSTEM == 2


class TestContractC4State:
    def test_construction(self):
        s = C4State(T=0, S=1, A=2)
        assert s.T == 0
        assert s.to_tuple() == (0, 1, 2)

    def test_from_tuple(self):
        s = C4State.from_tuple((1, 2, 0))
        assert s.T == 1
        assert s.S == 2

    def test_immutability(self):
        s = C4State(T=0, S=0, A=0)
        assert s.to_tuple() == (0, 0, 0)


class TestC4Path:
    def test_default_empty(self):
        p = C4Path()
        assert len(p) == 0
        assert p.states == []
        assert p.operators == []

    def test_with_states(self):
        s1 = C4State(T=0, S=0, A=0)
        s2 = C4State(T=1, S=1, A=1)
        p = C4Path(states=[s1, s2], operators=["T", "S"])
        assert len(p) == 2
        assert p.operators == ["T", "S"]
