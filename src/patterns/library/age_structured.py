"""
Age-Structured Population Pattern
McKendrick-von Foerster equation for structured populations

Based on:
- McKendrick-von Foerster equation (1926)
- Leslie matrix population projection
- Age-structured epidemiology
- Demographic transition theory
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
class AgeStructuredConfig:
    """Configuration for age-structured simulation"""
    max_age: int = 100
    age_groups: int = 20
    t_max: float = 100.0
    dt: float = 0.1

    # Demographic parameters
    birth_rate: float = 0.025  # Per capita birth rate
    carrying_capacity: float = 1000000

    # Survival curve type
    survival_type: str = "type1"  # type1 (human), type2, type3

    # Initial population
    initial_population: np.ndarray | None = None

    random_seed: int | None = None


@simulation_pattern(
    id="age_structured",
    name="Age-Structured Population",
    category="demography",
    description="McKendrick-von Foerster equation for structured populations",
)
class AgeStructuredPattern(SimulationPattern):
    """
    Age-structured population dynamics simulation

    Implements:
    - McKendrick-von Foerster partial differential equation
    - Leslie matrix projection
    - Age-specific mortality (survival curves)
    - Age-specific fertility
    - Stable age distribution
    - Population momentum
    """

    parameters = [
        SimulationParameter(
            name="max_age",
            type="int",
            default=100,
            min=50,
            max=150,
            description="Maximum age in years",
        ),
        SimulationParameter(
            name="age_groups",
            type="int",
            default=20,
            min=5,
            max=100,
            description="Number of age groups",
        ),
        SimulationParameter(
            name="t_max",
            type="float",
            default=100.0,
            min=10.0,
            max=500.0,
            description="Maximum simulation time (years)",
        ),
        SimulationParameter(
            name="birth_rate",
            type="float",
            default=0.025,
            min=0.0,
            max=0.1,
            description="Baseline birth rate",
        ),
        SimulationParameter(
            name="carrying_capacity",
            type="float",
            default=1000000.0,
            min=10000.0,
            max=10000000.0,
            description="Carrying capacity",
        ),
        SimulationParameter(
            name="survival_type",
            type="select",
            default="type1",
            options=["type1", "type2", "type3"],
            description="Survival curve type (human/birds/fish)",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.rng = np.random.default_rng()
        self.config: AgeStructuredConfig | None = None
        self.age_bins: np.ndarray = np.array([])
        self.population: np.ndarray = np.array([])
        self.survival_probs: np.ndarray = np.array([])
        self.fertility_rates: np.ndarray = np.array([])
        self.history: list[dict[str, Any]] = []

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if this pattern can simulate the hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()

        keywords = [
            "age structure", "age structured", "demography", "population dynamics",
            "leslie matrix", "mckendrick", "von foerster", "cohort",
            "life table", "survival curve", "fertility", "mortality",
            "generation time", "stable age distribution", "population momentum",
            "demographic transition", "aging population", "youth bulge",
        ]

        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute age-structured simulation"""
        start_time = datetime.now()
        simulation_id = f"age_struct_{start_time.timestamp()}"

        logger.info(f"Starting Age-Structured simulation {simulation_id}")

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
            logger.exception("Age-Structured simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> AgeStructuredConfig:
        """Parse configuration"""
        return AgeStructuredConfig(
            max_age=config.get("max_age", 100),
            age_groups=config.get("age_groups", 20),
            t_max=config.get("t_max", 100.0),
            dt=config.get("dt", 0.1),
            birth_rate=config.get("birth_rate", 0.025),
            carrying_capacity=config.get("carrying_capacity", 1000000.0),
            survival_type=config.get("survival_type", "type1"),
            random_seed=config.get("random_seed"),
        )

    async def _simulate(self, hypothesis: Hypothesis) -> dict[str, Any]:
        """Run age-structured simulation"""
        # Setup age bins
        self.age_bins = np.linspace(0, self.config.max_age, self.config.age_groups + 1)  # type: ignore[union-attr]
        da = self.age_bins[1] - self.age_bins[0]  # Age group width

        # Initialize survival probabilities
        self.survival_probs = self._get_survival_curve()

        # Initialize fertility rates (age-specific)
        self.fertility_rates = self._get_fertility_rates()

        # Initialize population
        if self.config.initial_population is not None:  # type: ignore[union-attr]
            self.population = self.config.initial_population.copy()  # type: ignore[union-attr]
        else:
            # Start with stable distribution
            self.population = self._initial_population()

        self.history = []

        # Time stepping
        n_steps = int(self.config.t_max / self.config.dt)  # type: ignore[union-attr]
        record_interval = max(1, n_steps // 100)

        for step in range(n_steps):
            t = step * self.config.dt  # type: ignore[union-attr]

            # Record
            if step % record_interval == 0:
                self._record(t)

            # Update population
            self._update_population(da)

            if step % 100 == 0:
                await asyncio.sleep(0)

        return self._analyze_results()

    def _get_survival_curve(self) -> np.ndarray:
        """Generate survival probabilities for each age group"""
        n_groups = self.config.age_groups  # type: ignore[union-attr]
        max_age = self.config.max_age  # type: ignore[union-attr]
        ages = np.linspace(0, max_age, n_groups)

        if self.config.survival_type == "type1":  # type: ignore[union-attr]
            # Type I: High survival early, rapid decline late (humans)
            # Gompertz-Makeham model
            a, b, c = 0.001, 0.0001, 0.1
            mortality = a + b * np.exp(c * ages / max_age * 10)
            survival = np.exp(-np.cumsum(mortality) * (max_age / n_groups))

        elif self.config.survival_type == "type2":  # type: ignore[union-attr]
            # Type II: Constant mortality (some birds)
            mortality = np.full(n_groups, 0.02)
            survival = np.exp(-np.cumsum(mortality) * (max_age / n_groups))

        else:  # type3
            # Type III: High mortality early, low late (fish, invertebrates)
            mortality = 0.5 * np.exp(-ages / (max_age * 0.2))
            survival = np.exp(-np.cumsum(mortality) * (max_age / n_groups))

        # Convert to age-group survival probabilities
        surv_probs = np.ones(n_groups)
        for i in range(1, n_groups):
            if survival[i-1] > 0:
                surv_probs[i-1] = survival[i] / survival[i-1]
            else:
                surv_probs[i-1] = 0

        surv_probs[-1] = 0  # No survival past max age
        return surv_probs

    def _get_fertility_rates(self) -> np.ndarray:
        """Generate age-specific fertility rates"""
        n_groups = self.config.age_groups  # type: ignore[union-attr]
        max_age = self.config.max_age  # type: ignore[union-attr]
        np.linspace(0, max_age, n_groups)

        # Human-like fertility curve
        fertility = np.zeros(n_groups)

        # Reproductive ages 15-45
        repro_start = int(15 / max_age * n_groups)
        repro_end = int(45 / max_age * n_groups)

        # Bell-shaped fertility curve
        peak_age = (repro_start + repro_end) // 2
        for i in range(repro_start, min(repro_end, n_groups)):
            fertility[i] = np.exp(-0.5 * ((i - peak_age) / (repro_end - repro_start) * 4)**2)

        # Normalize to match desired birth rate
        if np.sum(fertility) > 0:
            fertility = fertility / np.sum(fertility) * self.config.birth_rate * n_groups  # type: ignore[union-attr]

        return fertility

    def _initial_population(self) -> np.ndarray:
        """Generate initial population distribution"""
        n_groups = self.config.age_groups  # type: ignore[union-attr]

        # Start with exponential age distribution
        ages = np.arange(n_groups)
        pop = np.exp(-ages / (n_groups * 0.3))

        # Scale to carrying capacity
        pop = pop / np.sum(pop) * self.config.carrying_capacity * 0.5  # type: ignore[union-attr]

        return pop  # type: ignore[no-any-return]

    def _update_population(self, da: float) -> None:
        """Update population one time step"""
        n_groups = self.config.age_groups  # type: ignore[union-attr]

        # Calculate births
        births = np.sum(self.fertility_rates * self.population)

        # Density-dependent regulation
        total_pop = np.sum(self.population)
        regulation = max(0, 1 - total_pop / self.config.carrying_capacity)  # type: ignore[union-attr]
        births *= regulation

        # Age progression
        new_pop = np.zeros(n_groups)
        new_pop[0] = births * da  # Newborns

        # Survivors advance to next age group
        for i in range(n_groups - 1):
            new_pop[i + 1] = self.population[i] * self.survival_probs[i]

        self.population = new_pop

    def _record(self, t: float) -> None:
        """Record population state"""
        total = np.sum(self.population)

        # Calculate statistics
        ages = np.arange(self.config.age_groups) * (self.config.max_age / self.config.age_groups)  # type: ignore[union-attr]

        # Mean age
        mean_age = np.sum(ages * self.population) / total if total > 0 else 0

        # Dependency ratio (young + old / working age)
        young = np.sum(self.population[:int(15 / self.config.max_age * self.config.age_groups)])  # type: ignore[union-attr]
        working = np.sum(self.population[int(15 / self.config.max_age * self.config.age_groups):  # type: ignore[union-attr]
                                         int(65 / self.config.max_age * self.config.age_groups)])  # type: ignore[union-attr]
        old = np.sum(self.population[int(65 / self.config.max_age * self.config.age_groups):])  # type: ignore[union-attr]

        dependency_ratio = (young + old) / working if working > 0 else 0

        # Births and deaths this step
        births = self.population[0]
        deaths = total - np.sum(self.population[1:] * self.survival_probs[:-1])

        self.history.append({
            "time": t,
            "total_population": total,
            "mean_age": mean_age,
            "dependency_ratio": dependency_ratio,
            "young": young,
            "working": working,
            "old": old,
            "births": births,
            "deaths": deaths,
        })

    def _analyze_results(self) -> dict[str, Any]:
        """Analyze simulation results"""
        if not self.history:
            return {"metrics": {}, "logs": ["No simulation data"]}

        initial = self.history[0]
        final = self.history[-1]

        # Growth rate
        if initial["total_population"] > 0 and final["time"] > initial["time"]:
            r = np.log(final["total_population"] / initial["total_population"]) / (final["time"] - initial["time"])
        else:
            r = 0

        # Doubling time
        doubling_time = np.log(2) / r if r > 0 else float('inf')

        # Population momentum (ratio of actual to stable)
        stable_ratio = final["total_population"] / self.config.carrying_capacity  # type: ignore[union-attr]

        # Age structure changes
        initial_young_pct = initial["young"] / initial["total_population"] * 100
        final_young_pct = final["young"] / final["total_population"] * 100
        initial_old_pct = initial["old"] / initial["total_population"] * 100
        final_old_pct = final["old"] / final["total_population"] * 100

        metrics = {
            "initial_population": initial["total_population"],
            "final_population": final["total_population"],
            "growth_rate": float(r),
            "doubling_time": float(doubling_time),
            "carrying_capacity": self.config.carrying_capacity,  # type: ignore[union-attr]
            "stable_ratio": float(stable_ratio),
            "mean_age_initial": initial["mean_age"],
            "mean_age_final": final["mean_age"],
            "dependency_ratio_initial": initial["dependency_ratio"],
            "dependency_ratio_final": final["dependency_ratio"],
            "young_pct_change": float(final_young_pct - initial_young_pct),
            "old_pct_change": float(final_old_pct - initial_old_pct),
        }

        logs = [
            f"Age-Structured Population: {self.config.age_groups} age groups",  # type: ignore[union-attr]
            f"Initial population: {metrics['initial_population']:,.0f}",
            f"Final population: {metrics['final_population']:,.0f}",
            f"Growth rate: {r:.4f} per year",
        ]

        if doubling_time != float('inf'):
            logs.append(f"Doubling time: {doubling_time:.1f} years")

        logs.extend([
            f"Mean age: {metrics['mean_age_initial']:.1f} → {metrics['mean_age_final']:.1f}",
            f"Dependency ratio: {metrics['dependency_ratio_initial']:.2f} → {metrics['dependency_ratio_final']:.2f}",
        ])

        if r > 0.01:
            logs.append("Population is growing rapidly")
        elif r < -0.01:
            logs.append("Population is declining")
        else:
            logs.append("Population is near equilibrium")

        return {"metrics": metrics, "logs": logs}

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        if self.config.t_max >= 50:  # type: ignore[union-attr]
            factors.append(0.3)

        if metrics.get("growth_rate", 0) != 0:
            factors.append(0.2)

        if abs(metrics.get("young_pct_change", 0)) > 1:
            factors.append(0.25)

        if self.config.age_groups >= 10:  # type: ignore[union-attr]
            factors.append(0.2)

        return min(0.85, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        params = hypothesis.parameters
        age_groups = params.get("age_groups", 20)
        t_max = params.get("t_max", 100.0)

        estimated_time = age_groups * t_max / 10000

        return {
            "cpu_cores": 1,
            "memory_gb": 0.1,
            "gpu_required": False,
            "estimated_time_seconds": estimated_time,
        }
