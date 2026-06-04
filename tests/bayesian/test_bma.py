"""Tests for src/bayesian/bma.py."""

from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

from src.bayesian.bma import (
    BMAResult,
    ModelEvidence,
    SimpleBMAResult,
    aic_approximation,
    bayes_factor,
    bayesian_model_averaging,
    bic_approximation,
    bma_predictive_distribution,
    interpret_bayes_factor,
    laplace_approximation,
    model_averaging,
    model_selection_by_bic,
    numerical_integration_evidence,
)


class TestLaplaceApproximation:
    """Tests for Laplace approximation of model evidence."""

    def test_gaussian_posterior(self):
        def log_posterior(x: np.ndarray) -> float:
            return float(-0.5 * np.sum(x**2))

        mode = np.array([0.0])
        result = laplace_approximation(log_posterior, mode)
        assert isinstance(result, ModelEvidence)
        assert result.method == "laplace"
        expected = 0.5 * np.log(2 * np.pi)
        assert result.log_evidence == pytest.approx(expected, abs=0.1)

    def test_with_precomputed_hessian(self):
        def log_posterior(x: np.ndarray) -> float:
            return float(-0.5 * np.sum(x**2))

        mode = np.array([0.0])
        hessian = np.array([[1.0]])
        result = laplace_approximation(log_posterior, mode, hessian=hessian)
        assert result.log_evidence == pytest.approx(0.5 * np.log(2 * np.pi), abs=0.1)

    def test_multivariate(self):
        def log_posterior(x: np.ndarray) -> float:
            return float(-0.5 * np.sum(x**2))

        mode = np.array([0.0, 0.0])
        result = laplace_approximation(log_posterior, mode)
        expected = np.log(2 * np.pi)
        assert result.log_evidence == pytest.approx(expected, abs=0.2)

    def test_non_positive_definite_hessian_fallback(self):
        def log_posterior(x: np.ndarray) -> float:
            return float(-0.5 * x[0]**2)

        mode = np.array([0.0])
        hessian = np.array([[0.0]])
        result = laplace_approximation(log_posterior, mode, hessian=hessian)
        assert np.isfinite(result.log_evidence)


class TestNumericalIntegrationEvidence:
    """Tests for numerical integration evidence."""

    def test_1d_gaussian(self):
        def log_posterior(x: np.ndarray) -> float:
            return float(-0.5 * x[0]**2)

        result = numerical_integration_evidence(
            log_posterior,
            bounds=[(-5.0, 5.0)],
        )
        assert isinstance(result, ModelEvidence)
        assert result.method in ("quad", "grid")
        expected = np.log(np.sqrt(2 * np.pi))
        assert result.log_evidence == pytest.approx(expected, abs=0.5)

    def test_2d_gaussian(self):
        def log_posterior(x: np.ndarray) -> float:
            return float(-0.5 * np.sum(x**2))

        result = numerical_integration_evidence(
            log_posterior,
            bounds=[(-3.0, 3.0), (-3.0, 3.0)],
            n_points=50,
        )
        assert result.method == "grid"
        expected = np.log(2 * np.pi)
        assert result.log_evidence == pytest.approx(expected, abs=0.5)

    def test_narrow_bounds(self):
        def log_posterior(x: np.ndarray) -> float:
            return float(-0.5 * x[0]**2)

        result = numerical_integration_evidence(
            log_posterior,
            bounds=[(-10.0, 10.0)],
        )
        assert np.isfinite(result.log_evidence)


class TestBayesFactor:
    """Tests for Bayes factor computation."""

    def test_equal_models(self):
        bf = bayes_factor(0.0, 0.0)
        assert bf == pytest.approx(1.0)

    def test_strong_evidence(self):
        bf = bayes_factor(10.0, 0.0)
        assert bf == pytest.approx(np.exp(10.0))
        assert bf > 100.0

    def test_favors_model2(self):
        bf = bayes_factor(0.0, 5.0)
        assert bf < 1.0

    def test_interpretation(self):
        assert interpret_bayes_factor(0.5) == "negative (favors alternative)"
        assert interpret_bayes_factor(2.0) == "barely worth mentioning"
        assert interpret_bayes_factor(5.0) == "substantial"
        assert interpret_bayes_factor(15.0) == "strong"
        assert interpret_bayes_factor(50.0) == "very strong"
        assert interpret_bayes_factor(200.0) == "decisive"


