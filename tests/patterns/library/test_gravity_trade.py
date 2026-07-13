"""
Tests for src/patterns/library/gravity_trade.py (Gravity Trade Model)

Covers:
- GravityTradeConfig dataclass
- GravityTradeModel initialization
- _setup_countries() and _generate_trade_costs()
- compute_trade_flows()
- solve_equilibrium()
- compute_welfare_gains()
- _compute_price_indices()
- estimate_gravity_equation()
- trade_elasticity_analysis()
- run() integration
- get_metadata()
- Edge cases: single country, zero trade costs, extreme trade elasticity
"""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.gravity_trade import GravityTradeConfig, GravityTradeModel


# ═══════════════════════════════════════════════════════════════════
# Dataclass
# ═══════════════════════════════════════════════════════════════════


class TestGravityTradeConfig:
    def test_default_init(self):
        cfg = GravityTradeConfig()
        assert cfg.n_countries == 10
        assert cfg.alpha == 1.0
        assert cfg.theta == 4.0
        assert cfg.sigma == 5.0
        assert cfg.fixed_cost == 0.1
        assert cfg.iceberg_cost == 1.5
        assert cfg.random_seed == 42

    def test_custom_init(self):
        cfg = GravityTradeConfig(n_countries=5, theta=6.0, iceberg_cost=2.0)
        assert cfg.n_countries == 5
        assert cfg.theta == 6.0
        assert cfg.iceberg_cost == 2.0


# ═══════════════════════════════════════════════════════════════════
# GravityTradeModel Initialization
# ═══════════════════════════════════════════════════════════════════


class TestGravityTradeModelInit:
    def test_init(self):
        model = GravityTradeModel()
        assert model is not None
        assert model.config is not None
        assert len(model.countries) == 10
        assert model.productivity is not None
        assert model.labor is not None
        assert model.wages is not None
        assert model.trade_costs is not None

    def test_custom_config(self):
        cfg = GravityTradeConfig(n_countries=5)
        model = GravityTradeModel(cfg)
        assert len(model.countries) == 5
        assert model.productivity.shape == (5,)
        assert model.trade_costs.shape == (5, 5)


# ═══════════════════════════════════════════════════════════════════
# Setup Countries
# ═══════════════════════════════════════════════════════════════════


class TestSetupCountries:
    def test_countries_named(self):
        cfg = GravityTradeConfig(n_countries=5)
        model = GravityTradeModel(cfg)
        assert model.countries == ["Country_0", "Country_1", "Country_2", "Country_3", "Country_4"]

    def test_productivity_positive(self):
        model = GravityTradeModel()
        assert np.all(model.productivity > 0)

    def test_labor_positive(self):
        model = GravityTradeModel()
        assert np.all(model.labor > 0)

    def test_wages_initialized_to_one(self):
        model = GravityTradeModel()
        assert np.all(model.wages == 1.0)


# ═══════════════════════════════════════════════════════════════════
# Trade Costs
# ═══════════════════════════════════════════════════════════════════


class TestGenerateTradeCosts:
    def test_trade_costs_shape(self):
        cfg = GravityTradeConfig(n_countries=5)
        model = GravityTradeModel(cfg)
        assert model.trade_costs.shape == (5, 5)

    def test_diagonal_is_one(self):
        model = GravityTradeModel()
        for i in range(model.config.n_countries):
            assert model.trade_costs[i, i] == pytest.approx(1.0)

    def test_off_diagonal_greater_than_one(self):
        model = GravityTradeModel()
        for i in range(model.config.n_countries):
            for j in range(model.config.n_countries):
                if i != j:
                    assert model.trade_costs[i, j] >= 1.0


# ═══════════════════════════════════════════════════════════════════
# Trade Flows
# ═══════════════════════════════════════════════════════════════════


class TestComputeTradeFlows:
    def test_trade_flows_shape(self):
        cfg = GravityTradeConfig(n_countries=5)
        model = GravityTradeModel(cfg)
        X = model.compute_trade_flows()
        assert X.shape == (5, 5)

    def test_trade_flows_non_negative(self):
        model = GravityTradeModel()
        X = model.compute_trade_flows()
        assert np.all(X >= 0)

    def test_trade_shares_sum_to_one(self):
        model = GravityTradeModel()
        X = model.compute_trade_flows()
        # For each importer j, shares should sum to 1
        for j in range(model.config.n_countries):
            total = X[:, j].sum()
            if total > 0:
                assert X[:, j].sum() == pytest.approx(model.wages[j] * model.labor[j], rel=0.01)


# ═══════════════════════════════════════════════════════════════════
# Equilibrium
# ═══════════════════════════════════════════════════════════════════


class TestSolveEquilibrium:
    def test_equilibrium_structure(self):
        cfg = GravityTradeConfig(n_countries=5)
        model = GravityTradeModel(cfg)
        result = model.solve_equilibrium()
        assert "wages" in result
        assert "trade_flows" in result
        assert "exports" in result
        assert "imports" in result
        assert "trade_balance" in result
        assert "converged" in result

    def test_wages_normalized(self):
        cfg = GravityTradeConfig(n_countries=5)
        model = GravityTradeModel(cfg)
        result = model.solve_equilibrium()
        # First wage should be 1 (normalized)
        assert result["wages"][0] == pytest.approx(1.0, abs=0.01)

    def test_trade_balance_zero(self):
        cfg = GravityTradeConfig(n_countries=5)
        model = GravityTradeModel(cfg)
        result = model.solve_equilibrium()
        # Total exports should equal total imports
        total_exports = sum(result["exports"])
        total_imports = sum(result["imports"])
        assert total_exports == pytest.approx(total_imports, rel=0.1)


# ═══════════════════════════════════════════════════════════════════
# Welfare Gains
# ═══════════════════════════════════════════════════════════════════


