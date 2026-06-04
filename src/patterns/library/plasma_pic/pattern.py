"""
Plasma PIC Pattern[str]
Main pattern class for Particle-in-Cell simulation.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

import numpy as np

from ...core import (
    Hypothesis,
    SimulationParameter,
    SimulationPattern,
    SimulationResult,
    SimulationStatus,
    ValidationLevel,
    simulation_pattern,
)
from .config import PICConfig
from .core import PICSolver


logger = logging.getLogger(__name__)

@simulation_pattern(
    id="plasma_pic",
    name="Plasma PIC",
    category="physics",
    description="Particle-in-Cell simulation for plasma physics",
)
class PlasmaPICPattern(SimulationPattern):
    """
    Particle-in-Cell plasma simulation

    Implements:
    - 1D/2D electrostatic PIC
    - Cloud-in-Cell (CIC) charge deposition
    - Boris particle pusher
    - FFT-based field solver
    - Multiple species (electrons, ions)
    """

    parameters = [
        SimulationParameter(
            name="dimensions",
            type="select",
            default="2d",
            options=["1d", "2d"],
            description="Simulation dimensionality",
        ),
        SimulationParameter(
            name="n_particles",
            type="int",
            default=10000,
            min=1000,
            max=1000000,
            description="Number of particles",
        ),
        SimulationParameter(
            name="n_steps",
            type="int",
            default=1000,
            min=100,
            max=10000,
            description="Number of time steps",
        ),
        SimulationParameter(
            name="plasma_density",
            type="float",
            default=1e20,
            min=1e15,
            max=1e25,
            description="Plasma density (m^-3)",
        ),
        SimulationParameter(
            name="electron_temp",
            type="float",
            default=10.0,
            min=0.1,
            max=1000.0,
            description="Electron temperature (eV)",
        ),
        SimulationParameter(
            name="ion_temp",
            type="float",
            default=1.0,
            min=0.1,
            max=1000.0,
            description="Ion temperature (eV)",
        ),
        SimulationParameter(
            name="pusher",
            type="select",
            default="boris",
            options=["boris", "leapfrog", "rk4"],
            description="Particle pusher algorithm",
        ),
        SimulationParameter(
            name="grid_size",
            type="int",
            default=64,
            min=32,
            max=512,
            description="Grid size per dimension",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        # Physical constants
        self.q_e = 1.602e-19  # Elementary charge (C)
        self.m_e = 9.109e-31  # Electron mass (kg)
        self.eps0 = 8.854e-12  # Vacuum permittivity
        self.k_B = 1.381e-23  # Boltzmann constant
        self.c = 299792458.0   # Speed of light

        self.solver: PICSolver = None  # type: ignore[assignment]

        self.particles: list[Any] = []
        self.rho: np.ndarray | None = None
        self.phi: np.ndarray | None = None
        self.Ex: np.ndarray | None = None
        self.Ey: np.ndarray | None = None

    def _initialize_particles_1d(self, config: PICConfig) -> None:
        if self.solver is None:
            self.solver = PICSolver(config, self.q_e, self.m_e, self.eps0, self.k_B)
        self.solver.initialize_particles_1d()
        self.particles = self.solver.particles

    def _initialize_particles_2d(self, config: PICConfig) -> None:
        if self.solver is None:
            self.solver = PICSolver(config, self.q_e, self.m_e, self.eps0, self.k_B)
        self.solver.initialize_particles_2d()
        self.particles = self.solver.particles

    def _deposit_charge_1d(self, config: PICConfig) -> np.ndarray:
        if self.solver is None:
            self.solver = PICSolver(config, self.q_e, self.m_e, self.eps0, self.k_B)
        self.solver.particles = self.particles
        rho = self.solver.deposit_charge_1d()
        self.rho = rho
        return rho

    def _deposit_charge_2d(self, config: PICConfig) -> np.ndarray:
        if self.solver is None:
            self.solver = PICSolver(config, self.q_e, self.m_e, self.eps0, self.k_B)
        self.solver.particles = self.particles
        rho = self.solver.deposit_charge_2d()
        self.rho = rho
        return rho

    def _solve_poisson_1d(self, rho: np.ndarray, config: PICConfig) -> np.ndarray:
        if self.solver is None:
            self.solver = PICSolver(config, self.q_e, self.m_e, self.eps0, self.k_B)
        phi = self.solver.solve_poisson_1d(rho)
        self.phi = phi
        return phi

    def _solve_poisson_2d_fft(self, rho: np.ndarray, config: PICConfig) -> np.ndarray:
        if self.solver is None:
            self.solver = PICSolver(config, self.q_e, self.m_e, self.eps0, self.k_B)
        phi = self.solver.solve_poisson_2d_fft(rho)
        self.phi = phi
        return phi

    def _compute_electric_field_1d(self, phi: np.ndarray, config: PICConfig) -> np.ndarray:
        if self.solver is None:
            self.solver = PICSolver(config, self.q_e, self.m_e, self.eps0, self.k_B)
        Ex = self.solver.compute_electric_field_1d(phi)
        self.Ex = Ex
        return Ex

    def _compute_electric_field_2d(self, phi: np.ndarray, config: PICConfig) -> tuple[np.ndarray, np.ndarray]:
        if self.solver is None:
            self.solver = PICSolver(config, self.q_e, self.m_e, self.eps0, self.k_B)
        Ex, Ey = self.solver.compute_electric_field_2d(phi)
        self.Ex = Ex
        self.Ey = Ey
        return Ex, Ey

    def _push_particles_1d(self, Ex: np.ndarray, dt: float, config: PICConfig) -> None:
        if self.solver is None:
            self.solver = PICSolver(config, self.q_e, self.m_e, self.eps0, self.k_B)
        self.solver.particles = self.particles
        self.solver.push_particles_1d(Ex, dt)
        self.particles = self.solver.particles

    def _push_particles_2d(self, Ex: np.ndarray, Ey: np.ndarray, dt: float, config: PICConfig) -> None:
        if self.solver is None:
            self.solver = PICSolver(config, self.q_e, self.m_e, self.eps0, self.k_B)
        self.solver.particles = self.particles
        self.solver.push_particles_2d(Ex, Ey, dt)
        self.particles = self.solver.particles

    def _compute_kinetic_energy(self) -> float:
        if self.solver is None:
            return 0.0
        self.solver.particles = self.particles
        return self.solver.compute_kinetic_energy()

    def _compute_field_energy_1d(self, Ex: np.ndarray, config: PICConfig) -> float:
        if self.solver is None:
            self.solver = PICSolver(config, self.q_e, self.m_e, self.eps0, self.k_B)
        return self.solver.compute_field_energy_1d(Ex)

    def _compute_field_energy_2d(self, Ex: np.ndarray, Ey: np.ndarray, config: PICConfig) -> float:
        if self.solver is None:
            self.solver = PICSolver(config, self.q_e, self.m_e, self.eps0, self.k_B)
        return self.solver.compute_field_energy_2d(Ex, Ey)

    def _compute_total_momentum(self) -> float:
        if self.solver is None:
            return 0.0
        self.solver.particles = self.particles
        return self.solver.compute_total_momentum()

    def _compute_thermal_velocity(self, species: int = 0) -> float:
        if self.solver is None:
            return 0.0
        self.solver.particles = self.particles
        return self.solver.compute_thermal_velocity(species)

    @classmethod
    def can_simulate(cls, hypothesis: Hypothesis) -> bool:
        """Check if PIC can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()

        keywords = [
            "plasma", "particle in cell", "pic", "charged particle",
            "fusion", "tokamak", "iter", "magnetic confinement",
            "laser plasma", "wakefield", "accelerator",
            "debye length", "plasma frequency", "langmuir",
            "ion", "electron", "collective behavior",
        ]

        return any(kw in title or kw in desc for kw in keywords)

    async def run(
        self, hypothesis: Hypothesis | None = None, config: dict[str, Any] | None = None
    ) -> SimulationResult:
        """Execute PIC simulation"""
        start_time = datetime.now()
        simulation_id = f"pic_{start_time.timestamp()}"

        logger.info(f"Starting PIC simulation {simulation_id}")

        try:
            pic_config = self._parse_config(config)  # type: ignore[arg-type]
            self.solver = PICSolver(pic_config, self.q_e, self.m_e, self.eps0, self.k_B)

            if pic_config.nz == 1 and pic_config.ny == 1:
                results = await self._pic_1d(pic_config)
            else:
                results = await self._pic_2d(pic_config)

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
            logger.exception("PIC simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> PICConfig:
        """Parse configuration dict[str, Any] into PICConfig"""
        dims = config.get("dimensions", "2d")
        grid_size = config.get("grid_size", 64)

        return PICConfig(
            nx=grid_size,
            ny=1 if dims == "1d" else grid_size,
            nz=1,
            n_particles=config.get("n_particles", 10000),
            n_steps=config.get("n_steps", 1000),
            n0=config.get("plasma_density", 1e20),
            Te=config.get("electron_temp", 10.0),
            Ti=config.get("ion_temp", 1.0),
            pusher=config.get("pusher", "boris"),
        )

    async def _pic_1d(self, config: PICConfig) -> dict[str, Any]:
        """1D electrostatic PIC simulation"""
        self.solver.initialize_particles_1d()

        nx = config.nx
        dx = config.dx
        dt = config.dt

        omega_p = np.sqrt(config.n0 * self.q_e**2 / (self.m_e * self.eps0))
        lambda_D = np.sqrt(self.eps0 * self.k_B * config.Te * 11604 / (config.n0 * self.q_e))

        kinetic_energy_history = []
        field_energy_history = []
        total_momentum_history = []

        for step in range(config.n_steps):
            rho = self.solver.deposit_charge_1d()
            phi = self.solver.solve_poisson_1d(rho)
            Ex = self.solver.compute_electric_field_1d(phi)
            self.solver.push_particles_1d(Ex, dt)

            ke = self.solver.compute_kinetic_energy()
            fe = self.solver.compute_field_energy_1d(Ex)
            momentum = self.solver.compute_total_momentum()

            kinetic_energy_history.append(ke)
            field_energy_history.append(fe)
            total_momentum_history.append(momentum)

            if step % 100 == 0:
                await asyncio.sleep(0)

        final_ke = kinetic_energy_history[-1] if kinetic_energy_history else 0
        final_fe = field_energy_history[-1] if field_energy_history else 0

        total_energy_initial = kinetic_energy_history[0] + field_energy_history[0]
        total_energy_final = final_ke + final_fe
        energy_error = abs(total_energy_final - total_energy_initial) / total_energy_initial if total_energy_initial > 0 else 0

        v_rms_e = self.solver.compute_thermal_velocity(species=0)
        v_rms_i = self.solver.compute_thermal_velocity(species=1)

        metrics = {
            "n_particles": len(self.solver.particles),
            "n_steps": config.n_steps,
            "plasma_frequency": float(omega_p),
            "debye_length": float(lambda_D),
            "final_kinetic_energy": float(final_ke),
            "final_field_energy": float(final_fe),
            "energy_conservation_error": float(energy_error),
            "v_rms_electrons": float(v_rms_e),
            "v_rms_ions": float(v_rms_i),
            "nx": nx,
        }

        logs = [
            "1D PIC simulation completed",
            f"Particles: {len(self.solver.particles)}, Steps: {config.n_steps}",
            f"Plasma frequency: {omega_p/1e9:.3f} GHz",
            f"Debye length: {lambda_D*1e6:.3f} μm",
            f"Energy conservation error: {energy_error*100:.4f}%",
            f"Electron thermal velocity: {v_rms_e/1e6:.2f} x10⁶ m/s",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "energy_history": {
                "kinetic": kinetic_energy_history,
                "field": field_energy_history,
            }
        }

    async def _pic_2d(self, config: PICConfig) -> dict[str, Any]:
        """2D electrostatic PIC simulation"""
        self.solver.initialize_particles_2d()

        nx, ny = config.nx, config.ny
        dt = config.dt

        omega_p = np.sqrt(config.n0 * self.q_e**2 / (self.m_e * self.eps0))
        lambda_D = np.sqrt(self.eps0 * self.k_B * config.Te * 11604 / (config.n0 * self.q_e))

        kinetic_energy_history = []
        field_energy_history = []

        for step in range(config.n_steps):
            rho = self.solver.deposit_charge_2d()
            phi = self.solver.solve_poisson_2d_fft(rho)
            Ex, Ey = self.solver.compute_electric_field_2d(phi)
            self.solver.push_particles_2d(Ex, Ey, dt)

            ke = self.solver.compute_kinetic_energy()
            fe = self.solver.compute_field_energy_2d(Ex, Ey)

            kinetic_energy_history.append(ke)
            field_energy_history.append(fe)

            if step % 100 == 0:
                await asyncio.sleep(0)

        final_ke = kinetic_energy_history[-1] if kinetic_energy_history else 0
        final_fe = field_energy_history[-1] if field_energy_history else 0

        energy_initial = kinetic_energy_history[0] + field_energy_history[0] if kinetic_energy_history else 1
        energy_final = final_ke + final_fe
        energy_error = abs(energy_final - energy_initial) / energy_initial if energy_initial > 0 else 0

        metrics = {
            "n_particles": len(self.solver.particles),
            "n_steps": config.n_steps,
            "grid_cells": nx * ny,
            "plasma_frequency": float(omega_p),
            "debye_length": float(lambda_D),
            "final_kinetic_energy": float(final_ke),
            "final_field_energy": float(final_fe),
            "energy_conservation_error": float(energy_error),
        }

        logs = [
            "2D PIC simulation completed",
            f"Particles: {len(self.solver.particles)}, Grid: {nx}x{ny}",
            f"Plasma frequency: {omega_p/1e9:.3f} GHz",
            f"Energy conservation error: {energy_error*100:.4f}%",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
        }

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        energy_error = metrics.get("energy_conservation_error", 1.0)
        if energy_error < 0.01:
            factors.append(0.4)
        elif energy_error < 0.1:
            factors.append(0.2)

        omega_p = metrics.get("plasma_frequency", 0)
        if omega_p > 0:
            factors.append(0.2)

        if metrics.get("n_particles", 0) >= 1000:
            factors.append(0.2)

        v_rms = metrics.get("v_rms_electrons", 0)
        if 1e5 < v_rms < 1e8:
            factors.append(0.2)

        return min(0.85, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis | None = None) -> dict[str, Any]:
        """Estimate resources."""
        if hypothesis is None:
            return {}
        """Estimate computational resources"""
        params = hypothesis.parameters
        n_particles = params.get("n_particles", 10000)
        n_steps = params.get("n_steps", 1000)
        grid_size = params.get("grid_size", 64)

        particle_memory = n_particles * 7 * 8e-9
        grid_memory = grid_size ** 2 * 8e-9 * 5

        estimated_time = n_steps * n_particles / 1e7

        return {
            "cpu_cores": 4,
            "memory_gb": max(1.0, particle_memory + grid_memory),
            "gpu_required": n_particles > 100000,
            "estimated_time_seconds": estimated_time,
        }