class TestModelAveraging:
    """Tests for Bayesian Model Averaging."""

    def test_uniform_priors(self):
        evidences = {
            "M1": 0.0,
            "M2": 0.0,
        }
        result = model_averaging(evidences)
        assert isinstance(result, BMAResult)
        assert result.model_probs["M1"] == pytest.approx(0.5, abs=1e-10)
        assert result.model_probs["M2"] == pytest.approx(0.5, abs=1e-10)

    def test_strong_evidence_favors_one(self):
        evidences = {
            "M1": 10.0,
            "M2": 0.0,
        }
        result = model_averaging(evidences)
        assert result.model_probs["M1"] > 0.99
        assert result.best_model == "M1"

    def test_custom_priors(self):
        evidences = {
            "M1": 0.0,
            "M2": 0.0,
        }
        priors = {"M1": 0.8, "M2": 0.2}
        result = model_averaging(evidences, priors)
        assert result.model_probs["M1"] == pytest.approx(0.8, abs=1e-10)

    def test_three_models(self):
        evidences = {
            "M1": 0.0,
            "M2": 2.0,
            "M3": 1.0,
        }
        result = model_averaging(evidences)
        assert result.model_probs["M2"] > result.model_probs["M3"]
        assert result.model_probs["M3"] > result.model_probs["M1"]

    def test_model_evidences_preserved(self):
        evidences = {
            "M1": 3.0,
            "M2": 1.0,
        }
        result = model_averaging(evidences)
        assert result.model_evidences["M1"] == pytest.approx(3.0)
        assert result.model_evidences["M2"] == pytest.approx(1.0)


class TestBMAPredictiveDistribution:
    """Tests for BMA predictive distribution."""

    def test_basic_averaging(self):
        x = np.array([0.0, 1.0, 2.0])
        predictives = {
            "M1": np.array([0.5, 0.5, 0.5]),
            "M2": np.array([1.0, 1.0, 1.0]),
        }
        probs = {"M1": 0.5, "M2": 0.5}
        result = bma_predictive_distribution(x, predictives, probs)
        expected = np.array([0.75, 0.75, 0.75])
        np.testing.assert_array_almost_equal(result, expected)

    def test_single_model(self):
        x = np.array([0.0, 1.0])
        predictives = {
            "M1": np.array([0.3, 0.7]),
        }
        probs = {"M1": 1.0}
        result = bma_predictive_distribution(x, predictives, probs)
        np.testing.assert_array_almost_equal(result, np.array([0.3, 0.7]))

    def test_missing_model_prob(self):
        x = np.array([0.0])
        predictives = {
            "M1": np.array([1.0]),
            "M2": np.array([0.0]),
        }
        probs = {"M1": 1.0}
        result = bma_predictive_distribution(x, predictives, probs)
        assert result[0] == pytest.approx(1.0)


class TestBICApproximation:
    """Tests for BIC approximation."""

    def test_basic(self):
        log_like = 100.0
        n_params = 5
        n_obs = 100
        bic = bic_approximation(log_like, n_params, n_obs)
        expected = 100.0 - 0.5 * 5 * np.log(100)
        assert bic == pytest.approx(expected)

    def test_penalty_increases_with_params(self):
        bic1 = bic_approximation(100.0, 2, 100)
        bic2 = bic_approximation(100.0, 10, 100)
        assert bic2 < bic1

    def test_zero_observations(self):
        bic = bic_approximation(100.0, 5, 0)
        assert bic == pytest.approx(100.0)


class TestAICApproximation:
    """Tests for AIC approximation."""

    def test_basic(self):
        aic = aic_approximation(100.0, 5)
        expected = 100.0 - 5
        assert aic == pytest.approx(expected)

    def test_penalty_increases_with_params(self):
        aic1 = aic_approximation(100.0, 2)
        aic2 = aic_approximation(100.0, 10)
        assert aic2 < aic1


class TestModelSelectionByBIC:
    """Tests for BIC-based model selection."""

    def test_selects_simpler_when_equal_fit(self):
        models = {
            "Simple": (100.0, 2),
            "Complex": (100.0, 10),
        }
        best, bics = model_selection_by_bic(models, n_obs=100)
        assert best == "Simple"
        assert bics["Simple"] > bics["Complex"]

    def test_selects_better_fit(self):
        models = {
            "M1": (50.0, 2),
            "M2": (100.0, 2),
        }
        best, bics = model_selection_by_bic(models, n_obs=100)
        assert best == "M2"

    def test_returns_all_bics(self):
        models = {
            "M1": (50.0, 2),
            "M2": (100.0, 5),
        }
        best, bics = model_selection_by_bic(models, n_obs=100)
        assert len(bics) == 2
        assert "M1" in bics
        assert "M2" in bics


