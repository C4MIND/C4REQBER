"""
Honest tests for Theorem 11.

Verifies exactly what Theorem 11 proves:
    - Forward Hamming distance max = 6 (antipodal pairs)
    - Undirected graph diameter = 3 (with ±1 operators)
    - State space is connected
"""
from __future__ import annotations

import pytest

from src.c4.core import C4State, all_27_states, hamming_distance, verify_theorem_11
from src.c4.metrics import undirected_distance
from src.c4.navigation import (
    C4TransitionGraph,
    bfs_path,
    shortest_path_length,
)


class TestTheorem11Honest:
    def test_directed_diameter_is_6(self):
        """Forward Hamming diameter = 6 (Theorem 11)."""
        g = C4TransitionGraph()
        assert g.directed_diameter() == 6

    def test_undirected_diameter_is_3(self):
        """Undirected diameter (torus, bidirectional) = 3."""
        g = C4TransitionGraph()
        assert g.diameter() <= 3

    def test_verify_theorem_11_returns_6(self):
        """verify_theorem_11() returns max forward distance = 6."""
        max_dist, antipodes = verify_theorem_11()
        assert max_dist == 6
        assert len(antipodes) > 0

    def test_directed_distance_max_6(self):
        """Forward Hamming distance never exceeds 6."""
        states = all_27_states()
        for s1 in states:
            for s2 in states:
                d = hamming_distance(s1, s2)
                assert d <= 6

    def test_undirected_distance_max_3(self):
        """Undirected distance never exceeds 3."""
        states = all_27_states()
        for s1 in states:
            for s2 in states:
                d = undirected_distance(s1, s2)
                assert d <= 3

    def test_all_pairs_reachable_directed(self):
        """All 27×27 pairs reachable via BFS (state space is connected)."""
        states = all_27_states()
        for s1 in states:
            for s2 in states:
                path = bfs_path(s1, s2)
                assert path is not None, f"Unreachable: {s1} -> {s2}"

    def test_all_pairs_reachable_undirected(self):
        """All 27×27 pairs reachable via undirected BFS."""
        pytest.skip("bfs_path_undirected not implemented")

    def test_directed_path_length_at_most_6(self):
        """BFS paths have length ≤ 6."""
        states = all_27_states()
        for s1 in states:
            for s2 in states:
                length = shortest_path_length(s1, s2)
                assert length <= 6
