"""Tests for src/bayesian/mcmc.py."""

from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

from src.bayesian.mcmc import (
    MCMCResult,
    effective_sample_size,
    gelman_rubin,
    gibbs_sampling,
    hmc,
    metropolis_hastings,
    nuts,
)


class TestMetropolisHastings:
    """Tests for Metropolis-Hastings sampler."""

    def test_basic_sampling(self):
        def log_target(x: np.ndarray) -> float:
            return float(-0.5 * np.sum(x**2))

        result = metropolis_hastings(
            log_target=log_target,
            x0=np.array([0.0]),
            n_samples=1000,
            proposal_cov=np.array([[0.5]]),
            seed=42,
        )
        assert isinstance(result, MCMCResult)
        assert result.samples.shape == (1, 1000, 1)
        assert 0.0 < result.accept_rate < 1.0

    def test_mean_close_to_target(self):
        def log_target(x: np.ndarray) -> float:
            return float(-0.5 * np.sum((x - 2.0) ** 2))

        result = metropolis_hastings(
            log_target=log_target,
            x0=np.array([2.0]),
            n_samples=5000,
            proposal_cov=np.array([[0.5]]),
            seed=42,
        )
        samples = result.samples[0, 1000:].flatten()
        assert np.mean(samples) == pytest.approx(2.0, abs=0.3)

    def test_std_close_to_target(self):
        def log_target(x: np.ndarray) -> float:
            return float(-0.5 * np.sum(x**2))

        result = metropolis_hastings(
            log_target=log_target,
            x0=np.array([0.0]),
            n_samples=5000,
            proposal_cov=np.array([[0.5]]),
            seed=42,
        )
        samples = result.samples[0, 1000:].flatten()
        assert np.std(samples) == pytest.approx(1.0, abs=0.3)

    def test_multivariate(self):
        def log_target(x: np.ndarray) -> float:
            return float(-0.5 * np.sum(x**2))

        result = metropolis_hastings(
            log_target=log_target,
            x0=np.array([0.0, 0.0]),
            n_samples=2000,
            proposal_cov=np.eye(2) * 0.5,
            seed=42,
        )
        assert result.samples.shape == (1, 2000, 2)

    def test_parallel_chains(self):
        def log_target(x: np.ndarray) -> float:
            return float(-0.5 * np.sum(x**2))

        result = metropolis_hastings(
            log_target=log_target,
            x0=np.array([0.0]),
            n_samples=1000,
            n_chains=4,
            seed=42,
        )
        assert result.n_chains == 4
        assert result.samples.shape == (4, 1000, 1)

    def test_small_proposal_std_high_acceptance(self):
        def log_target(x: np.ndarray) -> float:
            return float(-0.5 * np.sum(x**2))

        result = metropolis_hastings(
            log_target=log_target,
            x0=np.array([0.0]),
            n_samples=2000,
            proposal_cov=np.array([[0.01]]),
            seed=42,
        )
        assert result.accept_rate > 0.7

    def test_large_proposal_std_low_acceptance(self):
        def log_target(x: np.ndarray) -> float:
            return float(-0.5 * np.sum(x**2))

        result = metropolis_hastings(
            log_target=log_target,
            x0=np.array([0.0]),
            n_samples=2000,
            proposal_cov=np.array([[10.0]]),
            seed=42,
        )
        assert result.accept_rate < 0.5

    def test_samples_are_diverse(self):
        def log_target(x: np.ndarray) -> float:
            return float(-0.5 * np.sum(x**2))

        result = metropolis_hastings(
            log_target=log_target,
            x0=np.array([0.0]),
            n_samples=1000,
            seed=42,
        )
        samples = result.samples[0, 100:].flatten()
        unique = len(set(np.round(samples, 6)))
        assert unique > 50

    def test_single_sample(self):
        def log_target(x: np.ndarray) -> float:
            return float(-0.5 * np.sum(x**2))

        result = metropolis_hastings(
            log_target=log_target,
            x0=np.array([0.0]),
            n_samples=1,
            seed=42,
        )
        assert result.samples.shape == (1, 1, 1)
        assert result.accept_rate == 0.0

    def test_shifted_target(self):
        def log_target(x: np.ndarray) -> float:
            mu = np.array([5.0, -3.0])
            return float(-0.5 * np.sum((x - mu) ** 2))

        result = metropolis_hastings(
            log_target=log_target,
            x0=np.array([5.0, -3.0]),
            n_samples=5000,
            proposal_cov=np.eye(2) * 0.3,
            seed=42,
        )
        samples = result.samples[0, 1000:]
        assert np.mean(samples[:, 0]) == pytest.approx(5.0, abs=0.3)
        assert np.mean(samples[:, 1]) == pytest.approx(-3.0, abs=0.3)


