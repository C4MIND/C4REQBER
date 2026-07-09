"""
Evolutionary Dynamics Pattern
Moran process and Wright-Fisher model for evolutionary dynamics

Based on:
- Moran process (1958)
- Wright-Fisher model (1931)
- Replicator dynamics
- Evolutionary game theory
- Fixation probability
"""

from __future__ import annotations

import asyncio
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
class EvolutionaryConfig:
    """Configuration for evolutionary dynamics simulation"""
    model_type: str = "moran"  # moran, wright_fisher, replicator
    N: int = 100  # Population size
    n_generations: int = 1000

    # Selection
    selection_strength: float = 1.0  # s
    fitness_landscape: str = "constant"  # constant, frequency_dependent

    # Mutation
    mutation_rate: float = 0.001

    # Initial condition
    initial_frequency: float = 0.5

    # For game theory models
    payoff_matrix: np.ndarray | None = None

    # For multi-type models
    n_types: int = 2

    n_realizations: int = 100
    random_seed: int | None = None


@simulation_pattern(
    id="evolutionary",
    name="Evolutionary Dynamics",
    category="biology",
    description="Moran process and Wright-Fisher model for evolutionary dynamics",
)
class EvolutionaryPattern(SimulationPattern):
    """
    Evolutionary dynamics simulation for allele frequencies

    Implements:
    - Moran process (birth-death)
    - Wright-Fisher model
    - Replicator dynamics
    - Fixation probability calculation
    - Time to fixation
    - Genetic drift vs selection
    """

    parameters = [
        SimulationParameter(
            name="model_type",
            type="select",
            default="moran",
            options=["moran", "wright_fisher", "replicator"],
            description="Evolutionary model",
        ),
        SimulationParameter(
            name="N",
            type="int",
            default=100,
            min=10,
            max=10000,
            description="Population size",
        ),
        SimulationParameter(
            name="n_generations",
            type="int",
            default=1000,
            min=100,
            max=100000,
            description="Number of generations",
        ),
        SimulationParameter(
            name="selection_strength",
            type="float",
            default=1.0,
            min=0.0,
            max=10.0,
            description="Selection coefficient",
        ),
        SimulationParameter(
            name="mutation_rate",
            type="float",
            default=0.001,
            min=0.0,
            max=0.1,
            description="Mutation rate per generation",
        ),
        SimulationParameter(
            name="initial_frequency",
            type="float",
            default=0.5,
            min=0.0,
            max=1.0,
            description="Initial mutant frequency",
        ),
        SimulationParameter(
            name="n_realizations",
            type="int",
            default=100,
            min=10,
            max=1000,
            description="Number of Monte Carlo realizations",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.rng = np.random.default_rng()
        self.config: EvolutionaryConfig | None = None
        self.trajectories: list[np.ndarray] = []
        self.fixation_data: list[dict[str, Any]] = []

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if this pattern can simulate the hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()

        keywords = [
            "evolution", "evolutionary dynamics", "moran process",
            "wright-fisher", "genetic drift", "natural selection",
            "fixation", "allele frequency", "population genetics",
            "replicator dynamics", "evolutionary game theory",
            "fitness", "mutation", "selection", "neutral evolution",
            "cooperation", "defection", "hawk dove", "prisoner's dilemma",
        ]

        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute evolutionary dynamics simulation"""
        start_time = datetime.now()
        simulation_id = f"evo_{start_time.timestamp()}"

        logger.info(f"Starting Evolutionary Dynamics simulation {simulation_id}")

        try:
            self.config = self._parse_config(config)
            if self.config.random_seed:
                self.rng = np.random.default_rng(self.config.random_seed)

            results = await self._simulate(hypothesis)

            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.COMPLETED,
                start_time=start_time,
                end_time=datetime.now(),
                metrics=results["metrics"],
                logs=results["logs"],
                confidence_score=self._calculate_confidence(results),
                validation_level=ValidationLevel.MONTE_CARLO,
            )

        except Exception as e:
            logger.exception("Evolutionary simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> EvolutionaryConfig:
        """Parse configuration"""
        return EvolutionaryConfig(
            model_type=config.get("model_type", "moran"),
            N=config.get("N", 100),
            n_generations=config.get("n_generations", 1000),
            selection_strength=config.get("selection_strength", 1.0),
            mutation_rate=config.get("mutation_rate", 0.001),
            initial_frequency=config.get("initial_frequency", 0.5),
            n_types=config.get("n_types", 2),
            n_realizations=config.get("n_realizations", 100),
            random_seed=config.get("random_seed"),
        )

    async def _simulate(self, hypothesis: Hypothesis) -> dict[str, Any]:
        """Run evolutionary simulation"""
        self.trajectories = []
        self.fixation_data = []

        for realization in range(self.config.n_realizations):  # type: ignore[union-attr]
            if self.config.model_type == "moran":  # type: ignore[union-attr]
                trajectory, fix_data = self._run_moran()
            elif self.config.model_type == "wright_fisher":  # type: ignore[union-attr]
                trajectory, fix_data = self._run_wright_fisher()
            else:  # replicator
                trajectory, fix_data = self._run_replicator()

            self.trajectories.append(trajectory)
            self.fixation_data.append(fix_data)

            if realization % 10 == 0:
                await asyncio.sleep(0)

        return self._analyze_results()

    def _run_moran(self) -> tuple[Any, ...]:
        """Run Moran process simulation"""
        N = self.config.N  # type: ignore[union-attr]
        n_gen = self.config.n_generations  # type: ignore[union-attr]
        s = self.config.selection_strength  # type: ignore[union-attr]
        mu = self.config.mutation_rate  # type: ignore[union-attr]

        # Initial mutant count
        i = int(self.config.initial_frequency * N)  # type: ignore[union-attr]
        i = max(1, min(N-1, i))  # Ensure at least one of each type

        trajectory = [i / N]
        fixation_time = None
        fixation_type = None

        for gen in range(n_gen):
            # Fitness of type A (mutant) and type B (wildtype)
            freq_A = i / N
            freq_B = 1 - freq_A

            # Frequency-dependent fitness
            fitness_A = 1 + s * freq_B  # Advantage when rare
            fitness_B = 1

            # Average fitness
            w_bar = freq_A * fitness_A + freq_B * fitness_B

            # Selection probabilities
            p_A = freq_A * fitness_A / w_bar
            freq_B * fitness_B / w_bar

            # Moran step: birth and death
            # Birth proportional to fitness
            if self.rng.random() < p_A:
                birth_A = True
            else:
                birth_A = False

            # Death uniform random
            death_A = self.rng.random() < freq_A

            # Update population
            if birth_A and not death_A:
                i += 1
            elif not birth_A and death_A:
                i -= 1

            # Mutation
            if self.rng.random() < mu:
                if self.rng.random() < 0.5:
                    i = min(N, i + 1)
                else:
                    i = max(0, i - 1)

            trajectory.append(i / N)

            # Check fixation
            if i == N and fixation_time is None:
                fixation_time = gen
                fixation_type = "A"
                if mu == 0:
                    break
            elif i == 0 and fixation_time is None:
                fixation_time = gen
                fixation_type = "B"
                if mu == 0:
                    break

        fix_data = {
            "fixation_time": fixation_time,
            "fixation_type": fixation_type,
            "final_frequency": i / N,
        }

        return np.array(trajectory), fix_data

    def _run_wright_fisher(self) -> tuple[Any, ...]:
        """Run Wright-Fisher model"""
        N = self.config.N  # type: ignore[union-attr]
        n_gen = self.config.n_generations  # type: ignore[union-attr]
        s = self.config.selection_strength  # type: ignore[union-attr]
        mu = self.config.mutation_rate  # type: ignore[union-attr]

        i = int(self.config.initial_frequency * N)  # type: ignore[union-attr]
        i = max(1, min(N-1, i))

        trajectory = [i / N]
        fixation_time = None
        fixation_type = None

        for gen in range(n_gen):
            freq_A = i / N
            freq_B = 1 - freq_A

            # Fitness
            fitness_A = 1 + s
            fitness_B = 1
            w_bar = freq_A * fitness_A + freq_B * fitness_B

            # Selection + mutation
            p = freq_A * fitness_A / w_bar
            p = p * (1 - mu) + (1 - p) * mu  # Include mutation

            # Binomial sampling
            i = self.rng.binomial(N, p)

            trajectory.append(i / N)

            if i == N and fixation_time is None:
                fixation_time = gen
                fixation_type = "A"
                if mu == 0:
                    break
            elif i == 0 and fixation_time is None:
                fixation_time = gen
                fixation_type = "B"
                if mu == 0:
                    break

        fix_data = {
            "fixation_time": fixation_time,
            "fixation_type": fixation_type,
            "final_frequency": i / N,
        }

        return np.array(trajectory), fix_data

    def _run_replicator(self) -> tuple[Any, ...]:
        """Run replicator dynamics"""
        n_gen = self.config.n_generations  # type: ignore[union-attr]
        s = self.config.selection_strength  # type: ignore[union-attr]

        x = self.config.initial_frequency  # type: ignore  # Frequency of type A
        trajectory = [x]

        for _gen in range(n_gen):
            # Replicator equation: dx/dt = x(1-x)(f_A - f_B)
            fitness_A = 1 + s
            fitness_B = 1

            f_bar = x * fitness_A + (1 - x) * fitness_B

            dx = x * (fitness_A - f_bar) / f_bar
            x = x + dx * 0.1  # Small step
            x = np.clip(x, 0, 1)

            trajectory.append(x)

        fix_data = {
            "fixation_time": None if 0 < x < 1 else n_gen,
            "fixation_type": "A" if x >= 1 else "B" if x <= 0 else None,
            "final_frequency": x,
        }

        return np.array(trajectory), fix_data

    def _analyze_results(self) -> dict[str, Any]:
        """Analyze simulation results"""
        if not self.trajectories:
            return {"metrics": {}, "logs": ["No simulation data"]}

        N = self.config.N  # type: ignore[union-attr]
        s = self.config.selection_strength  # type: ignore[union-attr]

        # Fixation statistics
        fixations_A = sum(1 for f in self.fixation_data if f["fixation_type"] == "A")
        fixations_B = sum(1 for f in self.fixation_data if f["fixation_type"] == "B")
        len(self.fixation_data) - fixations_A - fixations_B

        fixation_prob_A = fixations_A / len(self.fixation_data)
        fixation_prob_B = fixations_B / len(self.fixation_data)

        # Fixation times
        fixation_times = [f["fixation_time"] for f in self.fixation_data if f["fixation_time"] is not None]
        mean_fixation_time = np.mean(fixation_times) if fixation_times else None

        # Theoretical fixation probability (Moran: ρ = (1 - e^(-s)) / (1 - e^(-Ns)))
        if s != 0:
            rho_theory = (1 - np.exp(-s)) / (1 - np.exp(-N * s))
        else:
            rho_theory = 1 / N  # Neutral drift

        # Final frequency distribution
        final_freqs = [f["final_frequency"] for f in self.fixation_data]
        mean_final_freq = np.mean(final_freqs)

        # Heterozygosity decay (measure of genetic diversity)
        heterozygosity = []
        for traj in self.trajectories[:10]:  # Sample subset
            H = 2 * traj * (1 - traj)
            heterozygosity.append(H)
        mean_heterozygosity = np.mean([np.mean(h) for h in heterozygosity])

        metrics = {
            "fixation_prob_A": float(fixation_prob_A),
            "fixation_prob_B": float(fixation_prob_B),
            "fixation_prob_theory": float(rho_theory),
            "fixation_error": float(abs(fixation_prob_A - rho_theory)),
            "mean_fixation_time": float(mean_fixation_time) if mean_fixation_time else None,
            "mean_final_frequency": float(mean_final_freq),
            "mean_heterozygosity": float(mean_heterozygosity),
            "n_realizations": len(self.fixation_data),
            "selection_strength": s,
        }

        logs = [
            f"Evolutionary Dynamics ({self.config.model_type}): N={N}, s={s}",  # type: ignore[union-attr]
            f"Fixation probability (A): {fixation_prob_A:.4f}",
            f"Theoretical fixation prob: {rho_theory:.4f}",
            f"Mean final frequency: {mean_final_freq:.4f}",
        ]

        if mean_fixation_time:
            logs.append(f"Mean fixation time: {mean_fixation_time:.1f} generations")

        if s > 0:
            if fixation_prob_A > 0.5:
                logs.append("Selection favors type A")
            else:
                logs.append("Genetic drift dominates selection")
        else:
            logs.append("Neutral evolution (no selection)")

        return {"metrics": metrics, "logs": logs}

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        n_real = metrics.get("n_realizations", 0)
        if n_real >= 100:
            factors.append(0.3)
        elif n_real >= 50:
            factors.append(0.2)

        error = metrics.get("fixation_error", 1.0)
        if error < 0.05:
            factors.append(0.3)
        elif error < 0.1:
            factors.append(0.2)

        if metrics.get("mean_fixation_time"):
            factors.append(0.2)

        return min(0.85, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        params = hypothesis.parameters
        N = params.get("N", 100)
        n_gen = params.get("n_generations", 1000)
        n_real = params.get("n_realizations", 100)

        estimated_time = (N * n_gen * n_real) / 1e6

        return {
            "cpu_cores": 1,
            "memory_gb": 0.1 + n_real * 0.001,
            "gpu_required": False,
            "estimated_time_seconds": estimated_time,
        }
