"""
Monte Carlo Pi Pattern
Pi estimation using Monte Carlo methods

Based on:
- Buffon's needle (simplified to unit circle)
- Convergence analysis
- Error estimation
- Variance reduction
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np

from ..core import (
    Hypothesis,
    SimulationParameter,
    SimulationPattern,
    SimulationResult,
    SimulationStatus,
    ValidationLevel,
    simulation_pattern,
)


logger = logging.getLogger(__name__)


@dataclass
class MonteCarloPiConfig:
    """Configuration for Monte Carlo Pi estimation"""
    n_samples: int = 100000
    method: str = "unit_circle"  # "unit_circle" or "buffon"
    seed: int | None = None


@simulation_pattern(
    id="monte_carlo_pi",
    name="Monte Carlo Pi",
    category="mathematics",
    description="Pi estimation using Monte Carlo simulation",
)
class MonteCarloPiPattern(SimulationPattern):
    """
    Monte Carlo Pi estimation

    Implements:
    - Unit circle method
    - Buffon's needle (simplified)
    - Convergence tracking
    - Error estimation
    """

    parameters = [
        SimulationParameter(
            name="n_samples",
            type="int",
            default=100000,
            min=100,
            max=10000000,
            description="Number of random samples",
        ),
        SimulationParameter(
            name="method",
            type="select",
            default="unit_circle",
            options=["unit_circle", "buffon"],
            description="Estimation method",
        ),
        SimulationParameter(
            name="seed",
            type="int",
            default=42,
            min=0,
            max=1000000,
            description="Random seed",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config: MonteCarloPiConfig = MonteCarloPiConfig()

    def can_simulate(self, hypothesis: Hypothesis) -> bool:
        """Check if can simulate."""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        keywords = [
            "monte carlo", "pi estimation", "buffon", "random sampling",
            "circle area", "convergence", "approximation", "numerical integration",
        ]
        return any(kw in title or kw in desc for kw in keywords)

    async def run(self, hypothesis: Hypothesis, config: dict[str, Any]) -> SimulationResult:
        """Run."""
        start_time = datetime.now()
        simulation_id = f"mcpi_{start_time.timestamp()}"
        logger.info(f"Starting Monte Carlo Pi simulation {simulation_id}")

        try:
            self.config = self._parse_config(config)
            if self.config.method == "unit_circle":
                results = await self._simulate_unit_circle()
            else:
                results = await self._simulate_buffon()
            end_time = datetime.now()

            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.COMPLETED,
                start_time=start_time,
                end_time=end_time,
                metrics=results["metrics"],
                logs=results["logs"],
                confidence_score=self._calculate_confidence(results),
                validation_level=ValidationLevel.MONTE_CARLO,
            )
        except Exception as e:
            logger.exception("Monte Carlo Pi simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> MonteCarloPiConfig:
        cfg = MonteCarloPiConfig()
        if "n_samples" in config:
            cfg.n_samples = int(config["n_samples"])
        if "method" in config:
            cfg.method = str(config["method"])
        if "seed" in config:
            cfg.seed = int(config["seed"])
        return cfg

    async def _simulate_unit_circle(self) -> dict[str, Any]:
        cfg = self.config
        n = cfg.n_samples
        rng = np.random.default_rng(cfg.seed)

        # Generate random points in unit square
        x = rng.uniform(-1, 1, n)
        y = rng.uniform(-1, 1, n)

        # Count points inside unit circle
        inside = x**2 + y**2 <= 1
        count_inside = np.cumsum(inside)

        # Pi estimates at different sample sizes
        sample_points = np.unique(np.logspace(2, np.log10(n), 20).astype(int))
        pi_estimates = 4 * count_inside[sample_points - 1] / sample_points

        # Final estimate
        pi_estimate = 4 * count_inside[-1] / n
        error = abs(pi_estimate - np.pi)
        relative_error = error / np.pi

        # Standard error: sqrt(p*(1-p)/n) * 4 where p = pi/4
        p = np.pi / 4
        std_error = 4 * np.sqrt(p * (1 - p) / n)

        metrics = {
            "pi_estimate": float(pi_estimate),
            "absolute_error": float(error),
            "relative_error": float(relative_error),
            "standard_error": float(std_error),
            "n_samples": n,
            "inside_count": int(count_inside[-1]),
            "outside_count": int(n - count_inside[-1]),
            "method": "unit_circle",
        }

        logs = [
            f"Monte Carlo Pi (unit circle): {n} samples",
            f"Pi estimate: {pi_estimate:.8f}",
            f"True pi: {np.pi:.8f}",
            f"Absolute error: {error:.8f}",
            f"Relative error: {relative_error*100:.6f}%",
            f"Standard error: {std_error:.8f}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "sample_points": sample_points.tolist(),
            "pi_estimates": pi_estimates.tolist(),
            "x": x[:1000].tolist(),
            "y": y[:1000].tolist(),
            "inside": inside[:1000].tolist(),
        }

    async def _simulate_buffon(self) -> dict[str, Any]:
        cfg = self.config
        n = cfg.n_samples
        rng = np.random.default_rng(cfg.seed)

        # Buffon's needle: drop needles of length L on grid with spacing D
        # Simplified: L = D = 1
        # P(crossing) = 2/pi, so pi = 2/P
        L = 1.0
        D = 1.0

        # Random needle positions and angles
        y_center = rng.uniform(0, D, n)
        theta = rng.uniform(0, np.pi, n)

        # Check if needle crosses a line
        y_tip = y_center + 0.5 * L * np.sin(theta)
        y_tail = y_center - 0.5 * L * np.sin(theta)
        crosses = (y_tip > D) | (y_tail < 0)

        p_cross = np.mean(crosses)
        if p_cross > 0:
            pi_estimate = 2 * L / (D * p_cross)
        else:
            pi_estimate = float('inf')

        error = abs(pi_estimate - np.pi) if pi_estimate != float('inf') else float('inf')

        metrics = {
            "pi_estimate": float(pi_estimate) if pi_estimate != float('inf') else -1.0,
            "absolute_error": float(error) if error != float('inf') else -1.0,
            "n_samples": n,
            "crosses_count": int(np.sum(crosses)),
            "p_cross": float(p_cross),
            "method": "buffon",
        }

        logs = [
            f"Buffon's needle: {n} needles",
            f"Pi estimate: {pi_estimate:.8f}" if pi_estimate != float('inf') else "Pi estimate: inf (no crossings)",
            f"Crossings: {np.sum(crosses)} / {n}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
        }

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        metrics = results["metrics"]
        factors = []

        rel_err = metrics.get("relative_error", 1.0)
        if rel_err < 0.01:
            factors.append(0.4)
        elif rel_err < 0.1:
            factors.append(0.2)

        if metrics.get("n_samples", 0) >= 10000:
            factors.append(0.3)

        std_err = metrics.get("standard_error", 1.0)
        if std_err < 0.1:
            factors.append(0.3)

        return min(0.9, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:
        """Estimate resources."""
        params = hypothesis.parameters
        n = params.get("n_samples", 100000)
        return {
            "cpu_cores": 1,
            "memory_gb": 0.1,
            "gpu_required": False,
            "estimated_time_seconds": n / 1e7,
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "id": cls.id,
            "name": cls.name,
            "category": cls.category,
            "description": cls.description,
            "parameters": [
                {"name": p.name, "type": p.type, "default": p.default,
                 "min": p.min, "max": p.max, "description": p.description}
                for p in cls.parameters
            ],
            "references": [
                "Metropolis, N. & Ulam, S. (1949). The Monte Carlo method",
            ],
        }
