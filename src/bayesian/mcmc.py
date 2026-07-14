"""MCMC samplers for C4REQBER Bayesian Engine.

Implements Metropolis-Hastings, Gibbs sampling, and a simplified NUTS-like
Hamiltonian Monte Carlo with parallel chain support.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class MCMCResult:
    """Result container for MCMC sampling."""

    samples: NDArray[np.float64]
    accept_rate: float
    n_chains: int
    n_samples: int


def metropolis_hastings(
    log_target: Callable[[NDArray[np.float64]], float],
    x0: NDArray[np.float64],
    n_samples: int,
    proposal_cov: NDArray[np.float64] | None = None,
    n_chains: int = 1,
    seed: int | None = None,
) -> MCMCResult:
    """Metropolis-Hastings sampler with Gaussian random walk proposal.

    Args:
        log_target: Log of the unnormalized target density.
        x0: Initial state vector (shape (d,)).
        n_samples: Number of samples per chain.
        proposal_cov: Proposal covariance matrix (default identity scaled by 0.1).
        n_chains: Number of parallel chains.
        seed: Random seed.

    Returns:
        MCMCResult with stacked samples (shape (n_chains, n_samples, d)).
    """
    rng = np.random.default_rng(seed)
    d = x0.shape[0]
    if proposal_cov is None:
        proposal_cov = np.eye(d) * 0.1

    samples = np.zeros((n_chains, n_samples, d), dtype=np.float64)
    accepts = 0

    for c in range(n_chains):
        x = x0.copy() if c == 0 else rng.normal(loc=x0, scale=1.0)
        log_px = log_target(x)
        samples[c, 0] = x

        for i in range(1, n_samples):
            x_prop = rng.multivariate_normal(x, proposal_cov)
            log_p_prop = log_target(x_prop)
            log_alpha = log_p_prop - log_px

            if np.log(rng.random()) < log_alpha:
                x = x_prop
                log_px = log_p_prop
                accepts += 1

            samples[c, i] = x

    total_iters = n_chains * (n_samples - 1)
    accept_rate = accepts / total_iters if total_iters > 0 else 0.0
    return MCMCResult(
        samples=samples,
        accept_rate=accept_rate,
        n_chains=n_chains,
        n_samples=n_samples,
    )


def gibbs_sampling(
    conditional_samplers: list[Callable[[NDArray[np.float64]], float]],
    x0: NDArray[np.float64],
    n_samples: int,
    n_chains: int = 1,
    seed: int | None = None,
) -> MCMCResult:
    """Gibbs sampler using provided conditional distribution samplers.

    Args:
        conditional_samplers: List of functions, each takes the full state and
            returns a new sample for one coordinate.
        x0: Initial state vector (shape (d,)).
        n_samples: Number of samples per chain.
        n_chains: Number of parallel chains.
        seed: Random seed.

    Returns:
        MCMCResult with stacked samples.
    """
    rng = np.random.default_rng(seed)
    d = x0.shape[0]
    assert len(conditional_samplers) == d

    samples = np.zeros((n_chains, n_samples, d), dtype=np.float64)

    for c in range(n_chains):
        x = x0.copy() if c == 0 else rng.normal(loc=x0, scale=1.0)
        samples[c, 0] = x

        for i in range(1, n_samples):
            for j, sampler in enumerate(conditional_samplers):
                x[j] = sampler(x)
            samples[c, i] = x.copy()

    return MCMCResult(
        samples=samples,
        accept_rate=1.0,
        n_chains=n_chains,
        n_samples=n_samples,
    )


def _leapfrog(
    x: NDArray[np.float64],
    p: NDArray[np.float64],
    grad_log_target: Callable[[NDArray[np.float64]], NDArray[np.float64]],
    step_size: float,
    n_steps: int,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Leapfrog integrator for Hamiltonian dynamics.

    Args:
        x: Position vector.
        p: Momentum vector.
        grad_log_target: Gradient of log target density.
        step_size: Integration step size.
        n_steps: Number of leapfrog steps.

    Returns:
        (x_new, p_new) after integration.
    """
    x = x.copy()
    p = p.copy()
    p += 0.5 * step_size * grad_log_target(x)

    for _ in range(n_steps - 1):
        x += step_size * p
        p += step_size * grad_log_target(x)

    x += step_size * p
    p += 0.5 * step_size * grad_log_target(x)
    return x, -p


