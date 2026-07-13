"""Tests for src/visualization/c4_viz.py"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch


_root = Path(__file__).resolve().parent.parent
project_root = _root.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest

from c4.types import C4State
from src.visualization.c4_viz import (
    C4Visualizer,
    print_c4_cube,
    print_path,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def viz():
    return C4Visualizer()


@pytest.fixture
def sample_path():
    return [
        C4State(0, 0, 0),
        C4State(1, 0, 0),
        C4State(1, 1, 0),
        C4State(1, 1, 1),
        C4State(2, 1, 1),
        C4State(2, 2, 1),
        C4State(2, 2, 2),
    ]


@pytest.fixture
def sample_operators():
    return ["op1", "op2", "op3", "op4", "op5", "op6"]


# ═══════════════════════════════════════════════════════════════════
# C4Visualizer initialization
# ═══════════════════════════════════════════════════════════════════


class TestC4VisualizerInit:
    def test_default_init(self, viz):
        assert viz.width == 60
        assert viz.height == 20


# ═══════════════════════════════════════════════════════════════════
# draw_cube_2d
# ═══════════════════════════════════════════════════════════════════


class TestDrawCube2d:
    def test_basic_output(self, viz):
        output = viz.draw_cube_2d()
        assert "C4 COGNITIVE SPACE" in output
        assert "PAST (T=0)" in output
        assert "PRESENT (T=1)" in output
        assert "FUTURE (T=2)" in output
        assert "Legend:" in output

    def test_with_path(self, viz, sample_path):
        output = viz.draw_cube_2d(sample_path)
        assert "S " in output or "E " in output  # Start or End markers

    def test_path_coords_highlighted(self, viz, sample_path):
        output = viz.draw_cube_2d(sample_path)
        # Start state (0,0,0) should be marked
        assert "S " in output or " 0 " in output

    def test_empty_path(self, viz):
        output = viz.draw_cube_2d(None)
        assert "C4 COGNITIVE SPACE" in output

    def test_single_state_path(self, viz):
        output = viz.draw_cube_2d([C4State(1, 1, 1)])
        assert "S " in output or "E " in output

    def test_all_time_slices_present(self, viz):
        output = viz.draw_cube_2d()
        for name in ["PAST", "PRESENT", "FUTURE"]:
            assert name in output

    def test_grid_structure(self, viz):
        output = viz.draw_cube_2d()
        assert "┌" in output
        assert "┐" in output
        assert "└" in output
        assert "┘" in output

    def test_axis_labels(self, viz):
        output = viz.draw_cube_2d()
        assert "C = Concrete" in output
        assert "A = Abstract" in output
        assert "M = Meta" in output


# ═══════════════════════════════════════════════════════════════════
# draw_path_timeline
# ═══════════════════════════════════════════════════════════════════


class TestDrawPathTimeline:
    def test_basic(self, viz, sample_path, sample_operators):
        output = viz.draw_path_timeline(sample_path, sample_operators)
        assert "NAVIGATION PATH" in output
        assert "START:" in output
        assert "Total steps:" in output

    def test_step_numbering(self, viz, sample_path, sample_operators):
        output = viz.draw_path_timeline(sample_path, sample_operators)
        for i in range(1, len(sample_operators)):
            assert f"Step {i}:" in output

    def test_operator_names(self, viz, sample_path, sample_operators):
        output = viz.draw_path_timeline(sample_path, sample_operators)
        for op in sample_operators[1:]:
            assert op in output

    def test_state_representations(self, viz, sample_path, sample_operators):
        output = viz.draw_path_timeline(sample_path, sample_operators)
        assert "Past" in output or "Pres" in output or "Fut" in output
        assert "Conc" in output or "Abst" in output or "Meta" in output
        assert "Self" in output or "Othr" in output or "Syst" in output

    def test_theorem_11_reference(self, viz, sample_path, sample_operators):
        output = viz.draw_path_timeline(sample_path, sample_operators)
        assert "Theorem 11" in output
        assert "≤6" in output

    def test_single_step(self, viz):
        path = [C4State(1, 1, 1)]
        operators = ["op1"]
        output = viz.draw_path_timeline(path, operators)
        assert "START:" in output
        assert "Step 1" not in output  # Only start, no steps


# ═══════════════════════════════════════════════════════════════════
# draw_operator_frequencies
# ═══════════════════════════════════════════════════════════════════


class TestDrawOperatorFrequencies:
    def test_basic(self, viz):
        paths = [["op1", "op2", "op1"], ["op2", "op3"]]
        output = viz.draw_operator_frequencies(paths)
        assert "OPERATOR USAGE STATISTICS" in output
        assert "op1" in output
        assert "op2" in output
        assert "op3" in output

    def test_sorted_by_count(self, viz):
        paths = [["op1"] * 5, ["op2"] * 3, ["op3"] * 1]
        output = viz.draw_operator_frequencies(paths)
        lines = output.split("\n")
        # op1 should appear before op2, op2 before op3
        op1_idx = next(i for i, l in enumerate(lines) if "op1" in l and "│" in l)
        op2_idx = next(i for i, l in enumerate(lines) if "op2" in l and "│" in l)
        op3_idx = next(i for i, l in enumerate(lines) if "op3" in l and "│" in l)
        assert op1_idx < op2_idx < op3_idx

    def test_bar_chart(self, viz):
        paths = [["op1", "op1"]]
        output = viz.draw_operator_frequencies(paths)
        assert "█" in output

    def test_empty_paths(self, viz):
        output = viz.draw_operator_frequencies([])
        assert "OPERATOR USAGE STATISTICS" in output

    def test_max_15_operators(self, viz):
        paths = [[f"op{i}" for i in range(20)] * 2]
        output = viz.draw_operator_frequencies(paths)
        op_count = sum(
            1 for line in output.split("\n") if line.strip().startswith("op") and "│" in line
        )
        assert op_count <= 15


# ═══════════════════════════════════════════════════════════════════
# draw_confidence_gauge
# ═══════════════════════════════════════════════════════════════════


class TestDrawConfidenceGauge:
    def test_high_confidence(self, viz):
        output = viz.draw_confidence_gauge(0.9)
        assert "Confidence: 90.0%" in output
        assert "0.90" in output
        assert "\033[92m" in output  # Green

    def test_medium_confidence(self, viz):
        output = viz.draw_confidence_gauge(0.6)
        assert "Confidence: 60.0%" in output
        assert "\033[93m" in output  # Yellow

    def test_low_confidence(self, viz):
        output = viz.draw_confidence_gauge(0.3)
        assert "Confidence: 30.0%" in output
        assert "\033[91m" in output  # Red

    def test_zero_confidence(self, viz):
        output = viz.draw_confidence_gauge(0.0)
        assert "0.00" in output
        assert "░" in output

    def test_full_confidence(self, viz):
        output = viz.draw_confidence_gauge(1.0)
        assert "100.0%" in output
        assert "█" * 40 in output

    def test_custom_width(self, viz):
        output = viz.draw_confidence_gauge(0.5, width=20)
        assert "█" * 10 in output

    def test_reset_code(self, viz):
        output = viz.draw_confidence_gauge(0.5)
        assert "\033[0m" in output


# ═══════════════════════════════════════════════════════════════════
# draw_domain_map
# ═══════════════════════════════════════════════════════════════════


class TestDrawDomainMap:
    def test_basic(self, viz):
        discoveries = {"physics": 10, "biology": 5, "chemistry": 8}
        output = viz.draw_domain_map(discoveries)
        assert "DISCOVERIES BY DOMAIN" in output
        assert "physics" in output
        assert "biology" in output
        assert "chemistry" in output

    def test_sorted_by_count(self, viz):
        discoveries = {"a": 1, "b": 5, "c": 3}
        output = viz.draw_domain_map(discoveries)
        lines = [l for l in output.split("\n") if "│" in l]
        assert "b" in lines[0]
        assert "c" in lines[1]
        assert "a" in lines[2]

    def test_bar_chart_present(self, viz):
        discoveries = {"domain": 5}
        output = viz.draw_domain_map(discoveries)
        assert "■" in output

    def test_empty_dict(self, viz):
        output = viz.draw_domain_map({})
        assert "DISCOVERIES BY DOMAIN" in output


# ═══════════════════════════════════════════════════════════════════
# Utility functions
# ═══════════════════════════════════════════════════════════════════


class TestUtilityFunctions:
    def test_print_c4_cube(self, viz, sample_path):
        with patch("builtins.print") as mock_print:
            print_c4_cube(sample_path)
            mock_print.assert_called_once()
            output = mock_print.call_args[0][0]
            assert "C4 COGNITIVE SPACE" in output

    def test_print_c4_cube_no_path(self):
        with patch("builtins.print") as mock_print:
            print_c4_cube()
            mock_print.assert_called_once()

    def test_print_path(self, sample_path, sample_operators):
        with patch("builtins.print") as mock_print:
            print_path(sample_path, sample_operators)
            mock_print.assert_called_once()
            output = mock_print.call_args[0][0]
            assert "NAVIGATION PATH" in output


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_draw_cube_2d_path_with_duplicates(self, viz):
        path = [C4State(1, 1, 1), C4State(1, 1, 1)]
        output = viz.draw_cube_2d(path)
        assert "C4 COGNITIVE SPACE" in output

    def test_draw_path_timeline_empty_operators(self, viz):
        output = viz.draw_path_timeline([C4State(1, 1, 1)], [])
        assert "Total steps: 0" in output

    def test_draw_operator_frequencies_single_path(self, viz):
        output = viz.draw_operator_frequencies([["op1"]])
        assert "op1" in output
        assert "1" in output

    def test_draw_confidence_gauge_very_small(self, viz):
        output = viz.draw_confidence_gauge(0.01)
        assert "1.0%" in output

    def test_draw_domain_map_single_domain(self, viz):
        output = viz.draw_domain_map({"only": 1})
        assert "only" in output
        assert "1" in output

    def test_all_c4_states_in_path(self, viz):
        all_states = [C4State(t, s, a) for t in range(3) for s in range(3) for a in range(3)]
        output = viz.draw_cube_2d(all_states)
        assert "S " in output
        assert "E " in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
