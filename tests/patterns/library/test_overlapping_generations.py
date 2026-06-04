"""
Tests for src/patterns/library/overlapping_generations.py (Overlapping Generations Model)

Covers:
- OLGConfig dataclass
- OverlappingGenerationsModel initialization
- _compute_steady_state_k()
- _solve_savings_rate()
- _utility()
- run() simulation
- _calculate_welfare_gain()
- _compute_generational_accounts()
- get_metadata()
- Edge cases: extreme parameters, convergence
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.overlapping_generations import (
    OverlappingGenerationsModel,
    OLGConfig,
)


# ═══════════════════════════════════════════════════════════════════
# Config Tests
# ═══════════════════════════════════════════════════════════════════


class TestOLGConfig:
    def test_default_init(self):
        cfg = OLGConfig()
        assert cfg.n_generations == 20
        assert cfg.periods == 50
        assert cfg.alpha == 0.33
        assert cfg.beta == 0.96
        assert cfg.delta == 0.1
        assert cfg.gamma == 2.0
        assert cfg.random_seed == 42

    def test_custom_init(self):
        cfg = OLGConfig(
            n_generations=30,
            periods=100,
            alpha=0.4,
            beta=0.95,
        )
        assert cfg.n_generations == 30
        assert cfg.periods == 100
        assert cfg.alpha == 0.4
        assert cfg.beta == 0.95


# ═══════════════════════════════════════════════════════════════════
# Initialization Tests
# ═══════════════════════════════════════════════════════════════════


class TestOLGModelInit:
    def test_init_default(self):
        model = OverlappingGenerationsModel()
        assert model is not None
        assert model.alpha == 0.33
        assert model.beta == 0.96

    def test_init_with_config(self):
        cfg = OLGConfig(alpha=0.4, beta=0.95)
        model = OverlappingGenerationsModel(cfg)
        assert model.alpha == 0.4
        assert model.beta == 0.95

    def test_steady_state_computed(self):
        model = OverlappingGenerationsModel()
        assert model.k_ss > 0
        assert model.y_ss > 0
        assert model.w_ss > 0


# ═══════════════════════════════════════════════════════════════════
# Steady State Tests
# ═══════════════════════════════════════════════════════════════════


class TestSteadyState:
    def test_steady_state_positive(self):
        cfg = OLGConfig()
        model = OverlappingGenerationsModel(cfg)
        assert model.k_ss > 0
        assert model.y_ss > 0
        assert model.w_ss > 0
        assert model.r_ss > -1  # Interest rate can be negative but > -100%

    def test_steady_state_consistency(self):
        cfg = OLGConfig()
        model = OverlappingGenerationsModel(cfg)
        # Check production function consistency
        expected_y = model.A * model.k_ss ** model.alpha
        assert abs(model.y_ss - expected_y) < 0.01


# ═══════════════════════════════════════════════════════════════════
# Savings Rate Tests
# ═══════════════════════════════════════════════════════════════════


class TestSolveSavingsRate:
    def test_savings_rate_range(self):
        cfg = OLGConfig()
        model = OverlappingGenerationsModel(cfg)
        s_rate = model._solve_savings_rate(w=1.0, r=0.03)
        assert 0 < s_rate < 1

    def test_savings_rate_with_high_wage(self):
        cfg = OLGConfig()
        model = OverlappingGenerationsModel(cfg)
        s_rate = model._solve_savings_rate(w=10.0, r=0.03)
        assert 0 < s_rate < 1


# ═══════════════════════════════════════════════════════════════════
# Utility Tests
# ═══════════════════════════════════════════════════════════════════


class TestUtility:
    def test_log_utility(self):
        cfg = OLGConfig(gamma=1.0)
        model = OverlappingGenerationsModel(cfg)
        u = model._utility(c1=1.0, c2=1.0)
        assert u == pytest.approx(0.0, abs=1e-10)  # log(1) = 0

    def test_crra_utility(self):
        cfg = OLGConfig(gamma=2.0)
        model = OverlappingGenerationsModel(cfg)
        u = model._utility(c1=1.0, c2=1.0)
        # With gamma=2: (1^(1-2) - 1)/(1-2) = (1 - 1)/(-1) = 0
        assert u == pytest.approx(0.0, abs=1e-10)

    def test_utility_with_zero_consumption(self):
        cfg = OLGConfig(gamma=2.0)
        model = OverlappingGenerationsModel(cfg)
        u = model._utility(c1=0.0, c2=1.0)
        assert u < -900  # Large negative value


# ═══════════════════════════════════════════════════════════════════
# Run Tests
# ═══════════════════════════════════════════════════════════════════


class TestRun:
    def test_run_default(self):
        cfg = OLGConfig(periods=50)
        model = OverlappingGenerationsModel(cfg)
        result = model.run()
        assert result is not None
        assert "steady_state" in result
        assert "transition" in result
        assert "policy_analysis" in result

    def test_steady_state_structure(self):
        cfg = OLGConfig()
        model = OverlappingGenerationsModel(cfg)
        result = model.run()
        ss = result["steady_state"]
        assert "k_ss" in ss
        assert "y_ss" in ss
        assert "r_ss" in ss
        assert "w_ss" in ss

    def test_transition_structure(self):
        cfg = OLGConfig(periods=50)
        model = OverlappingGenerationsModel(cfg)
        result = model.run()
        trans = result["transition"]
        assert "capital" in trans
        assert "output" in trans
        assert "wages" in trans
        assert len(trans["capital"]) == 50

    def test_policy_analysis_structure(self):
        cfg = OLGConfig(tau=0.15, pension_rate=0.3)
        model = OverlappingGenerationsModel(cfg)
        result = model.run()
        policy = result["policy_analysis"]
        assert "welfare_gain_payg" in policy
        assert "dynamically_efficient" in policy
        assert isinstance(policy["dynamically_efficient"], bool)

    def test_capital_positive(self):
        cfg = OLGConfig(periods=50)
        model = OverlappingGenerationsModel(cfg)
        result = model.run()
        k_path = np.array(result["transition"]["capital"])
        assert np.all(k_path > 0)

    def test_convergence_period(self):
        cfg = OLGConfig(periods=50)
        model = OverlappingGenerationsModel(cfg)
        result = model.run()
        assert "convergence_period" in result
        assert result["convergence_period"] > 0


# ═══════════════════════════════════════════════════════════════════
# Generational Accounts Tests
# ═══════════════════════════════════════════════════════════════════


class TestGenerationalAccounts:
    def test_generational_accounts_structure(self):
        cfg = OLGConfig()
        model = OverlappingGenerationsModel(cfg)
        result = model.run()
        accounts = result["generational_accounts"]
        assert "generations" in accounts
        assert "net_accounts" in accounts
        assert len(accounts["generations"]) == len(accounts["net_accounts"])


# ═══════════════════════════════════════════════════════════════════
# Metadata Tests
# ═══════════════════════════════════════════════════════════════════


class TestMetadata:
    def test_metadata_structure(self):
        meta = OverlappingGenerationsModel.get_metadata()
        assert meta["pattern_id"] == 52
        assert meta["name"] == "Overlapping Generations"
        assert "Macroeconomics" in meta["category"]
        assert meta["author"] == "Peter Diamond"
        assert meta["year"] == 1965

    def test_metadata_parameters(self):
        meta = OverlappingGenerationsModel.get_metadata()
        assert "alpha" in meta["parameters"]
        assert "beta" in meta["parameters"]
        assert "gamma" in meta["parameters"]


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_high_discount_factor(self):
        cfg = OLGConfig(beta=0.999, periods=50)
        model = OverlappingGenerationsModel(cfg)
        result = model.run()
        assert "steady_state" in result

    def test_low_discount_factor(self):
        cfg = OLGConfig(beta=0.9, periods=50)
        model = OverlappingGenerationsModel(cfg)
        result = model.run()
        assert "steady_state" in result

    def test_high_capital_share(self):
        cfg = OLGConfig(alpha=0.5, periods=50)
        model = OverlappingGenerationsModel(cfg)
        result = model.run()
        assert "steady_state" in result

    def test_log_utility(self):
        cfg = OLGConfig(gamma=1.0, periods=50)
        model = OverlappingGenerationsModel(cfg)
        result = model.run()
        assert "steady_state" in result

    def test_with_tax(self):
        cfg = OLGConfig(tau=0.2, pension_rate=0.5, periods=50)
        model = OverlappingGenerationsModel(cfg)
        result = model.run()
        assert "policy_analysis" in result


# ═══════════════════════════════════════════════════════════════════
# Alias Test
# ═══════════════════════════════════════════════════════════════════


class TestAlias:
    def test_overlapping_generations_pattern_alias(self):
        from src.patterns.library.overlapping_generations import OverlappingGenerationsPattern

        assert OverlappingGenerationsPattern is OverlappingGenerationsModel


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
