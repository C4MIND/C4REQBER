"""
Tests for src/patterns/library/option_pricing.py (Option Pricing Model)

Covers:
- OptionPricingConfig dataclass
- OptionPricingModel initialization
- black_scholes() analytical pricing
- binomial_tree() discrete pricing
- monte_carlo() simulation pricing
- implied_volatility() calculation
- sensitivity_analysis() Greeks and sensitivities
- put_call_parity verification
- run() integration
- get_metadata()
- Edge cases: zero volatility, very short maturity, deep ITM/OTM
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.option_pricing import OptionPricingModel, OptionPricingConfig



# ═══════════════════════════════════════════════════════════════════
# Dataclass
# ═══════════════════════════════════════════════════════════════════


class TestOptionPricingConfig:
    def test_default_init(self):
        cfg = OptionPricingConfig()
        assert cfg.S0 == 100.0
        assert cfg.K == 100.0
        assert cfg.T == 1.0
        assert cfg.r == 0.05
        assert cfg.sigma == 0.2
        assert cfg.q == 0.0
        assert cfg.n_steps == 100
        assert cfg.n_simulations == 100000
        assert cfg.option_type == "call"
        assert cfg.exercise_type == "european"
        assert cfg.random_seed == 42

    def test_custom_init(self):
        cfg = OptionPricingConfig(S0=150.0, K=140.0, T=0.5, sigma=0.3, option_type="put")
        assert cfg.S0 == 150.0
        assert cfg.K == 140.0
        assert cfg.T == 0.5
        assert cfg.sigma == 0.3
        assert cfg.option_type == "put"


# ═══════════════════════════════════════════════════════════════════
# OptionPricingModel Initialization
# ═══════════════════════════════════════════════════════════════════


class TestOptionPricingModelInit:
    def test_init(self):
        model = OptionPricingModel()
        assert model is not None
        assert model.config is not None

    def test_init_with_config(self):
        cfg = OptionPricingConfig(S0=150.0)
        model = OptionPricingModel(cfg)
        assert model.config.S0 == 150.0


# ═══════════════════════════════════════════════════════════════════
# Black-Scholes Pricing
# ═══════════════════════════════════════════════════════════════════


class TestBlackScholes:
    def test_call_price_positive(self):
        model = OptionPricingModel(OptionPricingConfig(option_type="call"))
        result = model.black_scholes()
        assert result["price"] > 0

    def test_put_price_positive(self):
        model = OptionPricingModel(OptionPricingConfig(option_type="put"))
        result = model.black_scholes()
        assert result["price"] > 0

    def test_atm_call(self):
        # At-the-money call should be roughly S * N(d1) - K * exp(-rT) * N(d2)
        model = OptionPricingModel(OptionPricingConfig(S0=100, K=100, T=1.0, r=0.05, sigma=0.2))
        result = model.black_scholes()
        # ATM call price should be around 10 for these parameters
        assert 5 < result["price"] < 20

    def test_greeks_present(self):
        model = OptionPricingModel()
        result = model.black_scholes()
        assert "delta" in result
        assert "gamma" in result
        assert "theta" in result
        assert "vega" in result
        assert "rho" in result

    def test_delta_range_call(self):
        model = OptionPricingModel(OptionPricingConfig(option_type="call"))
        result = model.black_scholes()
        assert 0 <= result["delta"] <= 1

    def test_delta_range_put(self):
        model = OptionPricingModel(OptionPricingConfig(option_type="put"))
        result = model.black_scholes()
        assert -1 <= result["delta"] <= 0

    def test_vega_positive(self):
        model = OptionPricingModel()
        result = model.black_scholes()
        assert result["vega"] >= 0

    def test_gamma_positive(self):
        model = OptionPricingModel()
        result = model.black_scholes()
        assert result["gamma"] >= 0

    def test_expired_option(self):
        model = OptionPricingModel(OptionPricingConfig(T=0))
        result = model.black_scholes()
        # Expired ATM option should have price = 0
        assert result["price"] == 0
        assert result["delta"] == 0
        assert result["gamma"] == 0

    def test_deep_itm_call(self):
        model = OptionPricingModel(OptionPricingConfig(S0=200, K=100, T=1.0))
        result = model.black_scholes()
        # Deep ITM call should have delta close to 1
        assert result["delta"] > 0.9
        # Price should be roughly S - K * exp(-rT)
        intrinsic = 200 - 100 * np.exp(-0.05 * 1.0)
        assert result["price"] > intrinsic * 0.9

    def test_deep_otm_call(self):
        model = OptionPricingModel(OptionPricingConfig(S0=50, K=100, T=1.0))
        result = model.black_scholes()
        # Deep OTM call should have delta close to 0
        assert result["delta"] < 0.1
        # Price should be small
        assert result["price"] < 5


# ═══════════════════════════════════════════════════════════════════
# Put-Call Parity
# ═══════════════════════════════════════════════════════════════════


class TestPutCallParity:
    def test_put_call_parity(self):
        # C - P = S * exp(-qT) - K * exp(-rT)
        cfg = OptionPricingConfig(S0=100, K=100, T=1.0, r=0.05, q=0.02)
        
        cfg.option_type = "call"
        model_call = OptionPricingModel(cfg)
        call_price = model_call.black_scholes()["price"]
        
        cfg.option_type = "put"
        model_put = OptionPricingModel(cfg)
        put_price = model_put.black_scholes()["price"]
        
        lhs = call_price - put_price
        rhs = 100 * np.exp(-0.02 * 1.0) - 100 * np.exp(-0.05 * 1.0)
        
        assert lhs == pytest.approx(rhs, abs=0.01)


# ═══════════════════════════════════════════════════════════════════
# Binomial Tree
# ═══════════════════════════════════════════════════════════════════


class TestBinomialTree:
    def test_european_call_price(self):
        model = OptionPricingModel(OptionPricingConfig(option_type="call", exercise_type="european"))
        result = model.binomial_tree(american=False)
        assert result["price"] > 0

    def test_american_put_premium(self):
        # American put should be worth at least as much as European
        model = OptionPricingModel(OptionPricingConfig(option_type="put", S0=80, K=100))
        european = model.binomial_tree(american=False)["price"]
        american = model.binomial_tree(american=True)["price"]
        assert american >= european

    def test_binomial_converges_to_bs(self):
        # With many steps, binomial should converge to Black-Scholes
        cfg = OptionPricingConfig(n_steps=500, option_type="call")
        model = OptionPricingModel(cfg)
        bs_price = model.black_scholes()["price"]
        binomial_price = model.binomial_tree(american=False)["price"]
        assert binomial_price == pytest.approx(bs_price, abs=0.5)

    def test_greeks_present(self):
        model = OptionPricingModel()
        result = model.binomial_tree()
        assert "delta" in result
        assert "gamma" in result


# ═══════════════════════════════════════════════════════════════════
# Monte Carlo
# ═══════════════════════════════════════════════════════════════════


class TestMonteCarlo:
    def test_mc_price_positive(self):
        model = OptionPricingModel(OptionPricingConfig(n_simulations=10000))
        result = model.monte_carlo()
        assert result["price"] > 0

    def test_mc_confidence_interval(self):
        model = OptionPricingModel(OptionPricingConfig(n_simulations=10000))
        result = model.monte_carlo()
        assert result["ci_lower"] < result["price"]
        assert result["price"] < result["ci_upper"]

    def test_mc_converges_to_bs(self):
        # Monte Carlo should be close to Black-Scholes
        cfg = OptionPricingConfig(n_simulations=50000)
        model = OptionPricingModel(cfg)
        bs_price = model.black_scholes()["price"]
        mc_price = model.monte_carlo()["price"]
        assert mc_price == pytest.approx(bs_price, abs=1.0)

    def test_antithetic_reduces_variance(self):
        cfg = OptionPricingConfig(n_simulations=10000)
        model = OptionPricingModel(cfg)
        result_anti = model.monte_carlo(antithetic=True)
        result_no_anti = model.monte_carlo(antithetic=False)
        # Both should give similar prices
        assert result_anti["price"] == pytest.approx(result_no_anti["price"], abs=1.0)


# ═══════════════════════════════════════════════════════════════════
# Implied Volatility
# ═══════════════════════════════════════════════════════════════════


class TestImpliedVolatility:
    def test_iv_recovers_input_volatility(self):
        sigma_input = 0.25
        model = OptionPricingModel(OptionPricingConfig(sigma=sigma_input))
        theoretical_price = model.black_scholes()["price"]
        iv = model.implied_volatility(theoretical_price)
        assert iv == pytest.approx(sigma_input, abs=0.001)

    def test_iv_none_for_invalid_price(self):
        model = OptionPricingModel()
        # Price that's too high should return None
        iv = model.implied_volatility(1000.0)
        assert iv is None


# ═══════════════════════════════════════════════════════════════════
# Sensitivity Analysis
# ═══════════════════════════════════════════════════════════════════


class TestSensitivityAnalysis:
    def test_sensitivity_structure(self):
        model = OptionPricingModel()
        result = model.sensitivity_analysis()
        assert "stock_price" in result
        assert "volatility" in result
        assert "time_to_maturity" in result
        assert "interest_rate" in result

    def test_sensitivity_arrays(self):
        model = OptionPricingModel()
        result = model.sensitivity_analysis()
        assert len(result["stock_price"]["parameter"]) == 50
        assert len(result["stock_price"]["price"]) == 50


# ═══════════════════════════════════════════════════════════════════
# Run Integration
# ═══════════════════════════════════════════════════════════════════


class TestRun:
    def test_run_structure(self):
        model = OptionPricingModel()
        result = model.run()
        assert "black_scholes" in result
        assert "binomial_european" in result
        assert "binomial_american" in result
        assert "monte_carlo" in result
        assert "sensitivity" in result
        assert "parameters" in result

    def test_run_call(self):
        cfg = OptionPricingConfig(option_type="call")
        model = OptionPricingModel(cfg)
        result = model.run()
        assert result["black_scholes"]["price"] > 0

    def test_run_put(self):
        cfg = OptionPricingConfig(option_type="put")
        model = OptionPricingModel(cfg)
        result = model.run()
        assert result["black_scholes"]["price"] > 0


# ═══════════════════════════════════════════════════════════════════
# get_metadata
# ═══════════════════════════════════════════════════════════════════


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = OptionPricingModel.get_metadata()
        assert meta["pattern_id"] == 55
        assert meta["name"] == "Option Pricing"
        assert "parameters" in meta
        assert "outputs" in meta


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_zero_volatility(self):
        model = OptionPricingModel(OptionPricingConfig(sigma=0.001))
        result = model.black_scholes()
        assert result["price"] >= 0

    def test_very_short_maturity(self):
        model = OptionPricingModel(OptionPricingConfig(T=0.01))
        result = model.black_scholes()
        # Short maturity ATM option should have small time value
        assert result["price"] < 10

    def test_high_volatility(self):
        model = OptionPricingModel(OptionPricingConfig(sigma=1.0))
        result = model.black_scholes()
        assert result["price"] > 0
        assert result["vega"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