class TestBayesianModelAveragingSimple:
    """Tests for the simple BMA wrapper."""

    def test_basic_averaging(self):
        models = [
            ("M1", 0.5, 10.0),
            ("M2", 0.5, 20.0),
        ]
        result = bayesian_model_averaging(models)
        assert isinstance(result, SimpleBMAResult)
        assert result.weighted_prediction == pytest.approx(15.0)
        assert result.uncertainty > 0

    def test_single_model(self):
        models = [("M1", 1.0, 42.0)]
        result = bayesian_model_averaging(models)
        assert result.weighted_prediction == pytest.approx(42.0)
        assert result.uncertainty == pytest.approx(0.0, abs=1e-10)

    def test_dominant_model(self):
        models = [
            ("M1", 0.95, 100.0),
            ("M2", 0.05, 0.0),
        ]
        result = bayesian_model_averaging(models)
        assert result.weighted_prediction == pytest.approx(95.0, abs=1.0)

    def test_uncertainty_reduces_with_agreement(self):
        models_agree = [
            ("M1", 0.5, 10.0),
            ("M2", 0.5, 10.0),
        ]
        disagree = [
            ("M1", 0.5, 0.0),
            ("M2", 0.5, 100.0),
        ]
        r_agree = bayesian_model_averaging(models_agree)
        r_disagree = bayesian_model_averaging(disagree)
        assert r_agree.uncertainty < r_disagree.uncertainty

    def test_empty_models(self):
        result = bayesian_model_averaging([])
        assert result.weighted_prediction == 0.0
        assert result.uncertainty == 0.0
        assert result.models == []

    def test_zero_total_probability(self):
        models = [
            ("M1", 0.0, 10.0),
            ("M2", 0.0, 20.0),
        ]
        result = bayesian_model_averaging(models)
        assert result.weighted_prediction == 0.0

    def test_negative_prediction(self):
        models = [
            ("M1", 0.5, -10.0),
            ("M2", 0.5, 10.0),
        ]
        result = bayesian_model_averaging(models)
        assert result.weighted_prediction == pytest.approx(0.0)

    def test_model_objects_preserved(self):
        models = [
            ("Model_A", 0.7, 1.5),
            ("Model_B", 0.3, 3.0),
        ]
        result = bayesian_model_averaging(models)
        assert len(result.models) == 2
        assert result.models[0]["name"] == "Model_A"
        assert result.models[0]["posterior_prob"] == 0.7
        assert result.models[0]["prediction"] == 1.5

    def test_three_models(self):
        models = [
            ("M1", 0.2, 1.0),
            ("M2", 0.3, 5.0),
            ("M3", 0.5, 9.0),
        ]
        result = bayesian_model_averaging(models)
        expected = 0.2 * 1.0 + 0.3 * 5.0 + 0.5 * 9.0
        assert result.weighted_prediction == pytest.approx(expected)


class TestBMAIntegration:
    """Integration tests for full BMA workflow."""

    def test_full_workflow_linear_models(self):
        np.random.seed(42)
        x = np.linspace(0, 10, 50)
        y = 2.0 * x + 1.0 + np.random.randn(50) * 0.5

        def log_like_m1(params: np.ndarray) -> float:
            pred = params[0]
            rss = np.sum((y - pred) ** 2)
            return -0.5 * rss

        def log_like_m2(params: np.ndarray) -> float:
            pred = params[0] + params[1] * x
            rss = np.sum((y - pred) ** 2)
            return -0.5 * rss

        mode1 = np.array([np.mean(y)])
        mode2 = np.array([1.0, 2.0])

        ev1 = laplace_approximation(
            lambda p: log_like_m1(p) - 0.5 * np.sum(p**2),
            mode1,
        )
        ev2 = laplace_approximation(
            lambda p: log_like_m2(p) - 0.5 * np.sum(p**2),
            mode2,
        )

        result = model_averaging({
            "constant": ev1.log_evidence,
            "linear": ev2.log_evidence,
        })

        assert "constant" in result.model_probs
        assert "linear" in result.model_probs
        assert sum(result.model_probs.values()) == pytest.approx(1.0, abs=1e-10)

    def test_bic_vs_laplace_consistency(self):
        def log_posterior(x: np.ndarray) -> float:
            return float(-0.5 * x[0]**2)

        mode = np.array([0.0])
        laplace_ev = laplace_approximation(log_posterior, mode)
        bic_ev = bic_approximation(0.0, 1, 100)

        assert np.isfinite(laplace_ev.log_evidence)
        assert np.isfinite(bic_ev)

    def test_predictive_distribution_integration(self):
        x_grid = np.linspace(-3, 3, 100)

        pred_m1 = stats.norm.pdf(x_grid, loc=0.0, scale=1.0)
        pred_m2 = stats.norm.pdf(x_grid, loc=1.0, scale=1.5)

        result = bma_predictive_distribution(
            x_grid,
            {"M1": pred_m1, "M2": pred_m2},
            {"M1": 0.6, "M2": 0.4},
        )

        assert len(result) == len(x_grid)
        assert np.all(result >= 0)
        assert np.trapezoid(result, x_grid) == pytest.approx(1.0, abs=0.1)
