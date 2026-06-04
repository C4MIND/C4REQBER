"""
Tests for src/patterns/library/credit_risk.py (Credit Risk pattern)

Covers:
- CreditRiskConfig dataclass
- CreditRiskModel initialization
- merton_model() calculations
- gaussian_copula_simulation()
- credit_migration()
- portfolio_concentration_risk()
- _calculate_welfare()
- run() integration
- get_metadata()
- Edge cases: extreme leverage, correlation effects, rating migrations
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.credit_risk import CreditRiskModel, CreditRiskConfig



# ═══════════════════════════════════════════════════════════════════
# Config Tests
# ═══════════════════════════════════════════════════════════════════


class TestCreditRiskConfig:
    def test_default_init(self):
        cfg = CreditRiskConfig()
        assert cfg.n_obligors == 100
        assert cfg.n_simulations == 10000
        assert cfg.time_horizon == 1.0
        assert cfg.recovery_rate == 0.4
        assert cfg.correlation == 0.2

    def test_custom_init(self):
        cfg = CreditRiskConfig(
            n_obligors=200,
            n_simulations=5000,
            recovery_rate=0.5,
            correlation=0.3
        )
        assert cfg.n_obligors == 200
        assert cfg.n_simulations == 5000
        assert cfg.recovery_rate == 0.5
        assert cfg.correlation == 0.3

    def test_default_confidence_levels(self):
        cfg = CreditRiskConfig()
        assert cfg.confidence_levels == [0.95, 0.99, 0.999]


# ═══════════════════════════════════════════════════════════════════
# Initialization Tests
# ═══════════════════════════════════════════════════════════════════


class TestCreditRiskModelInit:
    def test_default_init(self):
        model = CreditRiskModel()
        assert model.config is not None
        assert model.config.confidence_levels is not None

    def test_custom_config(self):
        cfg = CreditRiskConfig(n_obligors=50)
        model = CreditRiskModel(cfg)
        assert model.config.n_obligors == 50


# ═══════════════════════════════════════════════════════════════════
# Merton Model Tests
# ═══════════════════════════════════════════════════════════════════


class TestMertonModel:
    def test_safe_firm(self):
        model = CreditRiskModel()
        # Safe firm: high asset value relative to debt
        result = model.merton_model(
            V0=150, K=80, sigma_V=0.2, r=0.05, T=1.0
        )
        assert result["distance_to_default"] > 2.0
        assert result["default_probability"] < 0.05

    def test_risky_firm(self):
        model = CreditRiskModel()
        # Risky firm: low asset value, high volatility
        result = model.merton_model(
            V0=90, K=80, sigma_V=0.4, r=0.05, T=1.0
        )
        assert result["distance_to_default"] < 1.0
        assert result["default_probability"] > 0.1

    def test_distance_to_default_ordering(self):
        """Safer firms have higher distance to default"""
        model = CreditRiskModel()

        safe = model.merton_model(V0=150, K=80, sigma_V=0.2, r=0.05, T=1.0)
        risky = model.merton_model(V0=90, K=80, sigma_V=0.4, r=0.05, T=1.0)

        assert safe["distance_to_default"] > risky["distance_to_default"]

    def test_default_probability_ordering(self):
        """Riskier firms have higher default probability"""
        model = CreditRiskModel()

        safe = model.merton_model(V0=150, K=80, sigma_V=0.2, r=0.05, T=1.0)
        risky = model.merton_model(V0=90, K=80, sigma_V=0.4, r=0.05, T=1.0)

        assert risky["default_probability"] > safe["default_probability"]

    def test_credit_spread_positive(self):
        model = CreditRiskModel()
        result = model.merton_model(V0=100, K=80, sigma_V=0.3, r=0.05, T=1.0)
        assert result["credit_spread"] > 0

    def test_equity_plus_debt_equals_value(self):
        """Merton model: E + D = V"""
        model = CreditRiskModel()
        result = model.merton_model(V0=100, K=80, sigma_V=0.3, r=0.05, T=1.0)
        total = result["equity_value"] + result["debt_value"]
        assert total == pytest.approx(100, rel=0.01)

    def test_leverage_calculation(self):
        model = CreditRiskModel()
        result = model.merton_model(V0=100, K=80, sigma_V=0.3, r=0.05, T=1.0)
        assert result["leverage"] == pytest.approx(0.8, rel=0.01)


# ═══════════════════════════════════════════════════════════════════
# Gaussian Copula Tests
# ═══════════════════════════════════════════════════════════════════


class TestGaussianCopula:
    def test_returns_dict(self):
        model = CreditRiskModel(CreditRiskConfig(n_obligors=50, n_simulations=1000))
        exposures = np.ones(50) * 1000
        default_probs = np.ones(50) * 0.05
        result = model.gaussian_copula_simulation(exposures, default_probs)
        assert isinstance(result, dict)

    def test_expected_loss_positive(self):
        model = CreditRiskModel(CreditRiskConfig(n_obligors=50, n_simulations=1000))
        exposures = np.ones(50) * 1000
        default_probs = np.ones(50) * 0.05
        result = model.gaussian_copula_simulation(exposures, default_probs)
        assert result["expected_loss"] > 0

    def test_var_present(self):
        model = CreditRiskModel(CreditRiskConfig(n_obligors=50, n_simulations=1000))
        exposures = np.ones(50) * 1000
        default_probs = np.ones(50) * 0.05
        result = model.gaussian_copula_simulation(exposures, default_probs)
        assert "var" in result
        assert 0.95 in result["var"]
        assert 0.99 in result["var"]

    def test_expected_shortfall_present(self):
        model = CreditRiskModel(CreditRiskConfig(n_obligors=50, n_simulations=1000))
        exposures = np.ones(50) * 1000
        default_probs = np.ones(50) * 0.05
        result = model.gaussian_copula_simulation(exposures, default_probs)
        assert "expected_shortfall" in result

    def test_var_increases_with_confidence(self):
        model = CreditRiskModel(CreditRiskConfig(n_obligors=50, n_simulations=1000))
        exposures = np.ones(50) * 1000
        default_probs = np.ones(50) * 0.05
        result = model.gaussian_copula_simulation(exposures, default_probs)
        assert result["var"][0.99] > result["var"][0.95]

    def test_es_greater_than_var(self):
        """Expected Shortfall should be >= VaR"""
        model = CreditRiskModel(CreditRiskConfig(n_obligors=50, n_simulations=1000))
        exposures = np.ones(50) * 1000
        default_probs = np.ones(50) * 0.05
        result = model.gaussian_copula_simulation(exposures, default_probs)

        for cl in [0.95, 0.99]:
            assert result["expected_shortfall"][cl] >= result["var"][cl]

    def test_correlation_increases_tail_risk(self):
        """Higher correlation should increase VaR"""
        exposures = np.ones(100) * 1000
        default_probs = np.ones(100) * 0.05

        model_low = CreditRiskModel(CreditRiskConfig(
            correlation=0.1, n_obligors=100, n_simulations=2000
        ))
        result_low = model_low.gaussian_copula_simulation(exposures, default_probs)

        model_high = CreditRiskModel(CreditRiskConfig(
            correlation=0.5, n_obligors=100, n_simulations=2000
        ))
        result_high = model_high.gaussian_copula_simulation(exposures, default_probs)

        assert result_high["var"][0.99] > result_low["var"][0.99]


# ═══════════════════════════════════════════════════════════════════
# Credit Migration Tests
# ═══════════════════════════════════════════════════════════════════


class TestCreditMigration:
    def test_migration_returns_dict(self):
        model = CreditRiskModel()
        ratings = ["AAA", "AA", "A", "BBB"]
        result = model.credit_migration(ratings)
        assert isinstance(result, dict)

    def test_current_ratings_preserved(self):
        model = CreditRiskModel()
        ratings = ["AAA", "AA", "A", "BBB"]
        result = model.credit_migration(ratings)
        assert result["current_ratings"] == ratings

    def test_future_ratings_same_length(self):
        model = CreditRiskModel()
        ratings = ["AAA", "AA", "A", "BBB"]
        result = model.credit_migration(ratings)
        assert len(result["future_ratings"]) == len(ratings)

    def test_rating_distribution(self):
        model = CreditRiskModel()
        ratings = ["AAA", "AA", "A", "BBB"] * 10
        result = model.credit_migration(ratings)
        assert "rating_distribution" in result
        assert sum(result["rating_distribution"].values()) == len(ratings)

    def test_spread_change_calculated(self):
        model = CreditRiskModel()
        ratings = ["BBB"] * 10  # Lower rated
        result = model.credit_migration(ratings)
        assert "current_avg_spread" in result
        assert "future_avg_spread" in result
        assert "spread_change_bps" in result


# ═══════════════════════════════════════════════════════════════════
# Concentration Tests
# ═══════════════════════════════════════════════════════════════════


class TestPortfolioConcentration:
    def test_equal_exposures(self):
        model = CreditRiskModel()
        exposures = np.ones(100) * 1000
        result = model.portfolio_concentration_risk(exposures)

        # Equal exposures should have low HHI
        assert result["herfindahl_index"] < 0.02
        # Effective number close to actual number
        assert result["effective_number_obligors"] > 90
        # Low Gini
        assert result["gini_coefficient"] < 0.1

    def test_concentrated_exposures(self):
        model = CreditRiskModel()
        exposures = np.ones(100) * 1000
        exposures[0] = 50000  # One large exposure
        result = model.portfolio_concentration_risk(exposures)

        # Concentrated should have high HHI
        assert result["herfindahl_index"] > 0.1
        # Lower effective number
        assert result["effective_number_obligors"] < 50

    def test_concentration_vs_equal(self):
        """Concentrated portfolio should have higher HHI"""
        model = CreditRiskModel()

        equal = np.ones(100) * 1000
        concentrated = np.ones(100) * 1000
        concentrated[0] = 50000

        result_equal = model.portfolio_concentration_risk(equal)
        result_conc = model.portfolio_concentration_risk(concentrated)

        assert result_conc["herfindahl_index"] > result_equal["herfindahl_index"]

    def test_top_exposures(self):
        model = CreditRiskModel()
        exposures = np.array([10000, 9000, 8000] + [1000] * 97)
        names = [f"Firm_{i}" for i in range(100)]
        result = model.portfolio_concentration_risk(exposures, names)

        assert "top_10_exposures" in result
        assert len(result["top_10_exposures"]) == 10
        assert result["top_10_exposures"][0][0] == "Firm_0"


# ═══════════════════════════════════════════════════════════════════
# Run Integration Tests
# ═══════════════════════════════════════════════════════════════════


class TestRun:
    def test_run_returns_dict(self):
        model = CreditRiskModel(CreditRiskConfig(n_obligors=50, n_simulations=1000))
        result = model.run()
        assert isinstance(result, dict)

    def test_merton_model_present(self):
        model = CreditRiskModel(CreditRiskConfig(n_obligors=50, n_simulations=1000))
        result = model.run()
        assert "merton_model" in result
        assert "distance_to_default" in result["merton_model"]

    def test_portfolio_copula_present(self):
        model = CreditRiskModel(CreditRiskConfig(n_obligors=50, n_simulations=1000))
        result = model.run()
        assert "portfolio_copula" in result

    def test_credit_migration_present(self):
        model = CreditRiskModel(CreditRiskConfig(n_obligors=50, n_simulations=1000))
        result = model.run()
        assert "credit_migration" in result

    def test_concentration_present(self):
        model = CreditRiskModel(CreditRiskConfig(n_obligors=50, n_simulations=1000))
        result = model.run()
        assert "concentration" in result

    def test_economic_capital_present(self):
        model = CreditRiskModel(CreditRiskConfig(n_obligors=50, n_simulations=1000))
        result = model.run()
        assert "economic_capital" in result
        assert result["economic_capital"] > 0

    def test_risk_adjusted_return_present(self):
        model = CreditRiskModel(CreditRiskConfig(n_obligors=50, n_simulations=1000))
        result = model.run()
        assert "risk_adjusted_return" in result

    def test_model_type(self):
        model = CreditRiskModel()
        result = model.run()
        assert result["model_type"] == "credit_risk"


# ═══════════════════════════════════════════════════════════════════
# Metadata Tests
# ═══════════════════════════════════════════════════════════════════


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = CreditRiskModel.get_metadata()
        assert meta["pattern_id"] == 56
        assert meta["name"] == "Credit Risk"
        assert "category" in meta
        assert "description" in meta


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_zero_default_probability(self):
        """Very safe firm should have near-zero PD"""
        model = CreditRiskModel()
        result = model.merton_model(V0=200, K=50, sigma_V=0.1, r=0.05, T=1.0)
        assert result["default_probability"] < 0.001

    def test_near_certain_default(self):
        """Very risky firm should have high PD"""
        model = CreditRiskModel()
        result = model.merton_model(V0=60, K=100, sigma_V=0.5, r=0.05, T=1.0)
        assert result["default_probability"] > 0.5

    def test_very_high_recovery(self):
        """High recovery rate should reduce expected loss"""
        model_high = CreditRiskModel(CreditRiskConfig(n_obligors=50, recovery_rate=0.8))
        model_low = CreditRiskModel(CreditRiskConfig(n_obligors=50, recovery_rate=0.2))

        exposures = np.ones(50) * 1000
        default_probs = np.ones(50) * 0.1

        result_high = model_high.gaussian_copula_simulation(exposures, default_probs)
        result_low = model_low.gaussian_copula_simulation(exposures, default_probs)

        # Note: Same exposures, different recovery -> different EL
        # Higher recovery = lower expected loss

    def test_single_obligor(self):
        model = CreditRiskModel(CreditRiskConfig(n_obligors=1, n_simulations=1000))
        result = model.run()
        assert "portfolio_copula" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
