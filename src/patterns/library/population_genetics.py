"""
Population Genetics Pattern
Wright-Fisher model and genetic drift

Based on:
- Wright-Fisher sampling
- Genetic drift
- Fixation probability
- Heterozygosity decay
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
class PopulationGeneticsConfig:
    """Configuration for population genetics simulation"""
    N: int = 100              # Population size (diploid: 2N alleles)
    p0: float = 0.5           # Initial allele frequency
    n_generations: int = 100  # Number of generations
    n_replicates: int = 100   # Number of replicate populations
    selection_coefficient: float = 0.0  # s
    mutation_rate: float = 0.0  # mu


@simulation_pattern(
    id="population_genetics",
    name="Population Genetics",
    category="biology",
    description="Wright-Fisher model with genetic drift and selection",
)
class PopulationGeneticsPattern(SimulationPattern):
    """
    Population genetics simulation

    Implements:
    - Wright-Fisher binomial sampling
    - Genetic drift
    - Selection
    - Fixation probability and time
    - Heterozygosity decay
    """

    parameters = [
        SimulationParameter(
            name="N",
            type="int",
            default=100,
            min=10,
            max=10000,
            description="Population size (diploid)",
        ),
        SimulationParameter(
            name="p0",
            type="float",
            default=0.5,
            min=0.0,
            max=1.0,
            description="Initial allele frequency",
        ),
        SimulationParameter(
            name="n_generations",
            type="int",
            default=100,
            min=10,
            max=10000,
            description="Number of generations",
        ),
        SimulationParameter(
            name="n_replicates",
            type="int",
            default=100,
            min=10,
            max=1000,
            description="Number of replicate populations",
        ),
        SimulationParameter(
            name="selection_coefficient",
            type="float",
            default=0.0,
            min=-1.0,
            max=1.0,
            description="Selection coefficient",
        ),
        SimulationParameter(
            name="mutation_rate",
            type="float",
            default=0.0,
            min=0.0,
            max=0.1,
            description="Mutation rate",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config: PopulationGeneticsConfig = PopulationGeneticsConfig()

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if population genetics can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        keywords = [
            "population genetics", "genetic drift", "wright fisher",
            "allele frequency", "fixation", "heterozygosity",
            "selection", "neutral evolution", "coalescent",
            "gene pool", "founder effect", "bottleneck",
        ]
        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute population genetics simulation"""
        start_time = datetime.now()
        simulation_id = f"pg_{start_time.timestamp()}"
        logger.info(f"Starting population genetics simulation {simulation_id}")

        try:
            self.config = self._parse_config(config)
            results = await self._simulate_genetics()
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
            logger.exception("Population genetics simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> PopulationGeneticsConfig:
        """Parse configuration dict"""
        cfg = PopulationGeneticsConfig()
        if "N" in config:
            cfg.N = int(config["N"])
        if "p0" in config:
            cfg.p0 = float(config["p0"])
        if "n_generations" in config:
            cfg.n_generations = int(config["n_generations"])
        if "n_replicates" in config:
            cfg.n_replicates = int(config["n_replicates"])
        if "selection_coefficient" in config:
            cfg.selection_coefficient = float(config["selection_coefficient"])
        if "mutation_rate" in config:
            cfg.mutation_rate = float(config["mutation_rate"])
        return cfg

    async def _simulate_genetics(self) -> dict[str, Any]:
        """Run Wright-Fisher simulation"""
        cfg = self.config
        N = cfg.N
        n_gen = cfg.n_generations
        n_rep = cfg.n_replicates
        s = cfg.selection_coefficient
        mu = cfg.mutation_rate

        # Track allele frequencies across replicates
        frequencies = np.zeros((n_rep, n_gen + 1))
        frequencies[:, 0] = cfg.p0

        # Track heterozygosity
        heterozygosity = np.zeros(n_gen + 1)
        heterozygosity[0] = 2 * cfg.p0 * (1 - cfg.p0)

        # Wright-Fisher simulation
        for rep in range(n_rep):
            p = cfg.p0
            for gen in range(1, n_gen + 1):
                if p <= 0:
                    p = mu  # Mutation from extinct allele
                elif p >= 1:
                    p = 1 - mu  # Mutation from fixed allele
                else:
                    # Selection: w_AA = 1, w_Aa = 1 + hs, w_aa = 1 + s
                    # Simplified: p' = p * (1 + s) / (p * (1 + s) + (1 - p))
                    if s != 0:
                        p = p * (1 + s) / (p * (1 + s) + (1 - p))

                    # Genetic drift: binomial sampling
                    p = np.random.binomial(2 * N, p) / (2 * N)

                frequencies[rep, gen] = p

        # Calculate heterozygosity over time
        for gen in range(n_gen + 1):
            mean_p = np.mean(frequencies[:, gen])
            heterozygosity[gen] = 2 * mean_p * (1 - mean_p)

        # Fixation statistics
        final_freqs = frequencies[:, -1]
        fixed = np.sum(final_freqs >= 0.99)
        lost = np.sum(final_freqs <= 0.01)
        polymorphic = n_rep - fixed - lost

        # Fixation probability
        fixation_prob = fixed / n_rep

        # Expected fixation probability (Kimura): (1 - exp(-4Nsp)) / (1 - exp(-4Ns))
        if s != 0:
            expected_fixation = (1 - np.exp(-4 * N * s * cfg.p0)) / (1 - np.exp(-4 * N * s))
        else:
            expected_fixation = cfg.p0

        # Time to fixation (for fixed replicates)
        fixation_times = []
        for rep in range(n_rep):
            if final_freqs[rep] >= 0.99:
                for gen in range(n_gen + 1):
                    if frequencies[rep, gen] >= 0.99:
                        fixation_times.append(gen)
                        break

        metrics = {
            "initial_frequency": cfg.p0,
            "final_mean_frequency": float(np.mean(final_freqs)),
            "final_frequency_std": float(np.std(final_freqs)),
            "fixation_probability": float(fixation_prob),
            "expected_fixation_prob": float(expected_fixation),
            "lost_count": int(lost),
            "fixed_count": int(fixed),
            "polymorphic_count": int(polymorphic),
            "mean_fixation_time": float(np.mean(fixation_times)) if fixation_times else 0.0,
            "initial_heterozygosity": float(heterozygosity[0]),
            "final_heterozygosity": float(heterozygosity[-1]),
            "selection_coefficient": s,
            "effective_population": N,
        }

        logs = [
            f"Wright-Fisher: N={N}, p0={cfg.p0}, {n_gen} generations, {n_rep} replicates",
            f"Fixation probability: {fixation_prob:.4f} (expected: {expected_fixation:.4f})",
            f"Fixed: {fixed}, Lost: {lost}, Polymorphic: {polymorphic}",
            f"Mean fixation time: {metrics['mean_fixation_time']:.1f} generations",
            f"Heterozygosity: {heterozygosity[0]:.4f} -> {heterozygosity[-1]:.4f}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "frequencies": frequencies.tolist(),
            "heterozygosity": heterozygosity.tolist(),
            "generations": list(range(n_gen + 1)),
        }

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        # Fixation probability close to expectation
        obs = metrics.get("fixation_probability", 0)
        exp = metrics.get("expected_fixation_prob", 0)
        if exp > 0 and abs(obs - exp) / exp < 0.5:
            factors.append(0.3)

        # Heterozygosity decay
        if metrics.get("final_heterozygosity", 1) < metrics.get("initial_heterozygosity", 0):
            factors.append(0.3)

        # Valid counts
        total = metrics.get("fixed_count", 0) + metrics.get("lost_count", 0) + metrics.get("polymorphic_count", 0)
        if total > 0:
            factors.append(0.2)

        # Population size reasonable
        if metrics.get("effective_population", 0) >= 10:
            factors.append(0.2)

        return min(0.9, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        params = hypothesis.parameters
        N = params.get("N", 100)
        n_gen = params.get("n_generations", 100)
        n_rep = params.get("n_replicates", 100)
        return {
            "cpu_cores": 1,
            "memory_gb": 0.1 + n_rep * n_gen * 8e-9,
            "gpu_required": False,
            "estimated_time_seconds": n_rep * n_gen * N / 1e7,
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "id": cls.id,
            "name": cls.name,  # type: ignore[attr-defined]
            "category": cls.category,  # type: ignore[attr-defined]
            "description": cls.description,  # type: ignore[attr-defined]
            "parameters": [
                {"name": p.name, "type": p.type, "default": p.default,
                 "min": p.min, "max": p.max, "description": p.description}
                for p in cls.parameters
            ],
            "references": [
                "Hartl, D.L. & Clark, A.G. (2007). Principles of Population Genetics",
            ],
        }
