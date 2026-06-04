"""
Tests for src/metamodels/hypercube.py
"""
from __future__ import annotations

import pytest

from metamodels.hypercube import Hypercube7D


class TestHypercube7D:
    def test_dimensions_count(self):
        hc = Hypercube7D()
        assert len(hc.DIMENSIONS) == 7
        assert "levels" in hc.DIMENSIONS
        assert "phases" in hc.DIMENSIONS
        assert "modality" in hc.DIMENSIONS
        assert "direction" in hc.DIMENSIONS
        assert "depth" in hc.DIMENSIONS
        assert "speed" in hc.DIMENSIONS
        assert "integration" in hc.DIMENSIONS

    def test_vertices_constant(self):
        hc = Hypercube7D()
        assert hc.VERTICES == 128

    def test_get_vertex(self):
        hc = Hypercube7D()
        vertex = hc.get_vertex((0, 1, 2, 0, 1, 2, 3))
        assert vertex["coords"] == (0, 1, 2, 0, 1, 2, 3)
        assert vertex["dimensions"] == 7

    def test_find_path(self):
        hc = Hypercube7D()
        start = (0, 0, 0, 0, 0, 0, 0)
        end = (1, 1, 1, 1, 1, 1, 1)
        distance = hc.find_path(start, end)
        assert distance == 7

    def test_find_path_zero(self):
        hc = Hypercube7D()
        start = (5, 5, 5, 5, 5, 5, 5)
        distance = hc.find_path(start, start)
        assert distance == 0

    def test_distance_alias(self):
        hc = Hypercube7D()
        a = (0, 0, 0, 0, 0, 0, 0)
        b = (2, 0, 0, 0, 0, 0, 0)
        assert hc.distance(a, b) == hc.find_path(a, b)

    def test_find_path_negative_coords(self):
        hc = Hypercube7D()
        start = (-1, 0, 0, 0, 0, 0, 0)
        end = (1, 0, 0, 0, 0, 0, 0)
        distance = hc.find_path(start, end)
        assert distance == 2

    def test_dimension_values(self):
        hc = Hypercube7D()
        assert hc.DIMENSIONS["levels"] == [
            "Context", "Operations", "Mechanics", "Principles", "Identity", "Society", "Synergy"
        ]
        assert hc.DIMENSIONS["phases"] == [
            "Scanning", "Diagnosis", "Modeling", "Design", "Creation",
            "Optimization", "Implementation", "Integration"
        ]
        assert hc.DIMENSIONS["modality"] == [
            "Analysis", "Synthesis", "Evaluation", "Generation"
        ]
        assert hc.DIMENSIONS["direction"] == ["Past", "Present", "Future"]
        assert hc.DIMENSIONS["depth"] == ["Surface", "Structure", "Essence"]
        assert hc.DIMENSIONS["speed"] == ["Slow", "Moderate", "Fast", "Instant"]
        assert hc.DIMENSIONS["integration"] == [
            "Isolation", "Connection", "System", "Ecosystem", "Universe"
        ]
