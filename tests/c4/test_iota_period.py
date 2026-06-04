"""
Tests for the iota (inversion) operator.

iota is an involution: period 2, not period 3.
It is NOT part of the formally proven Z₃ generator set.
"""
from __future__ import annotations

import pytest

from c4.core import C4State, all_27_states
from c4.engine import C4Space
from c4.extended_operators import verify_iota_involution


class TestIotaPeriod:
    def test_iota_is_involution(self):
        """iota(iota(x)) == x for all states."""
        for s in all_27_states():
            assert s.invert().invert() == s

    def test_iota_period_2_not_3(self):
        """iota² = id, but iota¹ ≠ id (for non-fixed states)."""
        s = C4State(t=0, s=0, a=0)
        assert s.invert() != s  # iota is not identity
        assert s.invert().invert() == s  # iota² is identity

    def test_iota_fixed_point(self):
        """Only (1,1,1) is fixed under iota."""
        fixed = C4State(t=1, s=1, a=1)
        assert fixed.invert() == fixed

        # All other states are moved
        for s in all_27_states():
            if s != fixed:
                assert s.invert() != s

    def test_iota_distinct_from_period_3(self):
        """iota is not a cyclic shift."""
        s = C4State(t=0, s=0, a=0)
        iota_result = s.invert()
        # None of the 6 period-3 shifts produce the iota result
        shifts = [
            s.shift_time(1), s.shift_time(-1),
            s.shift_scale(1), s.shift_scale(-1),
            s.shift_agency(1), s.shift_agency(-1),
        ]
        assert iota_result not in shifts

    def test_engine_iota_operator(self):
        """C4Space includes iota as an extended operator."""
        space = C4Space()
        s = C4State(t=0, s=1, a=2)
        neighbors = space.neighbors(s)
        op_names = {name for name, _ in neighbors}
        assert "iota" in op_names

    def test_verify_iota_involution_helper(self):
        """Extended operator helper verifies iota² = id."""
        for s in all_27_states():
            assert verify_iota_involution(s)
