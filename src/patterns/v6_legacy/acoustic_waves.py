"""
Pattern 23: Acoustic Waves (Spectral Methods)

Christopher Alexander Structure:
- Context: Simulating wave propagation in fluids and gases for acoustics,
  ultrasound, room acoustics, and seismic waves. Requires high accuracy
  over many wavelengths.
- Forces:
  * Numerical dispersion must be minimized for wave problems
  * Need for high-order accuracy in smooth regions
  * Computational cost of high-resolution simulations
  * Boundary condition implementation for complex geometries
- Solution: Spectral methods using Fourier/Chebyshev basis achieve exponential
  convergence. Pseudospectral collocation for nonlinear terms. Perfectly
  Matched Layers (PML) for absorbing boundaries.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Tuple
import numpy as np

try:
    from .base import BasePattern, BaseConfig, GPUMixin
except ImportError:
    from base import BasePattern, BaseConfig, GPUMixin


@dataclass
class AcousticWavesConfig(BaseConfig):
    """Configuration for Acoustic Waves simulation."""

    # Grid parameters
    nx: int = 128
    ny: int = 128
    nz: int = 1  # 2D if nz=1, 3D otherwise

    # Domain
    Lx: float = 1.0
    Ly: float = 1.0
    Lz: float = 1.0

    # Physics
    c0: float = 343.0  # Speed of sound (m/s)
    rho0: float = 1.225  # Ambient density (kg/m³)

    # Time stepping
    dt: float = None  # Computed from CFL
    n_steps: int = 500
    cfl: float = 0.5

    # Source
    source_type: str = "gaussian_pulse"  # "gaussian_pulse", "harmonic", "point"
    source_frequency: float = 1000.0  # Hz
    source_position: Tuple[float, ...] = (0.5, 0.5, 0.5)
    source_amplitude: float = 1.0

    # Boundaries
    boundary_type: str = "pml"  # "pml", "periodic", "rigid"
    pml_width: int = 16
    pml_sigma_max: float = 5.0

    # Method
    method: str = "pseudospectral"  # "pseudospectral", "fd", "spectral_element"

    def __post_init__(self):
        if self.dt is None:
            dx = self.Lx / self.nx
            self.dt = self.cfl * dx / self.c0


class AcousticWaves(BasePattern, GPUMixin):
    """
    Acoustic wave propagation using spectral methods.
    Complexity: O(N log N) per step with FFT, O(N) with FD.
    """

    PATTERN_ID = "acoustic_waves"
    PATTERN_VERSION = "6.5.0"

    def __init__(self, config: Optional[AcousticWavesConfig] = None):
        BasePattern.__init__(self, config or AcousticWavesConfig())
        GPUMixin.__init__(self)
        self.config: AcousticWavesConfig = self.config

        # Fields
        self.p: np.ndarray = None  # Pressure
        self.vx: np.ndarray = None  # x-velocity
        self.vy: np.ndarray = None  # y-velocity
        self.vz: np.ndarray = None  # z-velocity (3D only)

        # PML damping
        self.sigma_x: np.ndarray = None
        self.sigma_y: np.ndarray = None
        self.sigma_z: np.ndarray = None

        # Spectral operators
        self.kx: np.ndarray = None
        self.ky: np.ndarray = None
        self.kz: np.ndarray = None

        self._initialize_grid()
        self._initialize_fields()
        self._setup_pml()
        if self.config.method == "pseudospectral":
            self._setup_spectral_operators()

    def _initialize_grid(self):
        """Initialize computational grid."""
        nx, ny, nz = self.config.nx, self.config.ny, self.config.nz
        Lx, Ly, Lz = self.config.Lx, self.config.Ly, self.config.Lz

        # Physical coordinates
        self.x = np.linspace(0, Lx, nx, endpoint=False)
        self.y = np.linspace(0, Ly, ny, endpoint=False)
        if nz > 1:
            self.z = np.linspace(0, Lz, nz, endpoint=False)
            self.X, self.Y, self.Z = np.meshgrid(self.x, self.y, self.z, indexing="ij")
        else:
            self.X, self.Y = np.meshgrid(self.x, self.y, indexing="ij")

        self.dx = Lx / nx
        self.dy = Ly / ny
        if nz > 1:
            self.dz = Lz / nz

    def _initialize_fields(self):
        """Initialize pressure and velocity fields."""
        nx, ny, nz = self.config.nx, self.config.ny, self.config.nz

        if nz > 1:
            self.p = np.zeros((nx, ny, nz))
            self.vx = np.zeros((nx, ny, nz))
            self.vy = np.zeros((nx, ny, nz))
            self.vz = np.zeros((nx, ny, nz))
        else:
            self.p = np.zeros((nx, ny))
            self.vx = np.zeros((nx, ny))
            self.vy = np.zeros((nx, ny))

        # Initial condition - Gaussian pulse
        if self.config.source_type == "gaussian_pulse":
            sx, sy, sz = self.config.source_position
            sigma = 0.05
            if nz > 1:
                r2 = (self.X - sx) ** 2 + (self.Y - sy) ** 2 + (self.Z - sz) ** 2
            else:
                r2 = (self.X - sx) ** 2 + (self.Y - sy) ** 2
            self.p = self.config.source_amplitude * np.exp(-r2 / (2 * sigma**2))

    def _setup_pml(self):
        """Setup Perfectly Matched Layer damping profiles."""
        nx, ny, nz = self.config.nx, self.config.ny, self.config.nz
        pml_w = self.config.pml_width
        sigma_max = self.config.pml_sigma_max

        # 1D damping profiles
        damping_x = np.zeros(nx)
        damping_y = np.zeros(ny)

        # Left/right PML
        for i in range(min(pml_w, nx // 2)):
            damping_x[i] = sigma_max * ((pml_w - i) / pml_w) ** 2
            damping_x[nx - 1 - i] = sigma_max * ((pml_w - i) / pml_w) ** 2

        # Bottom/top PML
        for j in range(min(pml_w, ny // 2)):
            damping_y[j] = sigma_max * ((pml_w - j) / pml_w) ** 2
            damping_y[ny - 1 - j] = sigma_max * ((pml_w - j) / pml_w) ** 2

        # Expand to full grids
        if nz > 1:
            damping_z = np.zeros(nz)
            for k in range(min(pml_w, nz // 2)):
                damping_z[k] = sigma_max * ((pml_w - k) / pml_w) ** 2
                damping_z[nz - 1 - k] = sigma_max * ((pml_w - k) / pml_w) ** 2

            self.sigma_x = damping_x[:, np.newaxis, np.newaxis]
            self.sigma_y = damping_y[np.newaxis, :, np.newaxis]
            self.sigma_z = damping_z[np.newaxis, np.newaxis, :]
        else:
            self.sigma_x = damping_x[:, np.newaxis]
            self.sigma_y = damping_y[np.newaxis, :]
            self.sigma_z = np.zeros((nx, ny))

    def _setup_spectral_operators(self):
        """Setup wave number grids for spectral differentiation."""
        nx, ny, nz = self.config.nx, self.config.ny, self.config.nz
        Lx, Ly, Lz = self.config.Lx, self.config.Ly, self.config.Lz

        # Fourier wave numbers
        self.kx = 2 * np.pi * np.fft.fftfreq(nx, Lx / nx)
        self.ky = 2 * np.pi * np.fft.fftfreq(ny, Ly / ny)

        if nz > 1:
            self.kz = 2 * np.pi * np.fft.fftfreq(nz, Lz / nz)
            self.KX, self.KY, self.KZ = np.meshgrid(
                self.kx, self.ky, self.kz, indexing="ij"
            )
        else:
            self.KX, self.KY = np.meshgrid(self.kx, self.ky, indexing="ij")

    def _spectral_gradient(
        self, field: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Compute gradient using FFT."""
        # FFT
        field_hat = np.fft.fftn(field)

        # Spectral differentiation
        grad_x_hat = 1j * self.KX * field_hat
        grad_y_hat = 1j * self.KY * field_hat

        grad_x = np.real(np.fft.ifftn(grad_x_hat))
        grad_y = np.real(np.fft.ifftn(grad_y_hat))

        if self.config.nz > 1:
            grad_z_hat = 1j * self.KZ * field_hat
            grad_z = np.real(np.fft.ifftn(grad_z_hat))
        else:
            grad_z = np.zeros_like(grad_x)

        return grad_x, grad_y, grad_z

    def _spectral_divergence(
        self, vx: np.ndarray, vy: np.ndarray, vz: np.ndarray
    ) -> np.ndarray:
        """Compute divergence using FFT."""
        vx_hat = np.fft.fftn(vx)
        vy_hat = np.fft.fftn(vy)

        div_hat = 1j * self.KX * vx_hat + 1j * self.KY * vy_hat

        if self.config.nz > 1:
            vz_hat = np.fft.fftn(vz)
            div_hat += 1j * self.KZ * vz_hat

        return np.real(np.fft.ifftn(div_hat))

    def _fd_gradient(
        self, field: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Compute gradient using 4th-order finite differences."""
        grad_x = np.zeros_like(field)
        grad_y = np.zeros_like(field)

        # Interior points
        grad_x[2:-2] = (-field[4:] + 8 * field[3:-1] - 8 * field[1:-3] + field[:-4]) / (
            12 * self.dx
        )
        grad_y[:, 2:-2] = (
            -field[:, 4:] + 8 * field[:, 3:-1] - 8 * field[:, 1:-3] + field[:, :-4]
        ) / (12 * self.dy)

        # Boundaries (2nd order)
        grad_x[0] = (field[1] - field[0]) / self.dx
        grad_x[-1] = (field[-1] - field[-2]) / self.dx
        grad_y[:, 0] = (field[:, 1] - field[:, 0]) / self.dy
        grad_y[:, -1] = (field[:, -1] - field[:, -2]) / self.dy

        if self.config.nz > 1:
            grad_z = np.zeros_like(field)
            grad_z[:, :, 2:-2] = (
                -field[:, :, 4:]
                + 8 * field[:, :, 3:-1]
                - 8 * field[:, :, 1:-3]
                + field[:, :, :-4]
            ) / (12 * self.dz)
            return grad_x, grad_y, grad_z

        return grad_x, grad_y, np.zeros_like(grad_x)

    def _fd_divergence(
        self, vx: np.ndarray, vy: np.ndarray, vz: np.ndarray
    ) -> np.ndarray:
        """Compute divergence using finite differences."""
        _, grad_vx_x, _ = self._fd_gradient(vx)
        _, _, grad_vy_y = self._fd_gradient(vy)

        div = grad_vx_x + grad_vy_y

        if self.config.nz > 1:
            _, _, grad_vz_z = self._fd_gradient(vz)
            div += grad_vz_z

        return div

    def _add_source(self, step: int):
        """Add source term."""
        nx, ny, nz = self.config.nx, self.config.ny, self.config.nz
        sx, sy, sz = self.config.source_position

        # Convert to grid indices
        ix = int(sx / self.config.Lx * nx)
        iy = int(sy / self.config.Ly * ny)

        if self.config.source_type == "harmonic":
            # Continuous harmonic source
            t = step * self.config.dt
            omega = 2 * np.pi * self.config.source_frequency
            source_val = self.config.source_amplitude * np.sin(omega * t)

            if nz > 1:
                iz = int(sz / self.config.Lz * nz)
                self.p[ix, iy, iz] += source_val
            else:
                self.p[ix, iy] += source_val

        elif self.config.source_type == "gaussian_pulse" and step == 0:
            # Already initialized
            pass

    def _step_pseudospectral(self):
        """Single time step using pseudospectral method."""
        c0 = self.config.c0
        rho0 = self.config.rho0
        dt = self.config.dt
        nz = self.config.nz

        # Compute derivatives
        dp_dx, dp_dy, dp_dz = self._spectral_gradient(self.p)
        if nz > 1:
            div_v = self._spectral_divergence(self.vx, self.vy, self.vz)
        else:
            vz = np.zeros_like(self.vx)
            div_v = self._spectral_divergence(self.vx, self.vy, vz)

        # PML damping
        sigma_sum = self.sigma_x + self.sigma_y
        if nz > 1:
            sigma_sum = sigma_sum + self.sigma_z

        # Update pressure (split-field PML)
        self.p -= dt * (c0**2 * rho0 * div_v + sigma_sum * self.p)

        # Update velocities
        self.vx -= dt * (dp_dx / rho0 + self.sigma_x * self.vx)
        self.vy -= dt * (dp_dy / rho0 + self.sigma_y * self.vy)
        if nz > 1:
            self.vz -= dt * (dp_dz / rho0 + self.sigma_z * self.vz)

    def _step_fd(self):
        """Single time step using finite differences."""
        c0 = self.config.c0
        rho0 = self.config.rho0
        dt = self.config.dt
        nz = self.config.nz

        # Compute derivatives
        dp_dx, dp_dy, dp_dz = self._fd_gradient(self.p)
        if nz > 1:
            div_v = self._fd_divergence(self.vx, self.vy, self.vz)
        else:
            vz = np.zeros_like(self.vx)
            div_v = self._fd_divergence(self.vx, self.vy, vz)

        # PML damping
        sigma_sum = self.sigma_x + self.sigma_y
        if nz > 1:
            sigma_sum = sigma_sum + self.sigma_z

        # Update
        self.p -= dt * (c0**2 * rho0 * div_v + sigma_sum * self.p)
        self.vx -= dt * (dp_dx / rho0 + self.sigma_x * self.vx)
        self.vy -= dt * (dp_dy / rho0 + self.sigma_y * self.vy)
        if nz > 1:
            self.vz -= dt * (dp_dz / rho0 + self.sigma_z * self.vz)

    def _compute_energy(self) -> Tuple[float, float]:
        """Compute acoustic energy (potential + kinetic)."""
        # Potential energy ~ p^2 / (2 * rho0 * c0^2)
        pe = np.sum(self.p**2) / (2 * self.config.rho0 * self.config.c0**2)
        pe *= self.dx * self.dy
        if self.config.nz > 1:
            pe *= self.dz

        # Kinetic energy ~ 0.5 * rho0 * v^2
        v2 = self.vx**2 + self.vy**2
        if self.config.nz > 1:
            v2 += self.vz**2
        ke = 0.5 * self.config.rho0 * np.sum(v2)
        ke *= self.dx * self.dy
        if self.config.nz > 1:
            ke *= self.dz

        return pe, ke

    def run(self, hypothesis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute acoustic wave simulation.

        Returns:
            Dictionary with pressure field, energy history, and wave metrics.
        """
        pressure_history = []
        energy_history = []

        # Record initial state
        pe, ke = self._compute_energy()
        energy_history.append(
            {"step": 0, "potential": pe, "kinetic": ke, "total": pe + ke}
        )

        for step in range(self.config.n_steps):
            # Add source
            self._add_source(step)

            # Time step
            if self.config.method == "pseudospectral":
                self._step_pseudospectral()
            else:
                self._step_fd()

            # Record history
            if step % 10 == 0:
                pressure_history.append(self.p.copy())
                pe, ke = self._compute_energy()
                energy_history.append(
                    {"step": step + 1, "potential": pe, "kinetic": ke, "total": pe + ke}
                )

        # Statistics
        max_pressure = np.max(np.abs(self.p))
        rms_pressure = np.sqrt(np.mean(self.p**2))

        return {
            "pattern_id": self.PATTERN_ID,
            "final_pressure": self.p,
            "final_vx": self.vx,
            "final_vy": self.vy,
            "max_pressure": max_pressure,
            "rms_pressure": rms_pressure,
            "pressure_history": pressure_history,
            "energy_history": energy_history,
            "energy_drift": abs(
                energy_history[-1]["total"] - energy_history[0]["total"]
            )
            / energy_history[0]["total"],
            "wavelength": self.config.c0 / self.config.source_frequency,
            "points_per_wavelength": (self.config.c0 / self.config.source_frequency)
            / self.dx,
            "courant_number": self.config.c0 * self.config.dt / self.dx,
            "method": self.config.method,
        }

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        return {
            "pattern_id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Acoustic Waves (Spectral Methods)",
            "context": "When simulating wave propagation in fluids/gases requiring high "
            "accuracy over many wavelengths. Applications include room acoustics, "
            "ultrasound imaging, and seismic wave propagation.",
            "forces": [
                "Numerical dispersion: Low-order methods accumulate phase errors",
                "High accuracy requirement: Many wavelengths need consistent phase",
                "Computational cost: High resolution simulations are expensive",
                "Boundary absorption: Open boundaries need non-reflecting conditions",
                "Long-time stability: Energy must be conserved or correctly dissipated",
            ],
            "solution": "Pseudospectral methods use Fourier/Chebyshev basis functions "
            "achieving exponential convergence for smooth solutions. "
            "The wave equation is solved in spatial Fourier space where "
            "derivatives are exact (multiplication by ik). PML provides "
            "effective absorption at boundaries with minimal reflection. "
            "Split-field formulation handles PML damping correctly.",
            "complexity": "O(N log N) per step with FFT, O(N) with finite differences",
            "domain": "Acoustics, ultrasound, room acoustics, seismology, aeroacoustics",
            "parameters": [
                "c0: Speed of sound",
                "source_frequency: Driving frequency for harmonic sources",
                "pml_width: Thickness of absorbing layer",
                "method: Pseudospectral or finite difference",
            ],
        }
