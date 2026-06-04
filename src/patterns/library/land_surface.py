"""
C4REQBER v6.0 - Land Surface Pattern
Energy and water balance model for land surface processes.

Pattern Structure (Christopher Alexander):
- Context: Weather forecasting, climate modeling, hydrology
- Forces: Radiation balance, evapotranspiration, runoff, soil moisture
- Solution: Surface energy balance with bucket hydrology
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


@dataclass
class LandSurfaceConfig:
    """Configuration for land surface simulation"""

    # Grid settings
    nx: int = 50  # Grid points
    ny: int = 50

    # Domain
    Lx: float = 1.0e5  # 100 km
    Ly: float = 1.0e5

    # Time stepping
    dt: float = 3600.0  # 1 hour
    days: int = 365

    # Soil parameters
    soil_depth: float = 1.0  # m
    field_capacity: float = 0.35  # m^3/m^3
    wilting_point: float = 0.15
    porosity: float = 0.45
    K_s: float = 1.0e-5  # m/s saturated hydraulic conductivity

    # Surface parameters
    albedo: float = 0.2
    emissivity: float = 0.95
    z0: float = 0.1  # Roughness length (m)

    # Vegetation parameters
    lai_max: float = 5.0  # Maximum leaf area index
    rs_min: float = 40.0  # Minimum stomatal resistance (s/m)
    veg_fraction: float = 0.8  # Vegetation coverage

    # Initial conditions
    soil_moisture_init: float = 0.3
    temperature_init: float = 288.0  # K

    # Output
    output_interval: int = 24  # Daily output


class LandSurfacePattern:
    """
    Land Surface Model (LSM).

    Simulates surface energy balance, evapotranspiration,
    soil moisture dynamics, and runoff using the force-restore
    approach for temperature and bucket model for soil moisture.
    """

    PATTERN_ID = "land_surface"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: LandSurfaceConfig | None = None) -> None:
        self.config = config or LandSurfaceConfig()
        self._initialize_grid()
        self._initialize_fields()

    def _initialize_grid(self) -> None:
        """Initialize grid"""
        cfg = self.config

        self.x = np.linspace(0, cfg.Lx, cfg.nx)
        self.y = np.linspace(0, cfg.Ly, cfg.ny)
        self.dx = cfg.Lx / cfg.nx
        self.dy = cfg.Ly / cfg.ny

        self.X, self.Y = np.meshgrid(self.x, self.y, indexing="ij")

    def _initialize_fields(self) -> None:
        """Initialize surface and soil variables"""
        cfg = self.config

        shape = (cfg.nx, cfg.ny)

        # Surface temperature
        self.T_surf = np.ones(shape) * cfg.temperature_init

        # Soil moisture (fraction of saturation)
        self.soil_moisture = np.ones(shape) * cfg.soil_moisture_init

        # Soil temperature
        self.T_soil = np.ones(shape) * cfg.temperature_init

        # Snow water equivalent (mm)
        self.swe = np.zeros(shape)

        # Cumulative runoff (mm)
        self.runoff = np.zeros(shape)

        # Output storage
        self.history = {  # type: ignore[var-annotated]
            "T_surf": [],
            "T_soil": [],
            "soil_moisture": [],
            "ET": [],
            "runoff": [],
            "swe": [],
            "time": [],
            "energy_flux": [],
        }

    def _diurnal_temperature(
        self, day: float, hour: float
    ) -> tuple[np.ndarray, np.ndarray]:
        """Calculate diurnal cycle of atmospheric temperature and radiation"""
        cfg = self.config

        # Seasonal cycle
        day_of_year = day % 365
        season = 2 * np.pi * day_of_year / 365.0

        # Mean temperature with seasonal cycle
        T_mean = 288.0 + 15.0 * np.sin(season - np.pi / 2)

        # Diurnal cycle
        diurnal = 2 * np.pi * hour / 24.0
        T_atm = T_mean + 10.0 * np.sin(diurnal - np.pi / 2)

        # Downwelling shortwave (clear sky)
        S0 = 1361.0  # Solar constant
        cos_zenith = np.maximum(0, np.sin(diurnal))
        S_down = 0.7 * S0 * cos_zenith * (1 + 0.1 * np.sin(season))

        return np.ones((cfg.nx, cfg.ny)) * T_atm, np.ones((cfg.nx, cfg.ny)) * S_down

    def _surface_albedo(self) -> np.ndarray:
        """Calculate surface albedo based on conditions"""
        cfg = self.config

        # Base albedo
        albedo = np.ones((cfg.nx, cfg.ny)) * cfg.albedo

        # Increase albedo with snow
        snow_albedo = 0.8
        snow_fraction = np.minimum(self.swe / 10.0, 1.0)  # 10mm SWE = full snow cover
        albedo = (1 - snow_fraction) * cfg.albedo + snow_fraction * snow_albedo

        return albedo

    def _surface_resistance(self) -> np.ndarray:
        """Calculate surface resistance for evapotranspiration"""
        cfg = self.config

        # Stomatal resistance based on soil moisture stress
        # Wilting point = high resistance, field capacity = minimum resistance

        stress_factor = np.clip(
            (self.soil_moisture - cfg.wilting_point)
            / (cfg.field_capacity - cfg.wilting_point),
            0,
            1,
        )

        # Surface resistance
        rs = cfg.rs_min / (stress_factor * cfg.veg_fraction + 0.01)

        return rs

    def _energy_balance(
        self, T_atm: np.ndarray, S_down: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate surface energy balance.
        Returns net radiation, sensible heat, latent heat, ground heat flux.
        """
        cfg = self.config

        sigma = 5.67e-8  # Stefan-Boltzmann
        rho_air = 1.225  # kg/m^3
        cp = 1004.0
        Lv = 2.5e6

        # Albedo
        albedo = self._surface_albedo()

        # Net shortwave
        Q_sw = (1 - albedo) * S_down

        # Net longwave (simplified)
        eps = cfg.emissivity
        Q_lw_down = eps * sigma * T_atm**4
        Q_lw_up = eps * sigma * self.T_surf**4
        Q_lw = Q_lw_down - Q_lw_up

        # Net radiation
        Q_net = Q_sw + Q_lw

        # Aerodynamic resistance (simplified)
        u = 5.0  # Wind speed m/s
        ra = np.log(10 / cfg.z0) ** 2 / (0.4**2 * u)
        ra = np.clip(ra, 10, 500)

        # Sensible heat flux
        Q_h = rho_air * cp * (self.T_surf - T_atm) / ra

        # Latent heat flux (Penman-Monteith)
        # Saturation vapor pressure at surface
        es_surf = 611.2 * np.exp(17.67 * (self.T_surf - 273.15) / (self.T_surf - 29.65))
        es_atm = 611.2 * np.exp(17.67 * (T_atm - 273.15) / (T_atm - 29.65))

        rs = self._surface_resistance()

        # Penman-Monteith
        gamma = 66.0  # Psychrometric constant (Pa/K)
        Delta = 4098.0 * es_surf / (self.T_surf - 35.0) ** 2

        Q_le = (Delta * Q_net + rho_air * cp * (es_surf - 0.7 * es_atm) / ra) / (
            Delta + gamma * (1 + rs / ra)
        )
        Q_le = np.maximum(Q_le, 0)

        # Ground heat flux (residual)
        Q_g = Q_net - Q_h - Q_le

        return Q_net, Q_h, Q_le, Q_g

    def _soil_moisture_update(self, precip: np.ndarray, ET: np.ndarray) -> None:
        """Update soil moisture with precipitation and evapotranspiration"""
        cfg = self.config

        # Precipitation input (convert mm to m)
        P_m = precip / 1000.0

        # ET extraction (convert from W/m^2 to m/s)
        Lv = 2.5e6
        rho_water = 1000.0
        ET_m = ET / (rho_water * Lv)

        # Water balance
        dW_dt = (P_m - ET_m) / cfg.soil_depth

        # Update soil moisture
        self.soil_moisture += dW_dt * cfg.dt

        # Runoff when exceeding field capacity
        excess = np.maximum(0, self.soil_moisture - cfg.field_capacity)
        self.runoff += excess * cfg.soil_depth * 1000  # Convert to mm
        self.soil_moisture = np.minimum(self.soil_moisture, cfg.field_capacity)

        # Lower bound
        self.soil_moisture = np.maximum(self.soil_moisture, cfg.wilting_point)

    def _temperature_update(self, Q_g: np.ndarray) -> None:
        """Update surface and soil temperatures"""
        cfg = self.config

        # Heat capacity
        rho_soil = 1500.0  # kg/m^3
        c_soil = 800.0  # J/kg/K
        C = rho_soil * cfg.soil_depth * c_soil

        # Surface temperature change
        dT_dt = Q_g / C
        self.T_surf += dT_dt * cfg.dt

        # Soil temperature (lags surface)
        tau = 86400.0 * 5  # 5 day timescale
        self.T_soil += (self.T_surf - self.T_soil) / tau * cfg.dt

    def _snow_update(self, precip: np.ndarray, T_atm: np.ndarray) -> Any:
        """Update snow water equivalent"""
        cfg = self.config

        # Snow vs rain partitioning
        is_snow = T_atm < 273.15
        snow_fall = np.where(is_snow, precip, 0)
        rain_fall = np.where(is_snow, 0, precip)

        # Add snowfall
        self.swe += snow_fall

        # Melt
        melt_rate = 5.0 / 86400.0  # mm/s when T_surf > 0
        melt = np.where(
            self.T_surf > 273.15, np.minimum(self.swe, melt_rate * cfg.dt), 0
        )
        self.swe -= melt

        return rain_fall + melt  # Liquid water reaching soil

    def _step(self, day: float, hour: float) -> None:
        """Advance model by one time step"""
        cfg = self.config

        # Forcing
        T_atm, S_down = self._diurnal_temperature(day, hour)

        # Energy balance
        Q_net, Q_h, Q_le, Q_g = self._energy_balance(T_atm, S_down)

        # Precipitation (simplified)
        precip = 5.0 * np.exp(-(((day % 7) - 3) ** 2) / 2)  # Weekly cycle
        if hour > 12 and hour < 18:
            precip *= 2  # Afternoon rain
        precip = np.ones((cfg.nx, cfg.ny)) * precip

        # Snow processes
        precip_liquid = self._snow_update(precip, T_atm)

        # Soil moisture
        self._soil_moisture_update(precip_liquid, Q_le)

        # Temperature
        self._temperature_update(Q_g)

    def run(self, hypothesis: dict[str, Any] = None) -> dict[str, Any]:  # type: ignore[assignment]
        """Run the land surface simulation"""
        cfg = self.config
        n_steps = int(cfg.days * 86400 / cfg.dt)

        logger.info(
            f"Starting land surface simulation: {cfg.days} days, {n_steps} steps"
        )

        for step in range(n_steps):
            day = step * cfg.dt / 86400.0
            hour = (step * cfg.dt % 86400) / 3600.0

            self._step(day, hour)

            # Output
            if step % cfg.output_interval == 0:
                T_atm, S_down = self._diurnal_temperature(day, hour)
                Q_net, Q_h, Q_le, Q_g = self._energy_balance(T_atm, S_down)

                self.history["T_surf"].append(np.mean(self.T_surf))
                self.history["T_soil"].append(np.mean(self.T_soil))
                self.history["soil_moisture"].append(np.mean(self.soil_moisture))
                self.history["ET"].append(
                    np.mean(Q_le / 2.5e6 * 86400 * 1000 / 1000)
                )  # mm/day
                self.history["runoff"].append(np.mean(self.runoff))
                self.history["swe"].append(np.mean(self.swe))
                self.history["time"].append(day)
                self.history["energy_flux"].append(np.mean(Q_net))

            if step % 100 == 0:
                logger.debug(
                    f"Step {step}/{n_steps}, Day {day:.0f}, SM: {np.mean(self.soil_moisture):.3f}"
                )

        return self._format_output()

    def _format_output(self) -> dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        # Calculate totals
        total_ET = np.sum(self.history["ET"])
        total_runoff = float(np.mean(self.runoff))

        return {
            "surface_temperature": self.history["T_surf"],
            "soil_temperature": self.history["T_soil"],
            "soil_moisture": self.history["soil_moisture"],
            "evapotranspiration": self.history["ET"],
            "runoff": self.history["runoff"],
            "snow_water": self.history["swe"],
            "time_days": self.history["time"],
            "final_state": {
                "mean_T_surf": float(np.mean(self.T_surf)),
                "mean_T_soil": float(np.mean(self.T_soil)),
                "mean_soil_moisture": float(np.mean(self.soil_moisture)),
                "total_runoff_mm": total_runoff,
                "mean_swe": float(np.mean(self.swe)),
            },
            "water_balance": {
                "total_ET_mm": float(total_ET),
                "soil_moisture_change": float(
                    self.history["soil_moisture"][-1] - self.history["soil_moisture"][0]
                ),
                "field_capacity": cfg.field_capacity,
                "wilting_point": cfg.wilting_point,
            },
            "grid": {
                "nx": cfg.nx,
                "ny": cfg.ny,
                "Lx": cfg.Lx,
                "Ly": cfg.Ly,
            },
            "config": {
                "days": cfg.days,
                "albedo": cfg.albedo,
                "soil_depth": cfg.soil_depth,
            },
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Land Surface",
            "category": "ON_DEMAND",
            "domain": ["Hydrology", "Micrometeorology"],
            "description": "Land surface energy and water balance model",
            "computational_complexity": "O(N²)",
            "typical_runtime": "minutes",
            "accuracy": "Moderate (diagnostic grade)",
            "assumptions": [
                "Bucket hydrology",
                "Force-restore temperature",
                "Penman-Monteith ET",
                "Single soil layer",
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
                    "name": "days",
                    "type": "int",
                    "default": 365,
                    "description": "Simulation days",
                },
                {
                    "name": "albedo",
                    "type": "float",
                    "default": 0.2,
                    "description": "Surface albedo",
                },
                {
                    "name": "soil_depth",
                    "type": "float",
                    "default": 1.0,
                    "description": "Soil depth (m)",
                },
            ],
        }


