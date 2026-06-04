"""Bayesian Model Averaging (BMA) for C4REQBER.

Provides model evidence computation via Laplace approximation and numerical
integration, Bayes factors, and model selection utilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
from numpy.typing import NDArray
from scipy import integrate


@dataclass(frozen=True)
class ModelEvidence:
    """Container for model evidence results."""

    log_evidence: float
    method: str


@dataclass(frozen=True)
class BMAResult:
    """Result of Bayesian Model Averaging."""

    model_probs: dict[str, float]
    model_evidences: dict[str, float]
    best_model: str


def laplace_approximation(
    log_posterior: Callable[[NDArray[np.float64]], float],
    mode: NDArray[np.float64],
    hessian: NDArray[np.float64] | None = None,
) -> ModelEvidence:
    """Compute log marginal likelihood via Laplace approximation.

    log p(D | M) ≈ log p(D | θ̂, M) + log p(θ̂ | M) + (d/2) log(2π) - 0.5 log|H|

    where H is the Hessian of the negative log posterior at the mode.

    Args:
        log_posterior: Log of unnormalized posterior (log likelihood + log prior).
        mode: MAP estimate (posterior mode).
        hessian: Precomputed Hessian at mode (optional; estimated numerically if None).

    Returns:
        ModelEvidence with log marginal likelihood.
    """
    d = mode.shape[0]
    log_p_mode = log_posterior(mode)

    if hessian is None:
        hessian = _numerical_hessian(log_posterior, mode)

    sign, logdet = np.linalg.slogdet(hessian)
    if sign <= 0:
        # Fallback: use pseudo-determinant via eigendecomposition
        eigvals = np.linalg.eigvalsh(hessian)
        logdet = np.sum(np.log(eigvals[eigvals > 1e-12]))

    log_ev = log_p_mode + 0.5 * d * np.log(2.0 * np.pi) - 0.5 * logdet
    return ModelEvidence(log_evidence=float(log_ev), method="laplace")


def _numerical_hessian(
    f: Callable[[NDArray[np.float64]], float],
    x: NDArray[np.float64],
    eps: float = 1e-5,
) -> NDArray[np.float64]:
    """Numerical Hessian via central differences.

    Args:
        f: Scalar function.
        x: Point at which to evaluate Hessian.
        eps: Finite difference step.

    Returns:
        Hessian matrix (d x d).
    """
    d = x.shape[0]
    hess = np.zeros((d, d), dtype=np.float64)
    fx = f(x)

    for i in range(d):
        x_p = x.copy()
        x_m = x.copy()
        x_p[i] += eps
        x_m[i] -= eps
        hess[i, i] = (f(x_p) - 2 * fx + f(x_m)) / (eps**2)

    for i in range(d):
        for j in range(i + 1, d):
            x_pp = x.copy()
            x_pm = x.copy()
            x_mp = x.copy()
            x_mm = x.copy()
            x_pp[i] += eps
            x_pp[j] += eps
            x_pm[i] += eps
            x_pm[j] -= eps
            x_mp[i] -= eps
            x_mp[j] += eps
            x_mm[i] -= eps
            x_mm[j] -= eps
            hess[i, j] = (f(x_pp) - f(x_pm) - f(x_mp) + f(x_mm)) / (4 * eps**2)
            hess[j, i] = hess[i, j]

    return hess


def numerical_integration_evidence(
    log_posterior: Callable[[NDArray[np.float64]], float],
    bounds: list[tuple[float, float]],
    n_points: int = 100,
) -> ModelEvidence:
    """Compute log marginal likelihood via nested numerical integration.

    Args:
        log_posterior: Log of unnormalized posterior.
        bounds: List of (lower, upper) bounds for each dimension.
        n_points: Number of quadrature points per dimension.

    Returns:
        ModelEvidence with log marginal likelihood.
    """
    d = len(bounds)
    if d == 1:
        a, b = bounds[0]

        def integrand(x: float) -> float:
            """Integrand."""
            val = log_posterior(np.array([x], dtype=np.float64))
            return np.exp(val)  # type: ignore[no-any-return]

        result, _ = integrate.quad(integrand, a, b, limit=100)
        return ModelEvidence(log_evidence=np.log(max(result, 1e-300)), method="quad")

    # Multi-dimensional: use product grid (only practical for d <= 3)
    grids = [np.linspace(a, b, n_points) for a, b in bounds]
    mesh = np.meshgrid(*grids, indexing="ij")
    points = np.stack([m.ravel() for m in mesh], axis=1)
    log_vals = np.array([log_posterior(p) for p in points], dtype=np.float64)
    max_log = np.max(log_vals)
    vals = np.exp(log_vals - max_log)

    volumes = np.prod([(b - a) / n_points for a, b in bounds])
    integral = np.sum(vals) * volumes
    return ModelEvidence(
        log_evidence=max_log + np.log(max(integral, 1e-300)),
        method="grid",
    )


def bayes_factor(
    log_ev1: float,
    log_ev2: float,
) -> float:
    """Compute Bayes factor between two models.

    BF_12 = p(D | M_1) / p(D | M_2)

    Args:
        log_ev1: Log marginal likelihood for model 1.
        log_ev2: Log marginal likelihood for model 2.

    Returns:
        Bayes factor (model 1 vs model 2).
    """
    return float(np.exp(log_ev1 - log_ev2))


def interpret_bayes_factor(bf: float) -> str:
    """Interpret Bayes factor on Jeffreys' scale.

    Args:
        bf: Bayes factor value.

    Returns:
        Qualitative interpretation string.
    """
    if bf < 1:
        return "negative (favors alternative)"
    elif bf < 3:
        return "barely worth mentioning"
    elif bf < 10:
        return "substantial"
    elif bf < 30:
        return "strong"
    elif bf < 100:
        return "very strong"
    else:
        return "decisive"


def model_averaging(
    model_evidences: dict[str, float],
    prior_probs: dict[str, float] | None = None,
) -> BMAResult:
    """Compute posterior model probabilities via Bayesian Model Averaging.

    Args:
        model_evidences: Dictionary mapping model name to log marginal likelihood.
        prior_probs: Optional prior model probabilities (default uniform).

    Returns:
        BMAResult with posterior probabilities and best model.
    """
    names = list(model_evidences.keys())
    n_models = len(names)

    if prior_probs is None:
        prior_probs = {name: 1.0 / n_models for name in names}

    log_evs = np.array([model_evidences[name] for name in names], dtype=np.float64)
    priors = np.array([prior_probs.get(name, 1.0 / n_models) for name in names], dtype=np.float64)

    max_log = np.max(log_evs)
    evs = np.exp(log_evs - max_log)
    unnormalized = evs * priors
    total = np.sum(unnormalized)

    probs = {name: float(unnormalized[i] / total) for i, name in enumerate(names)}
    best = max(probs, key=probs.get)  # type: ignore[arg-type]

    return BMAResult(
        model_probs=probs,
        model_evidences={name: float(log_evs[i]) for i, name in enumerate(names)},
        best_model=best,
    )


def bma_predictive_distribution(
    x: NDArray[np.float64],
    model_predictives: dict[str, NDArray[np.float64]],
    model_probs: dict[str, float],
) -> NDArray[np.float64]:
    """Compute BMA predictive distribution.

    p(y | x, D) = Σ_k p(y | x, D, M_k) * p(M_k | D)

    Args:
        x: Input points.
        model_predictives: Dictionary mapping model name to predictive densities.
        model_probs: Posterior model probabilities.

    Returns:
        Averaged predictive distribution.
    """
    result = np.zeros_like(x, dtype=np.float64)
    for name, pred in model_predictives.items():
        result += pred * model_probs.get(name, 0.0)
    return result


def bic_approximation(
    log_likelihood_max: float,
    n_params: int,
    n_obs: int,
) -> float:
    """BIC approximation to log marginal likelihood.

    log p(D | M) ≈ log p(D | θ̂, M) - (k/2) log(n)

    Args:
        log_likelihood_max: Maximum log likelihood.
        n_params: Number of parameters.
        n_obs: Number of observations.

    Returns:
        BIC-based log marginal likelihood approximation.
    """
    return log_likelihood_max - 0.5 * n_params * np.log(max(n_obs, 1))  # type: ignore[no-any-return]


def aic_approximation(
    log_likelihood_max: float,
    n_params: int,
) -> float:
    """AIC approximation (not Bayesian, but useful for comparison).

    Args:
        log_likelihood_max: Maximum log likelihood.
        n_params: Number of parameters.

    Returns:
        AIC-based approximation.
    """
    return log_likelihood_max - n_params


def model_selection_by_bic(
    models: dict[str, tuple[float, int]],
    n_obs: int,
) -> tuple[str, dict[str, float]]:
    """Select best model by BIC approximation.

    Args:
        models: Dictionary mapping model name to (log_likelihood_max, n_params).
        n_obs: Number of observations.

    Returns:
        (best_model_name, bic_scores).
    """
    bics = {
        name: bic_approximation(log_like, k, n_obs)
        for name, (log_like, k) in models.items()
    }
    best = max(bics, key=bics.get)  # type: ignore[arg-type]
    return best, bics


@dataclass(frozen=True)
class SimpleBMAResult:
    """Simple result for Bayesian Model Averaging."""

    weighted_prediction: float
    uncertainty: float
    models: list[dict]


def bayesian_model_averaging(models: list[tuple[str, float, float]]) -> SimpleBMAResult:
    """Weight predictions by model posterior probabilities.

    Args:
        models: list of (name, posterior_probability, prediction)

    Returns:
        SimpleBMAResult with weighted_prediction, uncertainty, and model details
    """
    weighted_sum = 0.0
    weight_sum = 0.0
    model_details: list[dict[str, Any]] = []

    for name, prob, pred in models:
        weighted_sum += prob * pred
        weight_sum += prob
        model_details.append({"name": name, "posterior_prob": prob, "prediction": pred})

    weighted_pred = weighted_sum / weight_sum if weight_sum > 0 else 0.0
    variance = sum(
        float(m["posterior_prob"]) * (float(m["prediction"]) - weighted_pred) ** 2
        for m in model_details
    ) / weight_sum if weight_sum > 0 else 0.0

    return SimpleBMAResult(
        weighted_prediction=weighted_pred,
        uncertainty=variance ** 0.5,
        models=model_details,
    )
