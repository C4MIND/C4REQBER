"""
TURBO-CDI v6.0 - Sea Ice Pattern
Thermodynamic sea ice model with ice growth, melt, and dynamics.

Pattern Structure (Christopher Alexander):
- Context: Polar climate modeling, ice sheet studies, seasonal forecasting
- Forces: Energy balance, ice-albedo feedback, ocean-ice interaction
- Solution: Zero-layer thermodynamics with ice thickness distribution
"""

import numpy as np
import logging
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SeaIceConfig:
    """Configuration for sea ice simulation"""

    # Grid settings
    nx: int = 100  # Zonal grid points
    ny: int = 100  # Meridional grid points

    # Domain (Arctic basin scale)
    Lx: float = 4.0e6  # m (4000 km)
    Ly: float = 4.0e6  # m (4000 km)

    # Time stepping
    dt: float = 86400.0  # Time step (seconds) - daily
    days: int = 365  # Simulation duration

    # Physical parameters
    rho_ice: float = 917.0  # Ice density (kg/m^3)
    rho_water: float = 1026.0  # Seawater density (kg/m^3)
    L_fusion: float = 3.34e5  # Latent heat of fusion (J/kg)
    k_ice: float = 2.2  # Ice thermal conductivity (W/m/K)
    c_ice: float = 2100.0  # Ice specific heat (J/kg/K)

    # Albedo parameters
    albedo_ice: float = 0.65  # Ice albedo
    albedo_melt: float = 0.50  # Melt pond albedo
    albedo_water: float = 0.07  # Open water albedo

    # Thermodynamic parameters
    T_freeze: float = -1.8  # Ocean freezing temperature (C)
    h_min: float = 0.01  # Minimum ice thickness (m)
    h_max: float = 10.0  # Maximum ice thickness (m)

    # Dynamics parameters
    P_star: float = 2.75e4  # Ice strength parameter (N/m)
    C_star: float = 20.0  # Ice strength exponent
    e_ratio: float = 2.0  # Elliptic yield curve ratio

    # Atmospheric forcing
    T_atm_min: float = -30.0  # Minimum air temperature (C)
    T_atm_max: float = 5.0  # Maximum air temperature (C)

    # Ocean heat flux
    Q_ocean: float = 2.0  # Ocean heat flux (W/m^2)

    # Output
    output_interval: int = 1  # Output every N timesteps


