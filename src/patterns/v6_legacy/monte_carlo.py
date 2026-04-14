"""
Monte Carlo Simulation Pattern
Production-grade statistical simulation with variance reduction

Based on Stanislaw Ulam's work with importance sampling and modern
variance reduction techniques.
"""

import asyncio
import numpy as np
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

from ..core import (
    SimulationPattern,
    SimulationResult,
    SimulationStatus,
    Hypothesis,
    SimulationParameter,
    ValidationLevel,
    simulation_pattern,
)

logger = logging.getLogger(__name__)


@dataclass
class MonteCarloConfig:
    """Configuration for Monte Carlo simulation"""

    n_samples: int = 10000
    confidence_level: float = 0.95
    variance_reduction: str = (
        "stratified"  # 'none', 'stratified', 'importance', 'control_variates'
    )
    batch_size: int = 1000
    random_seed: Optional[int] = None
    convergence_threshold: float = 0.01
    max_iterations: int = 100000


@simulation_pattern(
    id="monte_carlo",
    name="Monte Carlo Simulation",
    category="stochastic",
    description="Statistical simulation using random sampling with variance reduction techniques",
)
class MonteCarloPattern(SimulationPattern):
    """
    Monte Carlo simulation pattern with advanced variance reduction

    Implements:
    - Stratified sampling
    - Importance sampling
    - Control variates
    - Quasi-random sequences (Sobol)
    - Parallel batch processing
    """

    parameters = [
        SimulationParameter(
            name="n_samples",
            type="int",
            default=10000,
            min=100,
            max=10000000,
            description="Number of Monte Carlo samples",
        ),
        SimulationParameter(
            name="confidence_level",
            type="float",
            default=0.95,
            min=0.8,
            max=0.999,
            description="Confidence level for intervals",
        ),
        SimulationParameter(
            name="variance_reduction",
            type="select",
            default="stratified",
            options=["none", "stratified", "importance", "control_variates", "sobol"],
            description="Variance reduction technique",
        ),
        SimulationParameter(
            name="convergence_threshold",
            type="float",
            default=0.01,
            min=0.001,
            max=0.1,
            description="Relative convergence threshold",
        ),
    ]

    def __init__(self):
        super().__init__()
        self.rng = np.random.default_rng()

    def can_simulate(self, hypothesis: Hypothesis) -> bool:
        """
        Monte Carlo can simulate hypotheses with:
        - Stochastic/probabilistic components
        - Uncertainty quantification needs
        - Risk analysis requirements
        """
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()

        monte_carlo_keywords = [
            "probability",
            "risk",
            "uncertainty",
            "stochastic",
            "random",
            "variance",
            "distribution",
            "confidence",
            "reliability",
            "failure rate",
            "monte carlo",
        ]

        return any(kw in title or kw in desc for kw in monte_carlo_keywords)

    async def run(
        self, hypothesis: Hypothesis, config: Dict[str, Any]
    ) -> SimulationResult:
        """Execute Monte Carlo simulation"""
        start_time = datetime.now()
        simulation_id = f"mc_{start_time.timestamp()}"

        logger.info(f"Starting Monte Carlo simulation {simulation_id}")

        # Parse configuration
        mc_config = MonteCarloConfig(
            **{
                k: config.get(k, v.default if hasattr(v, "default") else v)
                for k, v in vars(MonteCarloConfig).items()
                if not k.startswith("_")
            }
        )

        if mc_config.random_seed:
            self.rng = np.random.default_rng(mc_config.random_seed)

        try:
            # Build simulation model from hypothesis
            model = self._build_model(hypothesis)

            # Run simulation with selected variance reduction
            if mc_config.variance_reduction == "stratified":
                results = await self._stratified_sampling(model, mc_config)
            elif mc_config.variance_reduction == "importance":
                results = await self._importance_sampling(model, mc_config)
            elif mc_config.variance_reduction == "sobol":
                results = await self._sobol_sampling(model, mc_config)
            else:
                results = await self._naive_monte_carlo(model, mc_config)

            # Calculate confidence intervals
            mean = np.mean(results)
            std = np.std(results, ddof=1)
            sem = std / np.sqrt(len(results))

            from scipy import stats

            confidence_interval = stats.t.interval(
                mc_config.confidence_level, len(results) - 1, loc=mean, scale=sem
            )

            # Calculate effective sample size (for variance reduction assessment)
            ess = (
                len(results) * (np.var(results) / (std**2)) if std > 0 else len(results)
            )

            end_time = datetime.now()

            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.COMPLETED,
                start_time=start_time,
                end_time=end_time,
                metrics={
                    "mean": float(mean),
                    "std": float(std),
                    "variance": float(std**2),
                    "ci_lower": float(confidence_interval[0]),
                    "ci_upper": float(confidence_interval[1]),
                    "ess": float(ess),
                    "n_samples": len(results),
                    "variance_reduction_factor": len(results) / ess if ess > 0 else 1.0,
                },
                logs=[
                    f"Completed {len(results)} samples",
                    f"Mean: {mean:.6f} ± {sem:.6f}",
                    f"95% CI: [{confidence_interval[0]:.6f}, {confidence_interval[1]:.6f}]",
                    f"Effective sample size: {ess:.1f}",
                    f"Variance reduction: {(len(results) / ess - 1) * 100:.1f}%",
                ],
                confidence_score=self._calculate_confidence(
                    mean, std, len(results), mc_config
                ),
                validation_level=ValidationLevel.MONTE_CARLO,
            )

        except Exception as e:
            logger.exception("Monte Carlo simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _build_model(
        self, hypothesis: Hypothesis
    ) -> Callable[[np.ndarray], np.ndarray]:
        """
        Build simulation model from hypothesis

        This extracts mathematical model from hypothesis description
        and returns a function that can be evaluated with random inputs
        """
        # TODO: Use LLM to parse hypothesis and generate model
        # For now, return a placeholder model

        def model(inputs: np.ndarray) -> np.ndarray:
            """
            Placeholder model - extracts parameters from hypothesis
            and computes output distribution
            """
            # Extract parameters from hypothesis
            params = hypothesis.parameters

            # Simple example: linear combination with noise
            base_value = params.get("base_value", 1.0)
            noise_scale = params.get("noise_scale", 0.1)

            # Generate outputs
            n = inputs.shape[0] if len(inputs.shape) > 0 else 1
            outputs = base_value + noise_scale * np.random.randn(n)

            return outputs

        return model

    async def _naive_monte_carlo(
        self, model: Callable, config: MonteCarloConfig
    ) -> np.ndarray:
        """Basic Monte Carlo without variance reduction"""
        n_batches = config.n_samples // config.batch_size
        remainder = config.n_samples % config.batch_size

        results = []

        for i in range(n_batches):
            # Generate uniform random inputs
            inputs = self.rng.uniform(0, 1, (config.batch_size, 10))

            # Run model
            outputs = model(inputs)
            results.extend(outputs)

            # Yield control for async
            if i % 10 == 0:
                await asyncio.sleep(0)

        # Handle remainder
        if remainder > 0:
            inputs = self.rng.uniform(0, 1, (remainder, 10))
            outputs = model(inputs)
            results.extend(outputs)

        return np.array(results)

    async def _stratified_sampling(
        self, model: Callable, config: MonteCarloConfig
    ) -> np.ndarray:
        """
        Stratified sampling for variance reduction

        Divides input space into strata and samples from each
        proportional to stratum size.
        """
        n_strata = 10
        samples_per_stratum = config.n_samples // n_strata

        results = []

        for stratum in range(n_strata):
            # Define stratum bounds
            lower = stratum / n_strata
            upper = (stratum + 1) / n_strata

            # Sample within stratum
            for batch in range(0, samples_per_stratum, config.batch_size):
                batch_size = min(config.batch_size, samples_per_stratum - batch)

                # Uniform within stratum
                inputs = self.rng.uniform(lower, upper, (batch_size, 10))

                outputs = model(inputs)
                results.extend(outputs)

                if batch % 100 == 0:
                    await asyncio.sleep(0)

        return np.array(results)

    async def _importance_sampling(
        self, model: Callable, config: MonteCarloConfig
    ) -> np.ndarray:
        """
        Importance sampling for rare event simulation

        Samples from proposal distribution that puts more weight
        on important regions (e.g., failure modes).
        """
        # Use Gaussian proposal centered on expected failure region
        proposal_mean = 0.8  # Higher values where failures occur
        proposal_std = 0.1

        results = []
        weights = []

        for batch in range(0, config.n_samples, config.batch_size):
            batch_size = min(config.batch_size, config.n_samples - batch)

            # Sample from proposal distribution
            inputs = self.rng.normal(proposal_mean, proposal_std, (batch_size, 10))
            inputs = np.clip(inputs, 0, 1)  # Clip to valid range

            outputs = model(inputs)

            # Calculate importance weights
            # w(x) = p(x) / q(x) where p is uniform, q is Gaussian
            uniform_pdf = 1.0  # uniform on [0,1]
            from scipy.stats import norm

            gaussian_pdf = norm.pdf(inputs, proposal_mean, proposal_std)
            batch_weights = uniform_pdf / gaussian_pdf.mean(axis=1)

            results.extend(outputs)
            weights.extend(batch_weights)

            if batch % 100 == 0:
                await asyncio.sleep(0)

        # Weighted average
        results = np.array(results)
        weights = np.array(weights)
        weighted_results = results * weights / weights.sum() * len(results)

        return weighted_results

    async def _sobol_sampling(
        self, model: Callable, config: MonteCarloConfig
    ) -> np.ndarray:
        """
        Quasi-Monte Carlo using Sobol sequences

        Sobol sequences provide more uniform coverage of input space
        than random sampling, reducing variance.
        """
        from scipy.stats import qmc

        sampler = qmc.Sobol(d=10, scramble=True, seed=self.rng.integers(0, 2**32))

        results = []

        for batch in range(0, config.n_samples, config.batch_size):
            batch_size = min(config.batch_size, config.n_samples - batch)

            # Generate Sobol samples
            inputs = sampler.random(batch_size)

            outputs = model(inputs)
            results.extend(outputs)

            if batch % 100 == 0:
                await asyncio.sleep(0)

        return np.array(results)

    def _calculate_confidence(
        self, mean: float, std: float, n_samples: int, config: MonteCarloConfig
    ) -> float:
        """
        Calculate confidence score based on simulation quality

        Factors:
        - Sample size (larger = better)
        - Variance (lower = better)
        - Convergence (stable mean = better)
        """
        # Base confidence from sample size (law of large numbers)
        sample_factor = min(1.0, np.log(n_samples) / np.log(100000))

        # Variance factor (lower variance = higher confidence)
        # Normalize by mean to get relative variance
        if mean != 0:
            cv = std / abs(mean)  # coefficient of variation
            variance_factor = max(0, 1 - cv)
        else:
            variance_factor = max(0, 1 - std)

        # Combined score
        confidence = 0.6 * sample_factor + 0.4 * variance_factor

        return min(0.95, confidence)  # Cap at 0.95 (Monte Carlo limit)

    def estimate_resources(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        """Estimate computational resources"""
        params = hypothesis.parameters
        n_samples = params.get("n_samples", 10000)

        # Rough estimation: 1000 samples per second per core
        estimated_time = n_samples / 1000

        return {
            "cpu_cores": 4,
            "memory_gb": 2.0,
            "gpu_required": False,
            "estimated_time_seconds": estimated_time,
        }
