"""
Tests for C4State.neighbors() — torus wrap-around.

Verifies:
- 6 neighbors per state
- Wrap-around: t=0 ↔ t=2, s=0 ↔ s=2, a=0 ↔ a=2
"""
from __future__ import annotations

import pytest

from c4.types import C4State, all_27_states


class TestNeighborCount:
    def test_always_6(self):
        for s in all_27_states():
            nbrs = s.neighbors()
            assert len(nbrs) == 6

    def test_all_distinct(self):
        for s in all_27_states():
            nbrs = s.neighbors()
            assert len(nbrs) == len(set(nbrs))


class TestTimeWraparound:
    def test_t0_wraps_to_t2_backward(self):
        s = C4State(0, 1, 1)
        nbrs = s.neighbors()
        assert C4State(2, 1, 1) in nbrs

    def test_t2_wraps_to_t0_forward(self):
        s = C4State(2, 1, 1)
        nbrs = s.neighbors()
        assert C4State(0, 1, 1) in nbrs

    def test_t0_t2_are_mutual_neighbors(self):
        s0 = C4State(0, 1, 1)
        s2 = C4State(2, 1, 1)
        assert s2 in s0.neighbors()
        assert s0 in s2.neighbors()


class TestScaleWraparound:
    def test_s0_wraps_to_s2_backward(self):
        s = C4State(1, 0, 1)
        nbrs = s.neighbors()
        assert C4State(1, 2, 1) in nbrs

    def test_s2_wraps_to_s0_forward(self):
        s = C4State(1, 2, 1)
        nbrs = s.neighbors()
        assert C4State(1, 0, 1) in nbrs


class TestAgencyWraparound:
    def test_a0_wraps_to_a2_backward(self):
        s = C4State(1, 1, 0)
        nbrs = s.neighbors()
        assert C4State(1, 1, 2) in nbrs

    def test_a2_wraps_to_a0_forward(self):
        s = C4State(1, 1, 2)
        nbrs = s.neighbors()
        assert C4State(1, 1, 0) in nbrs


class TestNeighborDistances:
    def test_all_neighbors_at_distance_1(self):
        for s in all_27_states():
            for n in s.neighbors():
                assert s.distance(n) == 1

    def test_all_neighbors_at_directed_distance_1_or_2(self):
        for s in all_27_states():
            for n in s.neighbors():
                dd = s.directed_distance(n)
                assert dd in (1, 2)
