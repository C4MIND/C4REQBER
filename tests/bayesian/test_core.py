"""Comprehensive tests for src/bayesian/core.py."""

from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

from src.bayesian.core import (
    BetaBinomialResult,
    DirichletMultinomialResult,
    GammaPoissonResult,
    NormalNormalResult,
    beta_binomial,
    dirichlet_multinomial,
    gamma_poisson,
    normal_normal,
)


class TestNormalNormal:
    """Tests for normal_normal conjugate update."""

    def test_basic_update(self):
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        mu_prior = 0.0
        tau_prior = 1.0
        sigma_known = 2.0

        result = normal_normal(data, mu_prior, tau_prior, sigma_known)

        assert isinstance(result, NormalNormalResult)
        n = float(len(data))
        sample_mean = np.mean(data)
        sigma2 = sigma_known**2
        expected_tau = tau_prior + n / sigma2
        expected_mu = (tau_prior * mu_prior + n * sample_mean / sigma2) / expected_tau

        assert result.mu_post == pytest.approx(expected_mu, rel=1e-10)
        assert result.tau_post == pytest.approx(expected_tau, rel=1e-10)
        assert result.credible_interval[0] < result.credible_interval[1]
        assert result.credible_interval[0] < result.mu_post < result.credible_interval[1]

    def test_prior_dominance(self):
        """Strong prior precision + small data → posterior close to prior."""
        data = np.array([100.0])
        mu_prior = 0.0
        tau_prior = 100.0
        sigma_known = 1.0

        result = normal_normal(data, mu_prior, tau_prior, sigma_known)

        assert result.mu_post == pytest.approx(0.0, abs=2.0)
        assert result.tau_post > 50.0

    def test_data_dominance(self):
        """Weak prior precision + large data → posterior close to sample mean."""
        data = np.full(1000, 50.0)
        mu_prior = 0.0
        tau_prior = 0.01
        sigma_known = 10.0

        result = normal_normal(data, mu_prior, tau_prior, sigma_known)

        assert result.mu_post == pytest.approx(50.0, abs=0.5)
        assert result.tau_post > 5.0

    def test_credible_interval_bounds_95(self):
        data = np.array([0.0, 0.0, 0.0])
        result = normal_normal(data, mu_prior=0.0, tau_prior=1.0, sigma_known=1.0)

        std_post = np.sqrt(1.0 / result.tau_post)
        alpha = 0.025
        expected_low = stats.norm.ppf(alpha, loc=result.mu_post, scale=std_post)
        expected_high = stats.norm.ppf(1 - alpha, loc=result.mu_post, scale=std_post)

        assert result.credible_interval[0] == pytest.approx(expected_low, rel=1e-10)
        assert result.credible_interval[1] == pytest.approx(expected_high, rel=1e-10)

    def test_credible_interval_bounds_99(self):
        data = np.array([1.0, 2.0, 3.0])
        result = normal_normal(
            data, mu_prior=0.0, tau_prior=1.0, sigma_known=1.0, credible_level=0.99
        )

        std_post = np.sqrt(1.0 / result.tau_post)
        alpha = 0.005
        expected_low = stats.norm.ppf(alpha, loc=result.mu_post, scale=std_post)
        expected_high = stats.norm.ppf(1 - alpha, loc=result.mu_post, scale=std_post)

        assert result.credible_interval[0] == pytest.approx(expected_low, rel=1e-10)
        assert result.credible_interval[1] == pytest.approx(expected_high, rel=1e-10)
        assert result.credible_interval[0] < result.credible_interval[1]

    def test_empty_data(self):
        """Empty data → posterior mean is nan (numpy mean of empty slice), tau_post = prior."""
        data = np.array([], dtype=np.float64)
        result = normal_normal(data, mu_prior=5.0, tau_prior=2.0, sigma_known=1.0)

        assert np.isnan(result.mu_post)
        assert result.tau_post == pytest.approx(2.0, rel=1e-10)


