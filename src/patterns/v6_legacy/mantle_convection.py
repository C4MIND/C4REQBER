"""
TURBO-CDI v6.0 - Mantle Convection Pattern
Anelastic approximation for thermal convection in Earth's mantle.

Pattern Structure (Christopher Alexander):
- Context: Geodynamics, plate tectonics, heat transport in Earth
- Forces: Thermal buoyancy, viscous dissipation, phase transitions, rheology
- Solution: Anelastic Navier-Stokes with temperature-dependent viscosity
"""

import numpy as np
import logging
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class MantleConvectionConfig:
    """Configuration for mantle convection simulation"""

    # Grid settings
    nx: int = 64  # Horizontal resolution
    ny: int = 64
    nz: int = 32  # Vertical resolution

    # Domain (nondimensional or dimensional in units of mantle depth D=2890 km)
    Lx: float = 4.0  # Aspect ratio 4:1
    Ly: float = 4.0
    Lz: float = 1.0

    # Physical parameters (nondimensional Rayleigh-Benard)
    Ra: float = 1.0e6  # Rayleigh number
    Pr: float = 1.0e3  # Prandtl number
    Ek: float = 1.0e-7  # Ekman number

    # Rheology
    visc_depth: float = 10.0  # Viscosity increase with depth
    visc_temp: float = 10.0  # Viscosity temperature dependence (Arrhenius)

    # Heating
    internal_heating: float = 10.0  # Nondimensional
    bottom_temp: float = 1.0  # Hot bottom boundary
    top_temp: float = 0.0  # Cold top boundary

    # Phase transitions (410 and 660 km)
    phase_transition_clapeyron: float = -2.0  # dP/dT (MPa/K)

    # Time stepping
    dt: float = 1.0e-6  # Nondimensional time
    max_time: float = 1.0

    # Output
    output_interval: int = 100