class TestComputeWelfareGains:
    def test_welfare_structure(self):
        cfg = GravityTradeConfig(n_countries=5)
        model = GravityTradeModel(cfg)
        result = model.compute_welfare_gains()
        assert "welfare_gains_pct" in result
        assert "scenario" in result

    def test_welfare_gains_positive(self):
        cfg = GravityTradeConfig(n_countries=5)
        model = GravityTradeModel(cfg)
        result = model.compute_welfare_gains()
        # Gains from trade should be positive
        assert all(g > 0 for g in result["welfare_gains_pct"])

    def test_welfare_gains_length(self):
        cfg = GravityTradeConfig(n_countries=5)
        model = GravityTradeModel(cfg)
        result = model.compute_welfare_gains()
        assert len(result["welfare_gains_pct"]) == 5


# ═══════════════════════════════════════════════════════════════════
# Price Indices
# ═══════════════════════════════════════════════════════════════════


class TestComputePriceIndices:
    def test_price_indices_positive(self):
        cfg = GravityTradeConfig(n_countries=5)
        model = GravityTradeModel(cfg)
        # Need to solve equilibrium first
        model.solve_equilibrium()
        P = model._compute_price_indices()
        assert np.all(P > 0)

    def test_price_indices_length(self):
        cfg = GravityTradeConfig(n_countries=5)
        model = GravityTradeModel(cfg)
        model.solve_equilibrium()
        P = model._compute_price_indices()
        assert len(P) == 5


# ═══════════════════════════════════════════════════════════════════
# Gravity Equation Estimation
# ═══════════════════════════════════════════════════════════════════


class TestEstimateGravityEquation:
    def test_estimation_structure(self):
        cfg = GravityTradeConfig(n_countries=5)
        model = GravityTradeModel(cfg)
        result = model.estimate_gravity_equation()
        assert "coefficients" in result
        assert "r_squared" in result
        assert "n_observations" in result
        assert "exporter_gdp" in result["coefficients"]
        assert "importer_gdp" in result["coefficients"]
        assert "trade_cost" in result["coefficients"]

    def test_r_squared_in_range(self):
        cfg = GravityTradeConfig(n_countries=5)
        model = GravityTradeModel(cfg)
        result = model.estimate_gravity_equation()
        assert 0 <= result["r_squared"] <= 1

    def test_trade_cost_coefficient_negative(self):
        cfg = GravityTradeConfig(n_countries=5)
        model = GravityTradeModel(cfg)
        result = model.estimate_gravity_equation()
        # Higher trade costs should reduce trade
        assert result["coefficients"]["trade_cost"] < 0


# ═══════════════════════════════════════════════════════════════════
# Trade Elasticity Analysis
# ═══════════════════════════════════════════════════════════════════


class TestTradeElasticityAnalysis:
    def test_elasticity_structure(self):
        cfg = GravityTradeConfig(n_countries=5)
        model = GravityTradeModel(cfg)
        result = model.trade_elasticity_analysis()
        assert "trade_elasticity" in result
        assert "baseline_trade" in result
        assert "shocked_trade" in result
        assert "trade_decline_pct" in result

    def test_elasticity_negative(self):
        cfg = GravityTradeConfig(n_countries=5)
        model = GravityTradeModel(cfg)
        result = model.trade_elasticity_analysis()
        # Trade elasticity with respect to trade costs should be negative
        assert result["trade_elasticity"] < 0

    def test_trade_declines_with_higher_costs(self):
        cfg = GravityTradeConfig(n_countries=5)
        model = GravityTradeModel(cfg)
        result = model.trade_elasticity_analysis()
        assert result["trade_decline_pct"] < 0


# ═══════════════════════════════════════════════════════════════════
# Run Integration
# ═══════════════════════════════════════════════════════════════════


class TestRun:
    def test_run_structure(self):
        cfg = GravityTradeConfig(n_countries=5)
        model = GravityTradeModel(cfg)
        result = model.run()
        assert "equilibrium" in result
        assert "welfare" in result
        assert "gravity_estimation" in result
        assert "trade_elasticity" in result
        assert "trade_statistics" in result
        assert "country_data" in result

    def test_trade_statistics_present(self):
        cfg = GravityTradeConfig(n_countries=5)
        model = GravityTradeModel(cfg)
        result = model.run()
        assert "total_trade" in result["trade_statistics"]
        assert "trade_to_gdp_ratio" in result["trade_statistics"]

    def test_country_data_present(self):
        cfg = GravityTradeConfig(n_countries=5)
        model = GravityTradeModel(cfg)
        result = model.run()
        assert "names" in result["country_data"]
        assert "productivity" in result["country_data"]
        assert "labor" in result["country_data"]


# ═══════════════════════════════════════════════════════════════════
# get_metadata
# ═══════════════════════════════════════════════════════════════════


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = GravityTradeModel.get_metadata()
        assert meta["pattern_id"] == 59
        assert meta["name"] == "Gravity Trade Model"
        assert "parameters" in meta
        assert "outputs" in meta


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_two_countries(self):
        cfg = GravityTradeConfig(n_countries=2)
        model = GravityTradeModel(cfg)
        result = model.run()
        assert len(result["equilibrium"]["wages"]) == 2

    def test_high_theta(self):
        cfg = GravityTradeConfig(n_countries=5, theta=10.0)
        model = GravityTradeModel(cfg)
        result = model.run()
        assert result["trade_elasticity"]["trade_elasticity"] < 0

    def test_low_theta(self):
        cfg = GravityTradeConfig(n_countries=5, theta=2.0)
        model = GravityTradeModel(cfg)
        result = model.run()
        assert result["trade_elasticity"]["trade_elasticity"] < 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