class SeaIcePattern:
    """
    Thermodynamic sea ice model.

    Simulates sea ice thermodynamics (growth, melt) and simplified
    dynamics using the zero-layer approximation with ice thickness
    distribution. Includes ice-albedo feedback and ocean coupling.
    """

    PATTERN_ID = "sea_ice"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: Optional[SeaIceConfig] = None):
        self.config = config or SeaIceConfig()
        self._initialize_grid()
        self._initialize_fields()
        self._initialize_forcing()

    def _initialize_grid(self):
        """Initialize horizontal grid"""
        cfg = self.config

        self.x = np.linspace(-cfg.Lx / 2, cfg.Lx / 2, cfg.nx)
        self.y = np.linspace(-cfg.Ly / 2, cfg.Ly / 2, cfg.ny)
        self.dx = cfg.Lx / (cfg.nx - 1)
        self.dy = cfg.Ly / (cfg.ny - 1)

        # Distance from pole (for Coriolis)
        self.X, self.Y = np.meshgrid(self.x, self.y)
        self.R = np.sqrt(self.X**2 + self.Y**2)

        # Coriolis parameter (Arctic)
        self.f = 1.46e-4 * np.ones_like(self.R)  # Constant f for simplicity

    def _initialize_fields(self):
        """Initialize sea ice fields"""
        cfg = self.config

        # Ice concentration (0-1)
        self.a_ice = np.zeros((cfg.nx, cfg.ny))

        # Ice thickness (m)
        self.h_ice = np.zeros((cfg.nx, cfg.ny))

        # Snow thickness (m)
        self.h_snow = np.zeros((cfg.nx, cfg.ny))

        # Ice velocity (m/s)
        self.u = np.zeros((cfg.nx, cfg.ny))
        self.v = np.zeros((cfg.nx, cfg.ny))

        # Ice surface temperature (C)
        self.T_ice = np.ones((cfg.nx, cfg.ny)) * cfg.T_freeze

        # Initialize with some ice in the center
        center_mask = self.R < cfg.Lx / 4
        self.a_ice[center_mask] = 0.8
        self.h_ice[center_mask] = 2.0

        # Output storage
        self.history = {
            "a_ice": [],
            "h_ice": [],
            "T_ice": [],
            "time": [],
            "volume": [],
            "extent": [],
        }

    def _initialize_forcing(self):
        """Initialize atmospheric and oceanic forcing"""
        cfg = self.config

        # Seasonal temperature cycle
        self.T_atm = np.zeros((cfg.nx, cfg.ny))

        # Solar radiation (simplified)
        self.Q_solar = 200.0  # W/m^2 (annual average)

    def _update_atmospheric_forcing(self, day: float):
        """Update atmospheric forcing based on day of year"""
        cfg = self.config

        # Seasonal cycle
        day_of_year = day % 365
        season = 2 * np.pi * day_of_year / 365.0

        # Temperature varies with latitude (distance from center)
        for j in range(cfg.ny):
            for i in range(cfg.nx):
                lat_factor = 1 - 0.5 * (self.R[j, i] / (cfg.Lx / 2))
                T_seasonal = cfg.T_atm_min + (cfg.T_atm_max - cfg.T_atm_min) * np.sin(
                    season + np.pi / 2
                )
                self.T_atm[j, i] = T_seasonal * lat_factor

    def _calculate_albedo(self) -> np.ndarray:
        """Calculate surface albedo based on ice state"""
        cfg = self.config

        albedo = np.zeros_like(self.a_ice)

        # Melt pond fraction (simplified)
        melt_pond = np.where(self.T_ice > -0.5, 0.3, 0.0)

        # Area-weighted albedo
        albedo_ice_eff = (1 - melt_pond) * cfg.albedo_ice + melt_pond * cfg.albedo_melt

        albedo = self.a_ice * albedo_ice_eff + (1 - self.a_ice) * cfg.albedo_water

        return albedo

    def _surface_energy_balance(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate surface energy balance.
        Returns net heat flux and surface temperature.
        """
        cfg = self.config

        albedo = self._calculate_albedo()

        # Absorbed shortwave
        Q_sw = (1 - albedo) * self.Q_solar

        # Longwave radiation (simplified)
        sigma = 5.67e-8  # Stefan-Boltzmann constant

        # Surface temperature (K)
        T_surf_K = self.T_ice + 273.15

        # Net longwave (emitted - downwelling)
        eps = 0.95  # Emissivity
        Q_lw = eps * sigma * (T_surf_K**4) - 0.8 * sigma * (273.15 + self.T_atm) ** 4

        # Sensible heat flux
        C_h = 1.2e-3  # Exchange coefficient
        rho_atm = 1.3  # Air density
        u_atm = 5.0  # Wind speed
        Q_sens = rho_atm * c_p_air * C_h * u_atm * (self.T_ice - self.T_atm)

        # Latent heat flux
        L_subl = 2.83e6  # Sublimation
        Q_lat = (
            rho_atm
            * L_subl
            * C_h
            * u_atm
            * 0.001
            * np.maximum(0, self.T_atm - self.T_ice)
        )

        # Net surface flux
        Q_net = Q_sw - Q_lw - Q_sens - Q_lat

        return Q_net, self.T_ice

    def _thermodynamics(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate thermodynamic tendencies.
        Returns ice growth rate and concentration tendency.
        """
        cfg = self.config

        Q_net, T_surf = self._surface_energy_balance()

        # Ice growth/melt rate (m/s)
        dh_dt = np.zeros_like(self.h_ice)
        da_dt = np.zeros_like(self.a_ice)

        for j in range(cfg.ny):
            for i in range(cfg.nx):
                if self.a_ice[j, i] > 0.01:  # Ice present
                    # Conduction through ice
                    if self.h_ice[j, i] > cfg.h_min:
                        dT_dz = (T_surf[j, i] - cfg.T_freeze) / self.h_ice[j, i]
                        Q_cond = cfg.k_ice * dT_dz
                    else:
                        Q_cond = 0

                    # Bottom melt/growth
                    Q_bot = Q_cond - cfg.Q_ocean

                    # Surface melt
                    if Q_net[j, i] > 0 and T_surf[j, i] >= -0.1:
                        # Surface melting
                        dh_surf = Q_net[j, i] / (cfg.rho_ice * cfg.L_fusion)
                        dh_bot = -Q_bot / (cfg.rho_ice * cfg.L_fusion)
                        dh_dt[j, i] = dh_surf + dh_bot
                    else:
                        # Growth from bottom
                        dh_dt[j, i] = -Q_bot / (cfg.rho_ice * cfg.L_fusion)

                    # Ice concentration change
                    if dh_dt[j, i] < 0:  # Melting
                        da_dt[j, i] = -0.1 * self.a_ice[j, i] * abs(dh_dt[j, i])
                    else:  # Growth
                        da_dt[j, i] = 0.01 * (1 - self.a_ice[j, i])

                else:  # Open water
                    # New ice formation
                    if T_surf[j, i] <= cfg.T_freeze:
                        dh_dt[j, i] = 0.01 / 86400.0  # 1 cm per day
                        da_dt[j, i] = 0.01

        return dh_dt, da_dt

    def _dynamics(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate ice dynamics tendencies.
        Returns velocity tendencies.
        """
        cfg = self.config

        du_dt = np.zeros_like(self.u)
        dv_dt = np.zeros_like(self.v)

        # Coriolis force (only where ice exists)
        mask = self.a_ice > 0.1
        du_dt[mask] += self.f[mask] * self.v[mask]
        dv_dt[mask] -= self.f[mask] * self.u[mask]

        # Ice pressure gradient (simplified)
        P = cfg.P_star * self.h_ice * np.exp(-cfg.C_star * (1 - self.a_ice))

        dP_dx = np.zeros_like(P)
        dP_dy = np.zeros_like(P)

        dP_dx[1:-1, :] = (P[2:, :] - P[:-2, :]) / (2 * self.dx)
        dP_dy[:, 1:-1] = (P[:, 2:] - P[:, :-2]) / (2 * self.dy)

        du_dt -= dP_dx / (cfg.rho_ice * np.maximum(self.h_ice, cfg.h_min))
        dv_dt -= dP_dy / (cfg.rho_ice * np.maximum(self.h_ice, cfg.h_min))

        # Ocean drag
        C_w = 5.0e-3
        u_oc = 0.1  # Ocean current
        du_dt -= C_w * (self.u - u_oc)
        dv_dt -= C_w * (self.v - u_oc)

        # Internal ice stress (simplified viscosity)
        for j in range(1, cfg.ny - 1):
            for i in range(1, cfg.nx - 1):
                if self.a_ice[j, i] > 0.5:
                    nu = 1.0e8  # Viscosity
                    du_dt[i, j] += nu * (
                        (self.u[i + 1, j] - 2 * self.u[i, j] + self.u[i - 1, j])
                        / self.dx**2
                        + (self.u[i, j + 1] - 2 * self.u[i, j] + self.u[i, j - 1])
                        / self.dy**2
                    )

        return du_dt, dv_dt

    def _advect_ice(self):
        """Advect ice thickness and concentration"""
        cfg = self.config

        # Upwind advection for thickness
        h_new = self.h_ice.copy()
        a_new = self.a_ice.copy()

        for j in range(1, cfg.ny - 1):
            for i in range(1, cfg.nx - 1):
                # Upwind scheme
                if self.u[i, j] > 0:
                    h_new[i, j] -= (
                        cfg.dt
                        * self.u[i, j]
                        * (self.h_ice[i, j] - self.h_ice[i - 1, j])
                        / self.dx
                    )
                    a_new[i, j] -= (
                        cfg.dt
                        * self.u[i, j]
                        * (self.a_ice[i, j] - self.a_ice[i - 1, j])
                        / self.dx
                    )
                else:
                    h_new[i, j] -= (
                        cfg.dt
                        * self.u[i, j]
                        * (self.h_ice[i + 1, j] - self.h_ice[i, j])
                        / self.dx
                    )
                    a_new[i, j] -= (
                        cfg.dt
                        * self.u[i, j]
                        * (self.a_ice[i + 1, j] - self.a_ice[i, j])
                        / self.dx
                    )

                if self.v[i, j] > 0:
                    h_new[i, j] -= (
                        cfg.dt
                        * self.v[i, j]
                        * (self.h_ice[i, j] - self.h_ice[i, j - 1])
                        / self.dy
                    )
                    a_new[i, j] -= (
                        cfg.dt
                        * self.v[i, j]
                        * (self.a_ice[i, j] - self.a_ice[i, j - 1])
                        / self.dy
                    )
                else:
                    h_new[i, j] -= (
                        cfg.dt
                        * self.v[i, j]
                        * (self.h_ice[i, j + 1] - self.h_ice[i, j])
                        / self.dy
                    )
                    a_new[i, j] -= (
                        cfg.dt
                        * self.v[i, j]
                        * (self.a_ice[i, j + 1] - self.a_ice[i, j])
                        / self.dy
                    )

        self.h_ice = np.clip(h_new, 0, cfg.h_max)
        self.a_ice = np.clip(a_new, 0, 1)

    def _step(self, day: float):
        """Advance model by one time step"""
        cfg = self.config

        # Update forcing
        self._update_atmospheric_forcing(day)

        # Thermodynamics
        dh_dt, da_dt = self._thermodynamics()
        self.h_ice += dh_dt * cfg.dt
        self.a_ice += da_dt * cfg.dt

        # Ice surface temperature
        Q_net, _ = self._surface_energy_balance()
        dT_dt = Q_net / (cfg.rho_ice * cfg.c_ice * np.maximum(self.h_ice, cfg.h_min))
        self.T_ice += dT_dt * cfg.dt

        # Dynamics
        du_dt, dv_dt = self._dynamics()
        self.u += du_dt * cfg.dt
        self.v += dv_dt * cfg.dt

        # Advection
        self._advect_ice()

        # Apply limits
        self.h_ice = np.clip(self.h_ice, 0, cfg.h_max)
        self.a_ice = np.clip(self.a_ice, 0, 1)
        self.T_ice = np.clip(self.T_ice, -50, 10)

    def run(self, hypothesis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run the sea ice simulation"""
        cfg = self.config
        n_steps = int(cfg.days)

        logger.info(f"Starting sea ice simulation: {cfg.days} days, {n_steps} steps")

        for step in range(n_steps):
            day = step * cfg.dt / 86400.0
            self._step(day)

            # Output
            if step % cfg.output_interval == 0:
                # Calculate diagnostics
                ice_volume = np.sum(self.h_ice * self.a_ice) * self.dx * self.dy
                ice_extent = (
                    np.sum(self.a_ice > 0.15) * self.dx * self.dy / 1e12
                )  # Million km^2

                self.history["a_ice"].append(self.a_ice.copy())
                self.history["h_ice"].append(self.h_ice.copy())
                self.history["T_ice"].append(self.T_ice.copy())
                self.history["time"].append(day)
                self.history["volume"].append(ice_volume)
                self.history["extent"].append(ice_extent)

            if step % 30 == 0:
                logger.debug(
                    f"Step {step}/{n_steps}, Day {day:.0f}, Volume: {ice_volume:.4e} m^3"
                )

        return self._format_output()

    def _format_output(self) -> Dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        return {
            "ice_volume": self.history["volume"],
            "ice_extent": self.history["extent"],
            "time_days": self.history["time"],
            "final_state": {
                "mean_concentration": float(np.mean(self.a_ice)),
                "mean_thickness": float(np.mean(self.h_ice[self.h_ice > 0])),
                "max_thickness": float(np.max(self.h_ice)),
                "ice_area_fraction": float(
                    np.sum(self.a_ice > 0.15) / (cfg.nx * cfg.ny)
                ),
                "mean_temperature": float(np.mean(self.T_ice[self.a_ice > 0.1])),
            },
            "statistics": {
                "volume_trend": float(
                    np.polyfit(self.history["time"], self.history["volume"], 1)[0]
                ),
                "extent_trend": float(
                    np.polyfit(self.history["time"], self.history["extent"], 1)[0]
                ),
            },
            "grid": {
                "nx": cfg.nx,
                "ny": cfg.ny,
                "Lx": cfg.Lx,
                "Ly": cfg.Ly,
            },
            "config": {
                "days": cfg.days,
                "T_freeze": cfg.T_freeze,
                "albedo_ice": cfg.albedo_ice,
            },
        }

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Sea Ice",
            "category": "ON_DEMAND",
            "domain": ["Cryosphere", "Climate Science"],
            "description": "Thermodynamic sea ice model with ice thickness distribution",
            "computational_complexity": "O(N²)",
            "typical_runtime": "minutes",
            "accuracy": "Moderate (climate research)",
            "assumptions": [
                "Zero-layer thermodynamics",
                "Ice thickness distribution",
                "Simplified ice dynamics",
                "Constant ocean heat flux",
            ],
            "parameters": [
                {
                    "name": "nx",
                    "type": "int",
                    "default": 100,
                    "description": "Zonal grid points",
                },
                {
                    "name": "ny",
                    "type": "int",
                    "default": 100,
                    "description": "Meridional grid points",
                },
                {
                    "name": "days",
                    "type": "int",
                    "default": 365,
                    "description": "Simulation days",
                },
                {
                    "name": "albedo_ice",
                    "type": "float",
                    "default": 0.65,
                    "description": "Ice albedo",
                },
                {
                    "name": "Q_ocean",
                    "type": "float",
                    "default": 2.0,
                    "description": "Ocean heat flux",
                },
            ],
        }


c_p_air = 1004.0  # Specific heat of air


# Unit tests
import unittest


class TestSeaIce(unittest.TestCase):
    def test_initialization(self):
        """Test that pattern initializes correctly"""
        config = SeaIceConfig(nx=50, ny=50)
        pattern = SeaIcePattern(config)

        self.assertEqual(pattern.a_ice.shape, (50, 50))
        self.assertEqual(pattern.h_ice.shape, (50, 50))
        self.assertEqual(pattern.T_ice.shape, (50, 50))

    def test_albedo_calculation(self):
        """Test albedo calculation"""
        config = SeaIceConfig(nx=20, ny=20)
        pattern = SeaIcePattern(config)

        albedo = pattern._calculate_albedo()

        self.assertEqual(albedo.shape, (20, 20))
        self.assertTrue(np.all(albedo >= config.albedo_water))
        self.assertTrue(np.all(albedo <= config.albedo_ice))

    def test_energy_balance(self):
        """Test surface energy balance"""
        config = SeaIceConfig(nx=20, ny=20)
        pattern = SeaIcePattern(config)

        Q_net, T_surf = pattern._surface_energy_balance()

        self.assertEqual(Q_net.shape, (20, 20))
        self.assertTrue(np.all(np.isfinite(Q_net)))

    def test_thermodynamics(self):
        """Test thermodynamic tendencies"""
        config = SeaIceConfig(nx=20, ny=20)
        pattern = SeaIcePattern(config)

        dh_dt, da_dt = pattern._thermodynamics()

        self.assertEqual(dh_dt.shape, (20, 20))
        self.assertEqual(da_dt.shape, (20, 20))
        self.assertTrue(np.all(np.isfinite(dh_dt)))
        self.assertTrue(np.all(np.isfinite(da_dt)))

    def test_dynamics(self):
        """Test dynamics calculation"""
        config = SeaIceConfig(nx=20, ny=20)
        pattern = SeaIcePattern(config)

        du_dt, dv_dt = pattern._dynamics()

        self.assertEqual(du_dt.shape, (20, 20))
        self.assertEqual(dv_dt.shape, (20, 20))
        self.assertTrue(np.all(np.isfinite(du_dt)))

    def test_advection(self):
        """Test ice advection"""
        config = SeaIceConfig(nx=20, ny=20, dt=1000)
        pattern = SeaIcePattern(config)

        h_before = pattern.h_ice.copy()
        pattern._advect_ice()
        h_after = pattern.h_ice.copy()

        # Check that values remain bounded
        self.assertTrue(np.all(h_after >= 0))
        self.assertTrue(np.all(h_after <= config.h_max))

    def test_step(self):
        """Test single time step"""
        config = SeaIceConfig(nx=20, ny=20, dt=1000)
        pattern = SeaIcePattern(config)

        h_before = pattern.h_ice.copy()
        pattern._step(0)
        h_after = pattern.h_ice.copy()

        # Should change or stay bounded
        self.assertTrue(np.all(pattern.h_ice >= 0))
        self.assertTrue(np.all(pattern.a_ice >= 0))
        self.assertTrue(np.all(pattern.a_ice <= 1))

    def test_forcing_update(self):
        """Test atmospheric forcing update"""
        config = SeaIceConfig(nx=20, ny=20)
        pattern = SeaIcePattern(config)

        pattern._update_atmospheric_forcing(0)
        T_winter = pattern.T_atm.copy()

        pattern._update_atmospheric_forcing(180)
        T_summer = pattern.T_atm.copy()

        # Summer should be warmer than winter
        self.assertTrue(np.mean(T_summer) > np.mean(T_winter))

    def test_metadata(self):
        """Test metadata retrieval"""
        metadata = SeaIcePattern.get_metadata()

        self.assertEqual(metadata["id"], "sea_ice")
        self.assertIn("parameters", metadata)
        self.assertGreater(len(metadata["assumptions"]), 0)

    def test_short_simulation(self):
        """Test running a short simulation"""
        config = SeaIceConfig(nx=20, ny=20, days=10)
        pattern = SeaIcePattern(config)

        result = pattern.run()

        self.assertIn("ice_volume", result)
        self.assertIn("ice_extent", result)
        self.assertIn("final_state", result)
        self.assertGreater(len(result["time_days"]), 0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
