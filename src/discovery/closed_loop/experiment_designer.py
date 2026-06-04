"""
c4reqber: Experiment Designer

Designs next experiment to maximize information gain.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np

from src.discovery.closed_loop.bayesian_tracker import BayesianHypothesisTracker


logger = logging.getLogger("c4reqber.discovery.closed_loop")


@dataclass
class ExperimentDesign:
    simulator: str
    params: dict[str, float]
    n_runs: int
    target_uncertainty: float


class ExperimentDesigner:
    """Design experiments to maximize information gain."""

    DEFAULT_SIMULATORS = ["physics", "monte_carlo", "acoustic"]

    def design(
        self,
        tracker: BayesianHypothesisTracker,
        iteration: int,
        available_simulators: list[str] | None = None,
    ) -> ExperimentDesign:
        """Design next experiment.

        Args:
            tracker: Current belief state.
            iteration: Current iteration number.
            available_simulators: List of available simulator names.

        Returns:
            ExperimentDesign.
        """
        available_simulators = available_simulators or self.DEFAULT_SIMULATORS

        # If uncertainty is high, increase sample size
        if tracker.posterior < 0.3 or tracker.posterior > 0.7:
            n_runs = 10
            target_uncertainty = 0.5
        else:
            n_runs = 20
            target_uncertainty = 0.3

        # Rotate simulators
        simulator = available_simulators[iteration % len(available_simulators)]

        # Latin Hypercube-inspired parameter sampling
        rng = np.random.default_rng(42 + iteration)
        params = {
            "scale": float(rng.uniform(0.5, 2.0)),
            "seed": float(rng.integers(0, 10000)),
            "perturbation": float(rng.uniform(-1.0, 1.0)),
        }

        return ExperimentDesign(
            simulator=simulator,
            params=params,
            n_runs=n_runs,
            target_uncertainty=target_uncertainty,
        )
