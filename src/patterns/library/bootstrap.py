"""
Bootstrap Resampling Pattern
Statistical bootstrap for confidence intervals

Based on:
- Efron's bootstrap
- Bias and variance estimation
- Confidence intervals (percentile, BCa)
- Hypothesis testing
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
class BootstrapConfig:
    """Configuration for bootstrap simulation"""
    n_bootstrap: int = 1000
    sample_size: int = 100
    statistic: str = "mean"   # "mean", "median", "std", "correlation"
    confidence_level: float = 0.95
    seed: int | None = None


@simulation_pattern(
    id="bootstrap",
    name="Bootstrap Resampling",
    category="mathematics",
    description="Statistical bootstrap for confidence interval estimation",
)
class BootstrapPattern(SimulationPattern):
    """
    Bootstrap resampling simulation

    Implements:
    - Non-parametric bootstrap
    - Bias estimation
    - Standard error estimation
    - Percentile confidence intervals
    """

    parameters = [
        SimulationParameter(
            name="n_bootstrap",
            type="int",
            default=1000,
            min=100,
            max=100000,
            description="Number of bootstrap samples",
        ),
        SimulationParameter(
            name="sample_size",
            type="int",
            default=100,
            min=10,
            max=10000,
            description="Original sample size",
        ),
        SimulationParameter(
            name="statistic",
            type="select",
            default="mean",
            options=["mean", "median", "std", "correlation"],
            description="Statistic to estimate",
        ),
        SimulationParameter(
            name="confidence_level",
            type="float",
            default=0.95,
            min=0.5,
            max=0.999,
            description="Confidence level",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config: BootstrapConfig = BootstrapConfig()

    def can_simulate(self, hypothesis: Hypothesis) -> bool:
        """Check if can simulate."""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        keywords = [
            "bootstrap", "resampling", "confidence interval",
            "standard error", "bias estimation", "non-parametric",
            "sampling distribution", "statistical inference",
        ]
        return any(kw in title or kw in desc for kw in keywords)

    async def run(self, hypothesis: Hypothesis, config: dict[str, Any]) -> SimulationResult:
        """Run."""
        start_time = datetime.now()
        simulation_id = f"boot_{start_time.timestamp()}"
        logger.info(f"Starting bootstrap simulation {simulation_id}")

        try:
            self.config = self._parse_config(config)
            results = await self._simulate_bootstrap()
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
            logger.exception("Bootstrap simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> BootstrapConfig:
        cfg = BootstrapConfig()
        if "n_bootstrap" in config:
            cfg.n_bootstrap = int(config["n_bootstrap"])
        if "sample_size" in config:
            cfg.sample_size = int(config["sample_size"])
        if "statistic" in config:
            cfg.statistic = str(config["statistic"])
        if "confidence_level" in config:
            cfg.confidence_level = float(config["confidence_level"])
        if "seed" in config:
            cfg.seed = int(config["seed"])
        return cfg

    async def _simulate_bootstrap(self) -> dict[str, Any]:
        cfg = self.config
        rng = np.random.default_rng(cfg.seed)
        n = cfg.sample_size
        B = cfg.n_bootstrap

        # Generate original sample from known distribution
        # Using normal distribution for demonstration
        true_mean = 5.0
        true_std = 2.0
        original_sample = rng.normal(true_mean, true_std, n)

        # Compute original statistic
        if cfg.statistic == "mean":
            original_stat = np.mean(original_sample)
            true_value = true_mean
        elif cfg.statistic == "median":
            original_stat = np.median(original_sample)
            true_value = true_mean
        elif cfg.statistic == "std":
            original_stat = np.std(original_sample, ddof=1)
            true_value = true_std
        elif cfg.statistic == "correlation":
            x = rng.normal(0, 1, n)
            y = 0.5 * x + rng.normal(0, 0.5, n)
            original_stat = np.corrcoef(x, y)[0, 1]
            true_value = 0.5
            original_sample = np.column_stack([x, y])
        else:
            original_stat = np.mean(original_sample)
            true_value = true_mean

        # Bootstrap resampling
        bootstrap_stats = np.zeros(B)
        for b in range(B):
            if cfg.statistic == "correlation":
                indices = rng.integers(0, n, n)
                resample = original_sample[indices]
                bootstrap_stats[b] = np.corrcoef(resample[:, 0], resample[:, 1])[0, 1]
            else:
                resample = rng.choice(original_sample, size=n, replace=True)
                if cfg.statistic == "mean":
                    bootstrap_stats[b] = np.mean(resample)
                elif cfg.statistic == "median":
                    bootstrap_stats[b] = np.median(resample)
                elif cfg.statistic == "std":
                    bootstrap_stats[b] = np.std(resample, ddof=1)

        # Bias estimate
        bias = np.mean(bootstrap_stats) - original_stat

        # Standard error
        std_error = np.std(bootstrap_stats, ddof=1)

        # Confidence intervals (percentile method)
        alpha = 1 - cfg.confidence_level
        ci_lower = np.percentile(bootstrap_stats, 100 * alpha / 2)
        ci_upper = np.percentile(bootstrap_stats, 100 * (1 - alpha / 2))

        # Coverage check
        coverage = (ci_lower <= true_value <= ci_upper)

        metrics = {
            "original_statistic": float(original_stat),
            "true_value": float(true_value),
            "bootstrap_mean": float(np.mean(bootstrap_stats)),
            "bias": float(bias),
            "standard_error": float(std_error),
            "ci_lower": float(ci_lower),
            "ci_upper": float(ci_upper),
            "ci_width": float(ci_upper - ci_lower),
            "coverage": float(coverage),
            "n_bootstrap": B,
            "sample_size": n,
            "statistic": cfg.statistic,
        }

        logs = [
            f"Bootstrap: {cfg.statistic}, n={n}, B={B}",
            f"Original statistic: {original_stat:.4f}",
            f"True value: {true_value:.4f}",
            f"Bootstrap mean: {metrics['bootstrap_mean']:.4f}",
            f"Bias: {bias:.4f}",
            f"Standard error: {std_error:.4f}",
            f"{cfg.confidence_level*100:.0f}% CI: [{ci_lower:.4f}, {ci_upper:.4f}]",
            f"Coverage: {coverage}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "bootstrap_statistics": bootstrap_stats.tolist(),
            "original_sample": original_sample.tolist() if cfg.statistic != "correlation" else original_sample[:100].tolist(),
        }

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        metrics = results["metrics"]
        factors = []

        # CI contains true value
        if metrics.get("coverage", 0) > 0:
            factors.append(0.3)

        # Small bias
        bias = abs(metrics.get("bias", 0))
        true_val = metrics.get("true_value", 1.0)
        if true_val != 0 and bias / abs(true_val) < 0.1:
            factors.append(0.25)

        # Reasonable standard error
        se = metrics.get("standard_error", 0)
        if se > 0:
            factors.append(0.2)

        # Sufficient bootstrap samples
        if metrics.get("n_bootstrap", 0) >= 1000:
            factors.append(0.25)

        return min(0.9, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:
        """Estimate resources."""
        params = hypothesis.parameters
        B = params.get("n_bootstrap", 1000)
        n = params.get("sample_size", 100)
        return {
            "cpu_cores": 1,
            "memory_gb": 0.1 + B * 8e-9,
            "gpu_required": False,
            "estimated_time_seconds": B * n / 1e7,
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
                "Efron, B. (1979). Bootstrap methods: Another look at the jackknife",
            ],
        }
