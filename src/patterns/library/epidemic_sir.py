"""
SIR Epidemic Model Pattern
Simplified epidemic model (compartmental)

Based on:
- Kermack-McKendrick SIR model
- Basic reproduction number R0
- Herd immunity threshold
- Peak infection timing
"""

from __future__ import annotations

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
class SIRConfig:
    """Configuration for SIR model"""
    N: float = 1000000.0      # Total population
    I0: float = 1.0           # Initial infected
    R0: float = 0.0           # Initial recovered
    beta: float = 0.3         # Infection rate (per day)
    gamma: float = 0.1        # Recovery rate (per day)
    t_max: float = 160.0      # Simulation time (days)
    dt: float = 0.1           # Time step


@simulation_pattern(
    id="epidemic_sir",
    name="SIR Epidemic Model",
    category="biology",
    description="SIR compartmental epidemic model with R0 analysis",
)
class SIREpidemicPattern(SimulationPattern):
    """
    SIR epidemic model simulation

    Implements:
    - SIR differential equations
    - Basic reproduction number R0 = beta / gamma
    - Herd immunity threshold
    - Peak infection timing and magnitude
    - Final epidemic size
    """

    parameters = [
        SimulationParameter(
            name="N",
            type="float",
            default=1000000.0,
            min=1000.0,
            max=1e9,
            description="Total population",
        ),
        SimulationParameter(
            name="I0",
            type="float",
            default=1.0,
            min=1.0,
            max=10000.0,
            description="Initial infected",
        ),
        SimulationParameter(
            name="beta",
            type="float",
            default=0.3,
            min=0.01,
            max=2.0,
            description="Infection rate (per day)",
        ),
        SimulationParameter(
            name="gamma",
            type="float",
            default=0.1,
            min=0.01,
            max=1.0,
            description="Recovery rate (per day)",
        ),
        SimulationParameter(
            name="t_max",
            type="float",
            default=160.0,
            min=10.0,
            max=1000.0,
            description="Simulation time (days)",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config: SIRConfig = SIRConfig()

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if SIR can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        keywords = [
            "sir model", "epidemic", "infectious disease", "r0",
            "basic reproduction", "herd immunity", "outbreak",
            "compartmental model", "susceptible", "infected", "recovered",
            "pandemic", "transmission",
        ]
        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute SIR simulation"""
        start_time = datetime.now()
        simulation_id = f"sir_{start_time.timestamp()}"
        logger.info(f"Starting SIR simulation {simulation_id}")

        try:
            self.config = self._parse_config(config)
            results = await self._simulate_sir()
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
            logger.exception("SIR simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> SIRConfig:
        """Parse configuration dict"""
        cfg = SIRConfig()
        if "N" in config:
            cfg.N = float(config["N"])
        if "I0" in config:
            cfg.I0 = float(config["I0"])
        if "R0" in config:
            cfg.R0 = float(config["R0"])
        if "beta" in config:
            cfg.beta = float(config["beta"])
        if "gamma" in config:
            cfg.gamma = float(config["gamma"])
        if "t_max" in config:
            cfg.t_max = float(config["t_max"])
        if "dt" in config:
            cfg.dt = float(config["dt"])
        return cfg

    async def _simulate_sir(self) -> dict[str, Any]:
        """Run SIR simulation"""
        cfg = self.config
        N = cfg.N
        beta = cfg.beta
        gamma = cfg.gamma

        # Initial conditions
        S0 = N - cfg.I0 - cfg.R0
        I0 = cfg.I0
        R0_init = cfg.R0

        # Basic reproduction number
        R0 = beta / gamma

        # Herd immunity threshold
        herd_immunity = 1 - 1 / R0 if R0 > 1 else 0.0

        def equations(t: float, y: np.ndarray) -> np.ndarray:
            """SIR equations"""
            S, I, R = y
            dSdt = -beta * S * I / N
            dIdt = beta * S * I / N - gamma * I
            dRdt = gamma * I
            return np.array([dSdt, dIdt, dRdt])

        y0 = np.array([S0, I0, R0_init])
        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)

        sol = solve_ivp(equations, t_span, y0, t_eval=t_eval, method='RK45')
        t = sol.t
        S, I, R = sol.y

        # Find peak infection
        peak_idx = np.argmax(I)
        peak_infections = I[peak_idx]
        peak_time = t[peak_idx]

        # Final epidemic size
        final_size = R[-1]
        attack_rate = final_size / N

        # Doubling time (early epidemic)
        early_I = I[I > 0][:10]
        if len(early_I) >= 2:
            growth_rate = np.mean(np.diff(np.log(early_I)))
            doubling_time = np.log(2) / growth_rate if growth_rate > 0 else float('inf')
        else:
            doubling_time = float('inf')

        # Generation time
        generation_time = 1 / gamma

        metrics = {
            "R0": float(R0),
            "herd_immunity_threshold": float(herd_immunity),
            "peak_infections": float(peak_infections),
            "peak_time_days": float(peak_time),
            "final_epidemic_size": float(final_size),
            "attack_rate": float(attack_rate),
            "doubling_time_days": float(doubling_time) if doubling_time != float('inf') else -1.0,
            "generation_time_days": float(generation_time),
            "susceptible_at_end": float(S[-1]),
            "recovered_at_end": float(R[-1]),
        }

        logs = [
            f"SIR model: N={N:.0f}, beta={beta}, gamma={gamma}",
            f"R0 = {R0:.2f}",
            f"Herd immunity threshold: {herd_immunity*100:.1f}%",
            f"Peak infections: {peak_infections:.0f} at day {peak_time:.1f}",
            f"Final epidemic size: {final_size:.0f} ({attack_rate*100:.1f}%)",
            f"Generation time: {generation_time:.1f} days",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "S": S.tolist(),
            "I": I.tolist(),
            "R": R.tolist(),
        }

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        # R0 > 0
        if metrics.get("R0", 0) > 0:
            factors.append(0.2)

        # Peak exists for R0 > 1
        if metrics.get("R0", 0) > 1 and metrics.get("peak_infections", 0) > 0:
            factors.append(0.3)

        # Attack rate < 100%
        if 0 < metrics.get("attack_rate", 0) < 1:
            factors.append(0.2)

        # Herd immunity threshold valid
        if 0 <= metrics.get("herd_immunity_threshold", -1) <= 1:
            factors.append(0.2)

        # Generation time positive
        if metrics.get("generation_time_days", 0) > 0:
            factors.append(0.1)

        return min(0.9, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        params = hypothesis.parameters
        t_max = params.get("t_max", 160.0)
        return {
            "cpu_cores": 1,
            "memory_gb": 0.1,
            "gpu_required": False,
            "estimated_time_seconds": t_max / 1000,
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
                "Kermack, W.O. & McKendrick, A.G. (1927). Contributions to the mathematical theory of epidemics",
            ],
        }