def hmc(
    log_target: Callable[[NDArray[np.float64]], float],
    grad_log_target: Callable[[NDArray[np.float64]], NDArray[np.float64]],
    x0: NDArray[np.float64],
    n_samples: int,
    step_size: float = 0.01,
    n_leapfrog: int = 10,
    n_chains: int = 1,
    seed: int | None = None,
) -> MCMCResult:
    """Hamiltonian Monte Carlo sampler with fixed trajectory length.

    Args:
        log_target: Log of the unnormalized target density.
        grad_log_target: Gradient of log target density.
        x0: Initial state vector.
        n_samples: Number of samples per chain.
        step_size: Leapfrog step size.
        n_leapfrog: Number of leapfrog steps per proposal.
        n_chains: Number of parallel chains.
        seed: Random seed.

    Returns:
        MCMCResult with stacked samples.
    """
    rng = np.random.default_rng(seed)
    d = x0.shape[0]
    samples = np.zeros((n_chains, n_samples, d), dtype=np.float64)
    accepts = 0

    for c in range(n_chains):
        x = x0.copy() if c == 0 else rng.normal(loc=x0, scale=1.0)
        log_px = log_target(x)
        samples[c, 0] = x

        for i in range(1, n_samples):
            p = rng.standard_normal(d)
            current_h = log_px - 0.5 * np.dot(p, p)

            x_prop, p_prop = _leapfrog(x, p, grad_log_target, step_size, n_leapfrog)  # type: ignore[arg-type]
            log_p_prop = log_target(x_prop)
            proposed_h = log_p_prop - 0.5 * np.dot(p_prop, p_prop)

            log_alpha = proposed_h - current_h
            if np.log(rng.random()) < log_alpha:
                x = x_prop
                log_px = log_p_prop
                accepts += 1

            samples[c, i] = x

    total_iters = n_chains * (n_samples - 1)
    accept_rate = accepts / total_iters if total_iters > 0 else 0.0
    return MCMCResult(
        samples=samples,
        accept_rate=accept_rate,
        n_chains=n_chains,
        n_samples=n_samples,
    )


def nuts(
    log_target: Callable[[NDArray[np.float64]], float],
    grad_log_target: Callable[[NDArray[np.float64]], NDArray[np.float64]],
    x0: NDArray[np.float64],
    n_samples: int,
    step_size: float = 0.01,
    max_depth: int = 5,
    n_chains: int = 1,
    seed: int | None = None,
) -> MCMCResult:
    """Simplified No-U-Turn Sampler (NUTS) with fixed max tree depth.

    Args:
        log_target: Log of the unnormalized target density.
        grad_log_target: Gradient of log target density.
        x0: Initial state vector.
        n_samples: Number of samples per chain.
        step_size: Leapfrog step size.
        max_depth: Maximum binary tree depth for trajectory.
        n_chains: Number of parallel chains.
        seed: Random seed.

    Returns:
        MCMCResult with stacked samples.
    """
    rng = np.random.default_rng(seed)
    d = x0.shape[0]
    samples = np.zeros((n_chains, n_samples, d), dtype=np.float64)
    accepts = 0

    def _build_tree(
        x: NDArray[np.float64],
        p: NDArray[np.float64],
        u: float,
        v: int,
        j: int,
        step: float,
        x0_inner: NDArray[np.float64],
        p0_inner: NDArray[np.float64],
    ) -> tuple[
        NDArray[np.float64],
        NDArray[np.float64],
        NDArray[np.float64],
        NDArray[np.float64],
        NDArray[np.float64],
        int,
        bool,
    ]:
        if j == 0:
            x_new, p_new = _leapfrog(x, p, grad_log_target, step, 1)
            log_p_new = log_target(x_new)
            h_new = log_p_new - 0.5 * np.dot(p_new, p_new)
            n_valid = int(u < np.exp(min(h_new, 700.0)))
            valid = u < np.exp(min(h_new + 1000.0, 700.0))
            return x_new, p_new, x_new, p_new, x_new, n_valid, valid

        x_minus, p_minus, x_plus, p_plus, x_prop, n_prop, valid = _build_tree(
            x, p, u, v, j - 1, step, x0_inner, p0_inner
        )
        if not valid:
            return x_minus, p_minus, x_plus, p_plus, x_prop, n_prop, False

        if v == -1:
            x_minus, p_minus, _, _, x_prop2, n_prop2, valid2 = _build_tree(
                x_minus, p_minus, u, v, j - 1, step, x0_inner, p0_inner
            )
        else:
            _, _, x_plus, p_plus, x_prop2, n_prop2, valid2 = _build_tree(
                x_plus, p_plus, u, v, j - 1, step, x0_inner, p0_inner
            )

        if not valid2:
            return x_minus, p_minus, x_plus, p_plus, x_prop, n_prop, False

        if rng.random() < n_prop2 / max(n_prop + n_prop2, 1):
            x_prop = x_prop2

        valid = (
            np.dot(x_plus - x_minus, p_minus) >= 0
            and np.dot(x_plus - x_minus, p_plus) >= 0
        )
        return x_minus, p_minus, x_plus, p_plus, x_prop, n_prop + n_prop2, valid

    for c in range(n_chains):
        x = x0.copy() if c == 0 else rng.normal(loc=x0, scale=1.0)
        log_px = log_target(x)
        samples[c, 0] = x

        for i in range(1, n_samples):
            p0 = rng.standard_normal(d)
            u = rng.random() * np.exp(log_px - 0.5 * np.dot(p0, p0))
            x_minus, x_plus = x.copy(), x.copy()  # type: ignore[attr-defined]
            p_minus, p_plus = p0.copy(), p0.copy()  # type: ignore[attr-defined]
            j = 0
            x_prop = x.copy()
            n_total = 1
            valid = True

            while j < max_depth and valid:
                v = 1 if rng.random() < 0.5 else -1
                if v == -1:
                    x_minus, p_minus, _, _, x_prop2, n_prop, valid = _build_tree(
                        x_minus, p_minus, u, v, j, step_size, x, p0  # type: ignore[arg-type]
                    )
                else:
                    _, _, x_plus, p_plus, x_prop2, n_prop, valid = _build_tree(
                        x_plus, p_plus, u, v, j, step_size, x, p0  # type: ignore[arg-type]
                    )

                if valid:
                    if rng.random() < min(1.0, n_prop / max(n_total, 1)):
                        x_prop = x_prop2
                    n_total += n_prop

                j += 1

            log_p_prop = log_target(x_prop)
            if not np.isnan(log_p_prop) and not np.isinf(log_p_prop):
                x = x_prop
                log_px = log_p_prop
                accepts += 1

            samples[c, i] = x

    total_iters = n_chains * (n_samples - 1)
    accept_rate = accepts / total_iters if total_iters > 0 else 0.0
    return MCMCResult(
        samples=samples,
        accept_rate=accept_rate,
        n_chains=n_chains,
        n_samples=n_samples,
    )


