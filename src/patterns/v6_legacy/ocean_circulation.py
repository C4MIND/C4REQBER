"""
TURBO-CDI v6.0 - Ocean Circulation Pattern
Primitive equation ocean model for large-scale ocean circulation.

Pattern Structure (Christopher Alexander):
- Context: Ocean modeling, climate prediction, marine ecosystem studies
- Forces: Coriolis effects, stratification, bathymetry, boundary currents
- Solution: Primitive equations with hydrostatic approximation
"""

import numpy as np
import logging
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class OceanCirculationConfig:
    """Configuration for ocean circulation simulation"""

    # Grid settings
    nx: int = 128  # Zonal grid points
    ny: int = 64  # Meridional grid points
    nz: int = 20  # Vertical levels

    # Domain extent (m)
    Lx: float = 5.0e6  # 5000 km (basin width)
    Ly: float = 3.0e6  # 3000 km (basin height)
    H: float = 4000.0  # Maximum depth (m)

    # Time stepping
    dt: float = 3600.0  # Time step (seconds)
    days: int = 365  # Simulation duration

    # Physical parameters
    f0: float = 1.0e-4  # Coriolis parameter at equator (s^-1)
    beta: float = 2.0e-11  # Beta parameter (m^-1 s^-1)
    g: float = 9.81  # Gravity (m/s^2)
    rho0: float = 1025.0  # Reference density (kg/m^3)

    # Mixing coefficients
    Ah: float = 100.0  # Horizontal viscosity (m^2/s)
    Kh: float = 100.0  # Horizontal diffusivity (m^2/s)
    Az: float = 1.0e-3  # Vertical viscosity (m^2/s)
    Kz: float = 1.0e-5  # Vertical diffusivity (m^2/s)

    # Surface forcing
    wind_stress_max: float = 0.1  # Maximum wind stress (N/m^2)
    surface_heat_flux: float = 50.0  # W/m^2 (positive = warming)

    # Output
    output_interval: int = 24  # Output every N timesteps


