"""Tests for TOPSIS — Technique for Order Preference by Similarity to Ideal Solution."""

from __future__ import annotations

import math

import pytest

from src.decisions.topsis import TOPSISResult, topsis


class TestTOPSISResult:
    def test_create_result(self):
        r = TOPSISResult(
            ranks=[("A", 0.8), ("B", 0.3)],
            ideal_best=[0.6, 0.5],
            ideal_worst=[0.1, 0.1],
            distances_to_best={"A": 0.2, "B": 0.7},
            distances_to_worst={"A": 0.8, "B": 0.3},
        )
        assert r.ranks[0][0] == "A"
        assert r.ranks[0][1] == pytest.approx(0.8)
        assert len(r.ideal_best) == 2

    def test_perfect_closeness(self):
        r = TOPSISResult(
            ranks=[("Perfect", 1.0)],
            ideal_best=[1.0],
            ideal_worst=[0.0],
            distances_to_best={"Perfect": 0.0},
            distances_to_worst={"Perfect": 1.0},
        )
        assert r.ranks[0][1] == pytest.approx(1.0)


class TestTOPSISBasic:
    def test_simple_ranking(self):
        matrix = [
            [250, 16, 12],
            [200, 20, 10],
            [300, 14, 15],
        ]
        alternatives = ["Laptop A", "Laptop B", "Laptop C"]
        weights = [0.4, 0.35, 0.25]
        benefits = [False, True, True]
        result = topsis(matrix, alternatives, weights, benefits)
        assert len(result.ranks) == 3
        assert result.ranks[0][1] > result.ranks[-1][1]

    def test_all_benefits(self):
        matrix = [
            [10, 20],
            [15, 25],
            [12, 22],
        ]
        result = topsis(matrix, ["A", "B", "C"], [0.5, 0.5], [True, True])
        assert result.ranks[0][0] == "B"
        assert result.ideal_best[0] >= result.ideal_worst[0]
        assert result.ideal_best[1] >= result.ideal_worst[1]

    def test_all_costs(self):
        matrix = [
            [10, 20],
            [15, 25],
            [12, 22],
        ]
        result = topsis(matrix, ["A", "B", "C"], [0.6, 0.4], [False, False])
        assert result.ranks[0][0] == "A"
        assert result.ideal_best[0] <= result.ideal_worst[0]
        assert result.ideal_best[1] <= result.ideal_worst[1]

    def test_single_alternative(self):
        matrix = [[1.0, 2.0]]
        result = topsis(matrix, ["Only"], [0.5, 0.5], [True, True])
        assert len(result.ranks) == 1
        assert result.ranks[0][1] == pytest.approx(0.0) or result.ranks[0][1] >= 0.0

    def test_distance_ordering(self):
        matrix = [
            [1, 1],
            [5, 5],
        ]
        result = topsis(matrix, ["Close", "Far"], [0.5, 0.5], [True, True])
        assert result.ranks[0][0] == "Far"
        assert result.distances_to_best["Far"] < result.distances_to_best["Close"]
        assert result.distances_to_worst["Far"] > result.distances_to_worst["Close"]

    def test_weights_affect_ranking(self):
        matrix = [
            [10, 1],
            [5, 10],
        ]
        r1 = topsis(matrix, ["A", "B"], [0.9, 0.1], [True, True])
        r2 = topsis(matrix, ["A", "B"], [0.1, 0.9], [True, True])
        assert r1.ranks[0][0] != r2.ranks[0][0]

    def test_zero_col_norm_handled(self):
        matrix = [[0.0, 1.0], [0.0, 2.0]]
        result = topsis(matrix, ["A", "B"], [0.5, 0.5], [True, True])
        assert result.ranks[0][0] == "B"

    def test_all_zeros_matrix(self):
        matrix = [[0.0, 0.0], [0.0, 0.0]]
        result = topsis(matrix, ["A", "B"], [0.5, 0.5], [True, True])
        assert len(result.ranks) == 2
        for _, score in result.ranks:
            assert score == pytest.approx(0.0)

    def test_mixed_benefits_costs(self):
        matrix = [
            [100, 50],
            [200, 30],
            [150, 40],
        ]
        result = topsis(matrix, ["A", "B", "C"], [0.5, 0.5], [False, True])
        assert len(result.ranks) == 3

    def test_ideal_best_worst_disjoint(self):
        matrix = [
            [1, 10],
            [5, 5],
        ]
        result = topsis(matrix, ["A", "B"], [0.5, 0.5], [True, False])
        assert result.ideal_best[0] != result.ideal_worst[0] or result.ideal_best[1] != result.ideal_worst[1]

    def test_closeness_in_range(self):
        matrix = [
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9],
        ]
        result = topsis(matrix, ["X", "Y", "Z"], [0.3, 0.3, 0.4], [True, True, False])
        for _, score in result.ranks:
            assert 0.0 <= score <= 1.0

    def test_larger_decision_matrix(self):
        matrix = [
            [0.8, 0.7, 0.9, 0.6, 0.85],
            [0.6, 0.8, 0.7, 0.9, 0.75],
            [0.9, 0.6, 0.8, 0.7, 0.80],
        ]
        result = topsis(
            matrix,
            ["Alt1", "Alt2", "Alt3"],
            [0.25, 0.2, 0.2, 0.2, 0.15],
            [True, True, True, True, True],
        )
        assert len(result.ranks) == 3
        assert result.ranks[0][1] > 0.0

    def test_distances_match_closeness(self):
        matrix = [[3, 4], [6, 1]]
        result = topsis(matrix, ["A", "B"], [0.5, 0.5], [True, True])
        for alt, closeness in result.ranks:
            db = result.distances_to_best[alt]
            dw = result.distances_to_worst[alt]
            expected = dw / (db + dw) if (db + dw) else 0.0
            assert closeness == pytest.approx(expected)

    def test_unequal_weights(self):
        matrix = [
            [10, 20],
            [20, 10],
        ]
        weight_combos = [
            ([0.1, 0.9], "A"),
            ([0.9, 0.1], "B"),
        ]
        for w, expected_winner in weight_combos:
            result = topsis(matrix, ["A", "B"], w, [True, True])
            assert result.ranks[0][0] == expected_winner