def effective_sample_size(samples: NDArray[np.float64]) -> float:
    """Estimate effective sample size using autocorrelation.

    Args:
        samples: 1-D array of samples from a single chain.

    Returns:
        Effective sample size.
    """
    n = len(samples)
    if n < 2:
        return float(n)

    mean = np.mean(samples)
    var = np.var(samples, ddof=1)
    if var == 0:
        return float(n)

    max_lag = min(n // 3, 100)
    acf = np.zeros(max_lag, dtype=np.float64)
    for lag in range(1, max_lag + 1):
        acf[lag - 1] = np.mean((samples[:-lag] - mean) * (samples[lag:] - mean)) / var

    # Geyer's initial positive sequence
    gamma = np.zeros(max_lag, dtype=np.float64)
    for lag in range(max_lag):
        idx1 = 2 * lag
        idx2 = 2 * lag + 1
        if idx1 < len(acf):
            gamma[lag] = acf[idx1] + (acf[idx2] if idx2 < len(acf) else 0.0)
        else:
            break

    t_cut = max_lag - 1
    for t in range(1, max_lag):
        if gamma[t] < 0 or gamma[t] > gamma[t - 1]:
            t_cut = max(t - 1, 0)
            break

    ess = n / (1.0 + 2.0 * np.sum(gamma[: t_cut + 1]))
    return float(max(ess, 1.0))


def gelman_rubin(chains: NDArray[np.float64]) -> float:
    """Gelman-Rubin R-hat diagnostic for convergence.

    Args:
        chains: Array of shape (n_chains, n_samples).

    Returns:
        R-hat statistic (values near 1.0 indicate convergence).
    """
    m, n = chains.shape
    if m < 2:
        return np.nan

    chain_means = np.mean(chains, axis=1)
    chain_vars = np.var(chains, axis=1, ddof=1)
    np.mean(chain_means)

    b = n * np.var(chain_means, ddof=1)
    w = np.mean(chain_vars)
    var_est = (n - 1) / n * w + b / n

    if w == 0:
        return np.nan

    r_hat = np.sqrt(var_est / w)
    return float(r_hat)
