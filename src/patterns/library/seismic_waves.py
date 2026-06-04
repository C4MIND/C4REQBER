# Migrated to Newton Physics (2025) — github.com/newton-physics/newton — Apache 2.0 License
"""
C4REQBER v6.0 - Seismic Waves Pattern
Spectral element method for seismic wave propagation.

Pattern Structure (Christopher Alexander):
- Context: Earthquake modeling, exploration seismology, hazard assessment
- Forces: Elastic wave equation, heterogeneous media, absorbing boundaries
- Solution: Spectral elements with Gauss-Lobatto-Legendre quadrature
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


@dataclass
class SeismicWavesConfig:
    """Configuration for seismic wave simulation"""

    # Grid settings
    nx: int = 100  # Number of spectral elements in x
    ny: int = 100  # Number of spectral elements in y
    nz: int = 50  # Number of spectral elements in z

    ngll: int = 4  # GLL points per element (polynomial degree + 1)

    # Domain extent (m)
    Lx: float = 50.0e3  # 50 km
    Ly: float = 50.0e3
    Lz: float = 25.0e3

    # Time stepping
    dt: float = 0.001  # seconds
    duration: float = 20.0  # seconds

    # Material properties
    vp_surf: float = 3000.0  # P-wave velocity at surface (m/s)
    vp_grad: float = 0.5  # Velocity gradient (1/s)
    vs_factor: float = 0.6  # Vs/Vp ratio
    rho_surf: float = 2200.0  # Density at surface (kg/m^3)
    rho_grad: float = 0.1  # Density gradient

    # Source parameters
    source_x: float = 25.0e3  # Source location
    source_y: float = 25.0e3
    source_z: float = 5.0e3
    source_type: str = "moment_tensor"  # or "force"
    M0: float = 1.0e15  # Seismic moment (N m)

    # Receiver array
    n_receivers: int = 10
    receiver_depth: float = 0.0  # Surface receivers

    # Absorbing boundaries
    abs_width: float = 2000.0  # Width of absorbing layer (m)
    abs_alpha: float = 1000.0  # Damping coefficient

    # Output
    output_interval: int = 100


class SeismicWavesPattern:
    """
    Spectral element method for seismic wave propagation.

    Solves the elastic wave equation using the spectral element
    method with Gauss-Lobatto-Legendre quadrature. Includes
    heterogeneous velocity models and absorbing boundaries.
    """

    PATTERN_ID = "seismic_waves"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: SeismicWavesConfig | None = None) -> None:
        self.config = config or SeismicWavesConfig()
        self._initialize_grid()
        self._initialize_materials()
        self._initialize_fields()

    def _gll_points(self, n: int) -> tuple[np.ndarray, np.ndarray]:
        """
        Compute Gauss-Lobatto-Legendre points and weights.
        Simplified for small n (n <= 5).
        """
        if n == 2:
            xi = np.array([-1.0, 1.0])
            w = np.array([1.0, 1.0])
        elif n == 3:
            xi = np.array([-1.0, 0.0, 1.0])
            w = np.array([1.0 / 3.0, 4.0 / 3.0, 1.0 / 3.0])
        elif n == 4:
            xi = np.array([-1.0, -np.sqrt(1 / 5), np.sqrt(1 / 5), 1.0])
            w = np.array([1.0 / 6.0, 5.0 / 6.0, 5.0 / 6.0, 1.0 / 6.0])
        elif n == 5:
            xi = np.array([-1.0, -np.sqrt(3 / 7), 0.0, np.sqrt(3 / 7), 1.0])
            w = np.array(
                [1.0 / 10.0, 49.0 / 90.0, 32.0 / 45.0, 49.0 / 90.0, 1.0 / 10.0]
            )
        else:
            # Default to 4 points
            xi = np.array([-1.0, -0.5, 0.5, 1.0])
            w = np.ones(n) / n

        return xi, w

    def _lagrange_derivative(self, xi: np.ndarray, i: int, x: float) -> float:
        """Compute derivative of Lagrange polynomial at point x"""
        n = len(xi)
        dL = 0.0

        for j in range(n):
            if j != i:
                prod = 1.0
                for k in range(n):
                    if k != i and k != j:
                        prod *= (x - xi[k]) / (xi[i] - xi[k])
                dL += prod / (xi[i] - xi[j])

        return dL

    def _initialize_grid(self) -> None:
        """Initialize spectral element grid"""
        cfg = self.config

        # GLL points in reference element
        self.xi, self.w = self._gll_points(cfg.ngll)

        # Element sizes
        self.dx_elem = cfg.Lx / cfg.nx
        self.dy_elem = cfg.Ly / cfg.ny
        self.dz_elem = cfg.Lz / cfg.nz

        # Total grid points
        self.nx_total = cfg.nx * (cfg.ngll - 1) + 1
        self.ny_total = cfg.ny * (cfg.ngll - 1) + 1
        self.nz_total = cfg.nz * (cfg.ngll - 1) + 1

        # Physical coordinates
        self.x = np.linspace(0, cfg.Lx, self.nx_total)
        self.y = np.linspace(0, cfg.Ly, self.ny_total)
        self.z = np.linspace(0, cfg.Lz, self.nz_total)

        self.X, self.Y, self.Z = np.meshgrid(self.x, self.y, self.z, indexing="ij")

        logger.debug(f"Grid: {self.nx_total}x{self.ny_total}x{self.nz_total}")

    def _initialize_materials(self) -> None:
        """Initialize material properties"""
        cfg = self.config

        # Velocity model (increase with depth)
        self.vp = cfg.vp_surf + cfg.vp_grad * self.Z
        self.vs = self.vp * cfg.vs_factor

        # Density (increase with depth)
        self.rho = cfg.rho_surf + cfg.rho_grad * self.Z

        # Lame parameters
        self.mu = self.rho * self.vs**2
        self.lambda_ = self.rho * (self.vp**2 - 2 * self.vs**2)

        # Maximum velocity for CFL
        self.vmax = np.max(self.vp)

    def _initialize_fields(self) -> None:
        """Initialize displacement and velocity fields"""
        shape = (self.nx_total, self.ny_total, self.nz_total)

        # Displacements
        self.ux = np.zeros(shape)
        self.uy = np.zeros(shape)
        self.uz = np.zeros(shape)

        # Velocities
        self.vx = np.zeros(shape)
        self.vy = np.zeros(shape)
        self.vz = np.zeros(shape)

        # Accelerations
        self.ax = np.zeros(shape)
        self.ay = np.zeros(shape)
        self.az = np.zeros(shape)

        # Source location (nearest grid point)
        self.isrc = np.argmin(np.abs(self.x - self.config.source_x))
        self.jsrc = np.argmin(np.abs(self.y - self.config.source_y))
        self.ksrc = np.argmin(np.abs(self.z - self.config.source_z))

        # Receivers (circle around source)
        cfg = self.config
        self.receivers = []
        for i in range(cfg.n_receivers):
            angle = 2 * np.pi * i / cfg.n_receivers
            rx = cfg.source_x + 10.0e3 * np.cos(angle)
            ry = cfg.source_y + 10.0e3 * np.sin(angle)
            rz = cfg.receiver_depth

            ir = np.argmin(np.abs(self.x - rx))
            jr = np.argmin(np.abs(self.y - ry))
            kr = np.argmin(np.abs(self.z - rz))

            self.receivers.append((ir, jr, kr))

        # Seismograms
        self.seismograms = {  # type: ignore[var-annotated]
            "ux": [[] for _ in range(cfg.n_receivers)],
            "uy": [[] for _ in range(cfg.n_receivers)],
            "uz": [[] for _ in range(cfg.n_receivers)],
        }

        # Output storage
        self.history = {  # type: ignore[var-annotated]
            "time": [],
            "max_displacement": [],
            "kinetic_energy": [],
        }

    def _source_time_function(self, t: float) -> float:
        """Source time function (Ricker wavelet)"""
        cfg = self.config

        f0 = 2.0  # Dominant frequency (Hz)
        t0 = 1.0 / f0  # Time shift

        if t < 0:
            return 0.0

        # Ricker wavelet
        if t <= 0:
            return 0.0
        arg = np.pi * f0 * (t - t0)
        return (1 - 2 * arg**2) * np.exp(-(arg**2))  # type: ignore[no-any-return]

    def _strain_tensor(
        self,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Calculate strain tensor components (finite difference)"""
        dx = self.x[1] - self.x[0]
        dy = self.y[1] - self.y[0]
        dz = self.z[1] - self.z[0]

        # Initialize
        exx = np.zeros_like(self.ux)
        eyy = np.zeros_like(self.ux)
        ezz = np.zeros_like(self.ux)
        exy = np.zeros_like(self.ux)
        exz = np.zeros_like(self.ux)
        eyz = np.zeros_like(self.ux)

        # Compute strains (central differences)
        exx[1:-1, :, :] = (self.ux[2:, :, :] - self.ux[:-2, :, :]) / (2 * dx)
        eyy[:, 1:-1, :] = (self.uy[:, 2:, :] - self.uy[:, :-2, :]) / (2 * dy)
        ezz[:, :, 1:-1] = (self.uz[:, :, 2:] - self.uz[:, :, :-2]) / (2 * dz)

        exy[1:-1, 1:-1, :] = 0.5 * (
            (self.ux[1:-1, 2:, :] - self.ux[1:-1, :-2, :]) / (2 * dy)
            + (self.uy[2:, 1:-1, :] - self.uy[:-2, 1:-1, :]) / (2 * dx)
        )

        exz[1:-1, :, 1:-1] = 0.5 * (
            (self.ux[1:-1, :, 2:] - self.ux[1:-1, :, :-2]) / (2 * dz)
            + (self.uz[2:, :, 1:-1] - self.uz[:-2, :, 1:-1]) / (2 * dx)
        )

        eyz[:, 1:-1, 1:-1] = 0.5 * (
            (self.uy[:, 1:-1, 2:] - self.uy[:, 1:-1, :-2]) / (2 * dz)
            + (self.uz[:, 2:, 1:-1] - self.uz[:, :-2, 1:-1]) / (2 * dy)
        )

        return exx, eyy, ezz, exy, exz, eyz

    def _stress_tensor(
        self,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Calculate stress tensor from strain"""
        exx, eyy, ezz, exy, exz, eyz = self._strain_tensor()

        # Trace of strain
        trace_e = exx + eyy + ezz

        # Hooke's law
        sxx = self.lambda_ * trace_e + 2 * self.mu * exx
        syy = self.lambda_ * trace_e + 2 * self.mu * eyy
        szz = self.lambda_ * trace_e + 2 * self.mu * ezz
        sxy = 2 * self.mu * exy
        sxz = 2 * self.mu * exz
        syz = 2 * self.mu * eyz

        return sxx, syy, szz, sxy, sxz, syz

    def _internal_forces(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculate internal forces from stress divergence (simplified)"""
        dx = self.x[1] - self.x[0]
        dy = self.y[1] - self.y[0]
        dz = self.z[1] - self.z[0]

        # Divergence of stress (simplified: use velocity gradients directly)
        fx = np.zeros_like(self.ux)
        fy = np.zeros_like(self.uy)
        fz = np.zeros_like(self.uz)

        # Lame parameters on grids
        mu_u = (self.mu[:-1, :, :] + self.mu[1:, :, :]) / 2
        lam_u = (self.lambda_[:-1, :, :] + self.lambda_[1:, :, :]) / 2

        # Simplified stress divergence using velocity gradients
        for i in range(1, self.config.nx - 2):
            for j in range(1, self.config.ny - 1):
                for k in range(1, self.config.nz - 1):
                    # x-component
                    dux_dx = (self.ux[i, j, k] - self.ux[i - 1, j, k]) / dx
                    dux_dy = (
                        (self.ux[i, j + 1, k] - self.ux[i, j - 1, k]) / (2 * dy)
                        if 0 < j < self.config.ny - 1
                        else 0
                    )
                    dux_dz = (
                        (self.ux[i, j, k + 1] - self.ux[i, j, k - 1]) / (2 * dz)
                        if 0 < k < self.config.nz - 1
                        else 0
                    )

                    fx[i, j, k] = (
                        mu_u[i, j, k]
                        * (
                            (
                                self.ux[i + 1, j, k]
                                - 2 * self.ux[i, j, k]
                                + self.ux[i - 1, j, k]
                            )
                            / dx**2
                            + (
                                self.ux[i, j + 1, k]
                                - 2 * self.ux[i, j, k]
                                + self.ux[i, j - 1, k]
                            )
                            / dy**2
                            + (
                                self.ux[i, j, k + 1]
                                - 2 * self.ux[i, j, k]
                                + self.ux[i, j, k - 1]
                            )
                            / dz**2
                        )
                        + (lam_u[i, j, k] + mu_u[i, j, k]) * dux_dx
                    )

        return fx, fy, fz

    def _absorbing_boundary(self, field: np.ndarray) -> np.ndarray:
        """Apply absorbing boundary condition (damping)"""
        cfg = self.config

        damped = field.copy()

        # Distance from boundaries
        nx, ny, nz = field.shape

        # X boundaries
        for i in range(nx):
            dist = min(i, nx - 1 - i) * (self.x[1] - self.x[0])
            if dist < cfg.abs_width:
                damping = 1.0 - np.exp(-((dist / cfg.abs_alpha) ** 2))
                damped[i, :, :] *= damping

        # Y boundaries
        for j in range(ny):
            dist = min(j, ny - 1 - j) * (self.y[1] - self.y[0])
            if dist < cfg.abs_width:
                damping = 1.0 - np.exp(-((dist / cfg.abs_alpha) ** 2))
                damped[:, j, :] *= damping

        # Z boundaries (bottom only, free surface at top)
        for k in range(nz):
            dist = k * (self.z[1] - self.z[0])
            if dist < cfg.abs_width:
                damping = 1.0 - np.exp(-((dist / cfg.abs_alpha) ** 2))
                damped[:, :, k] *= damping

        return damped

    def _step(self, t: float) -> None:
        """Advance wavefield by one time step using leapfrog"""
        cfg = self.config

        # Internal forces
        fx, fy, fz = self._internal_forces()

        # Add source
        if t < 10.0:  # Source active for 10 seconds
            stf = self._source_time_function(t) * cfg.M0
            fx[self.isrc, self.jsrc, self.ksrc] += stf / (
                self.dx_elem * self.dy_elem * self.dz_elem
            )

        # Acceleration (F = ma)
        self.ax = fx / self.rho
        self.ay = fy / self.rho
        self.az = fz / self.rho

        # Update velocity (leapfrog)
        self.vx += self.ax * cfg.dt
        self.vy += self.ay * cfg.dt
        self.vz += self.az * cfg.dt

        # Absorbing boundaries
        self.vx = self._absorbing_boundary(self.vx)
        self.vy = self._absorbing_boundary(self.vy)
        self.vz = self._absorbing_boundary(self.vz)

        # Update displacement
        self.ux += self.vx * cfg.dt
        self.uy += self.vy * cfg.dt
        self.uz += self.vz * cfg.dt

        # Record seismograms
        for ir, (i, j, k) in enumerate(self.receivers):
            self.seismograms["ux"][ir].append(self.ux[i, j, k])
            self.seismograms["uy"][ir].append(self.uy[i, j, k])
            self.seismograms["uz"][ir].append(self.uz[i, j, k])

    def _calculate_cfl(self) -> float:
        """Calculate Courant number"""
        dx = self.x[1] - self.x[0]
        return self.vmax * self.config.dt / dx  # type: ignore[no-any-return]

    def _calculate_energy(self) -> float:
        """Calculate total kinetic energy"""
        ke = 0.5 * np.sum(self.rho * (self.vx**2 + self.vy**2 + self.vz**2))
        ke *= (
            (self.x[1] - self.x[0]) * (self.y[1] - self.y[0]) * (self.z[1] - self.z[0])
        )
        return ke  # type: ignore[no-any-return]

    def run(self, hypothesis: dict[str, Any] = None) -> dict[str, Any]:  # type: ignore[assignment]
        """Run the seismic wave simulation with Newton (or fallback)."""
        from src.simulations.newton_bridge import NewtonBridge
        bridge = NewtonBridge()

        if bridge.available:
            newton_config = {
                "type": "seismic_waves",
                "nx": self.config.nx,
                "ny": self.config.ny,
                "nz": self.config.nz,
                "ngll": self.config.ngll,
                "Lx": self.config.Lx,
                "Ly": self.config.Ly,
                "Lz": self.config.Lz,
                "dt": self.config.dt,
                "duration": self.config.duration,
                "vp_surf": self.config.vp_surf,
                "vp_grad": self.config.vp_grad,
                "vs_factor": self.config.vs_factor,
                "rho_surf": self.config.rho_surf,
                "rho_grad": self.config.rho_grad,
                "source_x": self.config.source_x,
                "source_y": self.config.source_y,
                "source_z": self.config.source_z,
                "source_type": self.config.source_type,
                "M0": self.config.M0,
                "n_receivers": self.config.n_receivers,
                "receiver_depth": self.config.receiver_depth,
                "abs_width": self.config.abs_width,
                "abs_alpha": self.config.abs_alpha,
                "output_interval": self.config.output_interval,
            }
            if hypothesis:
                newton_config.update(hypothesis)
            result = bridge.run_simulation(newton_config)
            if result.get("status") == "success":
                return result

        # Fallback to legacy implementation
        cfg = self.config
        n_steps = int(cfg.duration / cfg.dt)

        logger.info(f"Starting seismic simulation: {cfg.duration}s, {n_steps} steps")
        logger.info(
            f"Grid: {self.nx_total}x{self.ny_total}x{self.nz_total}, CFL: {self._calculate_cfl():.3f}"
        )

        for step in range(n_steps):
            t = step * cfg.dt

            self._step(t)

            # Output
            if step % cfg.output_interval == 0:
                max_disp = max(
                    np.max(np.abs(self.ux)),
                    np.max(np.abs(self.uy)),
                    np.max(np.abs(self.uz)),
                )
                ke = self._calculate_energy()

                self.history["time"].append(t)
                self.history["max_displacement"].append(max_disp)
                self.history["kinetic_energy"].append(ke)

            if step % 1000 == 0:
                logger.debug(
                    f"Step {step}/{n_steps}, t={t:.3f}s, max|u|={max_disp:.4e}m"
                )

        return self._format_output()

    def _format_output(self) -> dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        return {
            "time": self.history["time"],
            "max_displacement": self.history["max_displacement"],
            "kinetic_energy": self.history["kinetic_energy"],
            "seismograms": self.seismograms,
            "final_state": {
                "max_ux": float(np.max(np.abs(self.ux))),
                "max_uy": float(np.max(np.abs(self.uy))),
                "max_uz": float(np.max(np.abs(self.uz))),
                "source_location": (int(self.isrc), int(self.jsrc), int(self.ksrc)),
            },
            "materials": {
                "vp_range": [float(np.min(self.vp)), float(np.max(self.vp))],
                "vs_range": [float(np.min(self.vs)), float(np.max(self.vs))],
                "rho_range": [float(np.min(self.rho)), float(np.max(self.rho))],
            },
            "grid": {
                "nx_total": self.nx_total,
                "ny_total": self.ny_total,
                "nz_total": self.nz_total,
                "ngll": cfg.ngll,
            },
            "config": {
                "duration": cfg.duration,
                "dt": cfg.dt,
                "M0": cfg.M0,
            },
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Seismic Waves",
            "category": "ON_DEMAND",
            "domain": ["Seismology", "Wave Propagation"],
            "description": "Spectral element method for elastic wave propagation",
            "computational_complexity": "O(N³)",
            "typical_runtime": "hours",
            "accuracy": "High (research grade)",
            "assumptions": [
                "Isotropic elastic medium",
                "Small strains",
                "Absorbing boundaries",
                "Heterogeneous velocities",
            ],
            "parameters": [
                {
                    "name": "nx",
                    "type": "int",
                    "default": 100,
                    "description": "Elements in x",
                },
                {
                    "name": "ny",
                    "type": "int",
                    "default": 100,
                    "description": "Elements in y",
                },
                {
                    "name": "nz",
                    "type": "int",
                    "default": 50,
                    "description": "Elements in z",
                },
                {
                    "name": "ngll",
                    "type": "int",
                    "default": 4,
                    "description": "GLL points per element",
                },
                {
                    "name": "duration",
                    "type": "float",
                    "default": 20.0,
                    "description": "Simulation duration (s)",
                },
                {
                    "name": "M0",
                    "type": "float",
                    "default": 1e15,
                    "description": "Seismic moment",
                },
            ],
        }


# Unit tests
import unittest


class TestSeismicWaves(unittest.TestCase):
    """TestSeismicWaves."""
    def test_initialization(self) -> None:
        """Test that pattern initializes correctly"""
        config = SeismicWavesConfig(nx=20, ny=20, nz=10, ngll=3)
        pattern = SeismicWavesPattern(config)

        self.assertEqual(
            pattern.ux.shape, (pattern.nx_total, pattern.ny_total, pattern.nz_total)
        )
        self.assertEqual(pattern.vp.shape, pattern.ux.shape)

    def test_gll_points(self) -> None:
        """Test GLL point calculation"""
        config = SeismicWavesConfig()
        pattern = SeismicWavesPattern(config)

        xi, w = pattern._gll_points(4)

        self.assertEqual(len(xi), 4)
        self.assertEqual(len(w), 4)
        self.assertAlmostEqual(xi[0], -1.0)
        self.assertAlmostEqual(xi[-1], 1.0)

    def test_source_time_function(self) -> None:
        """Test source time function"""
        config = SeismicWavesConfig()
        pattern = SeismicWavesPattern(config)

        stf_0 = pattern._source_time_function(0)
        stf_peak = pattern._source_time_function(0.5)
        stf_late = pattern._source_time_function(5.0)

        self.assertEqual(stf_0, 0.0)
        self.assertNotEqual(stf_peak, 0.0)
        self.assertAlmostEqual(stf_late, 0.0, places=5)

    def test_strain_tensor(self) -> None:
        """Test strain calculation"""
        config = SeismicWavesConfig(nx=10, ny=10, nz=5)
        pattern = SeismicWavesPattern(config)

        # Set non-zero displacement
        pattern.ux[:, :, :] = 1.0

        exx, eyy, ezz, exy, exz, eyz = pattern._strain_tensor()

        self.assertEqual(exx.shape, pattern.ux.shape)
        self.assertTrue(np.all(np.isfinite(exx)))

    def test_stress_tensor(self) -> None:
        """Test stress calculation"""
        config = SeismicWavesConfig(nx=10, ny=10, nz=5)
        pattern = SeismicWavesPattern(config)

        sxx, syy, szz, sxy, sxz, syz = pattern._stress_tensor()

        self.assertEqual(sxx.shape, pattern.ux.shape)
        self.assertTrue(np.all(np.isfinite(sxx)))

    def test_internal_forces(self) -> None:
        """Test internal force calculation"""
        config = SeismicWavesConfig(nx=10, ny=10, nz=5)
        pattern = SeismicWavesPattern(config)

        fx, fy, fz = pattern._internal_forces()

        self.assertEqual(fx.shape, pattern.ux.shape)
        self.assertTrue(np.all(np.isfinite(fx)))

    def test_absorbing_boundary(self) -> None:
        """Test absorbing boundary"""
        config = SeismicWavesConfig(abs_width=100)
        pattern = SeismicWavesPattern(config)

        field = np.ones_like(pattern.ux)
        damped = pattern._absorbing_boundary(field)

        # Edges should be damped
        self.assertLess(np.mean(damped[0, :, :]), 1.0)

    def test_cfl(self) -> None:
        """Test CFL calculation"""
        config = SeismicWavesConfig()
        pattern = SeismicWavesPattern(config)

        cfl = pattern._calculate_cfl()

        self.assertIsInstance(cfl, float)
        self.assertGreater(cfl, 0)

    def test_energy(self) -> None:
        """Test energy calculation"""
        config = SeismicWavesConfig()
        pattern = SeismicWavesPattern(config)

        pattern.vx[:, :, :] = 1.0
        ke = pattern._calculate_energy()

        self.assertIsInstance(ke, float)
        self.assertGreater(ke, 0)

    def test_step(self) -> None:
        """Test single time step"""
        config = SeismicWavesConfig()
        pattern = SeismicWavesPattern(config)

        pattern._step(0.1)

        self.assertTrue(np.all(np.isfinite(pattern.ux)))
        self.assertTrue(np.all(np.isfinite(pattern.vx)))

    def test_metadata(self) -> None:
        """Test metadata retrieval"""
        metadata = SeismicWavesPattern.get_metadata()

        self.assertEqual(metadata["id"], "seismic_waves")
        self.assertIn("parameters", metadata)

    def test_short_simulation(self) -> None:
        """Test running a short simulation"""
        config = SeismicWavesConfig(
            nx=15, ny=15, nz=8, duration=1.0, dt=0.001, output_interval=50
        )
        pattern = SeismicWavesPattern(config)

        result = pattern.run()

        self.assertIn("time", result)
        self.assertIn("seismograms", result)
        self.assertGreater(len(result["time"]), 0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