class TestBetaBinomial:
    """Tests for beta_binomial conjugate update."""

    def test_basic_update(self):
        result = beta_binomial(successes=7, trials=10, alpha_prior=2.0, beta_prior=2.0)

        assert isinstance(result, BetaBinomialResult)
        assert result.alpha_post == pytest.approx(9.0, rel=1e-10)
        assert result.beta_post == pytest.approx(5.0, rel=1e-10)
        assert 0.0 < result.credible_interval[0] < result.credible_interval[1] < 1.0

    def test_zero_successes(self):
        result = beta_binomial(successes=0, trials=10, alpha_prior=1.0, beta_prior=1.0)

        assert result.alpha_post == pytest.approx(1.0, rel=1e-10)
        assert result.beta_post == pytest.approx(11.0, rel=1e-10)
        assert result.credible_interval[0] >= 0.0
        assert result.credible_interval[1] < 1.0

    def test_all_successes(self):
        result = beta_binomial(successes=10, trials=10, alpha_prior=1.0, beta_prior=1.0)

        assert result.alpha_post == pytest.approx(11.0, rel=1e-10)
        assert result.beta_post == pytest.approx(1.0, rel=1e-10)
        assert result.credible_interval[0] > 0.0
        assert result.credible_interval[1] <= 1.0

    def test_credible_interval_coverage(self):
        result = beta_binomial(successes=5, trials=10, alpha_prior=1.0, beta_prior=1.0)

        alpha = 0.025
        expected_low = stats.beta.ppf(alpha, result.alpha_post, result.beta_post)
        expected_high = stats.beta.ppf(1 - alpha, result.alpha_post, result.beta_post)

        assert result.credible_interval[0] == pytest.approx(expected_low, rel=1e-10)
        assert result.credible_interval[1] == pytest.approx(expected_high, rel=1e-10)

    def test_no_trials(self):
        """Zero trials → posterior equals prior."""
        result = beta_binomial(successes=0, trials=0, alpha_prior=3.0, beta_prior=4.0)

        assert result.alpha_post == pytest.approx(3.0, rel=1e-10)
        assert result.beta_post == pytest.approx(4.0, rel=1e-10)


class TestGammaPoisson:
    """Tests for gamma_poisson conjugate update."""

    def test_basic_update(self):
        data = np.array([2.0, 3.0, 4.0, 5.0])
        result = gamma_poisson(data, alpha_prior=1.0, beta_prior=1.0)

        assert isinstance(result, GammaPoissonResult)
        expected_alpha = 1.0 + np.sum(data)
        expected_beta = 1.0 + len(data)
        assert result.alpha_post == pytest.approx(expected_alpha, rel=1e-10)
        assert result.beta_post == pytest.approx(expected_beta, rel=1e-10)
        assert result.credible_interval[0] < result.credible_interval[1]
        assert result.credible_interval[0] > 0.0

    def test_empty_data(self):
        """Empty data → posterior equals prior."""
        data = np.array([], dtype=np.float64)
        result = gamma_poisson(data, alpha_prior=2.0, beta_prior=3.0)

        assert result.alpha_post == pytest.approx(2.0, rel=1e-10)
        assert result.beta_post == pytest.approx(3.0, rel=1e-10)

    def test_credible_interval_matches_scipy(self):
        data = np.array([1.0, 2.0, 3.0])
        result = gamma_poisson(data, alpha_prior=1.0, beta_prior=1.0)

        alpha = 0.025
        expected_low = stats.gamma.ppf(alpha, a=result.alpha_post, scale=1.0 / result.beta_post)
        expected_high = stats.gamma.ppf(
            1 - alpha, a=result.alpha_post, scale=1.0 / result.beta_post
        )

        assert result.credible_interval[0] == pytest.approx(expected_low, rel=1e-10)
        assert result.credible_interval[1] == pytest.approx(expected_high, rel=1e-10)

    def test_large_counts(self):
        data = np.array([100.0, 200.0, 300.0])
        result = gamma_poisson(data, alpha_prior=1.0, beta_prior=0.1)

        assert result.alpha_post == pytest.approx(601.0, rel=1e-10)
        assert result.beta_post == pytest.approx(3.1, rel=1e-10)
        assert result.credible_interval[0] < result.credible_interval[1]


class TestDirichletMultinomial:
    """Tests for dirichlet_multinomial conjugate update."""

    def test_basic_update_two_categories(self):
        counts = np.array([10, 20], dtype=np.int64)
        alpha_prior = np.array([1.0, 1.0], dtype=np.float64)
        result = dirichlet_multinomial(counts, alpha_prior)

        assert isinstance(result, DirichletMultinomialResult)
        expected_alpha = alpha_prior + counts.astype(np.float64)
        np.testing.assert_array_almost_equal(result.alpha_post, expected_alpha)
        assert len(result.credible_intervals) == 2
        for low, high in result.credible_intervals:
            assert 0.0 <= low < high <= 1.0

    def test_basic_update_three_categories(self):
        counts = np.array([5, 15, 30], dtype=np.int64)
        alpha_prior = np.array([2.0, 2.0, 2.0], dtype=np.float64)
        result = dirichlet_multinomial(counts, alpha_prior)

        expected_alpha = alpha_prior + counts.astype(np.float64)
        np.testing.assert_array_almost_equal(result.alpha_post, expected_alpha)
        assert len(result.credible_intervals) == 3
        for low, high in result.credible_intervals:
            assert 0.0 <= low < high <= 1.0

    def test_credible_intervals_match_beta_marginals(self):
        counts = np.array([10, 20, 30], dtype=np.int64)
        alpha_prior = np.array([1.0, 1.0, 1.0], dtype=np.float64)
        result = dirichlet_multinomial(counts, alpha_prior)

        alpha_post = alpha_prior + counts.astype(np.float64)
        total_alpha = float(np.sum(alpha_post))
        alpha_level = 0.025

        for i, a in enumerate(alpha_post):
            a_float = float(a)
            expected_low = stats.beta.ppf(alpha_level, a_float, total_alpha - a_float)
            expected_high = stats.beta.ppf(1 - alpha_level, a_float, total_alpha - a_float)
            low, high = result.credible_intervals[i]
            assert low == pytest.approx(expected_low, rel=1e-10)
            assert high == pytest.approx(expected_high, rel=1e-10)

    def test_zero_counts(self):
        """Some categories with zero observations."""
        counts = np.array([0, 50, 0], dtype=np.int64)
        alpha_prior = np.array([1.0, 1.0, 1.0], dtype=np.float64)
        result = dirichlet_multinomial(counts, alpha_prior)

        expected_alpha = np.array([1.0, 51.0, 1.0], dtype=np.float64)
        np.testing.assert_array_almost_equal(result.alpha_post, expected_alpha)
        assert len(result.credible_intervals) == 3

    def test_five_categories(self):
        counts = np.array([1, 2, 3, 4, 5], dtype=np.int64)
        alpha_prior = np.array([0.5, 0.5, 0.5, 0.5, 0.5], dtype=np.float64)
        result = dirichlet_multinomial(counts, alpha_prior)

        assert len(result.credible_intervals) == 5
        for low, high in result.credible_intervals:
            assert 0.0 <= low < high <= 1.0


