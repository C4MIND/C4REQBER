"""
c4reqber: Expected Information Gain (EIG) Estimator

Heuristic ranking proxy only — not information-theoretic EIG and not a
simulator ensemble. See ``estimate`` docstring.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np


logger = logging.getLogger("c4reqber.discovery.ranking")


class EIGEstimator:
    """Heuristic Expected Information Gain proxy (text-length prior + noise).

    Not a real simulator-based EIG. Callers should treat the float as a ranking
    heuristic only (`estimate` does not claim information-theoretic EIG).
    """

    def estimate(
        self,
        hypothesis: dict[str, Any],
        simulator: str,
        n_samples: int = 100,
    ) -> float:
        """Return a ranking heuristic in [0, 1] (NOT information-theoretic EIG).

        Args:
            hypothesis: Hypothesis dict.
            simulator: Unused domain/simulator label (kept for API compat).
            n_samples: Monte Carlo draws of the length-based prior.

        Returns:
            Heuristic score (higher = more variable length-prior draws).
        """
        _ = simulator
        try:
            prior_predictions = self._simulate_prior(hypothesis, n_samples)
            if prior_predictions is None or len(prior_predictions) == 0:
                return 0.5

            std = float(np.std(prior_predictions))
            return float(np.clip(std / 5.0, 0.0, 1.0))

        except Exception as e:
            logger.warning("EIG heuristic error: %s", e)
            return 0.5

    def _simulate_prior(
        self,
        hypothesis: dict[str, Any],
        n_samples: int,
    ) -> np.ndarray | None:
        """Length-based noise prior — not a physics simulator."""
        rng = np.random.default_rng(42)
        results = []

        for _ in range(n_samples):
            try:
                param_scale = rng.uniform(0.5, 2.0)
                hyp_text = hypothesis.get("text", "")
                base_value = len(hyp_text) % 10 + 1.0
                result = base_value * param_scale + rng.normal(0, 0.5)
                results.append(result)
            except Exception:
                continue

        if not results:
            return None
        return np.asarray(results, dtype=float)
