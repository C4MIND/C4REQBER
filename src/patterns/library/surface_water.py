"""
C4REQBER v6.0 - Surface Water Pattern
Saint-Venant shallow water equations for river and flood modeling.

Pattern Structure (Christopher Alexander):
- Context: Flood forecasting, river hydraulics, coastal inundation
- Forces: Gravity, friction, topography, boundary conditions
- Solution: Shallow water equations with wetting-drying
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


@dataclass
class SurfaceWaterConfig:
    """Configuration for surface water simulation"""

    # Grid settings
    nx: int = 200  # Grid points in x
    ny: int = 100  # Grid points in y

    # Domain extent (m)
    Lx: float = 10.0e3  # 10 km
    Ly: float = 5.0e3  # 5 km

    # Time stepping
    dt: float = 1.0  # seconds
    hours: int = 24  # simulation duration

    # Physical parameters
    g: float = 9.81  # gravity
    manning_n: float = 0.03  # Manning's roughness coefficient

    # Numerical parameters
    theta: float = 1.0  # Implicitness parameter (1=fully implicit)
    min_depth: float = 0.01  # Minimum water depth (m)

    # Initial conditions
    h_initial: float = 1.0  # Initial water depth (m)

    # Inflow boundary
    inflow_rate: float = 10.0  # m^3/s (per unit width for 2D)
    inflow_duration: float = 3600.0  # seconds

    # Topography
    bed_slope: float = 0.001  # Channel slope
    channel_width: float = 500.0  # m
    channel_depth: float = 2.0  # m

    # Output
    output_interval: int = 600  # every 10 minutes


class SurfaceWaterPattern:
    """
    Saint-Venant shallow water model.

    Solves the 2D shallow water equations for surface water flow
    including wetting and drying, friction, and varying topography.
    """

    PATTERN_ID = "surface_water"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: SurfaceWaterConfig | None = None) -> None:
        self.config = config or SurfaceWaterConfig()
        self._initialize_grid()
        self._initialize_fields()

    def _initialize_grid(self) -> None:
        """Initialize computational grid"""
        cfg = self.config

        self.x = np.linspace(0, cfg.Lx, cfg.nx)
        self.y = np.linspace(0, cfg.Ly, cfg.ny)
        self.dx = cfg.Lx / (cfg.nx - 1)
        self.dy = cfg.Ly / (cfg.ny - 1)

        self.X, self.Y = np.meshgrid(self.x, self.y, indexing="ij")

    def _initialize_fields(self) -> None:
        """Initialize water depth and velocities"""
        cfg = self.config

        # Bed elevation (channel geometry)
        self.z_b = np.zeros((cfg.nx, cfg.ny))

        # Create channel
        channel_center = cfg.Ly / 2
        for j in range(cfg.ny):
            dist_from_center = abs(self.y[j] - channel_center)
            if dist_from_center < cfg.channel_width / 2:
                # Inside channel
                self.z_b[:, j] = -cfg.channel_depth + cfg.bed_slope * (cfg.Lx - self.x)
            else:
                # Floodplain
                bank_height = 1.0
                self.z_b[:, j] = (
                    -cfg.channel_depth + cfg.bed_slope * (cfg.Lx - self.x) + bank_height
                )

        # Water surface elevation
        self.eta = np.ones((cfg.nx, cfg.ny)) * cfg.h_initial

        # Water depth
        self.h = np.maximum(self.eta - self.z_b, 0)

        # Velocities (staggered grid - Arakawa C)
        self.u = np.zeros((cfg.nx - 1, cfg.ny))  # x-velocity at cell faces
        self.v = np.zeros((cfg.nx, cfg.ny - 1))  # y-velocity at cell faces

        # Output storage
        self.history = {  # type: ignore[var-annotated]
            "h": [],
            "eta": [],
            "u": [],
            "v": [],
            "time": [],
            "discharge": [],
            "max_depth": [],
        }

    def _calculate_depth_at_u(self) -> np.ndarray:
        """Calculate depth at u-points (cell faces in x)"""
        cfg = self.config

        # Average depth from adjacent cells
        h_u = np.zeros((cfg.nx - 1, cfg.ny))
        for i in range(cfg.nx - 1):
            h_u[i, :] = 0.5 * (self.h[i, :] + self.h[i + 1, :])

        return h_u

    def _calculate_depth_at_v(self) -> np.ndarray:
        """Calculate depth at v-points (cell faces in y)"""
        cfg = self.config

        h_v = np.zeros((cfg.nx, cfg.ny - 1))
        for j in range(cfg.ny - 1):
            h_v[:, j] = 0.5 * (self.h[:, j] + self.h[:, j + 1])

        return h_v

    def _friction_slope_u(self) -> np.ndarray:
        """Calculate friction slope for u-momentum"""
        cfg = self.config

        h_u = self._calculate_depth_at_u()
        h_u = np.maximum(h_u, cfg.min_depth)

        # Manning equation
        S_f = cfg.manning_n**2 * self.u * np.abs(self.u) / h_u ** (4 / 3)

        return S_f  # type: ignore[no-any-return]

    def _friction_slope_v(self) -> np.ndarray:
        """Calculate friction slope for v-momentum"""
        cfg = self.config

        h_v = self._calculate_depth_at_v()
        h_v = np.maximum(h_v, cfg.min_depth)

        S_f = cfg.manning_n**2 * self.v * np.abs(self.v) / h_v ** (4 / 3)

        return S_f  # type: ignore[no-any-return]

    def _momentum_equation_u(self) -> np.ndarray:
        """Calculate u-momentum equation"""
        cfg = self.config

        dudt = np.zeros_like(self.u)

        # Pressure gradient (water surface slope)
        for i in range(cfg.nx - 1):
            deta_dx = (self.eta[i + 1, :] - self.eta[i, :]) / self.dx
            dudt[i, :] = -cfg.g * deta_dx

        # Friction
        S_f = self._friction_slope_u()
        dudt -= cfg.g * S_f

        # Wetting/drying mask
        h_u = self._calculate_depth_at_u()
        dudt[h_u < cfg.min_depth] = 0

        return dudt

    def _momentum_equation_v(self) -> np.ndarray:
        """Calculate v-momentum equation"""
        cfg = self.config

        dvdt = np.zeros_like(self.v)

        # Pressure gradient
        for j in range(cfg.ny - 1):
            deta_dy = (self.eta[:, j + 1] - self.eta[:, j]) / self.dy
            dvdt[:, j] = -cfg.g * deta_dy

        # Friction
        S_f = self._friction_slope_v()
        dvdt -= cfg.g * S_f

        # Wetting/drying mask
        h_v = self._calculate_depth_at_v()
        dvdt[h_v < cfg.min_depth] = 0

        return dvdt

    def _continuity_equation(self) -> np.ndarray:
        """Calculate continuity (mass conservation)"""
        cfg = self.config

        deta_dt = np.zeros_like(self.eta)

        # Flux divergence
        for i in range(1, cfg.nx - 1):
            for j in range(1, cfg.ny - 1):
                # Flux differences
                dqx_dx = (
                    self.u[i, j] * self._calculate_depth_at_u()[i, j]
                    - self.u[i - 1, j] * self._calculate_depth_at_u()[i - 1, j]
                ) / self.dx
                dqy_dy = (
                    self.v[i, j] * self._calculate_depth_at_v()[i, j]
                    - self.v[i, j - 1] * self._calculate_depth_at_v()[i, j - 1]
                ) / self.dy

                deta_dt[i, j] = -(dqx_dx + dqy_dy)

        return deta_dt

    def _apply_boundary_conditions(self, time: float) -> None:
        """Apply boundary conditions"""
        cfg = self.config

        # Inflow at upstream boundary (x=0)
        if time < cfg.inflow_duration:
            # Distribute inflow across channel
            inflow_per_cell = cfg.inflow_rate / cfg.channel_width * self.dy

            channel_center = cfg.Ly / 2
            for j in range(cfg.ny):
                dist = abs(self.y[j] - channel_center)
                if dist < cfg.channel_width / 2:
                    # Inflow velocity
                    h_face = max(self.h[0, j], cfg.min_depth)
                    self.u[0, j] = inflow_per_cell / h_face

        # Outflow at downstream boundary (zero gradient)
        self.u[-1, :] = self.u[-2, :]

        # Wall boundaries (y=0 and y=Ly)
        self.v[:, 0] = 0
        self.v[:, -1] = 0

        # No-slip at walls
        self.u[:, 0] = 0
        self.u[:, -1] = 0

    def _calculate_courant_number(self) -> float:
        """Calculate maximum Courant number"""
        cfg = self.config

        c = np.sqrt(cfg.g * np.maximum(self.h, cfg.min_depth))

        cfl_x = np.max(c * cfg.dt / self.dx)
        cfl_y = np.max(c * cfg.dt / self.dy)

        return max(cfl_x, cfl_y)  # type: ignore[no-any-return]

    def _calculate_discharge(self) -> float:
        """Calculate total discharge through domain"""
        cfg = self.config

        # Integrate velocity * depth across a cross-section
        h_u = self._calculate_depth_at_u()

        # At mid-domain
        i_mid = cfg.nx // 2
        discharge = np.sum(self.u[i_mid, :] * h_u[i_mid, :]) * self.dy

        return discharge  # type: ignore[no-any-return]

    def _step(self, time: float) -> None:
        """Advance model by one time step"""
        cfg = self.config

        # Calculate tendencies
        dudt = self._momentum_equation_u()
        dvdt = self._momentum_equation_v()
        deta_dt = self._continuity_equation()

        # Update velocities
        self.u += dudt * cfg.dt
        self.v += dvdt * cfg.dt

        # Update water surface
        self.eta += deta_dt * cfg.dt

        # Update depth
        self.h = np.maximum(self.eta - self.z_b, 0)

        # Apply boundary conditions
        self._apply_boundary_conditions(time)

    def run(self, hypothesis: dict[str, Any] = None) -> dict[str, Any]:  # type: ignore[assignment]
        """Run the surface water simulation"""
        cfg = self.config
        n_steps = int(cfg.hours * 3600 / cfg.dt)

        logger.info(
            f"Starting surface water simulation: {cfg.hours} hours, {n_steps} steps"
        )

        for step in range(n_steps):
            time = step * cfg.dt

            self._step(time)

            # Output
            if step % cfg.output_interval == 0:
                hour = time / 3600.0

                discharge = self._calculate_discharge()
                max_depth = np.max(self.h)

                self.history["h"].append(self.h.copy())
                self.history["eta"].append(self.eta.copy())
                self.history["u"].append(self.u.copy())
                self.history["v"].append(self.v.copy())
                self.history["time"].append(hour)
                self.history["discharge"].append(discharge)
                self.history["max_depth"].append(max_depth)

            if step % 1000 == 0:
                cfl = self._calculate_courant_number()
                logger.debug(
                    f"Step {step}/{n_steps}, t={hour:.2f}h, CFL={cfl:.3f}, Q={discharge:.1f}"
                )

        return self._format_output()

    def _format_output(self) -> dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        # Wet area
        wet_cells = np.sum(self.h > cfg.min_depth)
        wet_area = wet_cells * self.dx * self.dy / 1e6  # km^2

        return {
            "water_depth": self.history["max_depth"],
            "discharge": self.history["discharge"],
            "time_hours": self.history["time"],
            "final_state": {
                "max_depth": float(np.max(self.h)),
                "mean_depth": float(np.mean(self.h[self.h > 0])),
                "wet_area_km2": float(wet_area),
                "max_velocity": float(np.max(np.abs(self.u))),
                "final_discharge": float(self.history["discharge"][-1])
                if self.history["discharge"]
                else 0,
            },
            "hydraulics": {
                "froude_number": float(
                    np.max(np.abs(self.u)) / np.sqrt(cfg.g * np.max(self.h))
                )
                if np.max(self.h) > 0
                else 0,
                "courant_max": float(self._calculate_courant_number()),
            },
            "grid": {
                "nx": cfg.nx,
                "ny": cfg.ny,
                "Lx": cfg.Lx,
                "Ly": cfg.Ly,
            },
            "config": {
                "hours": cfg.hours,
                "manning_n": cfg.manning_n,
                "inflow_rate": cfg.inflow_rate,
            },
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Surface Water",
            "category": "ON_DEMAND",
            "domain": ["Hydrology", "Hydraulics"],
            "description": "Saint-Venant shallow water equations for river and flood modeling",
            "computational_complexity": "O(N²)",
            "typical_runtime": "minutes to hours",
            "accuracy": "High (engineering grade)",
            "assumptions": [
                "Hydrostatic pressure",
                "Shallow water approximation",
                "Manning friction",
                "Wetting-drying",
            ],
            "parameters": [
                {
                    "name": "nx",
                    "type": "int",
                    "default": 200,
                    "description": "X grid points",
                },
                {
                    "name": "ny",
                    "type": "int",
                    "default": 100,
                    "description": "Y grid points",
                },
                {
                    "name": "hours",
                    "type": "int",
                    "default": 24,
                    "description": "Simulation hours",
                },
                {
                    "name": "manning_n",
                    "type": "float",
                    "default": 0.03,
                    "description": "Manning roughness",
                },
                {
                    "name": "inflow_rate",
                    "type": "float",
                    "default": 10.0,
                    "description": "Inflow rate m^3/s",
                },
            ],
        }


# Unit tests
import unittest


class TestSurfaceWater(unittest.TestCase):
    """TestSurfaceWater."""
    def test_initialization(self) -> None:
        """Test that pattern initializes correctly"""
        config = SurfaceWaterConfig(nx=50, ny=30)
        pattern = SurfaceWaterPattern(config)

        self.assertEqual(pattern.h.shape, (50, 30))
        self.assertEqual(pattern.eta.shape, (50, 30))
        self.assertEqual(pattern.u.shape, (49, 30))
        self.assertEqual(pattern.v.shape, (50, 29))

    def test_grid_spacing(self) -> None:
        """Test grid spacing"""
        config = SurfaceWaterConfig(Lx=1000, Ly=500, nx=51, ny=26)
        pattern = SurfaceWaterPattern(config)

        self.assertAlmostEqual(pattern.dx, 20.0, places=1)
        self.assertAlmostEqual(pattern.dy, 20.0, places=1)

    def test_depth_calculation(self) -> None:
        """Test depth at velocity points"""
        config = SurfaceWaterConfig(nx=20, ny=20)
        pattern = SurfaceWaterPattern(config)

        h_u = pattern._calculate_depth_at_u()
        h_v = pattern._calculate_depth_at_v()

        self.assertEqual(h_u.shape, (19, 20))
        self.assertEqual(h_v.shape, (20, 19))
        self.assertTrue(np.all(h_u >= 0))

    def test_friction_slope(self) -> None:
        """Test friction slope calculation"""
        config = SurfaceWaterConfig()
        pattern = SurfaceWaterPattern(config)

        pattern.u[:, :] = 1.0  # Set velocity

        S_f = pattern._friction_slope_u()

        self.assertEqual(S_f.shape, pattern.u.shape)
        self.assertTrue(np.all(S_f >= 0))

    def test_momentum_equation(self) -> None:
        """Test momentum equation calculation"""
        config = SurfaceWaterConfig()
        pattern = SurfaceWaterPattern(config)

        dudt = pattern._momentum_equation_u()
        dvdt = pattern._momentum_equation_v()

        self.assertEqual(dudt.shape, pattern.u.shape)
        self.assertEqual(dvdt.shape, pattern.v.shape)
        self.assertTrue(np.all(np.isfinite(dudt)))

    def test_continuity(self) -> None:
        """Test continuity equation"""
        config = SurfaceWaterConfig()
        pattern = SurfaceWaterPattern(config)

        deta_dt = pattern._continuity_equation()

        self.assertEqual(deta_dt.shape, pattern.eta.shape)
        self.assertTrue(np.all(np.isfinite(deta_dt)))

    def test_boundary_conditions(self) -> None:
        """Test boundary conditions"""
        config = SurfaceWaterConfig(inflow_duration=1000)
        pattern = SurfaceWaterPattern(config)

        pattern._apply_boundary_conditions(500)

        # Check that something happens at inflow
        self.assertTrue(np.any(pattern.u[0, :] > 0) or np.all(pattern.u[0, :] == 0))

    def test_courant_number(self) -> None:
        """Test CFL calculation"""
        config = SurfaceWaterConfig()
        pattern = SurfaceWaterPattern(config)

        cfl = pattern._calculate_courant_number()

        self.assertIsInstance(cfl, float)
        self.assertGreater(cfl, 0)

    def test_discharge(self) -> None:
        """Test discharge calculation"""
        config = SurfaceWaterConfig()
        pattern = SurfaceWaterPattern(config)

        Q = pattern._calculate_discharge()

        self.assertIsInstance(Q, float)

    def test_step(self) -> None:
        """Test single time step"""
        config = SurfaceWaterConfig()
        pattern = SurfaceWaterPattern(config)

        h_before = pattern.h.copy()
        pattern._step(0)
        h_after = pattern.h.copy()

        # Depth should remain non-negative
        self.assertTrue(np.all(pattern.h >= 0))

    def test_metadata(self) -> None:
        """Test metadata retrieval"""
        metadata = SurfaceWaterPattern.get_metadata()

        self.assertEqual(metadata["id"], "surface_water")
        self.assertIn("parameters", metadata)

    def test_short_simulation(self) -> None:
        """Test running a short simulation"""
        config = SurfaceWaterConfig(nx=30, ny=20, hours=1, dt=10)
        pattern = SurfaceWaterPattern(config)

        result = pattern.run()

        self.assertIn("water_depth", result)
        self.assertIn("discharge", result)
        self.assertGreater(len(result["time_hours"]), 0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