class TestGibbsSampling:
    """Tests for Gibbs sampler."""

    def test_basic_gibbs(self):
        def cond_0(x: np.ndarray) -> float:
            return float(np.random.normal(loc=x[1] * 0.5, scale=1.0))

        def cond_1(x: np.ndarray) -> float:
            return float(np.random.normal(loc=x[0] * 0.5, scale=1.0))

        result = gibbs_sampling(
            conditional_samplers=[cond_0, cond_1],
            x0=np.array([0.0, 0.0]),
            n_samples=1000,
            seed=42,
        )
        assert isinstance(result, MCMCResult)
        assert result.samples.shape == (1, 1000, 2)
        assert result.accept_rate == 1.0

    def test_parallel_chains_gibbs(self):
        def cond_0(x: np.ndarray) -> float:
            return float(np.random.normal(loc=0.0, scale=1.0))

        def cond_1(x: np.ndarray) -> float:
            return float(np.random.normal(loc=0.0, scale=1.0))

        result = gibbs_sampling(
            conditional_samplers=[cond_0, cond_1],
            x0=np.array([0.0, 0.0]),
            n_samples=500,
            n_chains=3,
            seed=42,
        )
        assert result.n_chains == 3
        assert result.samples.shape == (3, 500, 2)

    def test_gibbs_convergence(self):
        np.random.seed(42)

        def cond_0(x: np.ndarray) -> float:
            return float(np.random.normal(loc=x[1] * 0.5, scale=1.0))

        def cond_1(x: np.ndarray) -> float:
            return float(np.random.normal(loc=x[0] * 0.5, scale=1.0))

        result = gibbs_sampling(
            conditional_samplers=[cond_0, cond_1],
            x0=np.array([0.0, 0.0]),
            n_samples=3000,
            seed=42,
        )
        samples = result.samples[0, 500:]
        assert np.abs(np.mean(samples[:, 0])) < 1.0
        assert np.abs(np.mean(samples[:, 1])) < 1.0


class TestHMC:
    """Tests for Hamiltonian Monte Carlo."""

    def test_basic_hmc(self):
        def log_target(x: np.ndarray) -> float:
            return float(-0.5 * np.sum(x**2))

        def grad_log_target(x: np.ndarray) -> np.ndarray:
            return -x

        result = hmc(
            log_target=log_target,
            grad_log_target=grad_log_target,
            x0=np.array([0.0]),
            n_samples=500,
            step_size=0.1,
            n_leapfrog=10,
            seed=42,
        )
        assert isinstance(result, MCMCResult)
        assert result.samples.shape == (1, 500, 1)
        assert 0.0 < result.accept_rate <= 1.0

    def test_hmc_mean(self):
        def log_target(x: np.ndarray) -> float:
            return float(-0.5 * np.sum((x - 3.0) ** 2))

        def grad_log_target(x: np.ndarray) -> np.ndarray:
            return -(x - 3.0)

        result = hmc(
            log_target=log_target,
            grad_log_target=grad_log_target,
            x0=np.array([3.0]),
            n_samples=2000,
            step_size=0.1,
            n_leapfrog=10,
            seed=42,
        )
        samples = result.samples[0, 500:].flatten()
        assert np.mean(samples) == pytest.approx(3.0, abs=0.3)

    def test_hmc_parallel_chains(self):
        def log_target(x: np.ndarray) -> float:
            return float(-0.5 * np.sum(x**2))

        def grad_log_target(x: np.ndarray) -> np.ndarray:
            return -x

        result = hmc(
            log_target=log_target,
            grad_log_target=grad_log_target,
            x0=np.array([0.0]),
            n_samples=500,
            n_chains=2,
            seed=42,
        )
        assert result.n_chains == 2
        assert result.samples.shape == (2, 500, 1)

    def test_hmc_multivariate(self):
        def log_target(x: np.ndarray) -> float:
            return float(-0.5 * np.sum(x**2))

        def grad_log_target(x: np.ndarray) -> np.ndarray:
            return -x

        result = hmc(
            log_target=log_target,
            grad_log_target=grad_log_target,
            x0=np.array([0.0, 0.0]),
            n_samples=500,
            step_size=0.1,
            n_leapfrog=10,
            seed=42,
        )
        assert result.samples.shape == (1, 500, 2)


