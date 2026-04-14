"""
TURBO-CDI v6.0 - Air Quality Pattern
Chemical transport model for atmospheric composition.

Pattern Structure (Christopher Alexander):
- Context: Air quality forecasting, pollution assessment, regulatory modeling
- Forces: Emissions, chemistry, transport, deposition, boundary conditions
- Solution: 3D chemical transport with gas-phase and aerosol chemistry
"""

import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AirQualityConfig:
    """Configuration for air quality simulation"""

    # Grid settings
    nx: int = 50  # Horizontal resolution
    ny: int = 50
    nz: int = 10  # Vertical layers

    # Domain (urban to regional scale)
    Lx: float = 200.0e3  # 200 km
    Ly: float = 200.0e3
    H: float = 5000.0  # 5 km depth

    # Time stepping
    dt: float = 600.0  # 10 minutes
    hours: int = 72  # 3-day forecast

    # Chemical species (simplified mechanism)
    species = ["NO", "NO2", "O3", "CO", "SO2", "PM25", "PM10", "VOC"]

    # Initial concentrations (ppb or ug/m3 for PM)
    initial_conc: Dict[str, float] = field(
        default_factory=lambda: {
            "NO": 5.0,
            "NO2": 10.0,
            "O3": 30.0,
            "CO": 200.0,
            "SO2": 2.0,
            "PM25": 15.0,
            "PM10": 25.0,
            "VOC": 50.0,
        }
    )

    # Emissions (per hour)
    emission_rates: Dict[str, float] = field(
        default_factory=lambda: {
            "NO": 1000.0,
            "NO2": 500.0,
            "CO": 5000.0,
            "SO2": 200.0,
            "PM25": 500.0,
            "PM10": 800.0,
            "VOC": 2000.0,
        }
    )

    # Source location (city center)
    source_x: float = 100.0e3
    source_y: float = 100.0e3
    source_radius: float = 20.0e3  # Urban area radius

    # Meteorology
    wind_speed: float = 5.0  # m/s
    wind_dir: float = 270.0  # degrees (from west)
    mixing_height: float = 1000.0  # m

    # Chemistry rates (simplified)
    k_no_no2: float = 1.0e-5  # NO + O3 -> NO2
    k_no2_o3: float = 1.0e-4  # NO2 + hv -> NO + O3
    k_oh_voc: float = 1.0e-6  # OH + VOC -> products

    # Deposition velocities (m/s)
    vd: Dict[str, float] = field(
        default_factory=lambda: {
            "NO": 0.001,
            "NO2": 0.002,
            "O3": 0.01,
            "CO": 0.0001,
            "SO2": 0.008,
            "PM25": 0.001,
            "PM10": 0.01,
            "VOC": 0.005,
        }
    )

    # Boundary conditions
    bc_conc: Dict[str, float] = field(
        default_factory=lambda: {
            "NO": 2.0,
            "NO2": 5.0,
            "O3": 40.0,
            "CO": 100.0,
            "SO2": 1.0,
            "PM25": 10.0,
            "PM10": 20.0,
            "VOC": 20.0,
        }
    )

    # Photolysis
    j_no2_max: float = 0.01  # /s at noon

    # Output
    output_interval: int = 6  # Every hour


