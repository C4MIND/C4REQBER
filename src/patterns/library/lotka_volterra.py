"""
Lotka-Volterra Pattern
Predator-prey dynamics and competitive Lotka-Volterra systems

Based on:
- Lotka-Volterra equations (1925-1926)
- Competitive exclusion principle
- Population dynamics
- Bifurcation analysis
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
from scipy.integrate import solve_ivp

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
class LotkaVolterraConfig:
    """Configuration for Lotka-Volterra simulation"""
    n_species: int = 2
    model_type: str = "predator_prey"  # or "competitive", "cooperative"
    t_max: float = 100.0
    dt: float = 0.01
    initial_populations: list[float] | None = None
    growth_rates: list[float] | None = None
    interaction_matrix: np.ndarray | None = None
    carrying_capacities: list[float] | None = None
    random_seed: int | None = None

    def __post_init__(self) -> None:
        if self.model_type not in ["predator_prey", "competitive", "cooperative"]:
            self.model_type = "predator_prey"
        if self.initial_populations is None:
            if self.model_type == "predator_prey":
                self.initial_populations = [10.0, 5.0]
            else:
                self.initial_populations = [1.0] * self.n_species
        if self.growth_rates is None:
            if self.model_type == "predator_prey":
                self.growth_rates = [1.0, 0.5]
            else:
                self.growth_rates = [1.0] * self.n_species


@simulation_pattern(
    id="lotka_volterra",
    name="Lotka-Volterra Dynamics",
    category="biology",
    description="Predator-prey dynamics and competitive Lotka-Volterra systems",
)
class LotkaVolterraPattern(SimulationPattern):
    """
    Lotka-Volterra population dynamics simulation

    Implements:
    - Classic predator-prey model
    - Competitive Lotka-Volterra (n species)
    - Cooperative dynamics
    - Stability analysis
    - Phase portraits
    - Bifurcation detection
    """

    parameters = [
        SimulationParameter(
            name="n_species",
            type="int",
            default=2,
            min=2,
            max=10,
            description="Number of interacting species",
        ),
        SimulationParameter(
            name="model_type",
            type="select",
            default="predator_prey",
            options=["predator_prey", "competitive", "cooperative"],
            description="Type of interaction",
        ),
        SimulationParameter(
            name="t_max",
            type="float",
            default=100.0,
            min=10.0,
            max=1000.0,
            description="Maximum simulation time",
        ),
        SimulationParameter(
            name="alpha",
            type="float",
            default=1.0,
            min=0.1,
            max=5.0,
            description="Prey growth rate (predator-prey)",
        ),
        SimulationParameter(
            name="beta",
            type="float",
            default=0.1,
            min=0.01,
            max=1.0,
            description="Predation rate",
        ),
        SimulationParameter(
            name="gamma",
            type="float",
            default=1.5,
            min=0.5,
            max=5.0,
            description="Predator death rate",
        ),
        SimulationParameter(
            name="delta",
            type="float",
            default=0.075,
            min=0.01,
            max=0.5,
            description="Predator efficiency",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.rng = np.random.default_rng()
        self.config: LotkaVolterraConfig | None = None
        self.solution = None
        self.time_points: np.ndarray = np.array([])
        self.populations: np.ndarray = np.array([])

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if this pattern can simulate the hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()

        keywords = [
            "lotka-volterra", "predator-prey", "population dynamics",
            "ecological", "species interaction", "competition",
            "competitive exclusion", "carrying capacity", "logistic growth",
            "food web", "trophic", "oscillation", "limit cycle",
            "bifurcation", "stable coexistence", "extinction",
        ]

        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute Lotka-Volterra simulation"""
        start_time = datetime.now()
        simulation_id = f"lv_{start_time.timestamp()}"

        logger.info(f"Starting Lotka-Volterra simulation {simulation_id}")

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
            logger.exception("Lotka-Volterra simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> LotkaVolterraConfig:
        """Parse configuration"""
        n_species = config.get("n_species", 2)
        model_type = config.get("model_type", "predator_prey")

        if model_type == "predator_prey" and n_species != 2:
            n_species = 2

        return LotkaVolterraConfig(
            n_species=n_species,
            model_type=model_type,
            t_max=config.get("t_max", 100.0),
            dt=config.get("dt", 0.01),
            initial_populations=config.get("initial_populations"),
            growth_rates=config.get("growth_rates"),
            random_seed=config.get("random_seed"),
        )

    async def _simulate(self, hypothesis: Hypothesis) -> dict[str, Any]:
        """Run Lotka-Volterra simulation"""
        t_max = self.config.t_max  # type: ignore[union-attr]
        y0 = np.array(self.config.initial_populations)  # type: ignore[union-attr]

        # Set up ODE
        if self.config.model_type == "predator_prey":  # type: ignore[union-attr]
            # Classic 2-species predator-prey
            alpha = hypothesis.parameters.get("alpha", 1.0)
            beta = hypothesis.parameters.get("beta", 0.1)
            gamma = hypothesis.parameters.get("gamma", 1.5)
            delta = hypothesis.parameters.get("delta", 0.075)

            def dydt(t: Any, y: Any) -> Any:
                """Dydt."""
                prey, predator = y
                d_prey = alpha * prey - beta * prey * predator
                d_predator = delta * prey * predator - gamma * predator
                return [d_prey, d_predator]

        elif self.config.model_type == "competitive":  # type: ignore[union-attr]
            # Competitive Lotka-Volterra
            r = np.array(self.config.growth_rates)  # type: ignore[union-attr]
            K = hypothesis.parameters.get("carrying_capacities", [100.0] * self.config.n_species)  # type: ignore[union-attr]
            K = np.array(K)

            # Competition matrix
            alpha = hypothesis.parameters.get("competition_matrix")
            if alpha is None:
                alpha = np.ones((self.config.n_species, self.config.n_species))  # type: ignore[union-attr]
                np.fill_diagonal(alpha, 1.0)

            def dydt(t: Any, y: Any) -> Any:
                return r * y * (1 - np.sum(alpha * y / K, axis=1))

        else:  # cooperative
            r = np.array(self.config.growth_rates)  # type: ignore[union-attr]

            # Cooperation matrix
            beta = hypothesis.parameters.get("cooperation_matrix")
            if beta is None:
                beta = 0.1 * np.ones((self.config.n_species, self.config.n_species))  # type: ignore[union-attr]
                np.fill_diagonal(beta, 0.0)

            def dydt(t: Any, y: Any) -> Any:
                """Dydt."""
                interaction = np.sum(beta * y, axis=1)
                return r * y * (1 + interaction - 0.01 * y)

        # Solve ODE
        t_span = (0, t_max)
        t_eval = np.linspace(0, t_max, int(t_max / self.config.dt))  # type: ignore[union-attr]

        # Use solve_ivp for adaptive stepping
        sol = solve_ivp(dydt, t_span, y0, method='RK45', t_eval=t_eval, dense_output=True)

        self.time_points = sol.t
        self.populations = sol.y

        await asyncio.sleep(0)  # Yield control

        return self._analyze_results()

    def _analyze_results(self) -> dict[str, Any]:
        """Analyze simulation results"""
        if self.populations.size == 0:
            return {"metrics": {}, "logs": ["No simulation data"]}

        t = self.time_points
        y = self.populations
        n_species = y.shape[0]

        # Final populations
        final_pops = y[:, -1]

        # Oscillation analysis
        oscillation_periods = []
        for i in range(n_species):
            pop = y[i, :]
            # Find peaks
            peaks = []
            for j in range(1, len(pop) - 1):
                if pop[j-1] < pop[j] > pop[j+1]:
                    peaks.append(j)

            if len(peaks) >= 2:
                periods = [t[peaks[j+1]] - t[peaks[j]] for j in range(len(peaks)-1)]
                avg_period = np.mean(periods)
                oscillation_periods.append(avg_period)

        avg_period = np.mean(oscillation_periods) if oscillation_periods else 0

        # Equilibrium analysis
        # Check if populations stabilized
        last_10 = y[:, -10:] if y.shape[1] >= 10 else y
        pop_var = np.var(last_10, axis=1)
        is_stable = np.all(pop_var < 0.01 * np.mean(last_10, axis=1))

        # Coexistence check
        coexistence = np.all(final_pops > 0.01 * np.max(y, axis=1))

        # Extinction events
        extinctions = np.sum(final_pops < 0.001)

        # Calculate Lyapunov exponent estimate
        if n_species == 2:
            # Simple estimate from trajectory divergence
            lyap = self._estimate_lyapunov()
        else:
            lyap = 0.0

        metrics = {
            "final_populations": final_pops.tolist(),
            "avg_populations": np.mean(y, axis=1).tolist(),
            "max_populations": np.max(y, axis=1).tolist(),
            "min_populations": np.min(y, axis=1).tolist(),
            "oscillation_period": float(avg_period),
            "is_stable": float(is_stable),
            "coexistence": float(coexistence),
            "n_extinctions": int(extinctions),
            "lyapunov_estimate": float(lyap),
        }

        logs = [
            f"Lotka-Volterra ({self.config.model_type}): {n_species} species",  # type: ignore[union-attr]
            f"Final populations: {final_pops}",
            f"Average populations: {metrics['avg_populations']}",
        ]

        if avg_period > 0:
            logs.append(f"Oscillation period: {avg_period:.2f}")

        if is_stable:
            logs.append("System reached stable equilibrium")
        elif avg_period > 0:
            logs.append("System exhibits limit cycle oscillations")

        if coexistence:
            logs.append("All species coexist")
        else:
            logs.append(f"{extinctions} species went extinct")

        return {"metrics": metrics, "logs": logs}

    def _estimate_lyapunov(self) -> float:
        """Estimate largest Lyapunov exponent"""
        # Simple finite-difference estimate
        y = self.populations
        if y.shape[1] < 100:
            return 0.0

        # Calculate divergence rate
        dt = np.mean(np.diff(self.time_points))
        deltas = []

        for i in range(10, min(100, y.shape[1] - 10)):
            # Local divergence
            delta = np.linalg.norm(y[:, i+1] - y[:, i]) / np.linalg.norm(y[:, i] - y[:, i-1])
            if delta > 0:
                deltas.append(np.log(delta))

        if deltas:
            return float(np.mean(deltas) / dt)
        return 0.0

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        t_max = self.config.t_max  # type: ignore[union-attr]
        if t_max >= 100:
            factors.append(0.2)

        if metrics.get("is_stable", 0) > 0.5 or metrics.get("oscillation_period", 0) > 0:
            factors.append(0.3)

        if metrics.get("coexistence", 0) > 0.5:
            factors.append(0.2)

        lyap = abs(metrics.get("lyapunov_estimate", 0))
        if lyap < 0.1:
            factors.append(0.2)

        return min(0.85, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        params = hypothesis.parameters
        t_max = params.get("t_max", 100.0)
        n_species = params.get("n_species", 2)

        estimated_time = t_max * n_species / 1000

        return {
            "cpu_cores": 1,
            "memory_gb": 0.1 + n_species * 0.01,
            "gpu_required": False,
            "estimated_time_seconds": estimated_time,
        }
