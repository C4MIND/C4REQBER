"""
Tests for src/patterns/library/heterogeneous_agents.py (Heterogeneous Agents Model)

Covers:
- HeterogeneousAgentsConfig dataclass
- HeterogeneousAgentsModel initialization
- _setup_grid() and _setup_transitions()
- production() function
- solve_individual_problem()
- simulate_distribution()
- _gini_coefficient()
- approximate_aggregation()
- _welfare_analysis()
- run() integration
- get_metadata()
- Edge cases: single agent, extreme inequality, zero productivity
"""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.heterogeneous_agents import (
    HeterogeneousAgentsConfig,
    HeterogeneousAgentsModel,
)


# ═══════════════════════════════════════════════════════════════════
# Dataclass
# ═══════════════════════════════════════════════════════════════════


class TestHeterogeneousAgentsConfig:
    def test_default_init(self):
        cfg = HeterogeneousAgentsConfig()
        assert cfg.n_agents == 1000
        assert cfg.n_assets == 50
        assert cfg.max_assets == 50.0
        assert cfg.alpha == 0.36
        assert cfg.beta == 0.96
        assert cfg.delta == 0.08
        assert cfg.gamma == 1.0
        assert cfg.p_good_good == 0.95
        assert cfg.p_bad_bad == 0.875
        assert cfg.unemployment_good == 0.04
        assert cfg.unemployment_bad == 0.10
        assert cfg.T == 100
        assert cfg.T_sim == 1000
        assert cfg.random_seed == 42

    def test_custom_init(self):
        cfg = HeterogeneousAgentsConfig(n_agents=500, alpha=0.4, beta=0.95)
        assert cfg.n_agents == 500
        assert cfg.alpha == 0.4
        assert cfg.beta == 0.95


# ═══════════════════════════════════════════════════════════════════
# HeterogeneousAgentsModel Initialization
# ═══════════════════════════════════════════════════════════════════


class TestHeterogeneousAgentsModelInit:
    def test_init(self):
        model = HeterogeneousAgentsModel()
        assert model is not None
        assert model.config is not None
        assert model.a_grid is not None
        assert model.P_agg is not None

    def test_custom_config(self):
        cfg = HeterogeneousAgentsConfig(n_agents=100, n_assets=20)
        model = HeterogeneousAgentsModel(cfg)
        assert model.config.n_agents == 100
        assert len(model.a_grid) == 20


# ═══════════════════════════════════════════════════════════════════
# Asset Grid
# ═══════════════════════════════════════════════════════════════════


class TestSetupGrid:
    def test_asset_grid_shape(self):
        cfg = HeterogeneousAgentsConfig(n_assets=30)
        model = HeterogeneousAgentsModel(cfg)
        assert len(model.a_grid) == 30

    def test_asset_grid_positive(self):
        cfg = HeterogeneousAgentsConfig()
        model = HeterogeneousAgentsModel(cfg)
        assert np.all(model.a_grid >= 0)

    def test_asset_grid_monotonic(self):
        cfg = HeterogeneousAgentsConfig()
        model = HeterogeneousAgentsModel(cfg)
        assert np.all(np.diff(model.a_grid) > 0)


# ═══════════════════════════════════════════════════════════════════
# Transition Matrices
# ═══════════════════════════════════════════════════════════════════


class TestSetupTransitions:
    def test_aggregate_transition_shape(self):
        model = HeterogeneousAgentsModel()
        assert model.P_agg.shape == (2, 2)

    def test_aggregate_transition_rows_sum_to_one(self):
        model = HeterogeneousAgentsModel()
        assert np.allclose(model.P_agg.sum(axis=1), 1.0)

    def test_employment_transitions_shape(self):
        model = HeterogeneousAgentsModel()
        assert model.P_emp_gg.shape == (2, 2)
        assert model.P_emp_bb.shape == (2, 2)

    def test_employment_transitions_rows_sum_to_one(self):
        model = HeterogeneousAgentsModel()
        assert np.allclose(model.P_emp_gg.sum(axis=1), 1.0)
        assert np.allclose(model.P_emp_bb.sum(axis=1), 1.0)


# ═══════════════════════════════════════════════════════════════════
# Production Function
# ═══════════════════════════════════════════════════════════════════


class TestProduction:
    def test_production_positive(self):
        model = HeterogeneousAgentsModel()
        Y, w, r = model.production(10.0, 1.0)
        assert Y > 0
        assert w > 0

    def test_marginal_products(self):
        model = HeterogeneousAgentsModel()
        Y1, w1, r1 = model.production(10.0, 1.0)
        Y2, w2, r2 = model.production(11.0, 1.0)
        # Higher K should increase output
        assert Y2 > Y1


# ═══════════════════════════════════════════════════════════════════
# Individual Problem
# ═══════════════════════════════════════════════════════════════════


class TestSolveIndividualProblem:
    def test_policy_shape(self):
        cfg = HeterogeneousAgentsConfig(n_assets=20)
        model = HeterogeneousAgentsModel(cfg)
        Y, w, r = model.production(15.0, 0.94)
        V = np.zeros((20, 2))
        policy = model.solve_individual_problem(w, r, V)
        assert policy.shape == (20, 2)

    def test_policy_non_negative(self):
        cfg = HeterogeneousAgentsConfig(n_assets=20)
        model = HeterogeneousAgentsModel(cfg)
        Y, w, r = model.production(15.0, 0.94)
        V = np.zeros((20, 2))
        policy = model.solve_individual_problem(w, r, V)
        assert np.all(policy >= 0)


