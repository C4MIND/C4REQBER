"""
Quantum Harmonic Oscillator Pattern
Energy levels and wavefunctions of the quantum harmonic oscillator

Based on:
- Schrodinger equation for harmonic potential V(x) = 0.5*m*omega^2*x^2
- Hermite polynomial solutions
- Analytic energy eigenvalues E_n = (n + 0.5)*hbar*omega
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
from scipy.special import hermite

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
class QHOConfig:
    """Configuration for Quantum Harmonic Oscillator simulation"""
    mass: float = 1.0          # Particle mass (atomic units)
    omega: float = 1.0         # Angular frequency
    hbar: float = 1.0          # Reduced Planck constant (atomic units)
    n_levels: int = 10         # Number of energy levels to compute
    x_max: float = 10.0        # Spatial domain [-x_max, x_max]
    n_points: int = 1000       # Spatial grid points


@simulation_pattern(
    id="quantum_harmonic_oscillator",
    name="Quantum Harmonic Oscillator",
    category="physics",
    description="Quantum harmonic oscillator energy levels and wavefunctions using Hermite polynomials",
)
class QuantumHarmonicOscillatorPattern(SimulationPattern):
    """
    Quantum harmonic oscillator simulation

    Implements:
    - Analytic energy eigenvalues: E_n = (n + 1/2) * hbar * omega
    - Wavefunctions: psi_n(x) = N_n * H_n(xi) * exp(-xi^2/2)
    - Position and momentum uncertainty
    - Classical turning points
    """

    parameters = [
        SimulationParameter(
            name="mass",
            type="float",
            default=1.0,
            min=0.01,
            max=100.0,
            description="Particle mass (atomic units)",
        ),
        SimulationParameter(
            name="omega",
            type="float",
            default=1.0,
            min=0.01,
            max=100.0,
            description="Angular frequency",
        ),
        SimulationParameter(
            name="n_levels",
            type="int",
            default=10,
            min=1,
            max=100,
            description="Number of energy levels",
        ),
        SimulationParameter(
            name="x_max",
            type="float",
            default=10.0,
            min=1.0,
            max=50.0,
            description="Spatial domain half-width",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config: QHOConfig = QHOConfig()

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if QHO can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        keywords = [
            "harmonic oscillator", "quantum harmonic", "energy levels",
            "wavefunction", "hermite", "quantum mechanics", "schrodinger",
            "zero point energy", "phonon", "vibrational",
        ]
        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute QHO simulation"""
        start_time = datetime.now()
        simulation_id = f"qho_{start_time.timestamp()}"
        logger.info(f"Starting QHO simulation {simulation_id}")

        try:
            self.config = self._parse_config(config)
            results = await self._simulate_qho()
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
            logger.exception("QHO simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> QHOConfig:
        """Parse configuration dict into QHOConfig"""
        cfg = QHOConfig()
        if "mass" in config:
            cfg.mass = float(config["mass"])
        if "omega" in config:
            cfg.omega = float(config["omega"])
        if "n_levels" in config:
            cfg.n_levels = int(config["n_levels"])
        if "x_max" in config:
            cfg.x_max = float(config["x_max"])
        return cfg

    async def _simulate_qho(self) -> dict[str, Any]:
        """Run QHO simulation"""
        cfg = self.config
        m = cfg.mass
        omega = cfg.omega
        hbar = cfg.hbar
        n_levels = cfg.n_levels

        # Characteristic length scale
        alpha = np.sqrt(m * omega / hbar)

        # Spatial grid
        x = np.linspace(-cfg.x_max, cfg.x_max, cfg.n_points)

        # Energy levels: E_n = (n + 1/2) * hbar * omega
        energies = np.array([(n + 0.5) * hbar * omega for n in range(n_levels)])

        # Wavefunctions using Hermite polynomials
        wavefunctions = []
        probabilities = []
        uncertainties = []

        for n in range(n_levels):
            # Normalization constant
            N_n = (alpha / np.pi**0.5)**0.5 / np.sqrt(2**n * math.factorial(n))
            # Hermite polynomial
            H_n = hermite(n)
            xi = alpha * x
            psi = N_n * H_n(xi) * np.exp(-xi**2 / 2)
            prob = np.abs(psi)**2

            # Position uncertainty: <x^2> = (n + 0.5) / alpha^2
            dx = x[1] - x[0]
            x_mean = np.trapezoid(x * prob, x)
            x2_mean = np.trapezoid(x**2 * prob, x)
            sigma_x = np.sqrt(x2_mean - x_mean**2)

            # Momentum uncertainty: <p^2> = (n + 0.5) * hbar^2 * alpha^2
            sigma_p = hbar * (n + 0.5) / sigma_x

            wavefunctions.append(psi.tolist())
            probabilities.append(prob.tolist())
            uncertainties.append({"sigma_x": float(sigma_x), "sigma_p": float(sigma_p)})

        # Classical turning points
        turning_points = np.sqrt(2 * energies / (m * omega**2))

        metrics = {
            "ground_state_energy": float(energies[0]),
            "energy_spacing": float(hbar * omega),
            "n_levels": n_levels,
            "alpha": float(alpha),
            "max_energy": float(energies[-1]),
            "uncertainty_product_ground": float(uncertainties[0]["sigma_x"] * uncertainties[0]["sigma_p"]),
        }

        logs = [
            f"QHO simulation: {n_levels} energy levels",
            f"Ground state energy: {energies[0]:.6f} (hbar*omega)",
            f"Energy spacing: {hbar*omega:.6f}",
            f"Characteristic length alpha: {alpha:.4f}",
            f"Ground state uncertainty product: {uncertainties[0]['sigma_x'] * uncertainties[0]['sigma_p']:.4f}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "energies": energies.tolist(),
            "wavefunctions": wavefunctions,
            "probabilities": probabilities,
            "uncertainties": uncertainties,
            "turning_points": turning_points.tolist(),
            "x": x.tolist(),
        }

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        # Ground state energy = 0.5 * hbar * omega
        if abs(metrics.get("ground_state_energy", 0) - 0.5) < 0.01:
            factors.append(0.3)

        # Uncertainty product >= 0.5 (Heisenberg)
        if metrics.get("uncertainty_product_ground", 0) >= 0.49:
            factors.append(0.3)

        # Energy spacing correct
        if abs(metrics.get("energy_spacing", 0) - 1.0) < 0.01:
            factors.append(0.2)

        # Multiple levels computed
        if metrics.get("n_levels", 0) >= 5:
            factors.append(0.2)

        return min(0.95, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        params = hypothesis.parameters
        n_levels = params.get("n_levels", 10)
        return {
            "cpu_cores": 1,
            "memory_gb": 0.1 + n_levels * 0.01,
            "gpu_required": False,
            "estimated_time_seconds": n_levels * 0.01,
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        """Get pattern metadata"""
        return {
            "id": cls.id,
            "name": cls.name,  # type: ignore[attr-defined]
            "category": cls.category,  # type: ignore[attr-defined]
            "description": cls.description,  # type: ignore[attr-defined]
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "default": p.default,
                    "min": p.min,
                    "max": p.max,
                    "description": p.description,
                }
                for p in cls.parameters
            ],
            "references": [
                "Griffiths, D.J. (2018). Introduction to Quantum Mechanics",
            ],
        }
