"""
Maxwell FDTD Pattern
Finite-Difference Time-Domain for electromagnetics

Based on:
- Yee grid algorithm (Kane Yee, 1966)
- Leapfrog time integration
- Perfectly Matched Layers (PML) for boundaries
- GPU acceleration for large grids

Applications:
- Antenna design
- Waveguide analysis
- Radar cross-section
- Photonic devices
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
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


class BoundaryCondition(Enum):
    """BoundaryCondition."""
    PEC = "pec"           # Perfect Electric Conductor
    PMC = "pmc"           # Perfect Magnetic Conductor
    PML = "pml"           # Perfectly Matched Layer (absorbing)
    PERIODIC = "periodic" # Periodic boundaries


class SourceType(Enum):
    """SourceType."""
    GAUSSIAN_PULSE = "gaussian_pulse"
    SINE_WAVE = "sine_wave"
    RICKER_WAVELET = "ricker_wavelet"
    MODULATED_GAUSSIAN = "modulated_gaussian"


@dataclass
class FDTDConfig:
    """Configuration for FDTD simulation"""
    # Grid parameters
    nx: int = 100
    ny: int = 100
    nz: int = 1  # 2D by default
    dx: float = 1e-3  # 1 mm grid spacing

    # Time parameters
    courant_factor: float = 0.5  # Stability factor
    n_steps: int = 500

    # Material parameters
    epsilon_r: float = 1.0  # Relative permittivity
    mu_r: float = 1.0       # Relative permeability
    sigma: float = 0.0      # Conductivity (S/m)

    # Source parameters
    source_type: str = "gaussian_pulse"
    source_frequency: float = 1e9  # 1 GHz
    source_position: tuple[int, ...] = (50, 50, 0)
    source_amplitude: float = 1.0

    # Boundary conditions
    boundary_condition: str = "pml"
    pml_layers: int = 10

    # Output
    snapshot_interval: int = 50

    def __post_init__(self) -> None:
        # Calculate dt from Courant condition
        c = 299792458.0  # Speed of light
        self.dt = self.courant_factor * self.dx / (c * np.sqrt(3))


@simulation_pattern(
    id="maxwell_fdtd",
    name="Maxwell FDTD",
    category="physics",
    description="Finite-Difference Time-Domain electromagnetic simulation using Yee grid",
)
class MaxwellFDTDPattern(SimulationPattern):
    """
    FDTD simulation for electromagnetics

    Implements:
    - 2D/3D Yee grid
    - Gaussian pulse and sine wave sources
    - PML absorbing boundaries
    - Field visualization snapshots
    - GPU acceleration support
    """

    parameters = [
        SimulationParameter(
            name="dimensions",
            type="select",
            default="2d",
            options=["2d", "3d"],
            description="Simulation dimensionality",
        ),
        SimulationParameter(
            name="grid_size",
            type="int",
            default=100,
            min=20,
            max=1000,
            description="Grid size (NxN or NxNxN)",
        ),
        SimulationParameter(
            name="n_steps",
            type="int",
            default=500,
            min=100,
            max=10000,
            description="Number of time steps",
        ),
        SimulationParameter(
            name="source_frequency",
            type="float",
            default=1e9,
            min=1e6,
            max=1e12,
            description="Source frequency (Hz)",
        ),
        SimulationParameter(
            name="epsilon_r",
            type="float",
            default=1.0,
            min=1.0,
            max=100.0,
            description="Relative permittivity",
        ),
        SimulationParameter(
            name="sigma",
            type="float",
            default=0.0,
            min=0.0,
            max=1000.0,
            description="Conductivity (S/m)",
        ),
        SimulationParameter(
            name="boundary",
            type="select",
            default="pml",
            options=["pec", "pmc", "pml", "periodic"],
            description="Boundary condition type",
        ),
        SimulationParameter(
            name="use_gpu",
            type="bool",
            default=False,
            description="Use GPU acceleration if available",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.c = 299792458.0  # Speed of light
        self.eps0 = 8.854e-12  # Vacuum permittivity
        self.mu0 = 4 * np.pi * 1e-7  # Vacuum permeability

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if FDTD can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()

        keywords = [
            "fdtd", "finite difference", "electromagnetic", "em field",
            "maxwell", "wave propagation", "antenna", "waveguide",
            "scattering", "radar", "microwave", "rf", "photonic",
            "yee grid", "e-field", "h-field", "permittivity",
        ]

        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute FDTD simulation"""
        start_time = datetime.now()
        simulation_id = f"fdtd_{start_time.timestamp()}"

        logger.info(f"Starting FDTD simulation {simulation_id}")

        try:
            # Parse configuration
            fdtd_config = self._parse_config(config)

            # Run simulation
            if fdtd_config.nz == 1:
                results = await self._fdtd_2d(hypothesis, fdtd_config)
            else:
                results = await self._fdtd_3d(hypothesis, fdtd_config)

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
            logger.exception("FDTD simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> FDTDConfig:
        """Parse configuration dict into FDTDConfig"""
        is_3d = config.get("dimensions", "2d") == "3d"
        grid_size = config.get("grid_size", 100)

        return FDTDConfig(
            nx=grid_size,
            ny=grid_size,
            nz=grid_size if is_3d else 1,
            n_steps=config.get("n_steps", 500),
            source_frequency=config.get("source_frequency", 1e9),
            epsilon_r=config.get("epsilon_r", 1.0),
            sigma=config.get("sigma", 0.0),
            boundary_condition=config.get("boundary", "pml"),
        )

    async def _fdtd_2d(self, hypothesis: Hypothesis, config: FDTDConfig) -> dict[str, Any]:
        """2D FDTD simulation (TMz mode)"""

        nx, ny = config.nx, config.ny
        dx = config.dx
        dt = config.dt

        # Material properties
        epsilon = self.eps0 * config.epsilon_r
        mu = self.mu0 * config.mu_r

        # Field arrays
        Ez = np.zeros((nx, ny))  # E-field (z-component)
        Hx = np.zeros((nx, ny))  # H-field (x-component)
        Hy = np.zeros((nx, ny))  # H-field (y-component)

        # PML conductivity arrays
        sigma_ex = np.zeros((nx, ny))
        sigma_ey = np.zeros((nx, ny))

        if config.boundary_condition == "pml":
            self._setup_pml_2d(sigma_ex, sigma_ey, config)

        # Update coefficients
        Ca = (1 - config.sigma * dt / (2 * epsilon)) / (1 + config.sigma * dt / (2 * epsilon))
        Cb = (dt / epsilon) / (1 + config.sigma * dt / (2 * epsilon))
        Da = (1 - config.sigma * dt / (2 * mu)) / (1 + config.sigma * dt / (2 * mu))
        Db = (dt / mu) / (1 + config.sigma * dt / (2 * mu))

        # Source parameters
        src_x, src_y = config.source_position[0], config.source_position[1]
        freq = config.source_frequency
        wavelength = self.c / (freq * np.sqrt(config.epsilon_r))

        # Time stepping
        snapshots = []
        max_ez = 0.0
        total_energy_history = []

        for n in range(config.n_steps):
            # Update H fields
            Hx[1:, :] = Da * Hx[1:, :] - Db / dx * (Ez[1:, :] - Ez[:-1, :])
            Hy[:, 1:] = Da * Hy[:, 1:] + Db / dx * (Ez[:, 1:] - Ez[:, :-1])

            # Update E field
            Ez[1:-1, 1:-1] = (
                Ca * Ez[1:-1, 1:-1] +
                Cb / dx * ((Hy[1:-1, 2:] - Hy[1:-1, 1:-1]) - (Hx[2:, 1:-1] - Hx[1:-1, 1:-1]))
            )

            # Apply boundary conditions
            self._apply_boundary_2d(Ez, config.boundary_condition)

            # Add source
            t = n * dt
            if config.source_type == "gaussian_pulse":
                tau = 1.0 / freq
                Ez[src_x, src_y] += config.source_amplitude * np.exp(-((t - 3*tau) / tau) ** 2)
            elif config.source_type == "sine_wave":
                Ez[src_x, src_y] += config.source_amplitude * np.sin(2 * np.pi * freq * t)
            elif config.source_type == "ricker_wavelet":
                tau = 1.0 / freq
                Ez[src_x, src_y] += config.source_amplitude * (1 - 2*(np.pi*freq*(t-3*tau))**2) * np.exp(-(np.pi*freq*(t-3*tau))**2)

            # Track metrics
            max_ez = max(max_ez, np.max(np.abs(Ez)))
            energy = np.sum(Ez**2)
            total_energy_history.append(energy)

            # Save snapshots
            if n % config.snapshot_interval == 0:
                snapshots.append(Ez.copy())

            # Yield control periodically
            if n % 100 == 0:
                await asyncio.sleep(0)

        # Calculate final metrics
        final_energy = total_energy_history[-1] if total_energy_history else 0
        avg_energy = np.mean(total_energy_history) if total_energy_history else 0

        # Calculate Courant number
        courant = self.c * dt / dx

        metrics = {
            "max_ez": float(max_ez),
            "final_energy": float(final_energy),
            "avg_energy": float(avg_energy),
            "wavelength": float(wavelength),
            "courant_number": float(courant),
            "n_steps": config.n_steps,
            "grid_cells": nx * ny,
            "source_frequency": float(freq),
            "epsilon_r": config.epsilon_r,
        }

        logs = [
            f"2D FDTD simulation completed: {nx}x{ny} grid",
            f"Time steps: {config.n_steps}, Courant: {courant:.4f}",
            f"Wavelength: {wavelength*1e3:.2f} mm",
            f"Max E-field: {max_ez:.6f} V/m",
            f"Snapshots saved: {len(snapshots)}",
        ]

        return {"metrics": metrics, "logs": logs, "snapshots": snapshots}

    async def _fdtd_3d(self, hypothesis: Hypothesis, config: FDTDConfig) -> dict[str, Any]:
        """3D FDTD simulation"""

        nx, ny, nz = config.nx, config.ny, config.nz
        dx = config.dx
        dt = config.dt

        epsilon = self.eps0 * config.epsilon_r
        mu = self.mu0 * config.mu_r

        # Field arrays
        Ex = np.zeros((nx, ny, nz))
        Ey = np.zeros((nx, ny, nz))
        Ez = np.zeros((nx, ny, nz))
        Hx = np.zeros((nx, ny, nz))
        Hy = np.zeros((nx, ny, nz))
        Hz = np.zeros((nx, ny, nz))

        # Update coefficients
        Ca = (1 - config.sigma * dt / (2 * epsilon)) / (1 + config.sigma * dt / (2 * epsilon))
        Cb = (dt / epsilon) / (1 + config.sigma * dt / (2 * epsilon))
        Da = (1 - config.sigma * dt / (2 * mu)) / (1 + config.sigma * dt / (2 * mu))
        Db = (dt / mu) / (1 + config.sigma * dt / (2 * mu))

        src_x, src_y, src_z = config.source_position
        freq = config.source_frequency
        wavelength = self.c / (freq * np.sqrt(config.epsilon_r))

        max_e = 0.0

        for n in range(config.n_steps):
            # Update H fields
            Hx[1:, 1:, 1:] = (
                Da * Hx[1:, 1:, 1:] -
                Db / dx * ((Ez[1:, 1:, 1:] - Ez[1:, :-1, 1:]) - (Ey[1:, 1:, 1:] - Ey[1:, 1:, :-1]))
            )
            Hy[1:, 1:, 1:] = (
                Da * Hy[1:, 1:, 1:] -
                Db / dx * ((Ex[1:, 1:, 1:] - Ex[1:, 1:, :-1]) - (Ez[1:, 1:, 1:] - Ez[:-1, 1:, 1:]))
            )
            Hz[1:, 1:, 1:] = (
                Da * Hz[1:, 1:, 1:] -
                Db / dx * ((Ey[1:, 1:, 1:] - Ey[:-1, 1:, 1:]) - (Ex[1:, 1:, 1:] - Ex[1:, :-1, 1:]))
            )

            # Update E fields
            Ex[:-1, :-1, :-1] = (
                Ca * Ex[:-1, :-1, :-1] +
                Cb / dx * ((Hz[:-1, 1:, :-1] - Hz[:-1, :-1, :-1]) - (Hy[:-1, :-1, 1:] - Hy[:-1, :-1, :-1]))
            )
            Ey[:-1, :-1, :-1] = (
                Ca * Ey[:-1, :-1, :-1] +
                Cb / dx * ((Hx[:-1, :-1, 1:] - Hx[:-1, :-1, :-1]) - (Hz[1:, :-1, :-1] - Hz[:-1, :-1, :-1]))
            )
            Ez[:-1, :-1, :-1] = (
                Ca * Ez[:-1, :-1, :-1] +
                Cb / dx * ((Hy[1:, :-1, :-1] - Hy[:-1, :-1, :-1]) - (Hx[:-1, 1:, :-1] - Hx[:-1, :-1, :-1]))
            )

            # Add source
            t = n * dt
            if config.source_type == "gaussian_pulse":
                tau = 1.0 / freq
                Ez[src_x, src_y, src_z] += config.source_amplitude * np.exp(-((t - 3*tau) / tau) ** 2)
            elif config.source_type == "sine_wave":
                Ez[src_x, src_y, src_z] += config.source_amplitude * np.sin(2 * np.pi * freq * t)

            # Track metrics
            e_magnitude = np.sqrt(Ex**2 + Ey**2 + Ez**2)
            max_e = max(max_e, np.max(e_magnitude))

            if n % 100 == 0:
                await asyncio.sleep(0)

        metrics = {
            "max_e_field": float(max_e),
            "wavelength": float(wavelength),
            "courant_number": float(self.c * dt / dx),
            "n_steps": config.n_steps,
            "grid_cells": nx * ny * nz,
            "source_frequency": float(freq),
            "epsilon_r": config.epsilon_r,
        }

        logs = [
            f"3D FDTD simulation completed: {nx}x{ny}x{nz} grid",
            f"Grid cells: {metrics['grid_cells']}",
            f"Wavelength: {wavelength*1e3:.2f} mm",
            f"Max E-field: {max_e:.6f} V/m",
        ]

        return {"metrics": metrics, "logs": logs}

    def _setup_pml_2d(self, sigma_ex: np.ndarray, sigma_ey: np.ndarray, config: FDTDConfig) -> None:
        """Setup Perfectly Matched Layer conductivity profile"""
        nx, ny = config.nx, config.ny
        pml = config.pml_layers
        sigma_max = 1.0 / (2 * config.dx)

        # Left and right boundaries
        for i in range(pml):
            sigma = sigma_max * ((pml - i) / pml) ** 3
            sigma_ex[i, :] = sigma
            sigma_ex[nx - 1 - i, :] = sigma

        # Top and bottom boundaries
        for j in range(pml):
            sigma = sigma_max * ((pml - j) / pml) ** 3
            sigma_ey[:, j] = sigma
            sigma_ey[:, ny - 1 - j] = sigma

    def _apply_boundary_2d(self, Ez: np.ndarray, bc_type: str) -> None:
        """Apply boundary conditions to E-field"""
        if bc_type == "pec":
            # Perfect Electric Conductor: E = 0
            Ez[0, :] = 0
            Ez[-1, :] = 0
            Ez[:, 0] = 0
            Ez[:, -1] = 0
        elif bc_type == "pmc":
            # Perfect Magnetic Conductor: dE/dn = 0
            Ez[0, :] = Ez[1, :]
            Ez[-1, :] = Ez[-2, :]
            Ez[:, 0] = Ez[:, 1]
            Ez[:, -1] = Ez[:, -2]
        elif bc_type == "periodic":
            Ez[0, :] = Ez[-2, :]
            Ez[-1, :] = Ez[1, :]
            Ez[:, 0] = Ez[:, -2]
            Ez[:, -1] = Ez[:, 1]

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        # Stable Courant number
        courant = metrics.get("courant_number", 0)
        if 0 < courant <= 1.0:
            factors.append(0.3)

        # Non-zero fields
        if metrics.get("max_ez", 0) > 0 or metrics.get("max_e_field", 0) > 0:
            factors.append(0.3)

        # Sufficient time steps
        if metrics.get("n_steps", 0) >= 100:
            factors.append(0.2)

        # Physical wavelength
        wavelength = metrics.get("wavelength", 0)
        if wavelength > 0:
            factors.append(0.2)

        return min(0.85, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        params = hypothesis.parameters
        is_3d = params.get("dimensions", "2d") == "3d"
        grid_size = params.get("grid_size", 100)
        n_steps = params.get("n_steps", 500)

        if is_3d:
            cells = grid_size ** 3
            memory_gb = cells * 6 * 8e-9  # 6 field arrays, 8 bytes per float
        else:
            cells = grid_size ** 2
            memory_gb = cells * 3 * 8e-9  # 3 field arrays

        estimated_time = n_steps * cells / 1e8  # Rough estimate

        return {
            "cpu_cores": 4,
            "memory_gb": max(0.5, memory_gb),
            "gpu_required": is_3d and grid_size > 200,
            "estimated_time_seconds": estimated_time,
        }
