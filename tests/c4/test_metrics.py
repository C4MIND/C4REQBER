"""
Tests for C4 metrics.

Verifies diameter bounds:
- undirected_distance: diameter = 3
- directed_distance: diameter = 6
"""
from __future__ import annotations

import pytest

from c4.metrics import directed_distance, undirected_distance
from c4.types import C4State, all_27_states


class TestUndirectedDistance:
    def test_diameter_is_3(self):
        """Maximum symmetric modular distance across all 27×27 pairs is 3."""
        max_dist = max(
            undirected_distance(a, b)
            for a in all_27_states()
            for b in all_27_states()
        )
        assert max_dist == 3

    def test_symmetry(self):
        for a in all_27_states():
            for b in all_27_states():
                assert undirected_distance(a, b) == undirected_distance(b, a)

    def test_triangle_inequality(self):
        states = all_27_states()
        for a in states:
            for b in states:
                for c in states:
                    assert (
                        undirected_distance(a, c)
                        <= undirected_distance(a, b) + undirected_distance(b, c)
                    )

    def test_identity(self):
        for s in all_27_states():
            assert undirected_distance(s, s) == 0

    def test_antipodal_pairs_at_3(self):
        origin = C4State(0, 0, 0)
        antipode = C4State(2, 2, 2)
        assert undirected_distance(origin, antipode) == 3


class TestDirectedDistance:
    def test_diameter_is_6(self):
        """Maximum asymmetric directed distance across all 27×27 pairs is 6."""
        max_dist = max(
            directed_distance(a, b)
            for a in all_27_states()
            for b in all_27_states()
        )
        assert max_dist == 6

    def test_not_symmetric(self):
        a = C4State(0, 0, 0)
        b = C4State(2, 2, 2)
        assert directed_distance(a, b) == 6
        assert directed_distance(b, a) == 3  # (0-2)%3 = 1 per axis, sum = 3

    def test_directed_triangle_inequality(self):
        states = all_27_states()
        for a in states:
            for b in states:
                for c in states:
                    assert (
                        directed_distance(a, c)
                        <= directed_distance(a, b) + directed_distance(b, c)
                    )

    def test_identity(self):
        for s in all_27_states():
            assert directed_distance(s, s) == 0

    def test_antipodal_pairs_at_6(self):
        origin = C4State(0, 0, 0)
        antipode = C4State(2, 2, 2)
        assert directed_distance(origin, antipode) == 6
