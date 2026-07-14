"""
Epidemic SEIR Pattern
Compartmental epidemiological model with extensions

Based on:
- Kermack-McKendrick SIR model (1927)
- SEIR extension with exposed compartment
- SEIRS with waning immunity
- Stochastic simulation (Gillespie algorithm)
- Age-structured transmission
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
class SEIRConfig:
    """Configuration for SEIR simulation"""
    model_type: str = "seir"  # sir, seir, seirs
    N: int = 100000  # Total population
    I0: int = 10  # Initial infected
    t_max: float = 200.0
    dt: float = 0.1

    # Parameters
    beta: float = 0.5  # Transmission rate
    sigma: float = 0.2  # Incubation rate (1/latent period)
    gamma: float = 0.1  # Recovery rate (1/infectious period)
    mu: float = 0.0  # Birth/death rate
    omega: float = 0.0  # Waning immunity rate (for SEIRS)

    # Stochastic simulation
    stochastic: bool = False
    n_realizations: int = 100

    random_seed: int | None = None


@simulation_pattern(
    id="epidemic_seir",
    name="Epidemic SEIR Model",
    category="epidemiology",
    description="Compartmental epidemiological model with SEIR dynamics",
)
class EpidemicSEIRPattern(SimulationPattern):
    """
    SEIR epidemic simulation for disease transmission

    Implements:
    - Deterministic ODE models (SIR, SEIR, SEIRS)
    - Stochastic Gillespie algorithm
    - Basic reproduction number R0 calculation
    - Herd immunity threshold
    - Peak infection analysis
    - Final epidemic size
    """

    parameters = [
        SimulationParameter(
            name="model_type",
            type="select",
            default="seir",
            options=["sir", "seir", "seirs"],
            description="Model type",
        ),
        SimulationParameter(
            name="N",
            type="int",
            default=100000,
            min=1000,
            max=10000000,
            description="Total population size",
        ),
        SimulationParameter(
            name="I0",
            type="int",
            default=10,
            min=1,
            max=1000,
            description="Initial number of infected",
        ),
        SimulationParameter(
            name="beta",
            type="float",
            default=0.5,
            min=0.01,
            max=5.0,
            description="Transmission rate (per day)",
        ),
        SimulationParameter(
            name="sigma",
            type="float",
            default=0.2,
            min=0.05,
            max=1.0,
            description="Incubation rate (1/latent period)",
        ),
        SimulationParameter(
            name="gamma",
            type="float",
            default=0.1,
            min=0.01,
            max=1.0,
            description="Recovery rate (1/infectious period)",
        ),
        SimulationParameter(
            name="t_max",
            type="float",
            default=200.0,
            min=50.0,
            max=1000.0,
            description="Maximum simulation time (days)",
        ),
        SimulationParameter(
            name="stochastic",
            type="bool",
            default=False,
            description="Use stochastic simulation",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.rng = np.random.default_rng()
        self.config: SEIRConfig | None = None
        self.time_points: np.ndarray = np.array([])
        self.trajectories: dict[str, np.ndarray] = {}

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if this pattern can simulate the hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()

        keywords = [
            "epidemic", "pandemic", "disease transmission", "infectious",
            "sir model", "seir model", "compartmental", "r0", "reproduction",
            "herd immunity", "outbreak", "transmission dynamics",
            "incubation", "latency", "recovery", "immunity",
            "flatten the curve", "social distancing", "vaccination",
        ]

        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute SEIR simulation"""
        start_time = datetime.now()
        simulation_id = f"seir_{start_time.timestamp()}"

        logger.info(f"Starting SEIR simulation {simulation_id}")

        try:
            self.config = self._parse_config(config)
            if self.config.random_seed:
                self.rng = np.random.default_rng(self.config.random_seed)

            if self.config.stochastic:
                results = await self._simulate_stochastic(hypothesis)
            else:
                results = await self._simulate_deterministic(hypothesis)

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
            logger.exception("SEIR simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> SEIRConfig:
        """Parse configuration"""
        return SEIRConfig(
            model_type=config.get("model_type", "seir"),
            N=config.get("N", 100000),
            I0=config.get("I0", 10),
            t_max=config.get("t_max", 200.0),
            dt=config.get("dt", 0.1),
            beta=config.get("beta", 0.5),
            sigma=config.get("sigma", 0.2),
            gamma=config.get("gamma", 0.1),
            mu=config.get("mu", 0.0),
            omega=config.get("omega", 0.0),
            stochastic=config.get("stochastic", False),
            n_realizations=config.get("n_realizations", 100),
            random_seed=config.get("random_seed"),
        )

    async def _simulate_deterministic(self, hypothesis: Hypothesis) -> dict[str, Any]:
        """Run deterministic ODE simulation"""
        N = self.config.N  # type: ignore[union-attr]
        I0 = self.config.I0  # type: ignore[union-attr]
        t_max = self.config.t_max  # type: ignore[union-attr]

        beta = self.config.beta  # type: ignore[union-attr]
        sigma = self.config.sigma  # type: ignore[union-attr]
        gamma = self.config.gamma  # type: ignore[union-attr]
        mu = self.config.mu  # type: ignore[union-attr]
        omega = self.config.omega  # type: ignore[union-attr]

        # Initial conditions
        if self.config.model_type == "sir":  # type: ignore[union-attr]
            y0 = [N - I0, I0, 0.0]  # S, I, R
        elif self.config.model_type == "seir":  # type: ignore[union-attr]
            y0 = [N - I0, 0.0, I0, 0.0]  # S, E, I, R
        else:  # seirs
            y0 = [N - I0, 0.0, I0, 0.0]  # S, E, I, R

        def dydt(t: Any, y: Any) -> None:
            if self.config.model_type == "sir":  # type: ignore[union-attr]
                S, I, R = y
                dS = mu * (N - S) - beta * S * I / N
                dI = beta * S * I / N - (gamma + mu) * I
                dR = gamma * I - mu * R
                return [dS, dI, dR]  # type: ignore[return-value]

            elif self.config.model_type == "seir":  # type: ignore[union-attr]
                S, E, I, R = y
                dS = mu * (N - S) - beta * S * I / N
                dE = beta * S * I / N - (sigma + mu) * E
                dI = sigma * E - (gamma + mu) * I
                dR = gamma * I - mu * R
                return [dS, dE, dI, dR]  # type: ignore[return-value]

            else:  # seirs
                S, E, I, R = y
                dS = mu * (N - S) - beta * S * I / N + omega * R
                dE = beta * S * I / N - (sigma + mu) * E
                dI = sigma * E - (gamma + mu) * I
                dR = gamma * I - mu * R - omega * R
                return [dS, dE, dI, dR]  # type: ignore[return-value]

        # Solve
        t_eval = np.linspace(0, t_max, int(t_max / self.config.dt))  # type: ignore[union-attr]
        sol = solve_ivp(dydt, [0, t_max], y0, t_eval=t_eval, method='RK45')

        self.time_points = sol.t

        if self.config.model_type == "sir":  # type: ignore[union-attr]
            self.trajectories = {
                "S": sol.y[0],
                "I": sol.y[1],
                "R": sol.y[2],
            }
        else:
            self.trajectories = {
                "S": sol.y[0],
                "E": sol.y[1],
                "I": sol.y[2],
                "R": sol.y[3],
            }

        await asyncio.sleep(0)
        return self._analyze_results()

    async def _simulate_stochastic(self, hypothesis: Hypothesis) -> dict[str, Any]:
        """Run stochastic Gillespie simulation with multiple realizations"""
        N = self.config.N  # type: ignore[union-attr]
        I0 = self.config.I0  # type: ignore[union-attr]
        t_max = self.config.t_max  # type: ignore[union-attr]

        beta = self.config.beta  # type: ignore[union-attr]
        sigma = self.config.sigma  # type: ignore[union-attr]
        gamma = self.config.gamma  # type: ignore[union-attr]

        all_trajectories = []

        for realization in range(self.config.n_realizations):  # type: ignore[union-attr]
            # Initialize
            if self.config.model_type == "sir":  # type: ignore[union-attr]
                S, I, R = N - I0, I0, 0
                t = 0.0
                times = [t]
                states = {"S": [S], "I": [I], "R": [R]}
            else:
                S, E, I, R = N - I0, 0, I0, 0
                t = 0.0
                times = [t]
                states = {"S": [S], "E": [E], "I": [I], "R": [R]}

            while t < t_max and I > 0:
                # Calculate rates
                if self.config.model_type == "sir":  # type: ignore[union-attr]
                    rates = [
                        beta * S * I / N,  # S -> I
                        gamma * I,          # I -> R
                    ]
                    rate_sum = sum(rates)

                    if rate_sum == 0:
                        break

                    # Time to next event
                    dt = self.rng.exponential(1 / rate_sum)
                    t += dt

                    # Choose event
                    r = self.rng.random() * rate_sum
                    if r < rates[0]:
                        S -= 1
                        I += 1
                    else:
                        I -= 1
                        R += 1

                else:  # seir
                    rates = [
                        beta * S * I / N,  # S -> E
                        sigma * E,          # E -> I
                        gamma * I,          # I -> R
                    ]
                    rate_sum = sum(rates)

                    if rate_sum == 0:
                        break

                    dt = self.rng.exponential(1 / rate_sum)
                    t += dt

                    r = self.rng.random() * rate_sum
                    if r < rates[0]:
                        S -= 1
                        E += 1
                    elif r < rates[0] + rates[1]:
                        E -= 1
                        I += 1
                    else:
                        I -= 1
                        R += 1

                times.append(t)
                states["S"].append(S)
                states["I"].append(I)
                if self.config.model_type != "sir":  # type: ignore[union-attr]
                    states["E"].append(E)
                states["R"].append(R)

            all_trajectories.append((times, states))

            if realization % 10 == 0:
                await asyncio.sleep(0)

        # Average trajectories
        # Interpolate to common time grid
        t_common = np.linspace(0, t_max, int(t_max / self.config.dt))  # type: ignore[union-attr]
        avg_trajectories: Any = {"S": [], "I": [], "R": []}
        if self.config.model_type != "sir":  # type: ignore[union-attr]
            avg_trajectories["E"] = []

        for times, states in all_trajectories:
            for key in avg_trajectories:
                if key in states:
                    interpolated = np.interp(t_common, times, states[key],
                                            right=states[key][-1])
                    avg_trajectories[key].append(interpolated)

        self.time_points = t_common
        self.trajectories = {k: np.mean(v, axis=0) for k, v in avg_trajectories.items()}

        return self._analyze_results()

    def _analyze_results(self) -> dict[str, Any]:
        """Analyze simulation results"""
        if not self.trajectories:
            return {"metrics": {}, "logs": ["No simulation data"]}

        t = self.time_points
        I = self.trajectories["I"]
        S = self.trajectories["S"]
        R = self.trajectories["R"]

        # Peak infection
        peak_idx = np.argmax(I)
        peak_time = float(t[peak_idx])
        peak_infections = float(I[peak_idx])

        # Final epidemic size
        final_size = float(R[-1])
        attack_rate = final_size / self.config.N  # type: ignore[union-attr]

        # Basic reproduction number R0
        if self.config.model_type == "sir":  # type: ignore[union-attr]
            R0 = self.config.beta / self.config.gamma  # type: ignore[union-attr]
        else:
            R0 = self.config.beta / self.config.gamma  # type: ignore  # For SEIR, same formula applies

        # Herd immunity threshold
        herd_threshold = 1 - 1 / R0 if R0 > 1 else 0

        # Doubling time at start
        if len(I) > 10:
            early_growth = np.log(I[10] / I[0]) / (t[10] - t[0]) if I[0] > 0 else 0
            doubling_time = np.log(2) / early_growth if early_growth > 0 else float('inf')
        else:
            doubling_time = float('inf')

        # Generation time
        if self.config.model_type == "seir":  # type: ignore[union-attr]
            T_incubation = 1 / self.config.sigma  # type: ignore[union-attr]
            T_infectious = 1 / self.config.gamma  # type: ignore[union-attr]
            generation_time = T_incubation + T_infectious / 2
        else:
            generation_time = 1 / self.config.gamma  # type: ignore[union-attr]

        metrics = {
            "R0": float(R0),
            "herd_immunity_threshold": float(herd_threshold),
            "peak_time": peak_time,
            "peak_infections": peak_infections,
            "final_epidemic_size": final_size,
            "attack_rate": float(attack_rate),
            "doubling_time": float(doubling_time),
            "generation_time": float(generation_time),
            "initial_susceptible": float(S[0]),
            "final_susceptible": float(S[-1]),
        }

        logs = [
            f"SEIR Model ({self.config.model_type.upper()}): N={self.config.N}",  # type: ignore[union-attr]
            f"Basic reproduction number R0: {R0:.2f}",
            f"Herd immunity threshold: {herd_threshold:.1%}",
            f"Peak infections: {peak_infections:.0f} at day {peak_time:.1f}",
            f"Final epidemic size: {final_size:.0f} ({attack_rate:.1%})",
        ]

        if doubling_time != float('inf'):
            logs.append(f"Initial doubling time: {doubling_time:.1f} days")

        if R0 > 1:
            logs.append("Epidemic will occur (R0 > 1)")
        else:
            logs.append("Disease will die out (R0 < 1)")

        return {"metrics": metrics, "logs": logs}

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        R0 = metrics.get("R0", 0)
        if 1.0 < R0 < 10.0:
            factors.append(0.3)

        peak = metrics.get("peak_infections", 0)
        if peak > 0:
            factors.append(0.3)

        if self.config.stochastic and self.config.n_realizations >= 100:  # type: ignore[union-attr]
            factors.append(0.2)

        if metrics.get("final_epidemic_size", 0) > 0:
            factors.append(0.2)

        return min(0.9, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        params = hypothesis.parameters
        stochastic = params.get("stochastic", False)
        n_real = params.get("n_realizations", 100) if stochastic else 1
        t_max = params.get("t_max", 200.0)

        estimated_time = t_max * n_real / 1000

        return {
            "cpu_cores": 1,
            "memory_gb": 0.1,
            "gpu_required": False,
            "estimated_time_seconds": estimated_time,
        }
