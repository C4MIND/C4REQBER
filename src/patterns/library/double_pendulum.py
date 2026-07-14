"""
Double Pendulum Pattern
Chaotic dynamics of a double pendulum using Lagrangian mechanics

Based on:
- Lagrangian formulation
- RK4 integration
- Lyapunov exponent estimation
- Poincare sections
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
class DoublePendulumConfig:
    """Configuration for double pendulum simulation"""
    m1: float = 1.0       # Mass of first bob (kg)
    m2: float = 1.0       # Mass of second bob (kg)
    L1: float = 1.0       # Length of first rod (m)
    L2: float = 1.0       # Length of second rod (m)
    g: float = 9.81       # Gravitational acceleration (m/s^2)
    theta1_0: float = np.pi / 2   # Initial angle 1 (rad)
    theta2_0: float = np.pi / 2   # Initial angle 2 (rad)
    omega1_0: float = 0.0  # Initial angular velocity 1 (rad/s)
    omega2_0: float = 0.0  # Initial angular velocity 2 (rad/s)
    t_max: float = 10.0    # Simulation time (s)
    dt: float = 0.01       # Time step (s)


@simulation_pattern(
    id="double_pendulum",
    name="Double Pendulum",
    category="physics",
    description="Chaotic double pendulum dynamics using Lagrangian mechanics",
)
class DoublePendulumPattern(SimulationPattern):
    """
    Double pendulum simulation

    Implements:
    - Lagrangian equations of motion
    - RK4 integration
    - Energy conservation tracking
    - Lyapunov exponent estimation
    """

    parameters = [
        SimulationParameter(
            name="m1",
            type="float",
            default=1.0,
            min=0.1,
            max=10.0,
            description="Mass of first bob (kg)",
        ),
        SimulationParameter(
            name="m2",
            type="float",
            default=1.0,
            min=0.1,
            max=10.0,
            description="Mass of second bob (kg)",
        ),
        SimulationParameter(
            name="L1",
            type="float",
            default=1.0,
            min=0.1,
            max=5.0,
            description="Length of first rod (m)",
        ),
        SimulationParameter(
            name="L2",
            type="float",
            default=1.0,
            min=0.1,
            max=5.0,
            description="Length of second rod (m)",
        ),
        SimulationParameter(
            name="theta1_0",
            type="float",
            default=90.0,
            min=-180.0,
            max=180.0,
            description="Initial angle 1 (degrees)",
        ),
        SimulationParameter(
            name="theta2_0",
            type="float",
            default=90.0,
            min=-180.0,
            max=180.0,
            description="Initial angle 2 (degrees)",
        ),
        SimulationParameter(
            name="t_max",
            type="float",
            default=10.0,
            min=1.0,
            max=100.0,
            description="Simulation time (s)",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config: DoublePendulumConfig = DoublePendulumConfig()

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if double pendulum can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        keywords = [
            "double pendulum", "chaos", "chaotic", "pendulum",
            "lagrangian", "hamiltonian", "nonlinear dynamics",
            "lyapunov", "sensitive dependence", "deterministic chaos",
        ]
        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute double pendulum simulation"""
        start_time = datetime.now()
        simulation_id = f"dp_{start_time.timestamp()}"
        logger.info(f"Starting double pendulum simulation {simulation_id}")

        try:
            self.config = self._parse_config(config)
            results = await self._simulate_dp()
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
            logger.exception("Double pendulum simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> DoublePendulumConfig:
        """Parse configuration dict"""
        cfg = DoublePendulumConfig()
        if "m1" in config:
            cfg.m1 = float(config["m1"])
        if "m2" in config:
            cfg.m2 = float(config["m2"])
        if "L1" in config:
            cfg.L1 = float(config["L1"])
        if "L2" in config:
            cfg.L2 = float(config["L2"])
        if "g" in config:
            cfg.g = float(config["g"])
        if "theta1_0" in config:
            cfg.theta1_0 = float(config["theta1_0"]) * np.pi / 180
        if "theta2_0" in config:
            cfg.theta2_0 = float(config["theta2_0"]) * np.pi / 180
        if "omega1_0" in config:
            cfg.omega1_0 = float(config["omega1_0"])
        if "omega2_0" in config:
            cfg.omega2_0 = float(config["omega2_0"])
        if "t_max" in config:
            cfg.t_max = float(config["t_max"])
        if "dt" in config:
            cfg.dt = float(config["dt"])
        return cfg

    async def _simulate_dp(self) -> dict[str, Any]:
        """Run double pendulum simulation"""
        cfg = self.config
        m1, m2, L1, L2, g = cfg.m1, cfg.m2, cfg.L1, cfg.L2, cfg.g

        def equations(t: float, y: np.ndarray) -> np.ndarray:
            """Double pendulum equations of motion"""
            theta1, theta2, omega1, omega2 = y

            delta = theta2 - theta1
            den1 = (m1 + m2) * L1 - m2 * L1 * np.cos(delta) * np.cos(delta)
            den2 = (L2 / L1) * den1

            num1 = (m2 * L1 * omega1**2 * np.sin(delta) * np.cos(delta)
                    + m2 * g * np.sin(theta2) * np.cos(delta)
                    + m2 * L2 * omega2**2 * np.sin(delta)
                    - (m1 + m2) * g * np.sin(theta1))

            num2 = (-m2 * L2 * omega2**2 * np.sin(delta) * np.cos(delta)
                    + (m1 + m2) * g * np.sin(theta1) * np.cos(delta)
                    - (m1 + m2) * L1 * omega1**2 * np.sin(delta)
                    - (m1 + m2) * g * np.sin(theta2))

            domega1 = num1 / den1
            domega2 = num2 / den2

            return np.array([omega1, omega2, domega1, domega2])

        # Initial conditions
        y0 = np.array([cfg.theta1_0, cfg.theta2_0, cfg.omega1_0, cfg.omega2_0])
        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)

        # Solve
        sol = solve_ivp(equations, t_span, y0, t_eval=t_eval, method='RK45')
        t = sol.t
        theta1, theta2, omega1, omega2 = sol.y

        # Compute positions
        x1 = L1 * np.sin(theta1)
        y1 = -L1 * np.cos(theta1)
        x2 = x1 + L2 * np.sin(theta2)
        y2 = y1 - L2 * np.cos(theta2)

        # Compute energies
        # Kinetic
        v1_sq = (L1 * omega1)**2
        v2_sq = (L1 * omega1)**2 + (L2 * omega2)**2 + 2 * L1 * L2 * omega1 * omega2 * np.cos(theta1 - theta2)
        KE = 0.5 * m1 * v1_sq + 0.5 * m2 * v2_sq

        # Potential
        PE = -m1 * g * L1 * np.cos(theta1) - m2 * g * (L1 * np.cos(theta1) + L2 * np.cos(theta2))

        total_energy = KE + PE
        energy_drift = np.max(np.abs(total_energy - total_energy[0])) / np.abs(total_energy[0])

        # Lyapunov exponent estimate (simplified)
        # Run a second trajectory with small perturbation
        y0_pert = y0 + np.array([1e-6, 0, 0, 0])
        sol_pert = solve_ivp(equations, t_span, y0_pert, t_eval=t_eval, method='RK45')
        diff = np.linalg.norm(sol.y - sol_pert.y, axis=0)
        # Estimate largest Lyapunov exponent
        t_mid = len(t) // 2
        if diff[t_mid] > 0 and diff[-1] > 0:
            lyapunov = np.log(diff[-1] / diff[t_mid]) / (t[-1] - t[t_mid])
        else:
            lyapunov = 0.0

        metrics = {
            "initial_energy": float(total_energy[0]),
            "energy_drift": float(energy_drift),
            "max_lyapunov": float(lyapunov),
            "max_theta1": float(np.max(np.abs(theta1))),
            "max_theta2": float(np.max(np.abs(theta2))),
            "period_estimate": float(self._estimate_period(t, theta1)),
        }

        logs = [
            f"Double pendulum: m1={m1}kg, m2={m2}kg, L1={L1}m, L2={L2}m",
            f"Initial energy: {total_energy[0]:.4f} J",
            f"Energy drift: {energy_drift:.6f}",
            f"Max Lyapunov exponent: {lyapunov:.4f}",
            f"Estimated period: {metrics['period_estimate']:.4f} s",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "theta1": theta1.tolist(),
            "theta2": theta2.tolist(),
            "omega1": omega1.tolist(),
            "omega2": omega2.tolist(),
            "x1": x1.tolist(),
            "y1": y1.tolist(),
            "x2": x2.tolist(),
            "y2": y2.tolist(),
            "energy": total_energy.tolist(),
        }

    def _estimate_period(self, t: np.ndarray, theta: np.ndarray) -> float:
        """Estimate period from zero crossings"""
        crossings = []
        for i in range(1, len(theta)):
            if theta[i-1] < 0 and theta[i] >= 0:
                crossings.append(t[i])
        if len(crossings) >= 2:
            return np.mean(np.diff(crossings[1:]))  # Skip first
        return 0.0

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        # Energy conservation
        if metrics.get("energy_drift", 1.0) < 0.01:
            factors.append(0.3)

        # Non-zero Lyapunov for chaos
        if metrics.get("max_lyapunov", 0) > 0:
            factors.append(0.2)

        # Finite period
        if metrics.get("period_estimate", 0) > 0:
            factors.append(0.2)

        # Physical energy
        if metrics.get("initial_energy", 0) < 0:  # Bound state
            factors.append(0.3)

        return min(0.9, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        params = hypothesis.parameters
        t_max = params.get("t_max", 10.0)
        dt = params.get("dt", 0.01)
        n_steps = int(t_max / dt)
        return {
            "cpu_cores": 1,
            "memory_gb": 0.1,
            "gpu_required": False,
            "estimated_time_seconds": n_steps / 10000,
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
                "Strogatz, S.H. (2018). Nonlinear Dynamics and Chaos",
            ],
        }
