"""Tests for AHP — Analytic Hierarchy Process module."""

from __future__ import annotations

import math

import pytest

from src.decisions.ahp import AHPResult, ahp


class TestAHPResult:
    def test_create_result(self):
        r = AHPResult(
            criteria_weights={"C1": 0.6, "C2": 0.4},
            alternative_scores={"A": {"C1": 0.8, "C2": 0.3}, "B": {"C1": 0.5, "C2": 0.9}},
            final_ranks=[("B", 0.66), ("A", 0.6)],
            consistency_ratio=0.03,
            is_consistent=True,
        )
        assert r.consistency_ratio == 0.03
        assert r.is_consistent is True
        assert len(r.final_ranks) == 2

    def test_inconsistent_result(self):
        r = AHPResult(criteria_weights={}, alternative_scores={}, final_ranks=[], consistency_ratio=0.15, is_consistent=False)
        assert r.is_consistent is False


class TestAHPBasic:
    def test_single_criterion_single_alternative(self):
        result = ahp(
            pairwise_matrix=[[1]],
            criteria=["C1"],
            alternatives=["A"],
            alt_scores={"A": [1.0]},
        )
        assert result.criteria_weights["C1"] == pytest.approx(1.0)
        assert result.final_ranks[0][0] == "A"
        assert result.final_ranks[0][1] == pytest.approx(1.0)

    def test_perfectly_consistent_3x3(self):
        pairwise = [
            [1, 3, 5],
            [1 / 3, 1, 3],
            [1 / 5, 1 / 3, 1],
        ]
        result = ahp(
            pairwise_matrix=pairwise,
            criteria=["Cost", "Speed", "Quality"],
            alternatives=["A", "B"],
            alt_scores={"A": [0.7, 0.5, 0.9], "B": [0.4, 0.8, 0.6]},
        )
        assert result.is_consistent
        assert result.consistency_ratio < 0.1
        w = result.criteria_weights
        assert w["Cost"] > w["Quality"]
        assert len(result.final_ranks) == 2

    def test_identity_matrix_equal_weights(self):
        n = 4
        pairwise = [[1.0] * n for _ in range(n)]
        result = ahp(
            pairwise_matrix=pairwise,
            criteria=["A", "B", "C", "D"],
            alternatives=["X"],
            alt_scores={"X": [0.5, 0.5, 0.5, 0.5]},
        )
        for w in result.criteria_weights.values():
            assert w == pytest.approx(0.25)
        assert result.final_ranks[0][1] == pytest.approx(0.5)

    def test_two_criteria(self):
        pairwise = [[1, 5], [1 / 5, 1]]
        result = ahp(
            pairwise_matrix=pairwise,
            criteria=["C1", "C2"],
            alternatives=["Alt1", "Alt2"],
            alt_scores={"Alt1": [0.9, 0.2], "Alt2": [0.3, 0.8]},
        )
        assert result.criteria_weights["C1"] > 0.8
        assert result.criteria_weights["C2"] < 0.2
        assert result.is_consistent

    def test_ranking_order(self):
        pairwise = [[1, 2], [1 / 2, 1]]
        result = ahp(
            pairwise_matrix=pairwise,
            criteria=["Price", "Quality"],
            alternatives=["Cheap", "Premium"],
            alt_scores={"Cheap": [0.9, 0.3], "Premium": [0.4, 0.9]},
        )
        scores = dict(result.final_ranks)
        assert scores["Cheap"] > scores["Premium"]

    def test_default_zero_scores_for_missing_alt(self):
        pairwise = [[1, 1], [1, 1]]
        result = ahp(
            pairwise_matrix=pairwise,
            criteria=["C1", "C2"],
            alternatives=["A", "B"],
            alt_scores={},
        )
        assert result.final_ranks[0][1] == pytest.approx(0.0)
        assert result.final_ranks[1][1] == pytest.approx(0.0)

    def test_partial_alt_scores(self):
        pairwise = [[1, 1], [1, 1]]
        result = ahp(
            pairwise_matrix=pairwise,
            criteria=["C1", "C2"],
            alternatives=["A", "B"],
            alt_scores={"A": [1.0, 1.0]},
        )
        score_a = dict(result.final_ranks)["A"]
        score_b = dict(result.final_ranks)["B"]
        assert score_a > score_b

    def test_consistency_ratio_perfectly_consistent(self):
        pairwise = [
            [1, 2, 4],
            [1 / 2, 1, 2],
            [1 / 4, 1 / 2, 1],
        ]
        result = ahp(
            pairwise_matrix=pairwise,
            criteria=["C1", "C2", "C3"],
            alternatives=["X"],
            alt_scores={"X": [1, 1, 1]},
        )
        assert result.consistency_ratio < 0.01

    def test_inconsistent_below_threshold(self):
        pairwise = [
            [1, 3, 7],
            [1 / 3, 1, 4],
            [1 / 7, 1 / 4, 1],
        ]
        result = ahp(
            pairwise_matrix=pairwise,
            criteria=["C1", "C2", "C3"],
            alternatives=["X"],
            alt_scores={"X": [0.5, 0.5, 0.5]},
        )
        assert result.consistency_ratio < 0.1
        assert result.is_consistent

    def test_weights_sum_to_one(self):
        pairwise = [[1, 3, 6], [1 / 3, 1, 2], [1 / 6, 1 / 2, 1]]
        result = ahp(
            pairwise_matrix=pairwise,
            criteria=["C1", "C2", "C3"],
            alternatives=["A"],
            alt_scores={"A": [1, 1, 1]},
        )
        assert sum(result.criteria_weights.values()) == pytest.approx(1.0)

    def test_zero_col_sum_handled(self):
        pairwise = [[0.0, 1.0], [0.0, 1.0]]
        result = ahp(
            pairwise_matrix=pairwise,
            criteria=["C1", "C2"],
            alternatives=["A"],
            alt_scores={"A": [0.5, 0.5]},
        )
        assert result.final_ranks[0][1] == pytest.approx(0.25)

    def test_api_compatible_input(self):
        pairwise = [[1, 2], [1 / 2, 1]]
        result = ahp(
            pairwise_matrix=pairwise,
            criteria=["Cost", "Performance"],
            alternatives=["Option1", "Option2", "Option3"],
            alt_scores={
                "Option1": [0.8, 0.4],
                "Option2": [0.5, 0.7],
                "Option3": [0.3, 0.9],
            },
        )
        assert len(result.final_ranks) == 3
        assert result.final_ranks[0][0] == "Option1"
        assert isinstance(result.consistency_ratio, (int, float))
        assert isinstance(result.is_consistent, bool)


class TestAHPConsistencyEdgeCases:
    def test_random_inconsistent_large_matrix(self):
        pairwise = [
            [1, 5, 3, 7],
            [1 / 5, 1, 2, 3],
            [1 / 3, 1 / 2, 1, 4],
            [1 / 7, 1 / 3, 1 / 4, 1],
        ]
        result = ahp(
            pairwise_matrix=pairwise,
            criteria=["C1", "C2", "C3", "C4"],
            alternatives=["A"],
            alt_scores={"A": [1, 1, 1, 1]},
        )
        assert 0.0 < result.consistency_ratio < 0.25
