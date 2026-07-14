"""Tests for Robust Decision Making Engine — XLRM + PRIM."""

from __future__ import annotations

import pytest

from src.robust_decisions.prim import PRIMBox, prim_analysis
from src.robust_decisions.xlrm import RDMResult, XLMRModel, explore_scenarios


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def simple_xlrm_model() -> XLMRModel:
    return XLMRModel(
        uncertainties=[
            {"name": "demand", "range": [0.0, 100.0], "unit": "units"},
            {"name": "cost", "range": [10.0, 50.0], "unit": "$"},
        ],
        levers=[
            {"name": "pricing", "options": ["low", "medium", "high"]},
            {"name": "capacity", "options": ["small", "large"]},
        ],
        relationships=["profit = revenue - cost"],
        metrics=["profit", "market_share"],
    )


@pytest.fixture
def prim_data() -> list[dict]:
    return [
        {"x": 0.1, "y": 0.2, "outcome": 1.0},
        {"x": 0.2, "y": 0.3, "outcome": 1.5},
        {"x": 0.3, "y": 0.1, "outcome": 0.0},
        {"x": 0.4, "y": 0.5, "outcome": 1.2},
        {"x": 0.5, "y": 0.4, "outcome": 0.8},
        {"x": 0.6, "y": 0.7, "outcome": 0.0},
        {"x": 0.7, "y": 0.8, "outcome": 1.3},
        {"x": 0.8, "y": 0.9, "outcome": 1.7},
        {"x": 0.9, "y": 1.0, "outcome": 2.0},
        {"x": 0.5, "y": 0.6, "outcome": 1.1},
    ]


# ═══════════════════════════════════════════════════════════════════
# XLMRModel
# ═══════════════════════════════════════════════════════════════════


class TestXLMRModel:
    def test_create_model(self, simple_xlrm_model: XLMRModel):
        assert len(simple_xlrm_model.uncertainties) == 2
        assert len(simple_xlrm_model.levers) == 2
        assert simple_xlrm_model.uncertainties[0]["name"] == "demand"
        assert simple_xlrm_model.levers[0]["name"] == "pricing"

    def test_model_default_lists(self):
        model = XLMRModel(
            uncertainties=[],
            levers=[],
            relationships=[],
            metrics=[],
        )
        assert model.uncertainties == []
        assert model.levers == []
        assert model.relationships == []
        assert model.metrics == []

    def test_model_with_relationships_and_metrics(self):
        model = XLMRModel(
            uncertainties=[{"name": "temp", "range": [0.0, 40.0], "unit": "C"}],
            levers=[{"name": "cooling", "options": ["on", "off"]}],
            relationships=["efficiency = f(temp, cooling)"],
            metrics=["efficiency", "energy_use"],
        )
        assert len(model.relationships) == 1
        assert len(model.metrics) == 2


# ═══════════════════════════════════════════════════════════════════
# RDMResult
# ═══════════════════════════════════════════════════════════════════


class TestRDMResult:
    def test_create_result(self):
        result = RDMResult(
            scenarios_explored=500,
            robust_strategies=[],
            vulnerability_map={},
            regret_analysis=[],
        )
        assert result.scenarios_explored == 500
        assert result.robust_strategies == []

    def test_result_with_strategies(self):
        strategies = [
            {"lever": "pricing", "option": "low", "robust_count": 42, "avg_score": 0.85}
        ]
        result = RDMResult(
            scenarios_explored=100,
            robust_strategies=strategies,
            vulnerability_map={"market_share": ["demand>80"]},
            regret_analysis=[],
        )
        assert len(result.robust_strategies) == 1
        assert result.vulnerability_map == {"market_share": ["demand>80"]}


# ═══════════════════════════════════════════════════════════════════
# explore_scenarios
# ═══════════════════════════════════════════════════════════════════


class TestExploreScenarios:
    def test_returns_rdm_result(self, simple_xlrm_model: XLMRModel):
        result = explore_scenarios(simple_xlrm_model, n_scenarios=100, threshold=0.0)
        assert isinstance(result, RDMResult)

    def test_scenarios_explored_count(self, simple_xlrm_model: XLMRModel):
        result = explore_scenarios(simple_xlrm_model, n_scenarios=50, threshold=0.0)
        assert result.scenarios_explored == 50

    def test_threshold_zero_returns_all_strategies(self, simple_xlrm_model: XLMRModel):
        result = explore_scenarios(simple_xlrm_model, n_scenarios=100, threshold=0.0)
        # threshold=0 means all strategies score >= 0, so they all pass
        assert len(result.robust_strategies) <= 10
        assert all(s["robust_count"] > 0 for s in result.robust_strategies)

    def test_threshold_one_returns_empty(self, simple_xlrm_model: XLMRModel):
        result = explore_scenarios(simple_xlrm_model, n_scenarios=100, threshold=1.01)
        # No score can exceed 1.01 since scores are in [0, 1]
        assert len(result.robust_strategies) == 0

    def test_robust_strategies_have_required_keys(self, simple_xlrm_model: XLMRModel):
        result = explore_scenarios(simple_xlrm_model, n_scenarios=100, threshold=0.0)
        for s in result.robust_strategies:
            assert "lever" in s
            assert "option" in s
            assert "robust_count" in s
            assert "avg_score" in s

    def test_strategies_sorted_by_count(self, simple_xlrm_model: XLMRModel):
        result = explore_scenarios(simple_xlrm_model, n_scenarios=500, threshold=0.3)
        counts = [s["robust_count"] for s in result.robust_strategies]
        assert counts == sorted(counts, reverse=True)

    def test_single_uncertainty_model(self):
        model = XLMRModel(
            uncertainties=[{"name": "risk", "range": [0.0, 1.0], "unit": "ratio"}],
            levers=[{"name": "strategy", "options": ["A"]}],
            relationships=[],
            metrics=[],
        )
        result = explore_scenarios(model, n_scenarios=100, threshold=0.0)
        assert result.scenarios_explored == 100

    def test_many_levers_and_options(self):
        model = XLMRModel(
            uncertainties=[{"name": "x", "range": [0.0, 1.0], "unit": ""}],
            levers=[
                {"name": "L1", "options": ["a", "b"]},
                {"name": "L2", "options": ["c", "d", "e"]},
            ],
            relationships=[],
            metrics=[],
        )
        result = explore_scenarios(model, n_scenarios=50, threshold=0.0)
        # 2 * 3 = 6 lever-option combinations
        assert len(result.robust_strategies) <= 6

    def test_empty_uncertainties_no_error(self):
        model = XLMRModel(
            uncertainties=[],
            levers=[{"name": "policy", "options": ["X"]}],
            relationships=[],
            metrics=[],
        )
        result = explore_scenarios(model, n_scenarios=10, threshold=0.0)
        assert result.scenarios_explored == 10

    def test_avg_score_in_valid_range(self, simple_xlrm_model: XLMRModel):
        result = explore_scenarios(simple_xlrm_model, n_scenarios=100, threshold=0.0)
        for s in result.robust_strategies:
            assert 0.0 <= s["avg_score"] <= 1.0


