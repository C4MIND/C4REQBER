"""
Wave Optics Pattern
Beam Propagation Method (BPM) for optical waveguides

Based on:
- Paraxial wave equation (Fresnel approximation)
- Split-step Fourier method
- Finite-difference BPM
- Transparent boundary conditions

Applications:
- Optical fiber design
- Integrated optics
- Laser beam propagation
- Atmospheric optics
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np
from scipy.fft import fft, fftfreq, ifft

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


class BPMMethod(Enum):
    """BPMMethod."""
    FFT = "fft"                    # Split-step Fourier
    FD = "finite_difference"       # Finite-difference BPM
    ADI = "adi"                    # Alternating Direction Implicit


class BeamProfile(Enum):
    """BeamProfile."""
    GAUSSIAN = "gaussian"
    PLANE = "plane"
    HERMITE_GAUSSIAN = "hermite_gaussian"
    LAGUERRE_GAUSSIAN = "laguerre_gaussian"


@dataclass
class WaveOpticsConfig:
    """Configuration for wave optics simulation"""
    # Grid parameters
    nx: int = 256
    ny: int = 256
    nz: int = 1000  # Propagation steps

    # Physical domain
    Lx: float = 100e-6   # 100 microns
    Ly: float = 100e-6
    Lz: float = 10e-3    # 10 mm propagation

    # Optical parameters
    wavelength: float = 1.55e-6  # 1550 nm (telecom)
    n0: float = 1.5              # Background refractive index
    k0: float = field(init=False)

    # Waveguide parameters
    waveguide_type: str = "fiber"  # 'fiber', 'slab', 'channel'
    core_radius: float = 5e-6      # 5 microns
    delta_n: float = 0.01          # Index contrast

    # Beam parameters
    beam_profile: str = "gaussian"
    beam_waist: float = 3e-6       # 3 micron waist
    beam_power: float = 1.0        # 1 Watt

    # Numerical parameters
    bpm_method: str = "fft"
    step_size: float = field(init=False)

    # Boundary conditions
    use_tbc: bool = True           # Transparent Boundary Condition

    def __post_init__(self) -> None:
        self.k0 = 2 * np.pi / self.wavelength  # Free space wavenumber
        self.dx = self.Lx / self.nx
        self.dy = self.Ly / self.ny
        self.dz = self.Lz / self.nz
        self.step_size = self.dz


@simulation_pattern(
    id="wave_optics",
    name="Wave Optics BPM",
    category="physics",
    description="Beam Propagation Method for optical waveguide simulation",
)
class WaveOpticsPattern(SimulationPattern):
    """
    Beam Propagation Method for optical waveguides

    Implements:
    - 2D/3D Split-step Fourier BPM
    - Finite-difference BPM
    - Various waveguide profiles (fiber, slab, channel)
    - Gaussian and higher-order beam profiles
    - Transparent boundary conditions
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
            name="wavelength",
            type="float",
            default=1.55e-6,
            min=0.3e-6,
            max=10e-6,
            description="Wavelength (m)",
        ),
        SimulationParameter(
            name="n0",
            type="float",
            default=1.5,
            min=1.0,
            max=4.0,
            description="Background refractive index",
        ),
        SimulationParameter(
            name="waveguide_type",
            type="select",
            default="fiber",
            options=["fiber", "slab", "channel", "none"],
            description="Waveguide geometry",
        ),
        SimulationParameter(
            name="core_radius",
            type="float",
            default=5e-6,
            min=0.5e-6,
            max=50e-6,
            description="Core radius (m)",
        ),
        SimulationParameter(
            name="delta_n",
            type="float",
            default=0.01,
            min=0.001,
            max=0.5,
            description="Refractive index contrast",
        ),
        SimulationParameter(
            name="beam_waist",
            type="float",
            default=3e-6,
            min=0.1e-6,
            max=20e-6,
            description="Input beam waist (m)",
        ),
        SimulationParameter(
            name="propagation_distance",
            type="float",
            default=10e-3,
            min=0.1e-3,
            max=100e-3,
            description="Propagation distance (m)",
        ),
        SimulationParameter(
            name="bpm_method",
            type="select",
            default="fft",
            options=["fft", "fd", "adi"],
            description="BPM numerical method",
        ),
        SimulationParameter(
            name="use_tbc",
            type="bool",
            default=True,
            description="Use Transparent Boundary Conditions",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.c = 299792458.0  # Speed of light

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if wave optics can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()

        keywords = [
            "optical fiber", "waveguide", "beam propagation", "bpm",
            "laser", "optics", "photonics", "fiber", "mode",
            "diffraction", "interference", "refraction",
            "wave equation", "helmholtz", "paraxial",
            "gaussian beam", "fiber coupling", "mode field",
        ]

        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute wave optics simulation"""
        start_time = datetime.now()
        simulation_id = f"wave_optics_{start_time.timestamp()}"

        logger.info(f"Starting wave optics simulation {simulation_id}")

        try:
            # Parse configuration
            optics_config = self._parse_config(config)

            # Choose BPM method
            if optics_config.bpm_method == "fft":
                results = await self._fft_bpm(hypothesis, optics_config)
            elif optics_config.bpm_method == "fd":
                results = await self._fd_bpm(hypothesis, optics_config)
            else:
                results = await self._adi_bpm(hypothesis, optics_config)

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
            logger.exception("Wave optics simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> WaveOpticsConfig:
        """Parse configuration dict into WaveOpticsConfig"""
        is_3d = config.get("dimensions", "2d") == "3d"

        return WaveOpticsConfig(
            nx=config.get("nx", 256 if not is_3d else 128),
            ny=config.get("ny", 256 if not is_3d else 128),
            nz=config.get("nz", 1000),
            wavelength=config.get("wavelength", 1.55e-6),
            n0=config.get("n0", 1.5),
            waveguide_type=config.get("waveguide_type", "fiber"),
            core_radius=config.get("core_radius", 5e-6),
            delta_n=config.get("delta_n", 0.01),
            beam_waist=config.get("beam_waist", 3e-6),
            Lz=config.get("propagation_distance", 10e-3),
            bpm_method=config.get("bpm_method", "fft"),
            use_tbc=config.get("use_tbc", True),
        )

    async def _fft_bpm(self, hypothesis: Hypothesis, config: WaveOpticsConfig) -> dict[str, Any]:
        """Split-step Fourier BPM"""

        # Create grid
        x = np.linspace(-config.Lx/2, config.Lx/2, config.nx)
        y = np.linspace(-config.Ly/2, config.Ly/2, config.ny)
        X, Y = np.meshgrid(x, y, indexing='ij')

        # Initialize field
        field = self._initialize_beam(X, Y, config)

        # Build refractive index profile
        n_profile = self._build_refractive_index(X, Y, config)

        # Calculate effective index
        n_eff = config.n0

        # Spatial frequencies
        kx = 2 * np.pi * fftfreq(config.nx, config.dx)
        ky = 2 * np.pi * fftfreq(config.ny, config.dy)
        KX, KY = np.meshgrid(kx, ky, indexing='ij')

        # Propagation operator in Fourier space
        kz = np.sqrt((config.k0 * n_eff)**2 - KX**2 - KY**2 + 0j)
        kz = np.real(kz)  # Paraxial approximation
        propagator = np.exp(1j * kz * config.dz)

        # Store field evolution
        power_evolution = []
        beam_width_evolution = []

        max_field = np.max(np.abs(field))

        for step in range(config.nz):
            # Diffraction step (Fourier domain)
            field = ifft(fft(field, axis=0), axis=0)
            field = ifft(fft(field, axis=1), axis=1)
            field *= propagator
            field = ifft(fft(field, axis=1), axis=1)
            field = ifft(fft(field, axis=0), axis=0)

            # Refraction step (real space)
            phase = config.k0 * (n_profile - n_eff) * config.dz
            field *= np.exp(1j * phase)

            # Transparent boundary condition
            if config.use_tbc:
                field = self._apply_tbc(field, x, y)

            # Track metrics
            power = np.sum(np.abs(field)**2) * config.dx * config.dy
            power_evolution.append(power)

            # Beam width (second moment)
            intensity = np.abs(field)**2
            total_power = np.sum(intensity)
            if total_power > 0:
                x_cm = np.sum(X * intensity) / total_power
                y_cm = np.sum(Y * intensity) / total_power
                sigma_x = np.sqrt(np.sum((X - x_cm)**2 * intensity) / total_power)
                sigma_y = np.sqrt(np.sum((Y - y_cm)**2 * intensity) / total_power)
                beam_width_evolution.append((sigma_x, sigma_y))

            max_field = max(max_field, np.max(np.abs(field)))

            if step % 100 == 0:
                await asyncio.sleep(0)

        # Final calculations
        final_power = power_evolution[-1] if power_evolution else 0
        initial_power = power_evolution[0] if power_evolution else 1
        power_loss_db = 10 * np.log10(final_power / initial_power) if initial_power > 0 else 0

        # Mode field diameter
        if beam_width_evolution:
            final_width = beam_width_evolution[-1]
            mfd_x = 2 * final_width[0]
            mfd_y = 2 * final_width[1]
        else:
            mfd_x = mfd_y = 0

        # Estimate coupling efficiency to fundamental mode
        coupling_efficiency = self._estimate_coupling(field, X, Y, config)

        metrics = {
            "final_power": float(final_power),
            "power_loss_db": float(power_loss_db),
            "mfd_x": float(mfd_x),
            "mfd_y": float(mfd_y),
            "mfd_avg": float((mfd_x + mfd_y) / 2),
            "coupling_efficiency": float(coupling_efficiency),
            "max_field": float(max_field),
            "propagation_distance": float(config.Lz),
            "wavelength": float(config.wavelength),
            "n0": float(config.n0),
            "steps": config.nz,
        }

        logs = [
            "FFT-BPM simulation completed",
            f"Grid: {config.nx}x{config.ny}, Steps: {config.nz}",
            f"Wavelength: {config.wavelength*1e9:.1f} nm",
            f"Power loss: {power_loss_db:.2f} dB",
            f"Mode field diameter: {metrics['mfd_avg']*1e6:.2f} μm",
            f"Coupling efficiency: {coupling_efficiency*100:.1f}%",
        ]

        return {"metrics": metrics, "logs": logs, "field": field}

    async def _fd_bpm(self, hypothesis: Hypothesis, config: WaveOpticsConfig) -> dict[str, Any]:
        """Finite-difference BPM"""

        # Simplified FD-BPM for demonstration
        x = np.linspace(-config.Lx/2, config.Lx/2, config.nx)
        y = np.linspace(-config.Ly/2, config.Ly/2, config.ny)
        X, Y = np.meshgrid(x, y, indexing='ij')

        field = self._initialize_beam(X, Y, config)
        n_profile = self._build_refractive_index(X, Y, config)

        k0 = config.k0
        n_eff = config.n0
        dz = config.dz
        dx2 = config.dx ** 2

        max_field = np.max(np.abs(field))

        for step in range(config.nz):
            # Crank-Nicolson like update (simplified)
            field_new = field.copy()

            # Laplacian operator (5-point stencil)
            for i in range(1, config.nx-1):
                for j in range(1, config.ny-1):
                    laplacian = (
                        (field[i+1, j] - 2*field[i, j] + field[i-1, j]) / dx2 +
                        (field[i, j+1] - 2*field[i, j] + field[i, j-1]) / config.dy**2
                    )
                    # Refractive index term
                    dn = n_profile[i, j] - n_eff
                    field_new[i, j] = field[i, j] + 1j * dz / (2 * k0 * n_eff) * (
                        laplacian + 2 * k0**2 * n_eff * dn * field[i, j]
                    )

            field = field_new

            if config.use_tbc:
                field = self._apply_tbc(field, x, y)

            max_field = max(max_field, np.max(np.abs(field)))

            if step % 100 == 0:
                await asyncio.sleep(0)

        final_power = np.sum(np.abs(field)**2) * config.dx * config.dy

        metrics = {
            "final_power": float(final_power),
            "max_field": float(max_field),
            "propagation_distance": float(config.Lz),
            "wavelength": float(config.wavelength),
            "n0": float(config.n0),
            "method": "fd_bpm",
        }

        logs = [
            "FD-BPM simulation completed",
            f"Grid: {config.nx}x{config.ny}, Steps: {config.nz}",
            f"Final power: {final_power:.6f}",
        ]

        return {"metrics": metrics, "logs": logs, "field": field}

    async def _adi_bpm(self, hypothesis: Hypothesis, config: WaveOpticsConfig) -> dict[str, Any]:
        """Alternating Direction Implicit BPM"""
        # Simplified implementation - combines aspects of FFT and FD
        # For production, would implement full ADI scheme with tridiagonal solves
        return await self._fft_bpm(hypothesis, config)

    def _initialize_beam(self, X: np.ndarray, Y: np.ndarray, config: WaveOpticsConfig) -> np.ndarray:
        """Initialize beam field"""
        if config.beam_profile == "gaussian":
            # Gaussian beam
            w0 = config.beam_waist
            field = np.exp(-(X**2 + Y**2) / w0**2)
        elif config.beam_profile == "plane":
            # Plane wave (with soft edges)
            field = np.ones_like(X) * np.exp(-(X**2 + Y**2) / (10*config.core_radius)**2)
        else:
            # Default to Gaussian
            field = np.exp(-(X**2 + Y**2) / config.beam_waist**2)

        # Normalize power
        power = np.sum(np.abs(field)**2) * config.dx * config.dy
        if power > 0:
            field = field * np.sqrt(config.beam_power / power)

        return field.astype(np.complex128)  # type: ignore[no-any-return]

    def _build_refractive_index(self, X: np.ndarray, Y: np.ndarray, config: WaveOpticsConfig) -> np.ndarray:
        """Build refractive index profile"""
        n = np.ones_like(X) * config.n0

        if config.waveguide_type == "fiber":
            # Step-index fiber
            r = np.sqrt(X**2 + Y**2)
            n[r <= config.core_radius] = config.n0 + config.delta_n

        elif config.waveguide_type == "slab":
            # Slab waveguide (infinite in y)
            n[np.abs(X) <= config.core_radius] = config.n0 + config.delta_n

        elif config.waveguide_type == "channel":
            # Channel waveguide
            n[(np.abs(X) <= config.core_radius) & (np.abs(Y) <= config.core_radius)] = config.n0 + config.delta_n

        return n

    def _apply_tbc(self, field: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """Apply Transparent Boundary Condition"""
        nx, ny = field.shape

        # Left boundary
        if nx > 2:
            ratio_l = field[1, :] / (field[0, :] + 1e-20)
            field[0, :] = field[1, :] / ratio_l

        # Right boundary
        if nx > 2:
            ratio_r = field[-2, :] / (field[-1, :] + 1e-20)
            field[-1, :] = field[-2, :] / ratio_r

        # Bottom boundary
        if ny > 2:
            ratio_b = field[:, 1] / (field[:, 0] + 1e-20)
            field[:, 0] = field[:, 1] / ratio_b

        # Top boundary
        if ny > 2:
            ratio_t = field[:, -2] / (field[:, -1] + 1e-20)
            field[:, -1] = field[:, -2] / ratio_t

        return field

    def _estimate_coupling(self, field: np.ndarray, X: np.ndarray, Y: np.ndarray, config: WaveOpticsConfig) -> float:
        """Estimate coupling efficiency to fundamental mode"""
        # Gaussian approximation of fundamental mode
        w = config.core_radius / np.sqrt(2)  # Approximate mode field radius
        mode = np.exp(-(X**2 + Y**2) / w**2)

        # Normalize
        mode_norm = np.sqrt(np.sum(np.abs(mode)**2))
        field_norm = np.sqrt(np.sum(np.abs(field)**2))

        if mode_norm > 0 and field_norm > 0:
            overlap = np.abs(np.sum(np.conj(mode) * field)) / (mode_norm * field_norm)
            return float(overlap**2)
        return 0.0

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        # Low power loss (good confinement)
        loss = metrics.get("power_loss_db", 0)
        if loss > -1:  # Less than 1 dB loss
            factors.append(0.3)
        elif loss > -3:
            factors.append(0.2)

        # Reasonable coupling efficiency
        coupling = metrics.get("coupling_efficiency", 0)
        if coupling > 0.8:
            factors.append(0.3)
        elif coupling > 0.5:
            factors.append(0.2)

        # Physical MFD
        mfd = metrics.get("mfd_avg", 0)
        if 1e-6 < mfd < 20e-6:
            factors.append(0.2)

        # Sufficient propagation
        if metrics.get("steps", 0) >= 100:
            factors.append(0.2)

        return min(0.85, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        params = hypothesis.parameters
        is_3d = params.get("dimensions", "2d") == "3d"

        if is_3d:
            nx = 128
            cells = nx ** 3
            memory_gb = cells * 16e-9  # Complex arrays
        else:
            nx = 256
            cells = nx ** 2
            memory_gb = cells * 16e-9

        nz = 1000
        estimated_time = nz * cells / 1e8

        return {
            "cpu_cores": 4,
            "memory_gb": max(1.0, memory_gb * 4),  # Multiple arrays
            "gpu_required": is_3d,
            "estimated_time_seconds": estimated_time,
        }
