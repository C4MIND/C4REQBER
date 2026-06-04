"""
Tests for prospect_theory pattern module.
"""
import numpy as np
import pytest

from src.patterns.library.prospect_theory import ProspectTheoryConfig, ProspectTheoryModel



class TestConfig:
    def test_default_config(self):
        cfg = ProspectTheoryConfig()
        assert cfg.alpha == 0.88
        assert cfg.beta == 0.88
        assert cfg.lambda_param == 2.25
        assert cfg.gamma == 0.65
        assert cfg.delta == 0.65

    def test_custom_config(self):
        cfg = ProspectTheoryConfig(alpha=0.9, lambda_param=3.0)
        assert cfg.alpha == 0.9
        assert cfg.lambda_param == 3.0


class TestInit:
    def test_model_init_default(self):
        model = ProspectTheoryModel()
        assert model.config is not None

    def test_model_init_custom(self):
        cfg = ProspectTheoryConfig(alpha=0.9)
        model = ProspectTheoryModel(cfg)
        assert model.config.alpha == 0.9


class TestValueFunction:
    def test_value_function_gain(self):
        model = ProspectTheoryModel()
        v = model.value_function(100)
        assert v > 0
        assert v < 100  # Concave

    def test_value_function_loss(self):
        model = ProspectTheoryModel()
        v = model.value_function(-100)
        assert v < 0
        assert abs(v) > 100 * 0.5  # Loss aversion

    def test_value_function_concave_gains(self):
        model = ProspectTheoryModel()
        v1 = model.value_function(100)
        v2 = model.value_function(200)
        assert v2 < 2 * v1

    def test_value_function_convex_losses(self):
        model = ProspectTheoryModel()
        v1 = model.value_function(-100)
        v2 = model.value_function(-200)
        assert v2 > 2 * v1

    def test_loss_aversion(self):
        model = ProspectTheoryModel()
        v_gain = model.value_function(100)
        v_loss = model.value_function(-100)
        assert abs(v_loss) > v_gain


class TestProbabilityWeighting:
    def test_overweight_low(self):
        model = ProspectTheoryModel()
        w = model.probability_weighting(0.05)
        assert w > 0.05

    def test_underweight_high(self):
        model = ProspectTheoryModel()
        w = model.probability_weighting(0.95)
        assert w < 0.95

    def test_certainty(self):
        model = ProspectTheoryModel()
        assert model.probability_weighting(1.0) == 1.0
        assert model.probability_weighting(0.0) == 0.0


class TestCPT:
    def test_cpt_calculation(self):
        model = ProspectTheoryModel()
        cpt = model.cumulative_prospect_value([100, -50], [0.5, 0.5])
        assert np.isfinite(cpt)

    def test_cpt_symmetric(self):
        model = ProspectTheoryModel()
        cpt = model.cumulative_prospect_value([100, -100], [0.5, 0.5])
        assert cpt < 0  # Loss aversion makes it negative


class TestAnalyzeGamble:
    def test_analyze_gamble(self):
        model = ProspectTheoryModel()
        result = model.analyze_gamble([100, 0], [0.5, 0.5], "Test")
        assert result["name"] == "Test"
        assert "cpt_value" in result
        assert "expected_value" in result
        assert "certainty_equivalent" in result

    def test_risk_premium(self):
        model = ProspectTheoryModel()
        result = model.analyze_gamble([100, 0], [0.5, 0.5])
        assert isinstance(result["risk_premium"], float)


class TestFourfoldPattern:
    def test_fourfold_pattern(self):
        model = ProspectTheoryModel()
        result = model.fourfold_pattern()
        assert "gambles" in result
        assert len(result["gambles"]) == 4
        assert "pattern" in result

    def test_fourfold_keys(self):
        model = ProspectTheoryModel()
        result = model.fourfold_pattern()
        assert "high_prob_gain" in result["gambles"]
        assert "low_prob_gain" in result["gambles"]
        assert "high_prob_loss" in result["gambles"]
        assert "low_prob_loss" in result["gambles"]


class TestLossAversion:
    def test_loss_aversion_analysis(self):
        model = ProspectTheoryModel()
        result = model.loss_aversion_analysis()
        assert "loss_aversion_coefficient" in result
        assert result["loss_aversion_coefficient"] == 2.25
        assert "gain_gamble" in result
        assert "loss_gamble" in result

    def test_loss_aversion_ratio(self):
        model = ProspectTheoryModel()
        result = model.loss_aversion_analysis()
        assert result["loss_aversion_ratio"] > 1.0


class TestPreferenceReversals:
    def test_preference_reversals(self):
        model = ProspectTheoryModel()
        result = model.preference_reversals()
        assert "common_consequence" in result
        assert "common_ratio" in result

    def test_allais_paradox(self):
        model = ProspectTheoryModel()
        result = model.preference_reversals()
        assert "problem_1" in result["common_consequence"]
        assert "problem_2" in result["common_consequence"]


class TestRun:
    def test_run(self):
        model = ProspectTheoryModel()
        result = model.run()
        assert "fourfold_pattern" in result
        assert "loss_aversion" in result
        assert "preference_reversals" in result
        assert "value_function" in result
        assert "probability_weighting" in result

    def test_metadata(self):
        meta = ProspectTheoryModel.get_metadata()
        assert "pattern_id" in meta
        assert "name" in meta


class TestEdgeCases:
    def test_zero_outcome(self):
        model = ProspectTheoryModel()
        v = model.value_function(0)
        assert v == 0

    def test_certain_gamble(self):
        model = ProspectTheoryModel()
        result = model.analyze_gamble([100], [1.0])
        assert result["certainty_equivalent"] == pytest.approx(100.0, abs=1e-5)

    def test_extreme_probability(self):
        model = ProspectTheoryModel()
        w = model.probability_weighting(0.001)
        assert w > 0.001  # Overweighting