class OceanCirculationPattern:
    """
    Primitive equation ocean circulation model.

    Solves the hydrostatic primitive equations for large-scale
    ocean circulation including momentum, continuity, temperature
    and salinity equations on a staggered Arakawa C-grid.
    """

    PATTERN_ID = "ocean_circulation"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: Optional[OceanCirculationConfig] = None):
        self.config = config or OceanCirculationConfig()
        self._initialize_grid()
        self._initialize_fields()
        self._initialize_forcing()

    def _initialize_grid(self):
        """Initialize staggered Arakawa C-grid"""
        cfg = self.config

        # Cell-centered grid
        self.x = np.linspace(0, cfg.Lx, cfg.nx)
        self.y = np.linspace(0, cfg.Ly, cfg.ny)
        self.z = np.linspace(-cfg.H, 0, cfg.nz)  # Negative downward

        # Grid spacing
        self.dx = cfg.Lx / (cfg.nx - 1)
        self.dy = cfg.Ly / (cfg.ny - 1)
        self.dz = cfg.H / (cfg.nz - 1)

        # Staggered grids (Arakawa C-grid)
        self.xu = self.x[:-1] + self.dx / 2  # u-points
        self.yv = self.y[:-1] + self.dy / 2  # v-points
        self.zw = self.z[:-1] + self.dz / 2  # w-points

        # Coriolis parameter (beta-plane)
        self.f = cfg.f0 + cfg.beta * (self.y - cfg.Ly / 2)
        self.f_u = cfg.f0 + cfg.beta * (self.yv - cfg.Ly / 2)

        # Bathymetry (sloping bottom with flat shelf)
        self.h = np.zeros((cfg.nx, cfg.ny))
        for j in range(cfg.ny):
            for i in range(cfg.nx):
                # Continental slope
                x_norm = self.x[i] / cfg.Lx
                self.h[i, j] = -cfg.H * (0.2 + 0.8 * x_norm)

        # Minimum depth mask
        self.mask = self.h < -100.0

    def _initialize_fields(self):
        """Initialize prognostic variables"""
        cfg = self.config

        # Velocities on staggered grids
        self.u = np.zeros((cfg.nx - 1, cfg.ny, cfg.nz))  # Zonal velocity
        self.v = np.zeros((cfg.nx, cfg.ny - 1, cfg.nz))  # Meridional velocity
        self.w = np.zeros((cfg.nx, cfg.ny, cfg.nz - 1))  # Vertical velocity

        # Tracers (cell-centered)
        self.T = np.zeros((cfg.nx, cfg.ny, cfg.nz))  # Temperature
        self.S = np.zeros((cfg.nx, cfg.ny, cfg.nz))  # Salinity

        # Initialize stratification
        for k in range(cfg.nz):
            depth = -self.z[k]  # Positive depth
            # Exponential thermocline
            self.T[:, :, k] = 25.0 * np.exp(-depth / 500.0) + 2.0
            self.S[:, :, k] = 36.0 - 2.0 * np.exp(-depth / 500.0)

        # Surface elevation
        self.eta = np.zeros((cfg.nx, cfg.ny))

        # Pressure (hydrostatic)
        self.p = np.zeros((cfg.nx, cfg.ny, cfg.nz))
        self._update_pressure()

        # Output storage
        self.history = {
            "u": [],
            "v": [],
            "T": [],
            "S": [],
            "eta": [],
            "time": [],
            "ke": [],
            "moc": [],
        }

    def _initialize_forcing(self):
        """Initialize surface forcing fields"""
        cfg = self.config

        # Wind stress (sinusoidal profile)
        self.taux = np.zeros((cfg.nx - 1, cfg.ny))
        self.tauy = np.zeros((cfg.nx, cfg.ny - 1))

        for j in range(cfg.ny):
            y_norm = self.y[j] / cfg.Ly
            # Double-gyre wind forcing
            wind = cfg.wind_stress_max * np.sin(2 * np.pi * y_norm)
            if j < cfg.ny - 1:
                self.taux[:, j] = wind

        # Heat flux (cooling in north, warming in south)
        self.Q = np.zeros((cfg.nx, cfg.ny))
        for j in range(cfg.ny):
            y_norm = self.y[j] / cfg.Ly
            self.Q[:, j] = cfg.surface_heat_flux * (0.5 - y_norm)

    def _update_pressure(self):
        """Calculate hydrostatic pressure"""
        cfg = self.config

        # Equation of state (linearized)
        alpha_T = 2.0e-4  # Thermal expansion coefficient
        beta_S = 7.6e-4  # Haline contraction coefficient

        # Reference profiles
        T_ref = 10.0
        S_ref = 35.0

        # Density anomaly
        drho = cfg.rho0 * (-alpha_T * (self.T - T_ref) + beta_S * (self.S - S_ref))

        # Hydrostatic integration (from bottom up)
        # z[0] = -H (bottom), z[-1] = 0 (surface)
        for k in range(cfg.nz - 1, -1, -1):
            if k == cfg.nz - 1:
                # Surface: pressure from sea surface elevation
                self.p[:, :, k] = cfg.rho0 * cfg.g * self.eta
            else:
                # Below surface: integrate downward
                self.p[:, :, k] = (
                    self.p[:, :, k + 1] + (cfg.rho0 + drho[:, :, k]) * cfg.g * self.dz
                )

    def _momentum_tendency_u(self) -> np.ndarray:
        """Calculate u-momentum tendencies"""
        cfg = self.config
        du_dt = np.zeros_like(self.u)

        # Coriolis term (on u-grid)
        for j in range(cfg.ny):
            if j < cfg.ny - 1:
                f_interp = (self.f[j] + self.f[j + 1]) / 2
                v_interp = (self.v[:-1, j, :] + self.v[1:, j, :]) / 2
                du_dt[:, j, :] += f_interp * v_interp

        # Pressure gradient
        for k in range(cfg.nz):
            du_dt[:, :, k] -= (self.p[1:, :, k] - self.p[:-1, :, k]) / (
                cfg.rho0 * self.dx
            )

        # Horizontal diffusion
        for k in range(cfg.nz):
            du_dt[:, :, k] += cfg.Ah * self._laplacian_h(self.u[:, :, k])

        # Vertical diffusion
        for j in range(cfg.ny):
            for i in range(cfg.nx - 1):
                for k in range(1, cfg.nz - 1):
                    d2u_dz2 = (
                        self.u[i, j, k + 1] - 2 * self.u[i, j, k] + self.u[i, j, k - 1]
                    ) / self.dz**2
                    du_dt[i, j, k] += cfg.Az * d2u_dz2

        # Surface forcing
        du_dt[:, :, 0] += self.taux / (cfg.rho0 * self.dz)

        return du_dt

    def _momentum_tendency_v(self) -> np.ndarray:
        """Calculate v-momentum tendencies"""
        cfg = self.config
        dv_dt = np.zeros_like(self.v)

        # Coriolis term
        for j in range(cfg.ny - 1):
            f_interp = self.f_u[j]
            u_interp = (self.u[:, j, :] + self.u[:, j + 1, :]) / 2
            dv_dt[:, j, :] -= f_interp * u_interp

        # Pressure gradient
        for k in range(cfg.nz):
            dv_dt[:, :, k] -= (self.p[:, 1:, k] - self.p[:, :-1, k]) / (
                cfg.rho0 * self.dy
            )

        # Horizontal diffusion
        for k in range(cfg.nz):
            dv_dt[:, :, k] += cfg.Ah * self._laplacian_h(self.v[:, :, k])

        # Vertical diffusion
        for j in range(cfg.ny - 1):
            for i in range(cfg.nx):
                for k in range(1, cfg.nz - 1):
                    d2v_dz2 = (
                        self.v[i, j, k + 1] - 2 * self.v[i, j, k] + self.v[i, j, k - 1]
                    ) / self.dz**2
                    dv_dt[i, j, k] += cfg.Az * d2v_dz2

        return dv_dt

    def _tracer_tendency_T(self) -> np.ndarray:
        """Calculate temperature tendencies"""
        cfg = self.config
        dT_dt = np.zeros_like(self.T)

        # Horizontal diffusion
        for k in range(cfg.nz):
            dT_dt[:, :, k] += cfg.Kh * self._laplacian_h(self.T[:, :, k])

        # Vertical diffusion
        for k in range(1, cfg.nz - 1):
            d2T_dz2 = (
                self.T[:, :, k + 1] - 2 * self.T[:, :, k] + self.T[:, :, k - 1]
            ) / self.dz**2
            dT_dt[:, :, k] += cfg.Kz * d2T_dz2

        # Surface heat flux
        dT_dt[:, :, 0] += self.Q / (cfg.rho0 * 3985 * self.dz)

        return dT_dt

    def _tracer_tendency_S(self) -> np.ndarray:
        """Calculate salinity tendencies"""
        cfg = self.config
        dS_dt = np.zeros_like(self.S)

        # Horizontal diffusion
        for k in range(cfg.nz):
            dS_dt[:, :, k] += cfg.Kh * self._laplacian_h(self.S[:, :, k])

        # Vertical diffusion
        for k in range(1, cfg.nz - 1):
            d2S_dz2 = (
                self.S[:, :, k + 1] - 2 * self.S[:, :, k] + self.S[:, :, k - 1]
            ) / self.dz**2
            dS_dt[:, :, k] += cfg.Kz * d2S_dz2

        return dS_dt

    def _laplacian_h(self, field: np.ndarray) -> np.ndarray:
        """Horizontal Laplacian on cell-centered or staggered grid"""
        lapl = np.zeros_like(field)

        if field.ndim == 2:
            lapl[1:-1, 1:-1] = (
                field[2:, 1:-1] - 2 * field[1:-1, 1:-1] + field[:-2, 1:-1]
            ) / self.dy**2 + (
                field[1:-1, 2:] - 2 * field[1:-1, 1:-1] + field[1:-1, :-2]
            ) / self.dx**2

        return lapl

    def _continuity(self):
        """Update vertical velocity from continuity"""
        cfg = self.config

        # Integrate continuity equation
        for k in range(cfg.nz - 1):
            if k == 0:
                # Surface boundary condition
                deta_dt = np.zeros((cfg.nx, cfg.ny))
                for j in range(cfg.ny - 1):
                    for i in range(cfg.nx - 2):
                        div_u = (self.u[i + 1, j, 0] - self.u[i, j, 0]) / self.dx
                        div_v = (self.v[i, j + 1, 0] - self.v[i, j, 0]) / self.dy
                        self.w[i, j, k] = -self.dz * (div_u + div_v)
                        deta_dt[i, j] = -(div_u + div_v)
            else:
                for j in range(cfg.ny - 1):
                    for i in range(cfg.nx - 2):
                        div_u = (self.u[i + 1, j, k] - self.u[i, j, k]) / self.dx
                        div_v = (self.v[i, j + 1, k] - self.v[i, j, k]) / self.dy
                        self.w[i, j, k] = self.w[i, j, k - 1] - self.dz * (
                            div_u + div_v
                        )

        # Update surface elevation
        self.eta += deta_dt * cfg.dt

    def _calculate_moc(self) -> np.ndarray:
        """Calculate meridional overturning circulation"""
        cfg = self.config
        moc = np.zeros((cfg.ny, cfg.nz))

        for j in range(cfg.ny):
            for k in range(cfg.nz):
                # Integrate v-velocity zonally
                if j < cfg.ny - 1:
                    moc[j, k] = np.sum(self.v[:, j, k]) * self.dx / 1e6  # Sv

        return moc

    def _step(self):
        """Advance model by one time step"""
        cfg = self.config

        # Calculate tendencies
        du_dt = self._momentum_tendency_u()
        dv_dt = self._momentum_tendency_v()
        dT_dt = self._tracer_tendency_T()
        dS_dt = self._tracer_tendency_S()

        # Update fields
        self.u += du_dt * cfg.dt
        self.v += dv_dt * cfg.dt
        self.T += dT_dt * cfg.dt
        self.S += dS_dt * cfg.dt

        # Apply boundary conditions
        self._apply_boundary_conditions()

        # Update pressure
        self._update_pressure()

        # Update vertical velocity
        self._continuity()

    def _apply_boundary_conditions(self):
        """Apply boundary conditions"""
        cfg = self.config

        # No-slip walls
        self.u[0, :, :] = 0  # Western boundary
        self.u[-1, :, :] = 0  # Eastern boundary
        self.v[:, 0, :] = 0  # Southern boundary
        self.v[:, -1, :] = 0  # Northern boundary

        # No flux through bottom
        self.w[:, :, -1] = 0

        # Sponge layers at boundaries
        sponge_width = 5
        for i in range(sponge_width):
            damping = 0.1 * (1 - i / sponge_width)
            self.u[i, :, :] *= 1 - damping
            self.u[-i - 1, :, :] *= 1 - damping

    def run(self, hypothesis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run the ocean circulation simulation"""
        cfg = self.config
        n_steps = int(cfg.days * 24 * 3600 / cfg.dt)

        logger.info(f"Starting ocean simulation: {cfg.days} days, {n_steps} steps")

        for step in range(n_steps):
            self._step()

            # Output
            if step % cfg.output_interval == 0:
                day = step * cfg.dt / (24 * 3600)

                # Calculate diagnostics
                ke = 0.5 * (np.mean(self.u**2) + np.mean(self.v**2))
                moc = self._calculate_moc()

                self.history["u"].append(self.u.copy())
                self.history["v"].append(self.v.copy())
                self.history["T"].append(self.T.copy())
                self.history["S"].append(self.S.copy())
                self.history["eta"].append(self.eta.copy())
                self.history["time"].append(day)
                self.history["ke"].append(ke)
                self.history["moc"].append(moc)

            if step % 100 == 0:
                logger.debug(f"Step {step}/{n_steps}, Day {day:.1f}, KE: {ke:.4e}")

        return self._format_output()

    def _format_output(self) -> Dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        # Time series
        T_surf_mean = [np.mean(T[:, :, 0]) for T in self.history["T"]]
        S_surf_mean = [np.mean(S[:, :, 0]) for S in self.history["S"]]

        # Final state statistics
        u_max = np.max(np.abs(self.u))
        v_max = np.max(np.abs(self.v))
        T_range = [np.min(self.T), np.max(self.T)]

        return {
            "mean_surface_temperature": T_surf_mean,
            "mean_surface_salinity": S_surf_mean,
            "kinetic_energy": self.history["ke"],
            "time_days": self.history["time"],
            "final_state": {
                "u_max": float(u_max),
                "v_max": float(v_max),
                "T_range": [float(T_range[0]), float(T_range[1])],
                "eta_mean": float(np.mean(self.eta)),
            },
            "overturning": {
                "moc_max": float(np.max(np.abs(self.history["moc"][-1]))),
                "moc_min": float(np.min(self.history["moc"][-1])),
            },
            "grid": {
                "nx": cfg.nx,
                "ny": cfg.ny,
                "nz": cfg.nz,
                "Lx": cfg.Lx,
                "Ly": cfg.Ly,
                "H": cfg.H,
            },
            "config": {
                "days": cfg.days,
                "dt": cfg.dt,
                "Ah": cfg.Ah,
                "Kh": cfg.Kh,
            },
        }

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Ocean Circulation",
            "category": "ON_DEMAND",
            "domain": ["Oceanography", "Climate Science"],
            "description": "Primitive equation ocean circulation model",
            "computational_complexity": "O(N³)",
            "typical_runtime": "hours",
            "accuracy": "High (research grade)",
            "assumptions": [
                "Hydrostatic balance",
                "Boussinesq approximation",
                "Beta-plane approximation",
                "Linear equation of state",
            ],
            "parameters": [
                {
                    "name": "nx",
                    "type": "int",
                    "default": 128,
                    "description": "Zonal grid points",
                },
                {
                    "name": "ny",
                    "type": "int",
                    "default": 64,
                    "description": "Meridional grid points",
                },
                {
                    "name": "nz",
                    "type": "int",
                    "default": 20,
                    "description": "Vertical levels",
                },
                {
                    "name": "days",
                    "type": "int",
                    "default": 365,
                    "description": "Simulation days",
                },
                {
                    "name": "Ah",
                    "type": "float",
                    "default": 100.0,
                    "description": "Horizontal viscosity",
                },
            ],
        }


# Unit tests
import unittest


class TestOceanCirculation(unittest.TestCase):
    def test_initialization(self):
        """Test that pattern initializes correctly"""
        config = OceanCirculationConfig(nx=32, ny=16, nz=5)
        pattern = OceanCirculationPattern(config)

        self.assertEqual(pattern.u.shape, (31, 16, 5))
        self.assertEqual(pattern.T.shape, (32, 16, 5))
        self.assertEqual(pattern.eta.shape, (32, 16))

    def test_grid_spacing(self):
        """Test grid spacing calculation"""
        config = OceanCirculationConfig(Lx=1e6, Ly=5e5, nx=51, ny=26)
        pattern = OceanCirculationPattern(config)

        self.assertAlmostEqual(pattern.dx, 20000.0, places=1)
        self.assertAlmostEqual(pattern.dy, 20000.0, places=1)

    def test_coriolis_parameter(self):
        """Test Coriolis parameter on beta-plane"""
        config = OceanCirculationConfig(f0=1e-4, beta=2e-11, Ly=1e6)
        pattern = OceanCirculationPattern(config)

        # Check f varies with y
        self.assertNotEqual(pattern.f[0], pattern.f[-1])
        # Midpoint should be close to f0
        mid_idx = len(pattern.f) // 2
        self.assertAlmostEqual(pattern.f[mid_idx], config.f0, places=5)

    def test_momentum_tendencies(self):
        """Test momentum tendency calculation"""
        config = OceanCirculationConfig(nx=16, ny=8, nz=3)
        pattern = OceanCirculationPattern(config)

        du_dt = pattern._momentum_tendency_u()
        self.assertEqual(du_dt.shape, pattern.u.shape)
        self.assertTrue(np.all(np.isfinite(du_dt)))

    def test_tracer_tendencies(self):
        """Test tracer tendency calculation"""
        config = OceanCirculationConfig(nx=16, ny=8, nz=3)
        pattern = OceanCirculationPattern(config)

        dT_dt = pattern._tracer_tendency_T()
        self.assertEqual(dT_dt.shape, pattern.T.shape)
        self.assertTrue(np.all(np.isfinite(dT_dt)))

    def test_pressure_update(self):
        """Test hydrostatic pressure calculation"""
        config = OceanCirculationConfig(nx=16, ny=8, nz=5)
        pattern = OceanCirculationPattern(config)

        pattern._update_pressure()

        # Pressure should increase with depth (more negative z)
        for j in range(config.ny):
            for i in range(config.nx):
                p_profile = pattern.p[i, j, :]
                self.assertTrue(np.all(np.diff(p_profile) >= -1e-6))

    def test_continuity(self):
        """Test continuity equation integration"""
        config = OceanCirculationConfig(nx=16, ny=8, nz=5)
        pattern = OceanCirculationPattern(config)

        pattern._continuity()

        # Vertical velocity at bottom should be zero
        self.assertTrue(np.allclose(pattern.w[:, :, -1], 0))

    def test_boundary_conditions(self):
        """Test boundary conditions application"""
        config = OceanCirculationConfig(nx=16, ny=8, nz=3)
        pattern = OceanCirculationPattern(config)

        # Set non-zero values at boundaries
        pattern.u[0, :, :] = 1.0
        pattern.u[-1, :, :] = 1.0

        pattern._apply_boundary_conditions()

        # Check no-slip condition
        self.assertTrue(np.allclose(pattern.u[0, :, :], 0))
        self.assertTrue(np.allclose(pattern.u[-1, :, :], 0))

    def test_moc_calculation(self):
        """Test meridional overturning calculation"""
        config = OceanCirculationConfig(nx=16, ny=8, nz=5)
        pattern = OceanCirculationPattern(config)

        moc = pattern._calculate_moc()

        self.assertEqual(moc.shape, (config.ny, config.nz))
        self.assertTrue(np.all(np.isfinite(moc)))

    def test_metadata(self):
        """Test metadata retrieval"""
        metadata = OceanCirculationPattern.get_metadata()

        self.assertEqual(metadata["id"], "ocean_circulation")
        self.assertIn("parameters", metadata)
        self.assertGreater(len(metadata["assumptions"]), 0)

    def test_short_simulation(self):
        """Test running a short simulation"""
        config = OceanCirculationConfig(nx=16, ny=8, nz=3, days=1, dt=3600)
        pattern = OceanCirculationPattern(config)

        result = pattern.run()

        self.assertIn("mean_surface_temperature", result)
        self.assertIn("kinetic_energy", result)
        self.assertIn("final_state", result)
        self.assertGreater(len(result["time_days"]), 0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
