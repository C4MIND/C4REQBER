"""
C4REQBER v6.0 - Cloud Microphysics Pattern
Bulk microphysics scheme for cloud and precipitation processes.

Pattern Structure (Christopher Alexander):
- Context: Weather forecasting, climate modeling, precipitation prediction
- Forces: Phase changes, collision-coalescence, sedimentation, advection
- Solution: Bulk microphysics with multiple hydrometeor categories
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


@dataclass
class CloudMicrophysicsConfig:
    """Configuration for cloud microphysics simulation"""

    # Grid settings
    nx: int = 50  # Horizontal points
    ny: int = 50
    nz: int = 30  # Vertical levels

    # Domain
    Lx: float = 1.0e5  # 100 km
    Ly: float = 1.0e5
    H: float = 15000.0  # 15 km

    # Time stepping
    dt: float = 60.0  # 1 minute
    minutes: int = 180  # 3 hours

    # Thermodynamic parameters
    T_surface: float = 288.0  # K
    T_tropopause: float = 220.0  # K
    p_surface: float = 101325.0  # Pa

    # Microphysics parameters
    # Autoconversion
    autoconv_thresh: float = 1.0e-3  # kg/kg (cloud water to rain)
    autoconv_rate: float = 1.0e-3  # /s

    # Accretion
    accretion_rate: float = 2.2  # coefficient

    # Evaporation
    evap_rate: float = 1.0e-3  # /s

    # Fall speeds
    v_qr: float = 5.0  # Rain fall speed (m/s)
    v_qs: float = 1.0  # Snow fall speed (m/s)

    # Saturation adjustment
    sat_adj_time: float = 100.0  # s

    # Aerosol
    N_c: float = 100e6  # Cloud droplet number concentration (/m^3)

    # Surface fluxes
    surface_moisture_flux: float = 1.0e-4  # kg/m^2/s
    surface_heat_flux: float = 50.0  # W/m^2

    # Output
    output_interval: int = 10


class CloudMicrophysicsPattern:
    """
    Bulk cloud microphysics model.

    Simulates cloud processes including condensation, evaporation,
    autoconversion, accretion, and precipitation formation for
    warm-rain (liquid only) processes.
    """

    PATTERN_ID = "cloud_microphysics"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: CloudMicrophysicsConfig | None = None) -> None:
        self.config = config or CloudMicrophysicsConfig()
        self._initialize_grid()
        self._initialize_fields()

    def _initialize_grid(self) -> None:
        """Initialize grid"""
        cfg = self.config

        self.x = np.linspace(0, cfg.Lx, cfg.nx)
        self.y = np.linspace(0, cfg.Ly, cfg.ny)
        self.z = np.linspace(0, cfg.H, cfg.nz)

        self.dx = cfg.Lx / cfg.nx
        self.dy = cfg.Ly / cfg.ny
        self.dz = cfg.H / cfg.nz

        # Pressure levels (hydrostatic)
        self.p = np.zeros(cfg.nz)
        for k in range(cfg.nz):
            self.p[k] = cfg.p_surface * np.exp(-self.z[k] / 8500)

    def _initialize_fields(self) -> None:
        """Initialize hydrometeor fields"""
        cfg = self.config

        shape = (cfg.nx, cfg.ny, cfg.nz)

        # Water vapor mixing ratio (kg/kg)
        self.qv = np.zeros(shape)

        # Cloud water mixing ratio
        self.qc = np.zeros(shape)

        # Rain water mixing ratio
        self.qr = np.zeros(shape)

        # Temperature
        self.T = np.zeros(shape)

        # Initialize thermodynamic profiles
        for k in range(cfg.nz):
            # Linear temperature profile
            self.T[:, :, k] = cfg.T_surface - (cfg.T_surface - cfg.T_tropopause) * (
                self.z[k] / cfg.H
            )

            # Moisture profile (decreases with height)
            qv_surf = 0.015  # kg/kg at surface
            self.qv[:, :, k] = qv_surf * np.exp(-self.z[k] / 2000)

        # Initialize a cloud in the center
        cx, cy, cz = cfg.nx // 2, cfg.ny // 2, cfg.nz // 3
        radius = 10
        for i in range(cfg.nx):
            for j in range(cfg.ny):
                for k in range(cfg.nz):
                    dist = np.sqrt((i - cx) ** 2 + (j - cy) ** 2 + (k - cz) ** 2)
                    if dist < radius:
                        self.qc[i, j, k] = 1.0e-3 * np.exp(-dist / 5)

        # Output storage
        self.history = {  # type: ignore[var-annotated]
            "qv": [],
            "qc": [],
            "qr": [],
            "T": [],
            "time": [],
            "precip_rate": [],
            "cloud_cover": [],
        }

    def _saturation_vapor_pressure(self, T: np.ndarray) -> np.ndarray:
        """Calculate saturation vapor pressure (Tetens equation)"""
        # Tetens equation
        es = 611.2 * np.exp(17.67 * (T - 273.15) / (T - 29.65))
        return es

    def _saturation_mixing_ratio(self, T: np.ndarray, p: float) -> np.ndarray:
        """Calculate saturation mixing ratio"""
        es = self._saturation_vapor_pressure(T)
        epsilon = 0.622  # Rd/Rv
        qs = epsilon * es / (p - es)
        return qs

    def _saturation_adjustment(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Saturation adjustment to maintain equilibrium.
        Returns condensation rate and temperature tendency.
        """
        cfg = self.config

        dqc_dt = np.zeros_like(self.qc)
        dT_dt = np.zeros_like(self.T)

        Lv = 2.5e6  # Latent heat of vaporization
        cp = 1004.0  # Specific heat

        for k in range(cfg.nz):
            qs = self._saturation_mixing_ratio(self.T[:, :, k], self.p[k])

            # Supersaturation
            S = self.qv[:, :, k] / qs - 1.0

            # Condensation/evaporation
            tau = cfg.sat_adj_time
            dqc = S * qs / tau * cfg.dt

            # Limit by available vapor/cloud
            dqc = np.clip(dqc, -self.qc[:, :, k], self.qv[:, :, k])

            dqc_dt[:, :, k] = dqc / cfg.dt

            # Temperature change from phase change
            dT_dt[:, :, k] = Lv / cp * dqc_dt[:, :, k]

        return dqc_dt, dT_dt

    def _autoconversion(self) -> np.ndarray:
        """
        Autoconversion: cloud water to rain.
        Returns cloud water sink / rain source.
        """
        cfg = self.config

        dqr_dt = np.zeros_like(self.qr)

        # Kessler autoconversion
        for k in range(cfg.nz):
            qc_excess = np.maximum(0, self.qc[:, :, k] - cfg.autoconv_thresh)
            dqr_dt[:, :, k] = cfg.autoconv_rate * qc_excess

        return dqr_dt

    def _accretion(self) -> np.ndarray:
        """
        Accretion: rain collecting cloud water.
        Returns cloud water sink / rain source.
        """
        cfg = self.config

        dqr_dt = np.zeros_like(self.qr)

        for k in range(cfg.nz):
            # Continuous collection equation
            dqr_dt[:, :, k] = (
                cfg.accretion_rate * self.qc[:, :, k] * self.qr[:, :, k] ** 0.875
            )

        return dqr_dt

    def _evaporation(self) -> np.ndarray:
        """
        Rain evaporation.
        Returns rain sink / vapor source.
        """
        cfg = self.config

        dqr_dt = np.zeros_like(self.qr)

        for k in range(cfg.nz):
            qs = self._saturation_mixing_ratio(self.T[:, :, k], self.p[k])

            # Undersaturation
            RH = self.qv[:, :, k] / qs
            undersat = np.maximum(0, 1.0 - RH)

            # Evaporation proportional to rain content and undersaturation
            dqr_dt[:, :, k] = (
                -cfg.evap_rate * undersat * np.sqrt(self.qr[:, :, k] + 1e-10)
            )

        # Limit to available rain
        dqr_dt = np.maximum(dqr_dt, -self.qr / cfg.dt)

        return dqr_dt

    def _sedimentation(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Hydrometeor sedimentation.
        Returns tendencies for cloud and rain due to fall.
        """
        cfg = self.config

        dqc_dt = np.zeros_like(self.qc)
        dqr_dt = np.zeros_like(self.qr)

        # Rain sedimentation (simple upwind)
        v_fall = cfg.v_qr  # Constant fall speed

        for k in range(cfg.nz - 1):
            # Flux at top of level k
            flux_top = v_fall * self.qr[:, :, k + 1]
            # Flux at bottom of level k
            flux_bot = v_fall * self.qr[:, :, k]

            dqr_dt[:, :, k] = (flux_top - flux_bot) / self.dz

        # Bottom boundary (precipitation at surface)
        dqr_dt[:, :, -1] = -v_fall * self.qr[:, :, -1] / self.dz

        return dqc_dt, dqr_dt

    def _tendencies(self) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Calculate tendencies for all variables"""

        # Saturation adjustment
        dqc_sat, dT_sat = self._saturation_adjustment()

        # Autoconversion
        dqr_auto = self._autoconversion()

        # Accretion
        dqr_accr = self._accretion()

        # Evaporation
        dqr_evap = self._evaporation()

        # Sedimentation
        dqc_sed, dqr_sed = self._sedimentation()

        # Sum tendencies
        dqv_dt = -dqc_sat - dqr_evap  # Vapor
        dqc_dt = dqc_sat - dqr_auto - dqr_accr + dqc_sed  # Cloud
        dqr_dt = dqr_auto + dqr_accr + dqr_evap + dqr_sed  # Rain
        dT_dt = dT_sat  # Temperature

        return dqv_dt, dqc_dt, dqr_dt, dT_dt

    def _calculate_precipitation_rate(self) -> float:
        """Calculate surface precipitation rate (mm/hr)"""
        cfg = self.config

        # Rain flux at surface
        rho_air = 1.2  # kg/m^3
        qr_surf = self.qr[:, :, -1]
        v_fall = cfg.v_qr

        # Flux kg/m^2/s
        precip_flux = rho_air * qr_surf * v_fall

        # Convert to mm/hr (1 kg/m^2 = 1 mm)
        precip_rate = np.mean(precip_flux) * 3600

        return precip_rate  # type: ignore[no-any-return]

    def _calculate_cloud_cover(self) -> float:
        """Calculate cloud cover fraction"""
        cfg = self.config

        # Cloud where qc > threshold
        cloud_mask = self.qc > 1.0e-5
        cloud_fraction = np.sum(cloud_mask) / (cfg.nx * cfg.ny * cfg.nz)

        return cloud_fraction  # type: ignore[return-value]

    def _step(self) -> None:
        """Advance model by one time step"""
        cfg = self.config

        # Get tendencies
        dqv_dt, dqc_dt, dqr_dt, dT_dt = self._tendencies()

        # Update fields
        self.qv += dqv_dt * cfg.dt
        self.qc += dqc_dt * cfg.dt
        self.qr += dqr_dt * cfg.dt
        self.T += dT_dt * cfg.dt

        # Ensure non-negative
        self.qv = np.maximum(self.qv, 0)
        self.qc = np.maximum(self.qc, 0)
        self.qr = np.maximum(self.qr, 0)

    def run(self, hypothesis: dict[str, Any] = None) -> dict[str, Any]:  # type: ignore[assignment]
        """Run the cloud microphysics simulation"""
        cfg = self.config
        n_steps = int(cfg.minutes * 60 / cfg.dt)

        logger.info(
            f"Starting microphysics simulation: {cfg.minutes} minutes, {n_steps} steps"
        )

        for step in range(n_steps):
            self._step()

            # Output
            if step % cfg.output_interval == 0:
                minute = step * cfg.dt / 60.0

                precip = self._calculate_precipitation_rate()
                cloud_cover = self._calculate_cloud_cover()

                self.history["qv"].append(np.mean(self.qv))
                self.history["qc"].append(np.mean(self.qc))
                self.history["qr"].append(np.mean(self.qr))
                self.history["T"].append(np.mean(self.T))
                self.history["time"].append(minute)
                self.history["precip_rate"].append(precip)
                self.history["cloud_cover"].append(cloud_cover)

            if step % 50 == 0:
                logger.debug(
                    f"Step {step}/{n_steps}, t={minute:.0f}min, rain={self._calculate_precipitation_rate():.2f}mm/hr"
                )

        return self._format_output()

    def _format_output(self) -> dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        # Find maximum precipitation
        max_precip = (
            max(self.history["precip_rate"]) if self.history["precip_rate"] else 0
        )

        # Total accumulated precipitation
        total_precip = (
            np.trapezoid(self.history["precip_rate"], self.history["time"]) / 60
        )  # mm

        return {
            "vapor": self.history["qv"],
            "cloud_water": self.history["qc"],
            "rain_water": self.history["qr"],
            "precipitation_rate": self.history["precip_rate"],
            "cloud_cover": self.history["cloud_cover"],
            "time_minutes": self.history["time"],
            "final_state": {
                "max_qc": float(np.max(self.qc)),
                "max_qr": float(np.max(self.qr)),
                "mean_T": float(np.mean(self.T)),
                "max_precip_rate": float(max_precip),
                "total_precipitation": float(total_precip),
                "cloud_fraction": float(self._calculate_cloud_cover()),
            },
            "processes": {
                "autoconversion_rate": cfg.autoconv_rate,
                "accretion_rate": cfg.accretion_rate,
                "evaporation_rate": cfg.evap_rate,
                "fall_speed": cfg.v_qr,
            },
            "grid": {
                "nx": cfg.nx,
                "ny": cfg.ny,
                "nz": cfg.nz,
            },
            "config": {
                "minutes": cfg.minutes,
                "dt": cfg.dt,
            },
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Cloud Microphysics",
            "category": "ON_DEMAND",
            "domain": ["Atmospheric Science", "Cloud Physics"],
            "description": "Bulk cloud microphysics for warm-rain processes",
            "computational_complexity": "O(N³)",
            "typical_runtime": "minutes",
            "accuracy": "High (weather research)",
            "assumptions": [
                "Warm rain only (no ice)",
                "Bulk microphysics",
                "Saturation adjustment",
                "Constant fall speeds",
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
                    "default": 30,
                    "description": "Vertical levels",
                },
                {
                    "name": "minutes",
                    "type": "int",
                    "default": 180,
                    "description": "Simulation minutes",
                },
                {
                    "name": "autoconv_rate",
                    "type": "float",
                    "default": 1e-3,
                    "description": "Autoconversion rate",
                },
            ],
        }