# ═══════════════════════════════════════════════════════════════════
# Gini Coefficient
# ═══════════════════════════════════════════════════════════════════


class TestGiniCoefficient:
    def test_gini_perfect_equality(self):
        model = HeterogeneousAgentsModel()
        x = np.ones(100)
        gini = model._gini_coefficient(x)
        assert gini == pytest.approx(0.0, abs=0.01)

    def test_gini_perfect_inequality(self):
        model = HeterogeneousAgentsModel()
        x = np.zeros(100)
        x[-1] = 100.0
        gini = model._gini_coefficient(x)
        assert gini > 0.9

    def test_gini_range(self):
        model = HeterogeneousAgentsModel()
        x = np.random.lognormal(0, 1, 100)
        gini = model._gini_coefficient(x)
        assert 0 <= gini <= 1

    def test_gini_empty(self):
        model = HeterogeneousAgentsModel()
        gini = model._gini_coefficient(np.array([]))
        assert np.isnan(gini) or gini == 0


# ═══════════════════════════════════════════════════════════════════
# Approximate Aggregation
# ═══════════════════════════════════════════════════════════════════


class TestApproximateAggregation:
    def test_aggregation_structure(self):
        model = HeterogeneousAgentsModel()
        result = model.approximate_aggregation()
        assert "good_times" in result
        assert "bad_times" in result
        assert "R_squared" in result
        assert "a" in result["good_times"]
        assert "b" in result["good_times"]


# ═══════════════════════════════════════════════════════════════════
# Welfare Analysis
# ═══════════════════════════════════════════════════════════════════


class TestWelfareAnalysis:
    def test_welfare_structure(self):
        cfg = HeterogeneousAgentsConfig(n_agents=100)
        model = HeterogeneousAgentsModel(cfg)
        assets = np.random.lognormal(2, 0.5, 100)
        employment = [0.94] * 100
        result = model._welfare_analysis(assets, employment)
        assert "welfare_complete_markets" in result
        assert "welfare_incomplete_markets" in result
        assert "welfare_cost_of_risk" in result
        assert "consumption_equivalent" in result


# ═══════════════════════════════════════════════════════════════════
# Run Integration
# ═══════════════════════════════════════════════════════════════════


class TestRun:
    def test_run_structure(self):
        cfg = HeterogeneousAgentsConfig(n_agents=100, T_sim=50)
        model = HeterogeneousAgentsModel(cfg)
        result = model.run()
        assert "equilibrium" in result
        assert "distribution" in result
        assert "inequality" in result
        assert "aggregate_law" in result
        assert "welfare" in result

    def test_equilibrium_structure(self):
        cfg = HeterogeneousAgentsConfig(n_agents=100, T_sim=50)
        model = HeterogeneousAgentsModel(cfg)
        result = model.run()
        eq = result["equilibrium"]
        assert "aggregate_capital" in eq
        assert "aggregate_labor" in eq
        assert "wage" in eq
        assert "interest_rate" in eq
        assert "output" in eq

    def test_inequality_structure(self):
        cfg = HeterogeneousAgentsConfig(n_agents=100, T_sim=50)
        model = HeterogeneousAgentsModel(cfg)
        result = model.run()
        ineq = result["inequality"]
        assert "gini" in ineq
        assert "top10_share" in ineq
        assert "bottom50_share" in ineq
        assert "mean_assets" in ineq
        assert "median_assets" in ineq

    def test_inequality_metrics_valid(self):
        cfg = HeterogeneousAgentsConfig(n_agents=100, T_sim=50)
        model = HeterogeneousAgentsModel(cfg)
        result = model.run()
        ineq = result["inequality"]
        assert 0 <= ineq["gini"] <= 1
        assert 0 <= ineq["top10_share"] <= 1
        assert 0 <= ineq["bottom50_share"] <= 1


# ═══════════════════════════════════════════════════════════════════
# get_metadata
# ═══════════════════════════════════════════════════════════════════


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = HeterogeneousAgentsModel.get_metadata()
        assert meta["pattern_id"] == 54
        assert meta["name"] == "Heterogeneous Agents"
        assert "parameters" in meta
        assert "outputs" in meta


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_small_population(self):
        cfg = HeterogeneousAgentsConfig(n_agents=10, T_sim=20)
        model = HeterogeneousAgentsModel(cfg)
        result = model.run()
        assert result["inequality"]["gini"] >= 0

    def test_high_depreciation(self):
        cfg = HeterogeneousAgentsConfig(delta=0.5, T_sim=20)
        model = HeterogeneousAgentsModel(cfg)
        result = model.run()
        assert result["equilibrium"]["interest_rate"] < 0.5

    def test_low_discount_factor(self):
        cfg = HeterogeneousAgentsConfig(beta=0.8, T_sim=20)
        model = HeterogeneousAgentsModel(cfg)
        result = model.run()
        assert "welfare" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