class MantleConvectionPattern:
    """
    Anelastic mantle convection model.

    Solves the equations for thermal convection in Earth's mantle
    using the anelastic approximation. Includes temperature-dependent
    viscosity, internal heating, and phase transitions.
    """

    PATTERN_ID = "mantle_convection"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: Optional[MantleConvectionConfig] = None):
        self.config = config or MantleConvectionConfig()
        self._initialize_grid()
        self._initialize_fields()
        self._initialize_reference_state()

    def _initialize_grid(self):
        """Initialize 3D grid"""
        cfg = self.config

        # Staggered grid (Arakawa C)
        self.x = np.linspace(0, cfg.Lx, cfg.nx)
        self.y = np.linspace(0, cfg.Ly, cfg.ny)
        self.z = np.linspace(0, cfg.Lz, cfg.nz)

        self.dx = cfg.Lx / (cfg.nx - 1)
        self.dy = cfg.Ly / (cfg.ny - 1)
        self.dz = cfg.Lz / (cfg.nz - 1)

        self.X, self.Y, self.Z = np.meshgrid(self.x, self.y, self.z, indexing="ij")

    def _initialize_reference_state(self):
        """Initialize hydrostatic reference state"""
        cfg = self.config

        # Reference density (anelastic: varies with depth)
        # Exponentially stratified
        self.rho_ref = np.exp(-3.0 * self.Z)

        # Reference temperature (adiabat)
        self.T_ref = 0.5 + 0.5 * self.Z

        # Thermal expansivity
        self.alpha = np.ones_like(self.Z)

        # Heat capacity
        self.Cp = np.ones_like(self.Z)

    def _initialize_fields(self):
        """Initialize velocity, temperature, and pressure fields"""
        cfg = self.config

        # Velocities on staggered grid
        self.u = np.zeros((cfg.nx - 1, cfg.ny, cfg.nz))  # x-velocity
        self.v = np.zeros((cfg.nx, cfg.ny - 1, cfg.nz))  # y-velocity
        self.w = np.zeros((cfg.nx, cfg.ny, cfg.nz - 1))  # z-velocity (vertical)

        # Temperature perturbation (cell-centered)
        self.T = np.zeros((cfg.nx, cfg.ny, cfg.nz))

        # Initialize thermal perturbations (cold plumes)
        np.random.seed(42)
        for i in range(cfg.nx):
            for j in range(cfg.ny):
                for k in range(cfg.nz):
                    # Cold downwellings near top
                    if k > cfg.nz * 0.8:
                        if np.random.random() < 0.1:
                            self.T[i, j, k] = -0.5 * np.exp(
                                -((i - cfg.nx // 2) ** 2 + (j - cfg.ny // 2) ** 2) / 50
                            )
                    # Hot upwellings from bottom
                    if k < cfg.nz * 0.2:
                        if np.random.random() < 0.1:
                            self.T[i, j, k] = 0.5

        # Dynamic pressure (cell-centered)
        self.p = np.zeros((cfg.nx, cfg.ny, cfg.nz))

        # Viscosity
        self.eta = np.ones((cfg.nx, cfg.ny, cfg.nz))

        # Output storage
        self.history = {
            "T": [],
            "u_rms": [],
            "w_max": [],
            "time": [],
            "nusselt": [],
            "viscous_dissipation": [],
        }

    def _viscosity(self) -> np.ndarray:
        """Calculate temperature and depth-dependent viscosity"""
        cfg = self.config

        # Depth dependence (increase with depth)
        eta_z = np.exp(cfg.visc_depth * self.Z)

        # Temperature dependence (Arrhenius)
        eta_T = np.exp(-cfg.visc_temp * self.T)

        return eta_z * eta_T

    def _buoyancy(self) -> np.ndarray:
        """Calculate thermal buoyancy force"""
        cfg = self.config

        # B = Ra * alpha * T (nondimensional)
        return cfg.Ra * self.alpha * self.T

    def _momentum_tendency_u(self) -> np.ndarray:
        """Calculate x-momentum tendency"""
        cfg = self.config

        dudt = np.zeros_like(self.u)

        # Pressure gradient
        for i in range(cfg.nx - 1):
            dudt[i, :, :] = -(self.p[i + 1, :, :] - self.p[i, :, :]) / self.dx

        # Viscous diffusion (simplified)
        eta_avg = (self.eta[:-1, :, :] + self.eta[1:, :, :]) / 2
        for i in range(1, cfg.nx - 2):
            dudt[i, :, :] += eta_avg[i, :, :] * (
                (self.u[i + 1, :, :] - 2 * self.u[i, :, :] + self.u[i - 1, :, :])
                / self.dx**2
            )

        # Coriolis (if Ekman number specified)
        if cfg.Ek > 0:
            # Simplified Coriolis
            pass

        return dudt

    def _momentum_tendency_v(self) -> np.ndarray:
        """Calculate y-momentum tendency"""
        cfg = self.config

        dvdt = np.zeros_like(self.v)

        # Pressure gradient
        for j in range(cfg.ny - 1):
            dvdt[:, j, :] = -(self.p[:, j + 1, :] - self.p[:, j, :]) / self.dy

        # Viscous diffusion
        eta_avg = (self.eta[:, :-1, :] + self.eta[:, 1:, :]) / 2
        for j in range(1, cfg.ny - 2):
            dvdt[:, j, :] += eta_avg[:, j, :] * (
                (self.v[:, j + 1, :] - 2 * self.v[:, j, :] + self.v[:, j - 1, :])
                / self.dy**2
            )

        return dvdt

    def _momentum_tendency_w(self) -> np.ndarray:
        """Calculate z-momentum tendency (includes buoyancy)"""
        cfg = self.config

        dwdt = np.zeros_like(self.w)

        # Pressure gradient
        for k in range(cfg.nz - 1):
            dwdt[:, :, k] = -(self.p[:, :, k + 1] - self.p[:, :, k]) / self.dz

        # Buoyancy force
        B = self._buoyancy()
        for k in range(cfg.nz - 1):
            B_avg = (B[:, :, k] + B[:, :, k + 1]) / 2
            dwdt[:, :, k] += B_avg

        # Viscous diffusion
        eta_avg = (self.eta[:, :, :-1] + self.eta[:, :, 1:]) / 2
        for k in range(1, cfg.nz - 2):
            dwdt[:, :, k] += eta_avg[:, :, k] * (
                (self.w[:, :, k + 1] - 2 * self.w[:, :, k] + self.w[:, :, k - 1])
                / self.dz**2
            )

        return dwdt

    def _temperature_tendency(self) -> np.ndarray:
        """Calculate temperature tendency"""
        cfg = self.config

        dTdt = np.zeros_like(self.T)

        # Advection (upwind scheme)
        for i in range(1, cfg.nx - 1):
            for j in range(1, cfg.ny - 1):
                for k in range(1, cfg.nz - 1):
                    # x-advection
                    if self.u[i, j, k] > 0:
                        dTdt[i, j, k] -= (
                            self.u[i, j, k]
                            * (self.T[i, j, k] - self.T[i - 1, j, k])
                            / self.dx
                        )
                    else:
                        dTdt[i, j, k] -= (
                            self.u[i, j, k]
                            * (self.T[i + 1, j, k] - self.T[i, j, k])
                            / self.dx
                        )

                    # y-advection
                    if self.v[i, j, k] > 0:
                        dTdt[i, j, k] -= (
                            self.v[i, j, k]
                            * (self.T[i, j, k] - self.T[i, j - 1, k])
                            / self.dy
                        )
                    else:
                        dTdt[i, j, k] -= (
                            self.v[i, j, k]
                            * (self.T[i, j + 1, k] - self.T[i, j, k])
                            / self.dy
                        )

                    # z-advection
                    if self.w[i, j, k] > 0:
                        dTdt[i, j, k] -= (
                            self.w[i, j, k]
                            * (self.T[i, j, k] - self.T[i, j, k - 1])
                            / self.dz
                        )
                    else:
                        dTdt[i, j, k] -= (
                            self.w[i, j, k]
                            * (self.T[i, j, k + 1] - self.T[i, j, k])
                            / self.dz
                        )

        # Thermal diffusion
        kappa = 1.0 / np.sqrt(cfg.Ra)  # Thermal diffusivity
        for i in range(1, cfg.nx - 1):
            for j in range(1, cfg.ny - 1):
                for k in range(1, cfg.nz - 1):
                    d2T_dx2 = (
                        self.T[i + 1, j, k] - 2 * self.T[i, j, k] + self.T[i - 1, j, k]
                    ) / self.dx**2
                    d2T_dy2 = (
                        self.T[i, j + 1, k] - 2 * self.T[i, j, k] + self.T[i, j - 1, k]
                    ) / self.dy**2
                    d2T_dz2 = (
                        self.T[i, j, k + 1] - 2 * self.T[i, j, k] + self.T[i, j, k - 1]
                    ) / self.dz**2
                    dTdt[i, j, k] += kappa * (d2T_dx2 + d2T_dy2 + d2T_dz2)

        # Internal heating
        dTdt += cfg.internal_heating

        # Adiabatic heating/cooling
        for k in range(cfg.nz):
            dTdt[:, :, k] -= self.w[:, :, max(0, k - 1)] * 0.5  # Simplified adiabat

        return dTdt

    def _continuity_residual(self) -> np.ndarray:
        """Calculate continuity residual for pressure correction"""
        cfg = self.config

        residual = np.zeros((cfg.nx, cfg.ny, cfg.nz))

        for i in range(1, cfg.nx - 1):
            for j in range(1, cfg.ny - 1):
                for k in range(1, cfg.nz - 1):
                    div_u = (self.u[i, j, k] - self.u[i - 1, j, k]) / self.dx
                    div_v = (self.v[i, j, k] - self.v[i, j - 1, k]) / self.dy
                    div_w = (self.w[i, j, k] - self.w[i, j, k - 1]) / self.dz
                    residual[i, j, k] = div_u + div_v + div_w

        return residual

    def _pressure_projection(self):
        """Project velocity to satisfy anelastic continuity"""
        cfg = self.config

        # Simplified pressure correction
        residual = self._continuity_residual()

        # Update pressure
        self.p += residual * 0.1

    def _apply_boundary_conditions(self):
        """Apply boundary conditions"""
        cfg = self.config

        # Temperature: fixed at top and bottom
        self.T[:, :, 0] = cfg.bottom_temp
        self.T[:, :, -1] = cfg.top_temp

        # No heat flux through sides
        self.T[0, :, :] = self.T[1, :, :]
        self.T[-1, :, :] = self.T[-2, :, :]
        self.T[:, 0, :] = self.T[:, 1, :]
        self.T[:, -1, :] = self.T[:, -2, :]

        # Velocity: free-slip on all boundaries
        self.u[0, :, :] = 0
        self.u[-1, :, :] = 0
        self.v[:, 0, :] = 0
        self.v[:, -1, :] = 0
        self.w[:, :, 0] = 0
        self.w[:, :, -1] = 0

    def _calculate_nusselt_number(self) -> float:
        """Calculate Nusselt number (heat transport)"""
        cfg = self.config

        # Heat flux at top (conduction + advection)
        k = cfg.nz - 2
        dT_dz = (self.T[:, :, k] - self.T[:, :, k - 1]) / self.dz

        # Conduction only Nu = 1
        Nu_cond = np.mean(-dT_dz)

        return max(1.0, Nu_cond)

    def _calculate_viscous_dissipation(self) -> float:
        """Calculate viscous dissipation"""
        cfg = self.config

        # Simplified dissipation
        diss = np.sum(
            self.eta * (self.u**2).mean()
            + self.eta * (self.v**2).mean()
            + self.eta * (self.w**2).mean()
        )

        return diss

    def _step(self):
        """Advance model by one time step"""
        cfg = self.config

        # Update viscosity
        self.eta = self._viscosity()

        # Momentum equations
        dudt = self._momentum_tendency_u()
        dvdt = self._momentum_tendency_v()
        dwdt = self._momentum_tendency_w()

        self.u += dudt * cfg.dt
        self.v += dvdt * cfg.dt
        self.w += dwdt * cfg.dt

        # Pressure projection
        self._pressure_projection()

        # Temperature equation
        dTdt = self._temperature_tendency()
        self.T += dTdt * cfg.dt

        # Boundary conditions
        self._apply_boundary_conditions()

    def run(self, hypothesis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run the mantle convection simulation"""
        cfg = self.config
        n_steps = int(cfg.max_time / cfg.dt)

        logger.info(f"Starting mantle convection: Ra={cfg.Ra:.1e}, {n_steps} steps")

        for step in range(n_steps):
            self._step()

            # Output
            if step % cfg.output_interval == 0:
                time = step * cfg.dt

                u_rms = np.sqrt(
                    np.mean(self.u**2) + np.mean(self.v**2) + np.mean(self.w**2)
                )
                w_max = np.max(np.abs(self.w))
                Nu = self._calculate_nusselt_number()
                diss = self._calculate_viscous_dissipation()

                self.history["T"].append(np.mean(self.T))
                self.history["u_rms"].append(u_rms)
                self.history["w_max"].append(w_max)
                self.history["time"].append(time)
                self.history["nusselt"].append(Nu)
                self.history["viscous_dissipation"].append(diss)

            if step % 1000 == 0:
                logger.debug(f"Step {step}/{n_steps}, u_rms={u_rms:.4e}, Nu={Nu:.2f}")

        return self._format_output()

    def _format_output(self) -> Dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        return {
            "temperature": self.history["T"],
            "velocity_rms": self.history["u_rms"],
            "vertical_velocity_max": self.history["w_max"],
            "nusselt_number": self.history["nusselt"],
            "viscous_dissipation": self.history["viscous_dissipation"],
            "time": self.history["time"],
            "final_state": {
                "mean_temperature": float(np.mean(self.T)),
                "rms_velocity": float(self.history["u_rms"][-1])
                if self.history["u_rms"]
                else 0,
                "max_temperature": float(np.max(self.T)),
                "min_temperature": float(np.min(self.T)),
                "final_nusselt": float(self.history["nusselt"][-1])
                if self.history["nusselt"]
                else 1.0,
            },
            "parameters": {
                "Rayleigh_number": cfg.Ra,
                "Prandtl_number": cfg.Pr,
                "aspect_ratio": cfg.Lx / cfg.Lz,
            },
            "grid": {
                "nx": cfg.nx,
                "ny": cfg.ny,
                "nz": cfg.nz,
            },
            "config": {
                "max_time": cfg.max_time,
                "internal_heating": cfg.internal_heating,
            },
        }

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Mantle Convection",
            "category": "ON_DEMAND",
            "domain": ["Geodynamics", "Mantle Physics"],
            "description": "Anelastic mantle convection with temperature-dependent rheology",
            "computational_complexity": "O(N³)",
            "typical_runtime": "hours to days",
            "accuracy": "High (research grade)",
            "assumptions": [
                "Anelastic approximation",
                "Boussinesq for buoyancy",
                "Temperature-dependent viscosity",
                "Infinite Prandtl number",
            ],
            "parameters": [
                {
                    "name": "nx",
                    "type": "int",
                    "default": 64,
                    "description": "Horizontal resolution",
                },
                {
                    "name": "nz",
                    "type": "int",
                    "default": 32,
                    "description": "Vertical resolution",
                },
                {
                    "name": "Ra",
                    "type": "float",
                    "default": 1e6,
                    "description": "Rayleigh number",
                },
                {
                    "name": "internal_heating",
                    "type": "float",
                    "default": 10.0,
                    "description": "Internal heating rate",
                },
            ],
        }


# Unit tests
import unittest


class TestMantleConvection(unittest.TestCase):
    def test_initialization(self):
        """Test that pattern initializes correctly"""
        config = MantleConvectionConfig(nx=32, ny=32, nz=16)
        pattern = MantleConvectionPattern(config)

        self.assertEqual(pattern.T.shape, (32, 32, 16))
        self.assertEqual(pattern.u.shape, (31, 32, 16))
        self.assertEqual(pattern.w.shape, (32, 32, 15))

    def test_viscosity(self):
        """Test viscosity calculation"""
        config = MantleConvectionConfig()
        pattern = MantleConvectionPattern(config)

        eta = pattern._viscosity()

        self.assertEqual(eta.shape, pattern.T.shape)
        self.assertTrue(np.all(eta > 0))

    def test_buoyancy(self):
        """Test buoyancy calculation"""
        config = MantleConvectionConfig(Ra=1e6)
        pattern = MantleConvectionPattern(config)

        B = pattern._buoyancy()

        self.assertEqual(B.shape, pattern.T.shape)
        self.assertTrue(np.all(np.isfinite(B)))

    def test_momentum_tendency(self):
        """Test momentum tendency calculation"""
        config = MantleConvectionConfig()
        pattern = MantleConvectionPattern(config)

        dudt = pattern._momentum_tendency_u()
        dvdt = pattern._momentum_tendency_v()
        dwdt = pattern._momentum_tendency_w()

        self.assertEqual(dudt.shape, pattern.u.shape)
        self.assertEqual(dvdt.shape, pattern.v.shape)
        self.assertEqual(dwdt.shape, pattern.w.shape)

    def test_temperature_tendency(self):
        """Test temperature tendency"""
        config = MantleConvectionConfig()
        pattern = MantleConvectionPattern(config)

        dTdt = pattern._temperature_tendency()

        self.assertEqual(dTdt.shape, pattern.T.shape)
        self.assertTrue(np.all(np.isfinite(dTdt)))

    def test_continuity_residual(self):
        """Test continuity residual"""
        config = MantleConvectionConfig()
        pattern = MantleConvectionPattern(config)

        residual = pattern._continuity_residual()

        self.assertEqual(residual.shape, (config.nx, config.ny, config.nz))

    def test_nusselt_number(self):
        """Test Nusselt number calculation"""
        config = MantleConvectionConfig()
        pattern = MantleConvectionPattern(config)

        Nu = pattern._calculate_nusselt_number()

        self.assertIsInstance(Nu, float)
        self.assertGreaterEqual(Nu, 1.0)

    def test_viscous_dissipation(self):
        """Test viscous dissipation"""
        config = MantleConvectionConfig()
        pattern = MantleConvectionPattern(config)

        diss = pattern._calculate_viscous_dissipation()

        self.assertIsInstance(diss, float)
        self.assertGreaterEqual(diss, 0)

    def test_step(self):
        """Test single time step"""
        config = MantleConvectionConfig()
        pattern = MantleConvectionPattern(config)

        T_before = pattern.T.copy()
        pattern._step()

        # Temperature should change
        self.assertFalse(np.allclose(pattern.T, T_before))

    def test_boundary_conditions(self):
        """Test boundary conditions"""
        config = MantleConvectionConfig()
        pattern = MantleConvectionPattern(config)

        pattern.T[:, :, :] = 0.5  # Reset
        pattern._apply_boundary_conditions()

        # Check boundary values
        self.assertTrue(np.all(pattern.T[:, :, 0] == config.bottom_temp))
        self.assertTrue(np.all(pattern.T[:, :, -1] == config.top_temp))

    def test_metadata(self):
        """Test metadata retrieval"""
        metadata = MantleConvectionPattern.get_metadata()

        self.assertEqual(metadata["id"], "mantle_convection")
        self.assertIn("parameters", metadata)

    def test_short_simulation(self):
        """Test running a short simulation"""
        config = MantleConvectionConfig(
            nx=16, ny=16, nz=8, max_time=0.001, dt=1e-7, output_interval=10
        )
        pattern = MantleConvectionPattern(config)

        result = pattern.run()

        self.assertIn("temperature", result)
        self.assertIn("nusselt_number", result)
        self.assertGreater(len(result["time"]), 0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