class AirQualityPattern:
    """
    Chemical Transport Model (CTM) for air quality.

    Simulates the transport and chemical transformation of
    atmospheric pollutants including NOx, O3, PM2.5, and VOCs.
    Includes emissions, deposition, and simplified gas-phase chemistry.
    """

    PATTERN_ID = "air_quality"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: Optional[AirQualityConfig] = None):
        self.config = config or AirQualityConfig()
        self._initialize_grid()
        self._initialize_fields()

    def _initialize_grid(self):
        """Initialize 3D grid"""
        cfg = self.config

        self.x = np.linspace(0, cfg.Lx, cfg.nx)
        self.y = np.linspace(0, cfg.Ly, cfg.ny)
        self.z = np.linspace(0, cfg.H, cfg.nz)

        self.dx = cfg.Lx / cfg.nx
        self.dy = cfg.Ly / cfg.ny
        self.dz = cfg.H / cfg.nz

        self.X, self.Y, self.Z = np.meshgrid(self.x, self.y, self.z, indexing="ij")

        # Wind components
        angle_rad = np.radians(270 - cfg.wind_dir)
        self.u = cfg.wind_speed * np.cos(angle_rad) * np.ones((cfg.nx, cfg.ny, cfg.nz))
        self.v = cfg.wind_speed * np.sin(angle_rad) * np.ones((cfg.nx, cfg.ny, cfg.nz))
        self.w = np.zeros((cfg.nx, cfg.ny, cfg.nz))

        logger.debug(
            f"Grid: {cfg.nx}x{cfg.ny}x{cfg.nz}, wind: {cfg.wind_speed} m/s from {cfg.wind_dir}°"
        )

    def _initialize_fields(self):
        """Initialize chemical concentrations"""
        cfg = self.config

        # Concentrations for each species
        self.conc = {}

        for sp in cfg.species:
            # Initialize with background + urban enhancement
            self.conc[sp] = np.ones((cfg.nx, cfg.ny, cfg.nz)) * cfg.initial_conc[sp]

            # Urban plume in center (surface layer only)
            r_surf = np.sqrt(
                (self.X[:, :, 0] - cfg.source_x) ** 2
                + (self.Y[:, :, 0] - cfg.source_y) ** 2
            )
            urban_mask_2d = r_surf < cfg.source_radius

            for k in range(cfg.nz):
                if self.z[k] < cfg.mixing_height:
                    # Apply urban enhancement where mask is True
                    layer = self.conc[sp][:, :, k]
                    layer[urban_mask_2d] *= 2.0
                    self.conc[sp][:, :, k] = layer

        # Output storage
        self.history = {
            "time": [],
            "aqi": [],
            "max_o3": [],
            "max_pm25": [],
        }

        # Per-species history
        for sp in cfg.species:
            self.history[f"mean_{sp}"] = []

    def _photolysis_rate(self, hour: float) -> float:
        """Calculate NO2 photolysis rate"""
        cfg = self.config

        # Diurnal cycle
        time_of_day = hour % 24

        if 6 <= time_of_day <= 18:
            # Daytime - sinusoidal
            j = cfg.j_no2_max * np.sin(np.pi * (time_of_day - 6) / 12)
        else:
            j = 0.0

        return max(0, j)

    def _emissions(self, hour: float) -> Dict[str, np.ndarray]:
        """Calculate emission fluxes"""
        cfg = self.config

        emissions = {}

        # Diurnal emission cycle (rush hours at 8am and 6pm)
        time_of_day = hour % 24

        if (7 <= time_of_day <= 9) or (17 <= time_of_day <= 19):
            diurnal_factor = 2.0
        elif 22 <= time_of_day or time_of_day <= 5:
            diurnal_factor = 0.3
        else:
            diurnal_factor = 1.0

        for sp in cfg.species:
            if sp in cfg.emission_rates:
                # Emission in surface layer only
                E = np.zeros((cfg.nx, cfg.ny, cfg.nz))

                r = np.sqrt(
                    (self.X[:, :, 0] - cfg.source_x) ** 2
                    + (self.Y[:, :, 0] - cfg.source_y) ** 2
                )
                urban_mask = r < cfg.source_radius

                # Surface emission (convert to concentration tendency)
                E[:, :, 0][urban_mask] = (
                    cfg.emission_rates[sp]
                    * diurnal_factor
                    / (self.dx * self.dy)
                    / self.dz
                )

                emissions[sp] = E
            else:
                emissions[sp] = np.zeros((cfg.nx, cfg.ny, cfg.nz))

        return emissions

    def _deposition(self) -> Dict[str, np.ndarray]:
        """Calculate dry deposition sink"""
        cfg = self.config

        deposition = {}

        for sp in cfg.species:
            D = np.zeros((cfg.nx, cfg.ny, cfg.nz))

            if sp in cfg.vd:
                # Deposition only at surface
                D[:, :, 0] = -cfg.vd[sp] * self.conc[sp][:, :, 0] / self.dz

            deposition[sp] = D

        return deposition

    def _gas_chemistry(self, hour: float) -> Dict[str, np.ndarray]:
        """Calculate chemical reaction tendencies"""
        cfg = self.config

        chemistry = {}

        for sp in cfg.species:
            chemistry[sp] = np.zeros((cfg.nx, cfg.ny, cfg.nz))

        # Photolysis rate
        j_no2 = self._photolysis_rate(hour)

        # NO + O3 -> NO2
        if "NO" in cfg.species and "O3" in cfg.species and "NO2" in cfg.species:
            rate_no = -cfg.k_no_no2 * self.conc["NO"] * self.conc["O3"]
            rate_o3 = -cfg.k_no_no2 * self.conc["NO"] * self.conc["O3"]
            rate_no2 = cfg.k_no_no2 * self.conc["NO"] * self.conc["O3"]

            chemistry["NO"] += rate_no
            chemistry["O3"] += rate_o3
            chemistry["NO2"] += rate_no2

        # NO2 + hv -> NO + O3
        if "NO2" in cfg.species and j_no2 > 0:
            rate_no2_photo = -j_no2 * self.conc["NO2"]
            rate_no_photo = j_no2 * self.conc["NO2"]
            rate_o3_photo = j_no2 * self.conc["NO2"]

            chemistry["NO2"] += rate_no2_photo
            chemistry["NO"] += rate_no_photo
            chemistry["O3"] += rate_o3_photo

        # VOC oxidation (simplified)
        if "VOC" in cfg.species:
            chemistry["VOC"] += -cfg.k_oh_voc * self.conc["VOC"]

        return chemistry

    def _transport(self, sp: str) -> np.ndarray:
        """Calculate transport tendency for a species"""
        cfg = self.config

        c = self.conc[sp]

        # Advection (upwind scheme)
        dcdt = np.zeros_like(c)

        # x-advection
        for i in range(1, cfg.nx - 1):
            if self.u[i, 0, 0] > 0:
                dcdt[i, :, :] -= (
                    self.u[i, :, :] * (c[i, :, :] - c[i - 1, :, :]) / self.dx
                )
            else:
                dcdt[i, :, :] -= (
                    self.u[i, :, :] * (c[i + 1, :, :] - c[i, :, :]) / self.dx
                )

        # y-advection
        for j in range(1, cfg.ny - 1):
            if self.v[0, j, 0] > 0:
                dcdt[:, j, :] -= (
                    self.v[:, j, :] * (c[:, j, :] - c[:, j - 1, :]) / self.dy
                )
            else:
                dcdt[:, j, :] -= (
                    self.v[:, j, :] * (c[:, j + 1, :] - c[:, j, :]) / self.dy
                )

        # Vertical diffusion (simplified)
        Kz = 10.0  # m^2/s eddy diffusivity
        for k in range(1, cfg.nz - 1):
            d2c_dz2 = (c[:, :, k + 1] - 2 * c[:, :, k] + c[:, :, k - 1]) / self.dz**2
            dcdt[:, :, k] += Kz * d2c_dz2

        return dcdt

    def _apply_boundary_conditions(self):
        """Apply boundary conditions"""
        cfg = self.config

        # Inflow boundaries: background concentrations
        for sp in cfg.species:
            bc_val = cfg.bc_conc[sp]

            # West boundary (inflow if u > 0)
            if self.u[0, 0, 0] > 0:
                self.conc[sp][0, :, :] = bc_val

            # South boundary (inflow if v > 0)
            if self.v[0, 0, 0] > 0:
                self.conc[sp][:, 0, :] = bc_val

            # Outflow: zero gradient
            if self.u[-1, 0, 0] < 0:
                self.conc[sp][-1, :, :] = self.conc[sp][-2, :, :]
            if self.v[0, -1, 0] < 0:
                self.conc[sp][:, -1, :] = self.conc[sp][:, -2, :]

            # Top: fixed background
            self.conc[sp][:, :, -1] = bc_val * 0.5  # Cleaner aloft

    def _calculate_aqi(self) -> float:
        """Calculate Air Quality Index (simplified US AQI)"""
        cfg = self.config

        # Get surface concentrations
        o3_ppb = np.max(self.conc["O3"][:, :, :2]) if "O3" in self.conc else 0
        pm25 = np.max(self.conc["PM25"][:, :, :2]) if "PM25" in self.conc else 0

        # AQI breakpoints (simplified)
        # O3 8-hr: 0-54 (Good), 55-70 (Moderate), etc.
        if o3_ppb <= 54:
            aqi_o3 = o3_ppb * 50 / 54
        elif o3_ppb <= 70:
            aqi_o3 = 50 + (o3_ppb - 54) * 50 / 16
        else:
            aqi_o3 = 100 + (o3_ppb - 70) * 50 / 30

        # PM2.5 24-hr: 0-12 (Good), 12.1-35.4 (Moderate)
        if pm25 <= 12:
            aqi_pm = pm25 * 50 / 12
        elif pm25 <= 35.4:
            aqi_pm = 50 + (pm25 - 12) * 50 / 23.4
        else:
            aqi_pm = 100 + (pm25 - 35.4) * 50 / 19.6

        return max(aqi_o3, aqi_pm)

    def _step(self, hour: float):
        """Advance model by one time step"""
        cfg = self.config

        # Get tendencies
        emissions = self._emissions(hour)
        deposition = self._deposition()
        chemistry = self._gas_chemistry(hour)

        # Update each species
        for sp in cfg.species:
            transport = self._transport(sp)

            dcdt = transport + emissions[sp] + deposition[sp] + chemistry[sp]

            self.conc[sp] += dcdt * cfg.dt

            # Ensure non-negative
            self.conc[sp] = np.maximum(self.conc[sp], 0)

        # Boundary conditions
        self._apply_boundary_conditions()

    def run(self, hypothesis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run the air quality simulation"""
        cfg = self.config
        n_steps = int(cfg.hours * 3600 / cfg.dt)

        logger.info(
            f"Starting air quality simulation: {cfg.hours} hours, {n_steps} steps"
        )

        for step in range(n_steps):
            hour = step * cfg.dt / 3600.0

            self._step(hour)

            # Output
            if step % cfg.output_interval == 0:
                aqi = self._calculate_aqi()
                max_o3 = np.max(self.conc["O3"]) if "O3" in self.conc else 0
                max_pm25 = np.max(self.conc["PM25"]) if "PM25" in self.conc else 0

                self.history["time"].append(hour)
                self.history["aqi"].append(aqi)
                self.history["max_o3"].append(max_o3)
                self.history["max_pm25"].append(max_pm25)

                for sp in cfg.species:
                    self.history[f"mean_{sp}"].append(np.mean(self.conc[sp]))

            if step % 50 == 0:
                logger.debug(f"Step {step}/{n_steps}, Hour {hour:.1f}, AQI={aqi:.0f}")

        return self._format_output()

    def _format_output(self) -> Dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        # AQI statistics
        aqi_max = max(self.history["aqi"]) if self.history["aqi"] else 0
        aqi_mean = np.mean(self.history["aqi"]) if self.history["aqi"] else 0

        # Determine AQI category
        if aqi_max <= 50:
            aqi_category = "Good"
        elif aqi_max <= 100:
            aqi_category = "Moderate"
        elif aqi_max <= 150:
            aqi_category = "Unhealthy for Sensitive"
        elif aqi_max <= 200:
            aqi_category = "Unhealthy"
        else:
            aqi_category = "Very Unhealthy"

        return {
            "aqi": self.history["aqi"],
            "max_ozone": self.history["max_o3"],
            "max_pm25": self.history["max_pm25"],
            "time_hours": self.history["time"],
            "final_concentrations": {
                sp: float(np.mean(self.conc[sp])) for sp in cfg.species
            },
            "aqi_summary": {
                "max_aqi": float(aqi_max),
                "mean_aqi": float(aqi_mean),
                "category": aqi_category,
            },
            "peak_concentrations": {
                sp: float(np.max(self.conc[sp])) for sp in cfg.species
            },
            "grid": {
                "nx": cfg.nx,
                "ny": cfg.ny,
                "nz": cfg.nz,
            },
            "config": {
                "hours": cfg.hours,
                "wind_speed": cfg.wind_speed,
                "wind_dir": cfg.wind_dir,
            },
        }

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Air Quality",
            "category": "ON_DEMAND",
            "domain": ["Atmospheric Chemistry", "Environmental Science"],
            "description": "Chemical transport model for air quality forecasting",
            "computational_complexity": "O(N³ * N_species)",
            "typical_runtime": "minutes to hours",
            "accuracy": "Moderate (regulatory grade)",
            "assumptions": [
                "Simplified gas-phase chemistry",
                "No aqueous-phase chemistry",
                "Parameterized deposition",
                "Offline meteorology",
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
                    "default": 10,
                    "description": "Vertical levels",
                },
                {
                    "name": "hours",
                    "type": "int",
                    "default": 72,
                    "description": "Forecast hours",
                },
                {
                    "name": "wind_speed",
                    "type": "float",
                    "default": 5.0,
                    "description": "Wind speed (m/s)",
                },
            ],
        }


# Unit tests
import unittest


class TestAirQuality(unittest.TestCase):
    def test_initialization(self):
        """Test that pattern initializes correctly"""
        config = AirQualityConfig(nx=20, ny=20, nz=5)
        pattern = AirQualityPattern(config)

        self.assertEqual(len(pattern.conc), len(config.species))
        for sp in config.species:
            self.assertEqual(pattern.conc[sp].shape, (20, 20, 5))

    def test_photolysis_rate(self):
        """Test photolysis rate calculation"""
        config = AirQualityConfig()
        pattern = AirQualityPattern(config)

        j_noon = pattern._photolysis_rate(12)
        j_midnight = pattern._photolysis_rate(0)
        j_morning = pattern._photolysis_rate(6)

        self.assertGreater(j_noon, j_morning)
        self.assertEqual(j_midnight, 0)
        self.assertLessEqual(j_noon, config.j_no2_max)

    def test_emissions(self):
        """Test emission calculation"""
        config = AirQualityConfig()
        pattern = AirQualityPattern(config)

        emissions = pattern._emissions(12)

        self.assertIn("NO", emissions)
        self.assertEqual(emissions["NO"].shape, (config.nx, config.ny, config.nz))

        # Rush hour should have higher emissions
        emissions_rush = pattern._emissions(8)
        emissions_night = pattern._emissions(2)

        self.assertGreater(np.sum(emissions_rush["NO"]), np.sum(emissions_night["NO"]))

    def test_deposition(self):
        """Test deposition calculation"""
        config = AirQualityConfig()
        pattern = AirQualityPattern(config)

        deposition = pattern._deposition()

        self.assertIn("O3", deposition)
        # Should be negative (sink)
        self.assertTrue(np.all(deposition["O3"][:, :, 0] <= 0))

    def test_gas_chemistry(self):
        """Test chemistry calculation"""
        config = AirQualityConfig()
        pattern = AirQualityPattern(config)

        chemistry = pattern._gas_chemistry(12)

        self.assertIn("NO", chemistry)
        self.assertIn("NO2", chemistry)
        self.assertIn("O3", chemistry)

    def test_transport(self):
        """Test transport calculation"""
        config = AirQualityConfig()
        pattern = AirQualityPattern(config)

        transport = pattern._transport("O3")

        self.assertEqual(transport.shape, (config.nx, config.ny, config.nz))
        self.assertTrue(np.all(np.isfinite(transport)))

    def test_boundary_conditions(self):
        """Test boundary conditions"""
        config = AirQualityConfig()
        pattern = AirQualityPattern(config)

        # Modify boundary
        pattern.conc["O3"][0, :, :] = 1000

        pattern._apply_boundary_conditions()

        # Should be reset to BC value
        self.assertTrue(np.all(pattern.conc["O3"][0, :, :] < 1000))

    def test_aqi(self):
        """Test AQI calculation"""
        config = AirQualityConfig()
        pattern = AirQualityPattern(config)

        aqi = pattern._calculate_aqi()

        self.assertIsInstance(aqi, float)
        self.assertGreaterEqual(aqi, 0)

    def test_step(self):
        """Test single time step"""
        config = AirQualityConfig()
        pattern = AirQualityPattern(config)

        o3_before = pattern.conc["O3"].copy()
        pattern._step(12)

        # Should change
        self.assertFalse(np.allclose(pattern.conc["O3"], o3_before))

    def test_metadata(self):
        """Test metadata retrieval"""
        metadata = AirQualityPattern.get_metadata()

        self.assertEqual(metadata["id"], "air_quality")
        self.assertIn("parameters", metadata)

    def test_short_simulation(self):
        """Test running a short simulation"""
        config = AirQualityConfig(nx=20, ny=20, nz=5, hours=2, dt=600)
        pattern = AirQualityPattern(config)

        result = pattern.run()

        self.assertIn("aqi", result)
        self.assertIn("final_concentrations", result)
        self.assertGreater(len(result["time_hours"]), 0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
