"""Bayesian Engine for c4-cdi-turbo.

Exports core conjugate inference, MCMC samplers, and Bayesian Model Averaging.
"""

from __future__ import annotations

from .bma import (
    BMAResult,
    ModelEvidence,
    aic_approximation,
    bayes_factor,
    bic_approximation,
    bma_predictive_distribution,
    interpret_bayes_factor,
    laplace_approximation,
    model_averaging,
    model_selection_by_bic,
    numerical_integration_evidence,
)
from .core import (
    BetaBinomialResult,
    DirichletMultinomialResult,
    GammaPoissonResult,
    NormalNormalResult,
    beta_binomial,
    credible_interval_from_samples,
    dirichlet_multinomial,
    gamma_poisson,
    normal_normal,
    posterior_predictive_beta_binomial,
    posterior_predictive_normal,
)
from .mcmc import (
    MCMCResult,
    effective_sample_size,
    gelman_rubin,
    gibbs_sampling,
    hmc,
    metropolis_hastings,
    nuts,
)


__all__ = [
    # core
    "NormalNormalResult",
    "BetaBinomialResult",
    "GammaPoissonResult",
    "DirichletMultinomialResult",
    "normal_normal",
    "beta_binomial",
    "gamma_poisson",
    "dirichlet_multinomial",
    "posterior_predictive_normal",
    "posterior_predictive_beta_binomial",
    "credible_interval_from_samples",
    # mcmc
    "MCMCResult",
    "metropolis_hastings",
    "gibbs_sampling",
    "hmc",
    "nuts",
    "effective_sample_size",
    "gelman_rubin",
    # bma
    "BMAResult",
    "ModelEvidence",
    "laplace_approximation",
    "numerical_integration_evidence",
    "bayes_factor",
    "interpret_bayes_factor",
    "model_averaging",
    "bma_predictive_distribution",
    "bic_approximation",
    "aic_approximation",
    "model_selection_by_bic",
]
