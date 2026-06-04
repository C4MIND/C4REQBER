"""Bayesian Engine core for C4REQBER.

Provides conjugate prior updating, posterior computation, and credible intervals
for Normal-Normal, Beta-Binomial, Gamma-Poisson, and Dirichlet-Multinomial models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import NDArray
from scipy import stats


@dataclass(frozen=True)
class NormalNormalResult:
    """Posterior result for Normal-Normal conjugate model."""

    mu_post: float
    tau_post: float
    credible_interval: tuple[float, float]


@dataclass(frozen=True)
class BetaBinomialResult:
    """Posterior result for Beta-Binomial conjugate model."""

    alpha_post: float
    beta_post: float
    credible_interval: tuple[float, float]


@dataclass(frozen=True)
class GammaPoissonResult:
    """Posterior result for Gamma-Poisson conjugate model."""

    alpha_post: float
    beta_post: float
    credible_interval: tuple[float, float]


@dataclass(frozen=True)
class DirichletMultinomialResult:
    """Posterior result for Dirichlet-Multinomial conjugate model."""

    alpha_post: NDArray[np.float64]
    credible_intervals: list[tuple[float, float]]


def normal_normal(
    data: NDArray[np.float64],
    mu_prior: float,
    tau_prior: float,
    sigma_known: float,
    credible_level: float = 0.95,
) -> NormalNormalResult:
    """Normal-Normal conjugate update.

    Likelihood: x_i ~ N(mu, sigma_known^2)
    Prior:      mu ~ N(mu_prior, 1 / tau_prior)

    Args:
        data: Observed data vector.
        mu_prior: Prior mean for mu.
        tau_prior: Prior precision (1 / variance) for mu.
        sigma_known: Known standard deviation of the likelihood.
        credible_level: Credible interval coverage (default 0.95).

    Returns:
        NormalNormalResult with posterior mean, precision, and credible interval.
    """
    n = float(data.size)
    sample_mean = float(np.mean(data))
    sigma2 = sigma_known**2

    tau_post = tau_prior + n / sigma2
    mu_post = (tau_prior * mu_prior + n * sample_mean / sigma2) / tau_post
    std_post = np.sqrt(1.0 / tau_post)

    alpha = (1.0 - credible_level) / 2.0
    ci = (
        float(stats.norm.ppf(alpha, loc=mu_post, scale=std_post)),
        float(stats.norm.ppf(1.0 - alpha, loc=mu_post, scale=std_post)),
    )
    return NormalNormalResult(mu_post=mu_post, tau_post=tau_post, credible_interval=ci)


def beta_binomial(
    successes: int,
    trials: int,
    alpha_prior: float,
    beta_prior: float,
    credible_level: float = 0.95,
) -> BetaBinomialResult:
    """Beta-Binomial conjugate update.

    Likelihood: k ~ Binomial(n, theta)
    Prior:      theta ~ Beta(alpha_prior, beta_prior)

    Args:
        successes: Number of successes observed.
        trials: Total number of trials.
        alpha_prior: Prior alpha parameter.
        beta_prior: Prior beta parameter.
        credible_level: Credible interval coverage (default 0.95).

    Returns:
        BetaBinomialResult with posterior parameters and credible interval.
    """
    alpha_post = alpha_prior + successes
    beta_post = beta_prior + (trials - successes)

    alpha = (1.0 - credible_level) / 2.0
    ci = (
        float(stats.beta.ppf(alpha, alpha_post, beta_post)),
        float(stats.beta.ppf(1.0 - alpha, alpha_post, beta_post)),
    )
    return BetaBinomialResult(
        alpha_post=alpha_post,
        beta_post=beta_post,
        credible_interval=ci,
    )


def gamma_poisson(
    data: NDArray[np.float64],
    alpha_prior: float,
    beta_prior: float,
    credible_level: float = 0.95,
) -> GammaPoissonResult:
    """Gamma-Poisson conjugate update.

    Likelihood: x_i ~ Poisson(lambda)
    Prior:      lambda ~ Gamma(alpha_prior, rate=beta_prior)

    Args:
        data: Observed count data.
        alpha_prior: Prior shape parameter.
        beta_prior: Prior rate parameter.
        credible_level: Credible interval coverage (default 0.95).

    Returns:
        GammaPoissonResult with posterior shape, rate, and credible interval.
    """
    n = float(data.size)
    total = float(np.sum(data))

    alpha_post = alpha_prior + total
    beta_post = beta_prior + n

    alpha = (1.0 - credible_level) / 2.0
    ci = (
        float(stats.gamma.ppf(alpha, a=alpha_post, scale=1.0 / beta_post)),
        float(stats.gamma.ppf(1.0 - alpha, a=alpha_post, scale=1.0 / beta_post)),
    )
    return GammaPoissonResult(
        alpha_post=alpha_post,
        beta_post=beta_post,
        credible_interval=ci,
    )


def dirichlet_multinomial(
    counts: NDArray[np.int64],
    alpha_prior: NDArray[np.float64],
    credible_level: float = 0.95,
) -> DirichletMultinomialResult:
    """Dirichlet-Multinomial conjugate update.

    Likelihood: counts ~ Multinomial(N, p)
    Prior:      p ~ Dirichlet(alpha_prior)

    Args:
        counts: Observed category counts.
        alpha_prior: Prior concentration parameters (K-vector).
        credible_level: Credible interval coverage (default 0.95).

    Returns:
        DirichletMultinomialResult with posterior alphas and marginal credible intervals.
    """
    alpha_post = alpha_prior + counts.astype(np.float64)

    alpha = (1.0 - credible_level) / 2.0
    cis: list[tuple[float, float]] = []
    for a in alpha_post:
        a_float = float(a)
        total = float(np.sum(alpha_post))
        # Marginal is Beta(a, total - a)
        low = float(stats.beta.ppf(alpha, a_float, total - a_float))
        high = float(stats.beta.ppf(1.0 - alpha, a_float, total - a_float))
        cis.append((low, high))

    return DirichletMultinomialResult(
        alpha_post=alpha_post,
        credible_intervals=cis,
    )


def posterior_predictive_normal(
    x_new: float,
    mu_post: float,
    tau_post: float,
    sigma_known: float,
) -> float:
    """Posterior predictive density for a new observation under Normal-Normal.

    Args:
        x_new: New observation.
        mu_post: Posterior mean.
        tau_post: Posterior precision.
        sigma_known: Known likelihood std.

    Returns:
        Predictive density value.
    """
    var_post = 1.0 / tau_post
    var_pred = var_post + sigma_known**2
    return float(stats.norm.pdf(x_new, loc=mu_post, scale=np.sqrt(var_pred)))


def posterior_predictive_beta_binomial(
    k_new: int,
    n_new: int,
    alpha_post: float,
    beta_post: float,
) -> float:
    """Posterior predictive probability for new Binomial count under Beta prior.

    Args:
        k_new: Number of successes in new trials.
        n_new: Number of new trials.
        alpha_post: Posterior alpha.
        beta_post: Posterior beta.

    Returns:
        Predictive probability mass.
    """
    from scipy.special import beta as beta_func
    from scipy.special import comb

    return float(
        comb(n_new, k_new)
        * beta_func(k_new + alpha_post, n_new - k_new + beta_post)
        / beta_func(alpha_post, beta_post)
    )


def credible_interval_from_samples(
    samples: NDArray[np.float64],
    level: float = 0.95,
    method: Literal["hpd", "equal-tailed"] = "equal-tailed",
) -> tuple[float, float]:
    """Compute credible interval from MCMC or other samples.

    Args:
        samples: 1-D array of posterior samples.
        level: Credible interval coverage.
        method: 'hpd' for highest posterior density or 'equal-tailed'.

    Returns:
        (lower, upper) credible interval bounds.
    """
    if method == "equal-tailed":
        lower = float(np.percentile(samples, 100 * (1 - level) / 2))
        upper = float(np.percentile(samples, 100 * (1 + level) / 2))
        return (lower, upper)

    # HPD via grid search on sorted samples
    sorted_samples = np.sort(samples)
    n = len(sorted_samples)
    interval_idx = int(np.floor(level * n))
    widths = sorted_samples[interval_idx:] - sorted_samples[: n - interval_idx]
    min_idx = int(np.argmin(widths))
    return (
        float(sorted_samples[min_idx]),
        float(sorted_samples[min_idx + interval_idx]),
    )
