"""Shared data models for the Bayesian Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MCMCSample:
    """Result of MCMC sampling with Metropolis-Hastings."""

    samples: list[float]
    acceptance_rate: float
    mean: float
    std: float

@dataclass
class Model:
    """Single model in Bayesian Model Averaging."""

    name: str
    posterior_prob: float
    prediction: float

@dataclass
class BMAResult:
    """Result of Bayesian Model Averaging."""

    models: list[Model]
    weighted_prediction: float
    uncertainty: float

@dataclass
class OptimizationResult:
    """Result of Bayesian Optimization."""

    best_x: float
    best_y: float
    history: list[tuple[float, float]] = field(default_factory=list[Any])
    iterations: int = 0

@dataclass
class DSTResult:
    """Result of Dempster-Shafer combination."""

    belief: dict[str, float]
    plausibility: dict[str, float]
    conflict: float

@dataclass
class FuzzyResult:
    """Result of fuzzy inference."""

    crisp_output: float
    membership_values: dict[str, float]
    rule_strengths: list[float]
