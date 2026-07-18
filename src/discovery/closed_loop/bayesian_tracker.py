"""
c4reqber: Bayesian Hypothesis Tracker

Tracks belief in a hypothesis given simulation evidence.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np


logger = logging.getLogger("c4reqber.discovery.closed_loop")


@dataclass
class EvidenceRecord:
    iteration: int
    simulator: str
    predicted: float
    observed: float
    likelihood: float
    posterior_after: float


@dataclass
class BayesianHypothesisTracker:
    """Track posterior belief in a hypothesis via Bayesian updating."""

    hypothesis: str
    prior: float = 0.5
    evidence_log: list[EvidenceRecord] = field(default_factory=list)

    @property
    def posterior(self) -> float:
        if not self.evidence_log:
            return self.prior
        return self.evidence_log[-1].posterior_after

    @property
    def bayes_factor(self) -> float:
        p = self.posterior
        if p >= 0.9999:
            return float("inf")
        if p <= 0.0001:
            return 0.0
        return p / (1.0 - p)

    def update(self, simulated_data: dict[str, Any], simulator_name: str) -> None:
        """Update belief given simulation results.

        Skips heuristic / unavailable / stub payloads — they must not move the posterior.
        """
        if simulated_data.get("heuristic") is True:
            logger.info("Skipping Bayesian update: heuristic simulation payload")
            return
        status = str(simulated_data.get("status", "")).lower()
        if status in {"unavailable", "heuristic_fallback", "error", "failed"}:
            return
        if simulated_data.get("stub") is True:
            return
        if simulated_data.get("predicted") is None or simulated_data.get("observed") is None:
            return

        predicted = simulated_data.get("predicted", 0.0)
        observed = simulated_data.get("observed", 0.0)
        uncertainty = simulated_data.get("uncertainty", 1.0)

        likelihood = self._compute_likelihood(predicted, observed, uncertainty)
        prior = self.posterior

        posterior = (likelihood * prior) / (likelihood * prior + (1.0 - likelihood) * (1.0 - prior))
        posterior = float(np.clip(posterior, 0.001, 0.999))

        self.evidence_log.append(
            EvidenceRecord(
                iteration=len(self.evidence_log),
                simulator=simulator_name,
                predicted=predicted,
                observed=observed,
                likelihood=likelihood,
                posterior_after=posterior,
            )
        )

    @staticmethod
    def _compute_likelihood(predicted: float, observed: float, uncertainty: float) -> float:
        """Compute P(data | hypothesis) as agreement between predicted and observed."""
        if uncertainty <= 0:
            uncertainty = 1.0
        # Gaussian likelihood: closer predicted to observed = higher likelihood
        diff = abs(predicted - observed)
        likelihood = np.exp(-0.5 * (diff / uncertainty) ** 2)
        return float(np.clip(likelihood, 0.01, 0.99))

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypothesis": self.hypothesis[:200],
            "prior": round(self.prior, 4),
            "posterior": round(self.posterior, 4),
            "bayes_factor": round(self.bayes_factor, 4)
            if self.bayes_factor != float("inf")
            else "inf",
            "evidence_count": len(self.evidence_log),
        }