# Unit tests
import unittest


class TestCloudMicrophysics(unittest.TestCase):
    """TestCloudMicrophysics."""
    def test_initialization(self) -> None:
        """Test that pattern initializes correctly"""
        config = CloudMicrophysicsConfig(nx=20, ny=20, nz=10)
        pattern = CloudMicrophysicsPattern(config)

        self.assertEqual(pattern.qv.shape, (20, 20, 10))
        self.assertEqual(pattern.qc.shape, (20, 20, 10))
        self.assertEqual(pattern.qr.shape, (20, 20, 10))

    def test_saturation_vapor_pressure(self) -> None:
        """Test saturation vapor pressure calculation"""
        config = CloudMicrophysicsConfig()
        pattern = CloudMicrophysicsPattern(config)

        T = np.array([273.15, 283.15, 293.15])
        es = pattern._saturation_vapor_pressure(T)

        # Should increase with temperature
        self.assertTrue(np.all(np.diff(es) > 0))

    def test_saturation_mixing_ratio(self) -> None:
        """Test saturation mixing ratio"""
        config = CloudMicrophysicsConfig()
        pattern = CloudMicrophysicsPattern(config)

        T = 288.0
        p = 100000.0
        qs = pattern._saturation_mixing_ratio(np.array([[T]]), p)

        self.assertGreater(qs[0, 0], 0)
        self.assertLess(qs[0, 0], 0.1)

    def test_autoconversion(self) -> None:
        """Test autoconversion calculation"""
        config = CloudMicrophysicsConfig()
        pattern = CloudMicrophysicsPattern(config)

        # Set high cloud water
        pattern.qc[:, :, 5] = 2.0e-3

        dqr_dt = pattern._autoconversion()

        self.assertEqual(dqr_dt.shape, pattern.qr.shape)
        self.assertTrue(np.all(dqr_dt >= 0))

    def test_accretion(self) -> None:
        """Test accretion calculation"""
        config = CloudMicrophysicsConfig()
        pattern = CloudMicrophysicsPattern(config)

        pattern.qc[:, :, 5] = 1.0e-3
        pattern.qr[:, :, 5] = 1.0e-3

        dqr_dt = pattern._accretion()

        self.assertTrue(np.all(dqr_dt >= 0))

    def test_evaporation(self) -> None:
        """Test evaporation calculation"""
        config = CloudMicrophysicsConfig()
        pattern = CloudMicrophysicsPattern(config)

        pattern.qr[:, :, 5] = 1.0e-3

        dqr_dt = pattern._evaporation()

        # Should be negative (rain evaporating)
        self.assertTrue(np.all(dqr_dt <= 0))

    def test_sedimentation(self) -> None:
        """Test sedimentation calculation"""
        config = CloudMicrophysicsConfig()
        pattern = CloudMicrophysicsPattern(config)

        pattern.qr[:, :, 5] = 1.0e-3

        dqc_dt, dqr_dt = pattern._sedimentation()

        self.assertEqual(dqr_dt.shape, pattern.qr.shape)

    def test_tendencies(self) -> None:
        """Test tendency calculation"""
        config = CloudMicrophysicsConfig()
        pattern = CloudMicrophysicsPattern(config)

        dqv_dt, dqc_dt, dqr_dt, dT_dt = pattern._tendencies()

        self.assertEqual(dqv_dt.shape, pattern.qv.shape)
        self.assertTrue(np.all(np.isfinite(dqc_dt)))

    def test_precipitation_rate(self) -> None:
        """Test precipitation rate calculation"""
        config = CloudMicrophysicsConfig()
        pattern = CloudMicrophysicsPattern(config)

        pattern.qr[:, :, -1] = 1.0e-3

        precip = pattern._calculate_precipitation_rate()

        self.assertIsInstance(precip, float)
        self.assertGreater(precip, 0)

    def test_cloud_cover(self) -> None:
        """Test cloud cover calculation"""
        config = CloudMicrophysicsConfig()
        pattern = CloudMicrophysicsPattern(config)

        cover = pattern._calculate_cloud_cover()

        self.assertIsInstance(cover, float)
        self.assertGreaterEqual(cover, 0)
        self.assertLessEqual(cover, 1)

    def test_step(self) -> None:
        """Test single time step"""
        config = CloudMicrophysicsConfig()
        pattern = CloudMicrophysicsPattern(config)

        pattern._step()

        self.assertTrue(np.all(pattern.qv >= 0))
        self.assertTrue(np.all(pattern.qc >= 0))
        self.assertTrue(np.all(pattern.qr >= 0))

    def test_metadata(self) -> None:
        """Test metadata retrieval"""
        metadata = CloudMicrophysicsPattern.get_metadata()

        self.assertEqual(metadata["id"], "cloud_microphysics")
        self.assertIn("parameters", metadata)

    def test_short_simulation(self) -> None:
        """Test running a short simulation"""
        config = CloudMicrophysicsConfig(nx=20, ny=20, nz=10, minutes=10, dt=30)
        pattern = CloudMicrophysicsPattern(config)

        result = pattern.run()

        self.assertIn("vapor", result)
        self.assertIn("precipitation_rate", result)
        self.assertGreater(len(result["time_minutes"]), 0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
