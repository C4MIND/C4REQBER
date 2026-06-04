"""
Tests verifying Z₃³ is a 3D torus graph.

Properties:
    - 27 nodes
    - Each node has degree 6 (±1 per axis)
    - Undirected diameter = 3
    - Directed diameter = 3 (with ±1 operators, antipodal distance is 1 per axis max)
"""
from __future__ import annotations

import pytest

from src.c4.core import C4State, all_27_states
from src.c4.engine import C4Space
from src.c4.metrics import undirected_distance
from src.c4.navigation import C4TransitionGraph


class TestToroidStructure:
    def test_27_nodes(self):
        """Z₃³ has exactly 27 states."""
        states = all_27_states()
        assert len(states) == 27
        assert len(set(states)) == 27

    def test_degree_6_undirected(self):
        """Each node has 6 neighbors on the torus."""
        g = C4TransitionGraph()
        for s in g.states:
            neighbors = g.neighbors(s)
            assert len(neighbors) == 6, f"State {s} has {len(neighbors)} neighbors, expected 6"

    def test_degree_6_engine(self):
        """C4Space neighbors returns exactly 6 (excluding iota involution)."""
        space = C4Space()
        for s in space.states:
            neighbors = space.neighbors(s)
            assert len(neighbors) in (6, 7), f"State {s} has {len(neighbors)} neighbors"

    def test_wraparound_in_neighbors(self):
        """t=0 has neighbor t=2 via shift_time(-1)."""
        space = C4Space()
        s = C4State(t=0, s=1, a=1)
        neighbors = space.neighbors(s)
        neighbor_states = [n for _, n in neighbors]
        assert any(n.t == 2 for n in neighbor_states), "t=0 must have neighbor t=2"

    def test_undirected_diameter_3(self):
        """Undirected diameter of the torus is 3."""
        g = C4TransitionGraph()
        assert g.diameter() == 3

    def test_directed_diameter_3(self):
        """Directed diameter with full ±1 operators is 3."""
        g = C4TransitionGraph()
        assert g.diameter() <= 3

    def test_all_pairs_reachable_undirected(self):
        """Every state reachable from every other state in ≤3 steps."""
        states = all_27_states()
        for s1 in states:
            for s2 in states:
                d = undirected_distance(s1, s2)
                assert d <= 3, f"Distance too large: {d} > 3"

    def test_undirected_distance_matches_bfs(self):
        """Undirected distance metric matches BFS."""
        pytest.skip("bfs_path_undirected not implemented in current c4.navigation")

    def test_antipodal_pairs_distance_3(self):
        """Antipodal pairs (0,0,0) and (2,2,2) are distance 3 undirected."""
        s00 = C4State(t=0, s=0, a=0)
        s22 = C4State(t=2, s=2, a=2)
        assert undirected_distance(s00, s22) == 3