class TestInvalidInputs:
    """Tests for invalid / edge-case inputs."""

    def test_normal_negative_sigma(self):
        data = np.array([1.0, 2.0, 3.0])
        # Module does not validate; negative sigma squares to positive, so no error
        result = normal_normal(data, mu_prior=0.0, tau_prior=1.0, sigma_known=-1.0)
        assert result.tau_post > 0.0

    def test_normal_zero_sigma(self):
        data = np.array([1.0, 2.0, 3.0])
        with pytest.raises((ValueError, ZeroDivisionError, FloatingPointError)):
            normal_normal(data, mu_prior=0.0, tau_prior=1.0, sigma_known=0.0)

    def test_beta_binomial_negative_successes(self):
        # Module does not validate inputs; negative successes just shift alpha_post
        result = beta_binomial(successes=-1, trials=10, alpha_prior=1.0, beta_prior=1.0)
        assert result.alpha_post == pytest.approx(0.0, abs=1e-10)

    def test_beta_binomial_successes_greater_than_trials(self):
        # Module does not validate; succeeds > trials is accepted
        result = beta_binomial(successes=11, trials=10, alpha_prior=1.0, beta_prior=1.0)
        assert result.alpha_post == pytest.approx(12.0, rel=1e-10)

    def test_beta_binomial_negative_trials(self):
        # Module does not validate; negative trials reduce beta_post
        result = beta_binomial(successes=0, trials=-5, alpha_prior=1.0, beta_prior=1.0)
        assert result.beta_post == pytest.approx(-4.0, rel=1e-10)

    def test_gamma_poisson_negative_prior(self):
        # Module does not validate; negative alpha_prior is accepted
        result = gamma_poisson(np.array([1.0, 2.0, 3.0]), alpha_prior=-1.0, beta_prior=1.0)
        assert result.alpha_post == pytest.approx(5.0, rel=1e-10)

    def test_gamma_poisson_zero_beta(self):
        # Module does not validate; zero beta is accepted
        result = gamma_poisson(np.array([1.0, 2.0, 3.0]), alpha_prior=1.0, beta_prior=0.0)
        assert result.beta_post == pytest.approx(3.0, rel=1e-10)
        # scipy handles scale=inf gracefully; just verify CI is valid
        assert result.credible_interval[0] < result.credible_interval[1]

    def test_dirichlet_mismatched_shapes(self):
        counts = np.array([10, 20, 30], dtype=np.int64)
        alpha_prior = np.array([1.0, 1.0], dtype=np.float64)
        with pytest.raises((ValueError, IndexError)):
            dirichlet_multinomial(counts, alpha_prior)

    def test_dirichlet_negative_counts(self):
        # Module does not validate; negative counts reduce alpha_post
        counts = np.array([-1, 5], dtype=np.int64)
        alpha_prior = np.array([1.0, 1.0], dtype=np.float64)
        result = dirichlet_multinomial(counts, alpha_prior)
        assert result.alpha_post[0] == pytest.approx(0.0, abs=1e-10)

    def test_dirichlet_negative_alpha_prior(self):
        # Module does not validate; negative alpha_prior is accepted
        counts = np.array([5, 5], dtype=np.int64)
        alpha_prior = np.array([-1.0, 1.0], dtype=np.float64)
        result = dirichlet_multinomial(counts, alpha_prior)
        assert result.alpha_post[0] == pytest.approx(4.0, rel=1e-10)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