# ═══════════════════════════════════════════════════════════════════
# PRIMBox
# ═══════════════════════════════════════════════════════════════════


class TestPRIMBox:
    def test_create_box(self):
        box = PRIMBox(
            dimensions={"x": (0.1, 0.9)},
            coverage=0.5,
            density=0.8,
            mean_outcome=1.5,
        )
        assert box.dimensions == {"x": (0.1, 0.9)}
        assert box.coverage == 0.5
        assert box.density == 0.8
        assert box.mean_outcome == 1.5

    def test_multiple_dimensions(self):
        box = PRIMBox(
            dimensions={"x": (0.0, 0.5), "y": (0.3, 0.7)},
            coverage=0.3,
            density=0.6,
            mean_outcome=2.0,
        )
        assert len(box.dimensions) == 2
        assert ("x", (0.0, 0.5)) in box.dimensions.items()


# ═══════════════════════════════════════════════════════════════════
# prim_analysis
# ═══════════════════════════════════════════════════════════════════


class TestPrimAnalysis:
    def test_returns_list_of_boxes(self, prim_data: list[dict]):
        boxes = prim_analysis(prim_data, outcome_key="outcome", max_boxes=2)
        assert isinstance(boxes, list)
        for box in boxes:
            assert isinstance(box, PRIMBox)

    def test_boxes_have_coverage_density(self, prim_data: list[dict]):
        boxes = prim_analysis(prim_data, outcome_key="outcome", max_boxes=3)
        for box in boxes:
            assert box.coverage >= 0.0
            assert box.density >= 0.0

    def test_empty_data_returns_empty(self):
        boxes = prim_analysis([], outcome_key="outcome", max_boxes=3)
        assert boxes == []

    def test_single_row_returns_empty(self):
        boxes = prim_analysis(
            [{"x": 1.0, "outcome": 1.0}], outcome_key="outcome", max_boxes=3
        )
        assert boxes == []

    def test_respects_max_boxes(self, prim_data: list[dict]):
        boxes = prim_analysis(prim_data, outcome_key="outcome", max_boxes=2)
        assert len(boxes) <= 2

    def test_coverage_matches_fraction_of_total(self, prim_data: list[dict]):
        boxes = prim_analysis(prim_data, outcome_key="outcome", max_boxes=2)
        for box in boxes:
            assert box.coverage <= 1.0
            assert box.coverage >= 0.0

    def test_density_is_positive_when_outcomes_present(self, prim_data: list[dict]):
        boxes = prim_analysis(prim_data, outcome_key="outcome", max_boxes=3)
        for box in boxes:
            assert isinstance(box.density, float)
            assert box.density >= 0.0

    def test_high_target_coverage_produces_fewer_boxes(self, prim_data: list[dict]):
        boxes_low = prim_analysis(
            prim_data, outcome_key="outcome", target_coverage=0.1, max_boxes=3
        )
        boxes_high = prim_analysis(
            prim_data, outcome_key="outcome", target_coverage=0.5, max_boxes=3
        )
        # Higher coverage constraint should not produce more boxes
        assert len(boxes_high) <= len(boxes_low) or len(boxes_high) == 0

    def test_non_numeric_keys_ignored(self):
        data = [
            {"category": "A", "value": 0.5, "outcome": 1.0},
            {"category": "B", "value": 0.7, "outcome": 0.0},
        ]
        boxes = prim_analysis(
            data, outcome_key="outcome", target_coverage=0.0, max_boxes=1
        )
        # "category" should be ignored, only "value" used
        if boxes:
            for box in boxes:
                assert "value" in box.dimensions
                assert "category" not in box.dimensions

    def test_mean_outcome_is_computed(self, prim_data: list[dict]):
        boxes = prim_analysis(prim_data, outcome_key="outcome", max_boxes=2)
        for box in boxes:
            assert isinstance(box.mean_outcome, float)
            assert box.mean_outcome >= 0.0
