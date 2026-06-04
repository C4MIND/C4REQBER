"""
c4reqber: Ensemble Runner

Runs simulator ensemble with different seeds/parameters.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np

from src.discovery.closed_loop.experiment_designer import ExperimentDesign


logger = logging.getLogger("c4reqber.discovery.closed_loop")


class EnsembleRunner:
    """Run simulator ensemble."""

    async def run_ensemble(
        self,
        design: ExperimentDesign,
    ) -> dict[str, Any]:
        """Run ensemble of simulations.

        Returns dict with predicted, observed, uncertainty.
        """
        rng = np.random.default_rng(int(design.params.get("seed", 42)))
        results = []

        for _ in range(design.n_runs):
            # Placeholder: in full implementation, call actual simulator
            # For now, simulate with noise
            base = 1.0 + design.params.get("perturbation", 0.0)
            result = base * design.params.get("scale", 1.0) + rng.normal(0, design.target_uncertainty)
            results.append(result)

        arr = np.array(results)
        return {
            "predicted": float(np.mean(arr)),
            "observed": float(np.mean(arr)),  # In real impl, observed = external data
            "uncertainty": float(np.std(arr)),
            "n_runs": design.n_runs,
            "simulator": design.simulator,
        }
