"""Tests for Game Theory — Shapley Value module."""

from __future__ import annotations

import pytest

from src.game_theory.shapley import shapley_value


class TestShapleyValue:
    def test_two_player_equal_split(self):
        values = shapley_value(
            players=["A", "B"],
            coalition_values={
                ("A",): 0,
                ("B",): 0,
                ("A", "B"): 100,
            },
        )
        assert values["A"] == pytest.approx(50.0)
        assert values["B"] == pytest.approx(50.0)

    def test_three_player_equal_split(self):
        values = shapley_value(
            players=["A", "B", "C"],
            coalition_values={
                ("A",): 0,
                ("B",): 0,
                ("C",): 0,
                ("A", "B"): 0,
                ("A", "C"): 0,
                ("B", "C"): 0,
                ("A", "B", "C"): 300,
            },
        )
        assert values["A"] == pytest.approx(100.0)
        assert values["B"] == pytest.approx(100.0)
        assert values["C"] == pytest.approx(100.0)

    def test_single_player_gets_all(self):
        values = shapley_value(
            players=["A"],
            coalition_values={
                ("A",): 42,
            },
        )
        assert values["A"] == pytest.approx(42.0)

    def test_airport_game(self):
        # Classic example: A needs short runway, B medium, C long
        players = ["A", "B", "C"]
        coalition_values = {
            ("A",): 10,
            ("B",): 10,
            ("C",): 10,
            ("A", "B"): 14,
            ("A", "C"): 14,
            ("B", "C"): 14,
            ("A", "B", "C"): 18,
        }
        values = shapley_value(players, coalition_values)
        assert sum(values.values()) == pytest.approx(18.0)

    def test_marginal_contribution_player(self):
        players = ["A", "B", "C"]
        coalition_values = {
            ("A",): 0,
            ("B",): 0,
            ("C",): 0,
            ("A", "B"): 100,
            ("A", "C"): 0,
            ("B", "C"): 0,
            ("A", "B", "C"): 100,
        }
        values = shapley_value(players, coalition_values)
        assert values["A"] == values["B"]
        assert values["C"] == pytest.approx(0.0)

    def test_efficiency_property(self):
        players = ["X", "Y", "Z"]
        grand_coalition = 120.0
        coalition_values = {
            ("X",): 10,
            ("Y",): 20,
            ("Z",): 30,
            ("X", "Y"): 50,
            ("X", "Z"): 60,
            ("Y", "Z"): 70,
            ("X", "Y", "Z"): grand_coalition,
        }
        values = shapley_value(players, coalition_values)
        assert sum(values.values()) == pytest.approx(grand_coalition)

    def test_symmetry_property(self):
        # Interchangeable players get equal values
        players = ["A", "B"]
        coalition_values = {
            ("A",): 5,
            ("B",): 5,
            ("A", "B"): 20,
        }
        values = shapley_value(players, coalition_values)
        assert values["A"] == pytest.approx(values["B"])

    def test_all_positive_values(self):
        values = shapley_value(
            players=["A", "B", "C"],
            coalition_values={
                ("A",): 10,
                ("B",): 0,
                ("C",): 0,
                ("A", "B"): 20,
                ("A", "C"): 20,
                ("B", "C"): 0,
                ("A", "B", "C"): 30,
            },
        )
        for v in values.values():
            assert v >= 0

    def test_sorting_independence(self):
        players = ["C", "A", "B"]
        coalition_values = {
            ("A", "B", "C"): 90,
            ("A", "B"): 60,
            ("A", "C"): 40,
            ("B", "C"): 30,
            ("A",): 10,
            ("B",): 20,
            ("C",): 0,
        }
        values = shapley_value(players, coalition_values)
        assert sum(values.values()) == pytest.approx(90.0)

    def test_large_coalition(self):
        players = [f"P{i}" for i in range(5)]
        coalition_values: dict[tuple[str, ...], float] = {}
        for i in range(5):
            coalition_values[(players[i],)] = float(i * 10)
        for combo in [(0, 1), (1, 2), (2, 3), (3, 4), (0, 4)]:
            key = tuple(sorted([players[i] for i in combo]))
            coalition_values[key] = sum(float(i * 10) for i in combo) + 20
        coalition_values[tuple(sorted(players))] = 200.0
        values = shapley_value(players, coalition_values)
        assert sum(values.values()) == pytest.approx(200.0)
        for v in values.values():
            assert v >= 0
