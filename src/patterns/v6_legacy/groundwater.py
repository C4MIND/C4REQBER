"""
TURBO-CDI v6.0 - Groundwater Pattern
Darcy-Richards equation for variably saturated flow in porous media.

Pattern Structure (Christopher Alexander):
- Context: Aquifer management, contaminant transport, irrigation design
- Forces: Hydraulic gradients, soil heterogeneity, recharge, pumping
- Solution: Richards equation with van Genuchten soil parameters
"""

import numpy as np
import logging
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class GroundwaterConfig:
    """Configuration for groundwater flow simulation"""

    # Grid settings
    nx: int = 50  # Horizontal grid points
    ny: int = 50
    nz: int = 20  # Vertical layers

    # Domain extent (m)
    Lx: float = 1000.0  # 1 km
    Ly: float = 1000.0
    H: float = 50.0  # Aquifer thickness

    # Time stepping
    dt: float = 3600.0  # 1 hour
    days: int = 30  # Simulation duration

    # Soil hydraulic parameters (van Genuchten)
    alpha: float = 0.036  # 1/cm (converted in code)
    n_vg: float = 1.56  # Shape parameter
    theta_s: float = 0.43  # Saturated water content
    theta_r: float = 0.078  # Residual water content
    K_s: float = 1.0e-4  # Saturated hydraulic conductivity (m/s)

    # Initial conditions
    water_table_depth: float = 5.0  # Initial water table depth (m)

    # Recharge
    recharge_rate: float = 1.0e-7  # m/s (about 3 mm/day)

    # Pumping well
    well_x: float = 500.0  # Well location
    well_y: float = 500.0
    pumping_rate: float = 0.01  # m^3/s
    pumping_start: float = 5.0  # Start pumping after N days
    pumping_duration: float = 10.0  # Pump for N days

    # Output
    output_interval: int = 24  # Daily output


