"""
Spring-Mass System Pattern
Coupled oscillators and normal modes analysis

Based on:
- Hooke's law
- Normal mode decomposition
- Eigenvalue problem for mode frequencies
- Energy conservation
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
from scipy.linalg import eigh

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
class SpringMassConfig:
    """Configuration for spring-mass system"""
    n_masses: int = 3         # Number of masses
    mass: float = 1.0         # Mass of each oscillator (kg)
    k: float = 1.0            # Spring constant (N/m)
    k_coupling: float = 0.5   # Coupling spring constant (N/m)
    dt: float = 0.01          # Time step (s)
    t_max: float = 10.0       # Simulation time (s)


@simulation_pattern(
    id="spring_mass",
    name="Spring-Mass System",
    category="physics",
    description="Coupled harmonic oscillators and normal mode analysis",
)
class SpringMassPattern(SimulationPattern):
    """
    Spring-mass system simulation

    Implements:
    - Coupled oscillator dynamics
    - Normal mode decomposition via eigenvalue problem
    - Energy conservation
    - Beating phenomena
    """

    parameters = [
        SimulationParameter(
            name="n_masses",
            type="int",
            default=3,
            min=2,
            max=20,
            description="Number of coupled masses",
        ),
        SimulationParameter(
            name="mass",
            type="float",
            default=1.0,
            min=0.1,
            max=10.0,
            description="Mass of each oscillator (kg)",
        ),
        SimulationParameter(
            name="k",
            type="float",
            default=1.0,
            min=0.1,
            max=100.0,
            description="Spring constant (N/m)",
        ),
        SimulationParameter(
            name="k_coupling",
            type="float",
            default=0.5,
            min=0.0,
            max=10.0,
            description="Coupling spring constant (N/m)",
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
        self.config: SpringMassConfig = SpringMassConfig()

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if spring-mass can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        keywords = [
            "spring mass", "coupled oscillator", "normal mode",
            "eigenmode", "vibration", "resonance", "harmonic oscillator",
            "lattice vibration", "phonon", "mechanical vibration",
        ]
        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute spring-mass simulation"""
        start_time = datetime.now()
        simulation_id = f"sm_{start_time.timestamp()}"
        logger.info(f"Starting spring-mass simulation {simulation_id}")

        try:
            self.config = self._parse_config(config)
            results = await self._simulate_spring_mass()
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
            logger.exception("Spring-mass simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> SpringMassConfig:
        """Parse configuration dict"""
        cfg = SpringMassConfig()
        if "n_masses" in config:
            cfg.n_masses = int(config["n_masses"])
        if "mass" in config:
            cfg.mass = float(config["mass"])
        if "k" in config:
            cfg.k = float(config["k"])
        if "k_coupling" in config:
            cfg.k_coupling = float(config["k_coupling"])
        if "dt" in config:
            cfg.dt = float(config["dt"])
        if "t_max" in config:
            cfg.t_max = float(config["t_max"])
        return cfg

    async def _simulate_spring_mass(self) -> dict[str, Any]:
        """Run spring-mass simulation"""
        cfg = self.config
        n = cfg.n_masses
        m = cfg.mass
        k = cfg.k
        kc = cfg.k_coupling

        # Build stiffness matrix K and mass matrix M
        # For chain: each mass connected to neighbors with kc, and to ground with k
        K = np.zeros((n, n))
        M = np.eye(n) * m

        for i in range(n):
            K[i, i] = k + 2 * kc
            if i > 0:
                K[i, i-1] = -kc
                K[i-1, i] = -kc
        # Boundary masses only have one coupling
        K[0, 0] = k + kc
        K[-1, -1] = k + kc

        # Solve generalized eigenvalue problem: K * v = omega^2 * M * v
        eigenvalues, eigenvectors = eigh(K, M)
        frequencies = np.sqrt(np.maximum(eigenvalues, 0))

        # Initial conditions: displace first mass
        x0 = np.zeros(n)
        x0[0] = 1.0
        v0 = np.zeros(n)

        # Project initial conditions onto normal modes
        # q_j = v_j^T * M * x0
        q0 = np.array([eigenvectors[:, j] @ M @ x0 for j in range(n)])
        dq0 = np.array([eigenvectors[:, j] @ M @ v0 for j in range(n)])

        # Time evolution
        t = np.arange(0, cfg.t_max, cfg.dt)
        n_steps = len(t)

        # x(t) = sum_j [A_j * cos(omega_j * t) + B_j * sin(omega_j * t)] * v_j
        # A_j = q0_j, B_j = dq0_j / omega_j (if omega_j > 0)
        x_t = np.zeros((n, n_steps))
        for j in range(n):
            omega_j = frequencies[j]
            if omega_j > 1e-10:
                A_j = q0[j]
                B_j = dq0[j] / omega_j
                mode_amplitude = A_j * np.cos(omega_j * t) + B_j * np.sin(omega_j * t)
            else:
                mode_amplitude = q0[j] * np.ones_like(t)
            for i in range(n):
                x_t[i, :] += mode_amplitude * eigenvectors[i, j]

        # Compute energies
        # KE = 0.5 * v^T * M * v
        # PE = 0.5 * x^T * K * x
        KE = np.zeros(n_steps)
        PE = np.zeros(n_steps)
        for step in range(n_steps):
            x_step = x_t[:, step]
            # Velocity via finite difference
            if step == 0:
                v_step = np.zeros(n)
            else:
                v_step = (x_t[:, step] - x_t[:, step-1]) / cfg.dt
            KE[step] = 0.5 * v_step @ M @ v_step
            PE[step] = 0.5 * x_step @ K @ x_step

        total_energy = KE + PE
        energy_drift = np.max(np.abs(total_energy - total_energy[0])) / total_energy[0]

        metrics = {
            "n_masses": n,
            "fundamental_frequency": float(frequencies[0]),
            "highest_frequency": float(frequencies[-1]),
            "frequency_ratio": float(frequencies[-1] / frequencies[0]) if frequencies[0] > 0 else 0.0,
            "energy_drift": float(energy_drift),
            "initial_energy": float(total_energy[0]),
            "max_displacement": float(np.max(np.abs(x_t))),
        }

        logs = [
            f"Spring-mass system: {n} masses, m={m}kg, k={k}N/m, kc={kc}N/m",
            f"Fundamental frequency: {frequencies[0]:.4f} rad/s",
            f"Highest frequency: {frequencies[-1]:.4f} rad/s",
            f"Energy drift: {energy_drift:.8f}",
            f"Max displacement: {metrics['max_displacement']:.4f} m",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "positions": x_t.tolist(),
            "frequencies": frequencies.tolist(),
            "eigenvectors": eigenvectors.tolist(),
            "kinetic_energy": KE.tolist(),
            "potential_energy": PE.tolist(),
            "total_energy": total_energy.tolist(),
        }

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        # Energy conservation
        if metrics.get("energy_drift", 1.0) < 0.01:
            factors.append(0.3)

        # Positive frequencies
        if metrics.get("fundamental_frequency", 0) > 0:
            factors.append(0.3)

        # Frequency separation
        ratio = metrics.get("frequency_ratio", 1.0)
        if ratio > 1.0:
            factors.append(0.2)

        # Physical displacement
        if 0 < metrics.get("max_displacement", 0) < 10:
            factors.append(0.2)

        return min(0.9, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        params = hypothesis.parameters
        n = params.get("n_masses", 3)
        t_max = params.get("t_max", 10.0)
        dt = params.get("dt", 0.01)
        n_steps = int(t_max / dt)
        return {
            "cpu_cores": 1,
            "memory_gb": 0.1 + n * n_steps * 8e-9,
            "gpu_required": False,
            "estimated_time_seconds": n_steps * n / 1e6,
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
                "Goldstein, H. (2002). Classical Mechanics",
            ],
        }