class TestNUTS:
    """Tests for No-U-Turn Sampler."""

    def test_basic_nuts(self):
        def log_target(x: np.ndarray) -> float:
            return float(-0.5 * np.sum(x**2))

        def grad_log_target(x: np.ndarray) -> np.ndarray:
            return -x

        result = nuts(
            log_target=log_target,
            grad_log_target=grad_log_target,
            x0=np.array([0.0]),
            n_samples=200,
            step_size=0.1,
            max_depth=3,
            seed=42,
        )
        assert isinstance(result, MCMCResult)
        assert result.samples.shape == (1, 200, 1)
        assert result.accept_rate > 0.0

    def test_nuts_mean(self):
        def log_target(x: np.ndarray) -> float:
            return float(-0.5 * np.sum((x - 2.0) ** 2))

        def grad_log_target(x: np.ndarray) -> np.ndarray:
            return -(x - 2.0)

        result = nuts(
            log_target=log_target,
            grad_log_target=grad_log_target,
            x0=np.array([2.0]),
            n_samples=500,
            step_size=0.1,
            max_depth=4,
            seed=42,
        )
        samples = result.samples[0, 100:].flatten()
        assert np.mean(samples) == pytest.approx(2.0, abs=0.5)

    def test_nuts_parallel_chains(self):
        def log_target(x: np.ndarray) -> float:
            return float(-0.5 * np.sum(x**2))

        def grad_log_target(x: np.ndarray) -> np.ndarray:
            return -x

        result = nuts(
            log_target=log_target,
            grad_log_target=grad_log_target,
            x0=np.array([0.0]),
            n_samples=200,
            n_chains=2,
            seed=42,
        )
        assert result.n_chains == 2
        assert result.samples.shape == (2, 200, 1)

    def test_nuts_multivariate(self):
        def log_target(x: np.ndarray) -> float:
            return float(-0.5 * np.sum(x**2))

        def grad_log_target(x: np.ndarray) -> np.ndarray:
            return -x

        result = nuts(
            log_target=log_target,
            grad_log_target=grad_log_target,
            x0=np.array([0.0, 0.0]),
            n_samples=200,
            step_size=0.1,
            max_depth=3,
            seed=42,
        )
        assert result.samples.shape == (1, 200, 2)


class TestEffectiveSampleSize:
    """Tests for ESS computation."""

    def test_ess_independent_samples(self):
        samples = np.random.randn(1000)
        ess = effective_sample_size(samples)
        assert ess > 500

    def test_ess_correlated_samples(self):
        ar = np.zeros(1000)
        ar[0] = np.random.randn()
        for i in range(1, 1000):
            ar[i] = 0.95 * ar[i - 1] + np.random.randn() * 0.3
        ess = effective_sample_size(ar)
        assert ess < 500

    def test_ess_single_sample(self):
        ess = effective_sample_size(np.array([1.0]))
        assert ess == 1.0

    def test_ess_constant(self):
        ess = effective_sample_size(np.full(100, 5.0))
        assert ess == 100.0

    def test_ess_two_samples(self):
        ess = effective_sample_size(np.array([1.0, 2.0]))
        assert ess >= 1.0


class TestGelmanRubin:
    """Tests for Gelman-Rubin diagnostic."""

    def test_converged_chains(self):
        chains = np.array([
            np.random.normal(0, 1, 1000),
            np.random.normal(0, 1, 1000),
            np.random.normal(0, 1, 1000),
        ])
        r_hat = gelman_rubin(chains)
        assert r_hat == pytest.approx(1.0, abs=0.1)

    def test_unconverged_chains(self):
        chains = np.array([
            np.random.normal(0, 1, 500),
            np.random.normal(5, 1, 500),
        ])
        r_hat = gelman_rubin(chains)
        assert r_hat > 1.1

    def test_single_chain_returns_nan(self):
        chains = np.random.normal(0, 1, 100).reshape(1, -1)
        r_hat = gelman_rubin(chains)
        assert np.isnan(r_hat)

    def test_identical_chains(self):
        identical = np.full((3, 100), 5.0)
        r_hat = gelman_rubin(identical)
        assert np.isnan(r_hat)


