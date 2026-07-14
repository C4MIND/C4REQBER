"""
Phase Field Pattern
Cahn-Hilliard equation for phase separation and interface dynamics

Based on:
- Cahn-Hilliard equation (1958)
- Phase field modeling
- Spinodal decomposition
- Interface dynamics
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
from scipy.fft import fft2, fftfreq, ifft2

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
class PhaseFieldConfig:
    """Configuration for phase field simulation"""
    grid_size: int = 128
    dx: float = 1.0
    dt: float = 0.01
    n_steps: int = 10000
    M: float = 1.0  # Mobility
    gamma: float = 0.5  # Interface energy coefficient
    epsilon: float = 2.0  # Interface width parameter
    record_interval: int = 100
    random_seed: int | None = None


@simulation_pattern(
    id="phase_field",
    name="Phase Field Model",
    category="physics",
    description="Cahn-Hilliard equation for phase separation and interface dynamics",
)
class PhaseFieldPattern(SimulationPattern):
    """
    Phase field simulation for microstructure evolution

    Implements:
    - Cahn-Hilliard equation with spectral methods
    - Spinodal decomposition
    - Coarsening dynamics
    - Structure factor analysis
    - Interface tracking
    """

    parameters = [
        SimulationParameter(
            name="grid_size",
            type="int",
            default=128,
            min=32,
            max=512,
            description="Grid resolution (N×N)",
        ),
        SimulationParameter(
            name="dt",
            type="float",
            default=0.01,
            min=0.001,
            max=0.1,
            description="Time step",
        ),
        SimulationParameter(
            name="n_steps",
            type="int",
            default=10000,
            min=100,
            max=100000,
            description="Number of time steps",
        ),
        SimulationParameter(
            name="M",
            type="float",
            default=1.0,
            min=0.1,
            max=10.0,
            description="Mobility parameter",
        ),
        SimulationParameter(
            name="gamma",
            type="float",
            default=0.5,
            min=0.1,
            max=2.0,
            description="Interface energy coefficient",
        ),
        SimulationParameter(
            name="epsilon",
            type="float",
            default=2.0,
            min=0.5,
            max=5.0,
            description="Interface width parameter",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.rng = np.random.default_rng()
        self.phi: np.ndarray = np.array([])
        self.config: PhaseFieldConfig | None = None
        self.history: list[dict[str, Any]] = []

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if this pattern can simulate the hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()

        keywords = [
            "phase field", "cahn-hilliard", "phase separation",
            "spinodal", "coarsening", "microstructure", "interface",
            "diffusion", "alloy", "binary mixture", "demixing",
            "surface tension", "interfacial", "domain growth",
        ]

        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute phase field simulation"""
        start_time = datetime.now()
        simulation_id = f"phasefield_{start_time.timestamp()}"

        logger.info(f"Starting Phase Field simulation {simulation_id}")

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
            logger.exception("Phase Field simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> PhaseFieldConfig:
        """Parse configuration"""
        return PhaseFieldConfig(
            grid_size=config.get("grid_size", 128),
            dx=config.get("dx", 1.0),
            dt=config.get("dt", 0.01),
            n_steps=config.get("n_steps", 10000),
            M=config.get("M", 1.0),
            gamma=config.get("gamma", 0.5),
            epsilon=config.get("epsilon", 2.0),
            record_interval=config.get("record_interval", 100),
            random_seed=config.get("random_seed"),
        )

    async def _simulate(self, hypothesis: Hypothesis) -> dict[str, Any]:
        """Run Cahn-Hilliard simulation using spectral method"""
        N = self.config.grid_size  # type: ignore[union-attr]
        dt = self.config.dt  # type: ignore[union-attr]
        M = self.config.M  # type: ignore[union-attr]
        gamma = self.config.gamma  # type: ignore[union-attr]
        epsilon = self.config.epsilon  # type: ignore[union-attr]

        # Initialize with small random fluctuations around c=0
        self.phi = 0.1 * self.rng.standard_normal((N, N))

        # Fourier grid
        k = 2 * np.pi * fftfreq(N, self.config.dx)  # type: ignore[union-attr]
        kx, ky = np.meshgrid(k, k)
        k2 = kx**2 + ky**2
        k4 = k2**2

        self.history = []

        for step in range(self.config.n_steps):  # type: ignore[union-attr]
            # Semi-implicit spectral method
            # phi^(n+1) = (phi^n - dt*M*k^2*mu_nonlinear) / (1 + dt*M*gamma*k^4)

            # Chemical potential in real space
            mu = self._chemical_potential(self.phi, epsilon)

            # Fourier transforms
            phi_hat = fft2(self.phi)
            mu_hat = fft2(mu)

            # Update in Fourier space
            phi_hat = (phi_hat - dt * M * k2 * mu_hat) / (1 + dt * M * gamma * k4)

            # Inverse transform
            self.phi = np.real(ifft2(phi_hat))

            # Record measurements
            if step % self.config.record_interval == 0:  # type: ignore[union-attr]
                self._record(step)

            # Yield control
            if step % 500 == 0:
                await asyncio.sleep(0)

        return self._analyze_results()

    def _chemical_potential(self, phi: np.ndarray, epsilon: float) -> np.ndarray:
        """Calculate chemical potential: mu = f'(phi) - epsilon^2 * ∇²phi"""
        # Double-well potential: f(phi) = (phi^2 - 1)^2 / 4
        # f'(phi) = phi^3 - phi = phi * (phi^2 - 1)
        f_prime = phi * (phi**2 - 1)

        # Laplacian
        laplacian = (
            np.roll(phi, 1, axis=0) + np.roll(phi, -1, axis=0) +
            np.roll(phi, 1, axis=1) + np.roll(phi, -1, axis=1) - 4 * phi
        ) / (self.config.dx ** 2)  # type: ignore[union-attr]

        return f_prime - epsilon**2 * laplacian  # type: ignore[no-any-return]

    def _record(self, step: int) -> None:
        """Record measurements at current step"""
        phi = self.phi

        # Volume fraction
        c_mean = float(np.mean(phi))
        c_var = float(np.var(phi))

        # Interface length (perimeter approximation)
        grad_x = np.gradient(phi, axis=0)
        grad_y = np.gradient(phi, axis=1)
        grad_mag = np.sqrt(grad_x**2 + grad_y**2)
        interface_length = float(np.sum(grad_mag))

        # Domain size estimate from structure factor
        N = self.config.grid_size  # type: ignore[union-attr]
        phi_hat = fft2(phi - c_mean)
        S = np.abs(phi_hat)**2

        # Radial average of structure factor
        k = 2 * np.pi * fftfreq(N, self.config.dx)  # type: ignore[union-attr]
        kx, ky = np.meshgrid(k, k)
        k_mag = np.sqrt(kx**2 + ky**2)

        # Find characteristic wavenumber
        if np.sum(S) > 0:
            k_avg = float(np.sum(k_mag * S) / np.sum(S))
            domain_size = 2 * np.pi / k_avg if k_avg > 0 else N
        else:
            domain_size = N

        self.history.append({
            "step": step,
            "time": step * self.config.dt,  # type: ignore[union-attr]
            "concentration_mean": c_mean,
            "concentration_var": c_var,
            "interface_length": interface_length,
            "domain_size": domain_size,
        })

    def _analyze_results(self) -> dict[str, Any]:
        """Analyze simulation results"""
        if not self.history:
            return {"metrics": {}, "logs": ["No data recorded"]}

        # Final state
        final = self.history[-1]
        self.history[0]

        # Growth exponent estimate
        if len(self.history) >= 3:
            times = np.array([h["time"] for h in self.history[10:]])
            sizes = np.array([h["domain_size"] for h in self.history[10:]])

            if len(times) > 1 and np.all(times > 0) and np.all(sizes > 0):
                log_t = np.log(times)
                log_s = np.log(sizes)
                # Linear fit to get exponent
                coeffs = np.polyfit(log_t, log_s, 1)
                growth_exponent = float(coeffs[0])
            else:
                growth_exponent = 0.0
        else:
            growth_exponent = 0.0

        # Check for phase separation
        final_var = final["concentration_var"]
        phase_separated = final_var > 0.1  # Threshold

        metrics = {
            "final_concentration": final["concentration_mean"],
            "final_variance": final_var,
            "final_interface_length": final["interface_length"],
            "final_domain_size": final["domain_size"],
            "growth_exponent": growth_exponent,
            "phase_separated": float(phase_separated),
            "total_time": final["time"],
            "n_records": len(self.history),
        }

        logs = [
            f"Phase Field simulation: {self.config.grid_size}×{self.config.grid_size}",  # type: ignore[union-attr]
            f"Final concentration: {metrics['final_concentration']:.4f}",
            f"Final variance: {metrics['final_variance']:.4f}",
            f"Domain size: {metrics['final_domain_size']:.2f}",
            f"Growth exponent: {metrics['growth_exponent']:.3f}",
        ]

        if phase_separated:
            logs.append("System shows clear phase separation")
        else:
            logs.append("System remains mixed")

        if 0.25 <= growth_exponent <= 0.35:
            logs.append("Growth exponent consistent with Lifshitz-Slyozov (1/3)")

        return {"metrics": metrics, "logs": logs}

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        n_records = metrics.get("n_records", 0)
        if n_records >= 50:
            factors.append(0.3)
        elif n_records >= 20:
            factors.append(0.2)

        if metrics.get("phase_separated", 0) > 0.5:
            factors.append(0.2)

        growth_exp = metrics.get("growth_exponent", 0)
        if 0.2 <= growth_exp <= 0.4:
            factors.append(0.3)

        return min(0.85, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        params = hypothesis.parameters
        N = params.get("grid_size", 128)
        n_steps = params.get("n_steps", 10000)

        # FFT operations are O(N² log N)
        estimated_time = (N * N * np.log2(N) * n_steps) / 1e7

        return {
            "cpu_cores": 1,
            "memory_gb": 0.1 + (N * N * 8) / 1e6,
            "gpu_required": False,
            "estimated_time_seconds": estimated_time,
        }