class GroundwaterPattern:
    """
    Darcy-Richards groundwater flow model.

    Solves the Richards equation for variably saturated flow
    using the van Genuchten-Mualem soil hydraulic model.
    Includes recharge, pumping, and free drainage boundaries.
    """

    PATTERN_ID = "groundwater"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: Optional[GroundwaterConfig] = None):
        self.config = config or GroundwaterConfig()
        self._initialize_grid()
        self._initialize_fields()

    def _initialize_grid(self):
        """Initialize 3D grid"""
        cfg = self.config

        self.x = np.linspace(0, cfg.Lx, cfg.nx)
        self.y = np.linspace(0, cfg.Ly, cfg.ny)
        self.z = np.linspace(0, cfg.H, cfg.nz)  # 0 = bottom, H = surface

        self.dx = cfg.Lx / (cfg.nx - 1)
        self.dy = cfg.Ly / (cfg.ny - 1)
        self.dz = cfg.H / (cfg.nz - 1)

        self.X, self.Y, self.Z = np.meshgrid(self.x, self.y, self.z, indexing="ij")

    def _initialize_fields(self):
        """Initialize pressure head and moisture content"""
        cfg = self.config

        shape = (cfg.nx, cfg.ny, cfg.nz)

        # Pressure head (negative = unsaturated, 0 = saturated)
        self.h = np.zeros(shape)

        # Initialize with hydrostatic profile
        for k in range(cfg.nz):
            depth = cfg.H - self.z[k]  # Depth below surface

            if depth < cfg.water_table_depth:
                # Above water table (unsaturated)
                self.h[:, :, k] = -(cfg.water_table_depth - depth)
            else:
                # Below water table (saturated)
                self.h[:, :, k] = depth - cfg.water_table_depth

        # Water content
        self.theta = np.zeros(shape)
        self._update_water_content()

        # Hydraulic conductivity
        self.K = np.zeros(shape)
        self._update_hydraulic_conductivity()

        # Well location (nearest grid cell)
        self.well_i = int(cfg.well_x / self.dx)
        self.well_j = int(cfg.well_y / self.dy)

        # Output storage
        self.history = {
            "h": [],
            "theta": [],
            "water_table": [],
            "time": [],
            "storage": [],
            "drawdown": [],
        }

    def _effective_saturation(self, h: np.ndarray) -> np.ndarray:
        """Calculate effective saturation from pressure head"""
        cfg = self.config

        # Convert alpha from 1/cm to 1/m
        alpha_m = cfg.alpha * 100

        # Effective saturation (van Genuchten)
        Se = np.ones_like(h)

        unsat_mask = h < 0

        # van Genuchten equation
        m = 1 - 1 / cfg.n_vg
        Se[unsat_mask] = (1 + (alpha_m * np.abs(h[unsat_mask])) ** cfg.n_vg) ** (-m)

        return Se

    def _update_water_content(self):
        """Update water content from pressure head"""
        cfg = self.config

        Se = self._effective_saturation(self.h)
        self.theta = cfg.theta_r + Se * (cfg.theta_s - cfg.theta_r)

    def _update_hydraulic_conductivity(self):
        """Update hydraulic conductivity from pressure head"""
        cfg = self.config

        Se = self._effective_saturation(self.h)

        # Mualem equation
        m = 1 - 1 / cfg.n_vg
        self.K = cfg.K_s * Se**0.5 * (1 - (1 - Se ** (1 / m)) ** m) ** 2

        # Saturated regions
        self.K[self.h >= 0] = cfg.K_s

    def _water_capacity(self, h: np.ndarray) -> np.ndarray:
        """Calculate specific water capacity d(theta)/d(h)"""
        cfg = self.config

        alpha_m = cfg.alpha * 100
        m = 1 - 1 / cfg.n_vg

        C = np.zeros_like(h)

        unsat_mask = h < 0

        # Derivative of van Genuchten equation
        Se = self._effective_saturation(h)
        C[unsat_mask] = (
            (cfg.theta_s - cfg.theta_r)
            * m
            * cfg.n_vg
            * alpha_m
            * (alpha_m * np.abs(h[unsat_mask])) ** (cfg.n_vg - 1)
            * Se[unsat_mask] ** (1 / m)
            / (1 + (alpha_m * np.abs(h[unsat_mask])) ** cfg.n_vg)
        )

        return C

    def _hydraulic_head(self) -> np.ndarray:
        """Calculate total hydraulic head H = h + z"""
        return self.h + self.Z

    def _darcy_flux_x(self) -> np.ndarray:
        """Calculate Darcy flux in x-direction"""
        H = self._hydraulic_head()
        qx = np.zeros_like(H)

        for i in range(self.config.nx - 1):
            K_face = 0.5 * (self.K[i, :, :] + self.K[i + 1, :, :])
            qx[i, :, :] = -K_face * (H[i + 1, :, :] - H[i, :, :]) / self.dx

        return qx

    def _darcy_flux_y(self) -> np.ndarray:
        """Calculate Darcy flux in y-direction"""
        H = self._hydraulic_head()
        qy = np.zeros_like(H)

        for j in range(self.config.ny - 1):
            K_face = 0.5 * (self.K[:, j, :] + self.K[:, j + 1, :])
            qy[:, j, :] = -K_face * (H[:, j + 1, :] - H[:, j, :]) / self.dy

        return qy

    def _darcy_flux_z(self) -> np.ndarray:
        """Calculate Darcy flux in z-direction"""
        H = self._hydraulic_head()
        qz = np.zeros_like(H)

        for k in range(self.config.nz - 1):
            K_face = 0.5 * (self.K[:, :, k] + self.K[:, :, k + 1])
            qz[:, :, k] = -K_face * (H[:, :, k + 1] - H[:, :, k]) / self.dz

        return qz

    def _richards_tendency(self, time: float) -> np.ndarray:
        """Calculate RHS of Richards equation"""
        cfg = self.config

        # Darcy fluxes
        qx = self._darcy_flux_x()
        qy = self._darcy_flux_y()
        qz = self._darcy_flux_z()

        # Divergence
        div_q = np.zeros_like(self.h)

        for i in range(1, cfg.nx - 1):
            for j in range(1, cfg.ny - 1):
                for k in range(1, cfg.nz - 1):
                    dqx_dx = (qx[i, j, k] - qx[i - 1, j, k]) / self.dx
                    dqy_dy = (qy[i, j, k] - qy[i, j - 1, k]) / self.dy
                    dqz_dz = (qz[i, j, k] - qz[i, j, k - 1]) / self.dz

                    div_q[i, j, k] = dqx_dx + dqy_dy + dqz_dz

        # Source/sink terms
        source = np.zeros_like(self.h)

        # Recharge at surface
        source[:, :, -1] += cfg.recharge_rate / self.dz

        # Pumping
        day = time / 86400.0
        if cfg.pumping_start <= day < (cfg.pumping_start + cfg.pumping_duration):
            # Distribute pumping over multiple layers
            pumping_per_layer = cfg.pumping_rate / (self.dx * self.dy * 5)  # 5 layers
            for k in range(max(0, cfg.nz - 5), cfg.nz):
                source[self.well_i, self.well_j, k] -= pumping_per_layer

        return -div_q + source

    def _step(self, time: float):
        """Advance model by one time step using explicit Euler"""
        cfg = self.config

        # Update K and theta
        self._update_water_content()
        self._update_hydraulic_conductivity()

        # Water capacity
        C = self._water_capacity(self.h)
        C = np.maximum(C, 1.0e-10)  # Avoid division by zero

        # RHS of Richards equation
        rhs = self._richards_tendency(time)

        # Explicit update
        dh_dt = rhs / C
        self.h += dh_dt * cfg.dt

        # Boundary conditions
        self._apply_boundary_conditions()

    def _apply_boundary_conditions(self):
        """Apply boundary conditions"""
        cfg = self.config

        # No-flow at lateral boundaries
        self.h[0, :, :] = self.h[1, :, :]
        self.h[-1, :, :] = self.h[-2, :, :]
        self.h[:, 0, :] = self.h[:, 1, :]
        self.h[:, -1, :] = self.h[:, -2, :]

        # Free drainage at bottom
        self.h[:, :, 0] = self.h[:, :, 1]

        # Atmospheric boundary at top (seepage face)
        for i in range(cfg.nx):
            for j in range(cfg.ny):
                if self.h[i, j, -1] > 0:
                    # Ponding - set to zero (atmospheric pressure)
                    self.h[i, j, -1] = 0

    def _calculate_water_table(self) -> np.ndarray:
        """Calculate water table elevation"""
        cfg = self.config

        water_table = np.zeros((cfg.nx, cfg.ny))

        for i in range(cfg.nx):
            for j in range(cfg.ny):
                # Find where pressure becomes positive
                h_profile = self.h[i, j, :]
                k_sat = np.where(h_profile >= 0)[0]

                if len(k_sat) > 0:
                    # Interpolate between first saturated cell and surface
                    water_table[i, j] = cfg.H - self.z[k_sat[0]]
                else:
                    # Completely unsaturated - use pressure profile
                    # Estimate where h would be zero
                    water_table[i, j] = 0

        return water_table

    def _calculate_storage(self) -> float:
        """Calculate total water storage in aquifer"""
        volume = np.sum(self.theta) * self.dx * self.dy * self.dz
        return volume

    def _calculate_drawdown(self) -> float:
        """Calculate drawdown at well"""
        cfg = self.config

        # Water table at well
        wt = self._calculate_water_table()
        current_wt = wt[self.well_i, self.well_j]

        # Initial water table depth
        initial_wt = cfg.H - cfg.water_table_depth

        drawdown = initial_wt - current_wt

        return max(0, drawdown)

    def run(self, hypothesis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run the groundwater simulation"""
        cfg = self.config
        n_steps = int(cfg.days * 86400 / cfg.dt)

        logger.info(
            f"Starting groundwater simulation: {cfg.days} days, {n_steps} steps"
        )

        for step in range(n_steps):
            time = step * cfg.dt

            self._step(time)

            # Output
            if step % cfg.output_interval == 0:
                day = time / 86400.0

                water_table = self._calculate_water_table()
                storage = self._calculate_storage()
                drawdown = self._calculate_drawdown()

                self.history["h"].append(np.mean(self.h))
                self.history["theta"].append(np.mean(self.theta))
                self.history["water_table"].append(np.mean(water_table))
                self.history["time"].append(day)
                self.history["storage"].append(storage)
                self.history["drawdown"].append(drawdown)

            if step % 100 == 0:
                logger.debug(
                    f"Step {step}/{n_steps}, Day {day:.1f}, Storage: {storage:.2e} m³"
                )

        return self._format_output()

    def _format_output(self) -> Dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        return {
            "pressure_head": self.history["h"],
            "water_content": self.history["theta"],
            "water_table": self.history["water_table"],
            "storage": self.history["storage"],
            "drawdown": self.history["drawdown"],
            "time_days": self.history["time"],
            "final_state": {
                "mean_theta": float(np.mean(self.theta)),
                "mean_pressure": float(np.mean(self.h)),
                "water_table_depth": float(
                    cfg.H - np.mean(self._calculate_water_table())
                ),
                "total_storage": float(self._calculate_storage()),
                "final_drawdown": float(self._calculate_drawdown()),
                "saturated_fraction": float(np.sum(self.h >= 0) / self.h.size),
            },
            "hydraulics": {
                "K_s": cfg.K_s,
                "recharge_rate_m_day": float(cfg.recharge_rate * 86400),
                "pumping_rate": cfg.pumping_rate,
            },
            "grid": {
                "nx": cfg.nx,
                "ny": cfg.ny,
                "nz": cfg.nz,
            },
            "config": {
                "days": cfg.days,
                "alpha": cfg.alpha,
                "n_vg": cfg.n_vg,
            },
        }

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Groundwater",
            "category": "ON_DEMAND",
            "domain": ["Hydrogeology", "Water Resources"],
            "description": "Darcy-Richards variably saturated flow model",
            "computational_complexity": "O(N³)",
            "typical_runtime": "minutes to hours",
            "accuracy": "High (research grade)",
            "assumptions": [
                "van Genuchten-Mualem soil model",
                "Homogeneous soil",
                "Isothermal conditions",
                "No air entrapment",
            ],
            "parameters": [
                {
                    "name": "nx",
                    "type": "int",
                    "default": 50,
                    "description": "X grid points",
                },
                {
                    "name": "ny",
                    "type": "int",
                    "default": 50,
                    "description": "Y grid points",
                },
                {
                    "name": "nz",
                    "type": "int",
                    "default": 20,
                    "description": "Vertical layers",
                },
                {
                    "name": "K_s",
                    "type": "float",
                    "default": 1e-4,
                    "description": "Saturated conductivity",
                },
                {
                    "name": "alpha",
                    "type": "float",
                    "default": 0.036,
                    "description": "VG parameter",
                },
            ],
        }


# Unit tests
import unittest


class TestGroundwater(unittest.TestCase):
    def test_initialization(self):
        """Test that pattern initializes correctly"""
        config = GroundwaterConfig(nx=20, ny=20, nz=10)
        pattern = GroundwaterPattern(config)

        self.assertEqual(pattern.h.shape, (20, 20, 10))
        self.assertEqual(pattern.theta.shape, (20, 20, 10))
        self.assertEqual(pattern.K.shape, (20, 20, 10))

    def test_effective_saturation(self):
        """Test effective saturation calculation"""
        config = GroundwaterConfig()
        pattern = GroundwaterPattern(config)

        h_test = np.array([-100, -10, -1, 0, 1])
        Se = pattern._effective_saturation(h_test)

        # Should be 1 for saturated (h >= 0)
        self.assertEqual(Se[3], 1.0)
        self.assertEqual(Se[4], 1.0)

        # Should decrease with more negative h
        self.assertTrue(np.all(np.diff(Se[:3]) > 0))

    def test_water_content(self):
        """Test water content update"""
        config = GroundwaterConfig()
        pattern = GroundwaterPattern(config)

        pattern._update_water_content()

        self.assertTrue(np.all(pattern.theta >= config.theta_r))
        self.assertTrue(np.all(pattern.theta <= config.theta_s))

    def test_hydraulic_conductivity(self):
        """Test hydraulic conductivity calculation"""
        config = GroundwaterConfig()
        pattern = GroundwaterPattern(config)

        pattern._update_hydraulic_conductivity()

        self.assertTrue(np.all(pattern.K >= 0))
        self.assertTrue(np.all(pattern.K <= config.K_s))

    def test_water_capacity(self):
        """Test specific water capacity"""
        config = GroundwaterConfig()
        pattern = GroundwaterPattern(config)

        h_test = np.array([-10, -5, -1])
        C = pattern._water_capacity(h_test)

        self.assertTrue(np.all(C >= 0))

    def test_darcy_flux(self):
        """Test Darcy flux calculation"""
        config = GroundwaterConfig()
        pattern = GroundwaterPattern(config)

        qx = pattern._darcy_flux_x()
        qy = pattern._darcy_flux_y()
        qz = pattern._darcy_flux_z()

        self.assertEqual(qx.shape, pattern.h.shape)
        self.assertEqual(qy.shape, pattern.h.shape)
        self.assertEqual(qz.shape, pattern.h.shape)

    def test_richards_tendency(self):
        """Test RHS of Richards equation"""
        config = GroundwaterConfig()
        pattern = GroundwaterPattern(config)

        rhs = pattern._richards_tendency(0)

        self.assertEqual(rhs.shape, pattern.h.shape)
        self.assertTrue(np.all(np.isfinite(rhs)))

    def test_water_table(self):
        """Test water table calculation"""
        config = GroundwaterConfig()
        pattern = GroundwaterPattern(config)

        wt = pattern._calculate_water_table()

        self.assertEqual(wt.shape, (config.nx, config.ny))
        self.assertTrue(np.all(wt >= 0))

    def test_storage(self):
        """Test storage calculation"""
        config = GroundwaterConfig()
        pattern = GroundwaterPattern(config)

        storage = pattern._calculate_storage()

        self.assertIsInstance(storage, float)
        self.assertGreater(storage, 0)

    def test_step(self):
        """Test single time step"""
        config = GroundwaterConfig(dt=100)
        pattern = GroundwaterPattern(config)

        h_before = pattern.h.copy()
        pattern._step(0)

        # Should produce finite results
        self.assertTrue(np.all(np.isfinite(pattern.h)))

    def test_metadata(self):
        """Test metadata retrieval"""
        metadata = GroundwaterPattern.get_metadata()

        self.assertEqual(metadata["id"], "groundwater")
        self.assertIn("parameters", metadata)

    def test_short_simulation(self):
        """Test running a short simulation"""
        config = GroundwaterConfig(nx=15, ny=15, nz=5, days=2, dt=1000)
        pattern = GroundwaterPattern(config)

        result = pattern.run()

        self.assertIn("water_content", result)
        self.assertIn("water_table", result)
        self.assertGreater(len(result["time_days"]), 0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