# Unit tests
import unittest


class TestLandSurface(unittest.TestCase):
    """TestLandSurface."""
    def test_initialization(self) -> None:
        """Test that pattern initializes correctly"""
        config = LandSurfaceConfig(nx=30, ny=30)
        pattern = LandSurfacePattern(config)

        self.assertEqual(pattern.T_surf.shape, (30, 30))
        self.assertEqual(pattern.soil_moisture.shape, (30, 30))
        self.assertEqual(pattern.swe.shape, (30, 30))

    def test_diurnal_cycle(self) -> None:
        """Test diurnal temperature cycle"""
        config = LandSurfaceConfig()
        pattern = LandSurfacePattern(config)

        T_day, S_day = pattern._diurnal_temperature(100, 12)
        T_night, S_night = pattern._diurnal_temperature(100, 0)

        # Day should be warmer
        self.assertGreater(np.mean(T_day), np.mean(T_night))
        # More sun at noon
        self.assertGreater(np.mean(S_day), np.mean(S_night))

    def test_surface_albedo(self) -> None:
        """Test surface albedo calculation"""
        config = LandSurfaceConfig()
        pattern = LandSurfacePattern(config)

        # No snow
        albedo_no_snow = pattern._surface_albedo()
        self.assertTrue(np.allclose(albedo_no_snow, config.albedo))

        # With snow
        pattern.swe[:, :] = 20.0
        albedo_snow = pattern._surface_albedo()
        self.assertTrue(np.all(albedo_snow > albedo_no_snow))

    def test_surface_resistance(self) -> None:
        """Test surface resistance calculation"""
        config = LandSurfaceConfig()
        pattern = LandSurfacePattern(config)

        rs = pattern._surface_resistance()

        self.assertEqual(rs.shape, (config.nx, config.ny))
        self.assertTrue(np.all(rs > 0))

    def test_energy_balance(self) -> None:
        """Test energy balance calculation"""
        config = LandSurfaceConfig()
        pattern = LandSurfacePattern(config)

        T_atm = np.ones((config.nx, config.ny)) * 288.0
        S_down = np.ones((config.nx, config.ny)) * 500.0

        Q_net, Q_h, Q_le, Q_g = pattern._energy_balance(T_atm, S_down)

        self.assertEqual(Q_net.shape, (config.nx, config.ny))
        # Energy should be conserved
        residual = Q_net - Q_h - Q_le - Q_g
        self.assertTrue(np.allclose(residual, 0, atol=1e-6))

    def test_soil_moisture_update(self) -> None:
        """Test soil moisture update"""
        config = LandSurfaceConfig()
        pattern = LandSurfacePattern(config)

        sm_before = pattern.soil_moisture.copy()

        precip = np.ones((config.nx, config.ny)) * 10.0  # 10 mm
        ET = np.ones((config.nx, config.ny)) * 50.0  # W/m^2

        pattern._soil_moisture_update(precip, ET)

        # Should remain within bounds
        self.assertTrue(np.all(pattern.soil_moisture >= config.wilting_point))
        self.assertTrue(np.all(pattern.soil_moisture <= config.field_capacity))

    def test_temperature_update(self) -> None:
        """Test temperature update"""
        config = LandSurfaceConfig()
        pattern = LandSurfacePattern(config)

        T_before = pattern.T_surf.copy()
        Q_g = np.ones((config.nx, config.ny)) * 50.0

        pattern._temperature_update(Q_g)

        # Should change
        self.assertFalse(np.allclose(pattern.T_surf, T_before))

    def test_snow_update(self) -> None:
        """Test snow processes"""
        config = LandSurfaceConfig()
        pattern = LandSurfacePattern(config)

        precip = np.ones((config.nx, config.ny)) * 10.0
        T_atm = np.ones((config.nx, config.ny)) * 260.0  # Cold

        liquid = pattern._snow_update(precip, T_atm)

        # Should accumulate snow
        self.assertTrue(np.all(pattern.swe > 0))

    def test_step(self) -> None:
        """Test single time step"""
        config = LandSurfaceConfig()
        pattern = LandSurfacePattern(config)

        pattern._step(1.0, 12.0)

        # Should produce finite results
        self.assertTrue(np.all(np.isfinite(pattern.T_surf)))
        self.assertTrue(np.all(np.isfinite(pattern.soil_moisture)))

    def test_metadata(self) -> None:
        """Test metadata retrieval"""
        metadata = LandSurfacePattern.get_metadata()

        self.assertEqual(metadata["id"], "land_surface")
        self.assertIn("parameters", metadata)

    def test_short_simulation(self) -> None:
        """Test running a short simulation"""
        config = LandSurfaceConfig(nx=20, ny=20, days=5, dt=3600)
        pattern = LandSurfacePattern(config)

        result = pattern.run()

        self.assertIn("surface_temperature", result)
        self.assertIn("soil_moisture", result)
        self.assertIn("evapotranspiration", result)
        self.assertGreater(len(result["time_days"]), 0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