class TestMCMCConvergence:
    """Integration tests verifying convergence on known distributions."""

    def test_mh_on_standard_normal(self):
        def log_target(x: np.ndarray) -> float:
            return float(stats.norm.logpdf(x[0], loc=0.0, scale=1.0))

        result = metropolis_hastings(
            log_target=log_target,
            x0=np.array([0.0]),
            n_samples=8000,
            n_chains=4,
            seed=42,
        )
        all_samples = result.samples[:, 2000:].flatten()
        assert np.mean(all_samples) == pytest.approx(0.0, abs=0.2)
        assert np.std(all_samples) == pytest.approx(1.0, abs=0.2)

        r_hat = gelman_rubin(result.samples[:, 2000:, 0])
        assert r_hat == pytest.approx(1.0, abs=0.1)

    def test_hmc_on_standard_normal(self):
        def log_target(x: np.ndarray) -> float:
            return float(-0.5 * np.sum(x**2))

        def grad_log_target(x: np.ndarray) -> np.ndarray:
            return -x

        result = hmc(
            log_target=log_target,
            grad_log_target=grad_log_target,
            x0=np.array([0.0]),
            n_samples=3000,
            step_size=0.15,
            n_leapfrog=15,
            n_chains=2,
            seed=42,
        )
        all_samples = result.samples[:, 500:].flatten()
        assert np.mean(all_samples) == pytest.approx(0.0, abs=0.2)
        assert np.std(all_samples) == pytest.approx(1.0, abs=0.2)

    def test_nuts_on_standard_normal(self):
        def log_target(x: np.ndarray) -> float:
            return float(-0.5 * np.sum(x**2))

        def grad_log_target(x: np.ndarray) -> np.ndarray:
            return -x

        result = nuts(
            log_target=log_target,
            grad_log_target=grad_log_target,
            x0=np.array([0.0]),
            n_samples=1000,
            step_size=0.15,
            max_depth=5,
            n_chains=2,
            seed=42,
        )
        all_samples = result.samples[:, 200:].flatten()
        assert np.mean(all_samples) == pytest.approx(0.0, abs=0.3)

    def test_gibbs_on_bivariate_normal(self):
        rho = 0.8
        sigma = 1.0

        def cond_0(x: np.ndarray) -> float:
            return float(np.random.normal(loc=rho * x[1], scale=sigma * np.sqrt(1 - rho**2)))

        def cond_1(x: np.ndarray) -> float:
            return float(np.random.normal(loc=rho * x[0], scale=sigma * np.sqrt(1 - rho**2)))

        result = gibbs_sampling(
            conditional_samplers=[cond_0, cond_1],
            x0=np.array([0.0, 0.0]),
            n_samples=5000,
            n_chains=2,
            seed=42,
        )
        all_samples = result.samples[:, 1000:].reshape(-1, 2)
        assert np.mean(all_samples[:, 0]) == pytest.approx(0.0, abs=0.3)
        assert np.mean(all_samples[:, 1]) == pytest.approx(0.0, abs=0.3)
        assert np.corrcoef(all_samples[:, 0], all_samples[:, 1])[0, 1] == pytest.approx(rho, abs=0.1)

    def test_ess_increases_with_more_samples(self):
        def log_target(x: np.ndarray) -> float:
            return float(-0.5 * np.sum(x**2))

        result1 = metropolis_hastings(
            log_target=log_target,
            x0=np.array([0.0]),
            n_samples=1000,
            seed=42,
        )
        result2 = metropolis_hastings(
            log_target=log_target,
            x0=np.array([0.0]),
            n_samples=5000,
            seed=42,
        )
        ess1 = effective_sample_size(result1.samples[0, 100:].flatten())
        ess2 = effective_sample_size(result2.samples[0, 100:].flatten())
        assert ess2 > ess1
