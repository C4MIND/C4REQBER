"""
Tests for economic_growth pattern module.
"""

import numpy as np
import pytest

from src.patterns.library.economic_growth import EconomicGrowthConfig, EconomicGrowthModel


class TestConfig:
    def test_default_config(self):
        cfg = EconomicGrowthConfig()
        assert cfg.model_type == "solow"
        assert cfg.T == 100
        assert cfg.alpha == 0.33
        assert cfg.s == 0.25

    def test_custom_config(self):
        cfg = EconomicGrowthConfig(model_type="ramsey", T=50)
        assert cfg.model_type == "ramsey"
        assert cfg.T == 50


class TestInit:
    def test_model_init_default(self):
        model = EconomicGrowthModel()
        assert model.config is not None

    def test_model_init_custom(self):
        cfg = EconomicGrowthConfig(T=50)
        model = EconomicGrowthModel(cfg)
        assert model.config.T == 50


class TestProduction:
    def test_production_positive(self):
        model = EconomicGrowthModel()
        Y, MPK, wage = model.production(10, 10, 1)
        assert Y > 0
        assert MPK > 0
        assert wage >= 0

    def test_diminishing_returns(self):
        model = EconomicGrowthModel()
        Y1, MPK1, _ = model.production(10, 10, 1)
        Y2, MPK2, _ = model.production(20, 10, 1)
        assert Y2 > Y1
        assert MPK2 < MPK1


class TestSolow:
    def test_solow_steady_state(self):
        model = EconomicGrowthModel()
        result = model.solow_model()
        assert result["steady_state"]["k_star"] > 0
        assert result["steady_state"]["y_star"] > 0

    def test_solow_transition(self):
        model = EconomicGrowthModel()
        result = model.solow_model()
        k_path = np.array(result["transition"]["capital_per_worker"])
        assert np.all(k_path > 0)
        assert len(k_path) == model.config.T

    def test_solow_golden_rule(self):
        model = EconomicGrowthModel()
        result = model.solow_model()
        gr = result["golden_rule"]
        assert 0 < gr["savings_rate"] < 1
        assert gr["consumption"] > 0


class TestRamsey:
    def test_ramsey_optimal_path(self):
        cfg = EconomicGrowthConfig(model_type="ramsey", T=50)
        model = EconomicGrowthModel(cfg)
        result = model.ramsey_model()
        assert "optimal_path" in result
        assert "capital" in result["optimal_path"]
        assert len(result["optimal_path"]["capital"]) == 50

    def test_ramsey_steady_state(self):
        cfg = EconomicGrowthConfig(model_type="ramsey", T=50)
        model = EconomicGrowthModel(cfg)
        result = model.ramsey_model()
        assert result["steady_state"]["k_star"] > 0
        assert result["steady_state"]["c_star"] > 0


class TestRomer:
    def test_romer_growth(self):
        cfg = EconomicGrowthConfig(model_type="romer")
        model = EconomicGrowthModel(cfg)
        result = model.romer_model()
        knowledge = np.array(result["knowledge_path"])
        assert knowledge[-1] > knowledge[0]

    def test_romer_output(self):
        cfg = EconomicGrowthConfig(model_type="romer")
        model = EconomicGrowthModel(cfg)
        result = model.romer_model()
        output = np.array(result["output_path"])
        assert output[-1] > output[0]


class TestConvergence:
    def test_convergence_countries(self):
        model = EconomicGrowthModel()
        result = model.convergence_analysis()
        assert len(result["countries"]) == 5

    def test_conditional_convergence(self):
        model = EconomicGrowthModel()
        result = model.convergence_analysis()
        assert result["conditional_convergence"] is True


class TestRun:
    def test_run_solow(self):
        cfg = EconomicGrowthConfig(model_type="solow")
        model = EconomicGrowthModel(cfg)
        result = model.run()
        assert result["model_type"] == "solow"
        assert "model_results" in result
        assert "convergence" in result

    def test_run_ramsey(self):
        cfg = EconomicGrowthConfig(model_type="ramsey", T=50)
        model = EconomicGrowthModel(cfg)
        result = model.run()
        assert result["model_type"] == "ramsey"

    def test_run_romer(self):
        cfg = EconomicGrowthConfig(model_type="romer")
        model = EconomicGrowthModel(cfg)
        result = model.run()
        assert result["model_type"] == "romer"

    def test_metadata(self):
        meta = EconomicGrowthModel.get_metadata()
        assert "pattern_id" in meta
        assert "name" in meta


class TestEdgeCases:
    def test_zero_capital(self):
        model = EconomicGrowthModel()
        Y, MPK, wage = model.production(0, 10, 1)
        assert Y == 0
        assert MPK == float("inf")

    def test_high_savings_rate(self):
        cfg = EconomicGrowthConfig(s=0.9)
        model = EconomicGrowthModel(cfg)
        result = model.solow_model()
        assert result["steady_state"]["k_star"] > 0

    def test_comparative_statics(self):
        model = EconomicGrowthModel()
        result = model.run()
        assert "comparative_statics" in result
        assert "savings_rate_effect" in result["comparative_statics"]
