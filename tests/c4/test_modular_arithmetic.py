"""
Tests for modular arithmetic correctness in Z₃³.

Verifies that ALL shift operations use % 3 (no clamping)
and that wrap-around works correctly.
"""
from __future__ import annotations

import pytest

from c4.engine import C4State


class TestModularArithmetic:
    def test_shift_time_wrap_2_to_0(self):
        """t=2 + 1 = 0 (mod 3)."""
        s = C4State(t=2, s=0, a=0)
        result = s.shift_time(1)
        assert result.t == 0

    def test_shift_time_wrap_0_to_2(self):
        """t=0 - 1 = 2 (mod 3)."""
        s = C4State(t=0, s=0, a=0)
        result = s.shift_time(-1)
        assert result.t == 2

    def test_shift_scale_wrap_2_to_0(self):
        s = C4State(t=0, s=2, a=0)
        result = s.shift_scale(1)
        assert result.s == 0

    def test_shift_agency_wrap_2_to_0(self):
        s = C4State(t=0, s=0, a=2)
        result = s.shift_agency(1)
        assert result.a == 0

    def test_all_wraparound_cases(self):
        """Exhaustive check: (2 + 1) % 3 == 0 on all axes."""
        for axis_shift in ["shift_time", "shift_scale", "shift_agency"]:
            s = C4State(t=2, s=2, a=2)
            result = getattr(s, axis_shift)(1)
            coord = {"shift_time": "t", "shift_scale": "s", "shift_agency": "a"}[axis_shift]
            assert getattr(result, coord) == 0, f"{axis_shift} failed wrap-around"

    def test_no_clamping(self):
        """Ensure coordinates wrap, not clamp."""
        s = C4State(t=0, s=0, a=0)
        # If clamped, shift_time(-1) would give t=0 or raise
        # With modulo, it gives t=2
        result = s.shift_time(-1)
        assert result.t == 2

    def test_from_coords_modulo(self):
        """C4State.from_coords applies % 3."""
        s = C4State.from_coords(3, 4, 5)
        assert s.t == 0
        assert s.s == 1
        assert s.a == 2

    def test_negative_modulo(self):
        """Negative coordinates wrap correctly."""
        s = C4State.from_coords(-1, -2, -3)
        assert s.t == 2  # -1 % 3 = 2
        assert s.s == 1  # -2 % 3 = 1
        assert s.a == 0  # -3 % 3 = 0
