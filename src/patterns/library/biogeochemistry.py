"""
C4REQBER v6.0 - Biogeochemistry Pattern
NPZD (Nutrient-Phytoplankton-Zooplankton-Detritus) ecosystem model.

Pattern Structure (Christopher Alexander):
- Context: Marine ecosystem modeling, carbon cycle studies, fisheries management
- Forces: Nutrient limitation, grazing pressure, recycling, sinking
- Solution: NPZD model with multiple nutrients and functional groups
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


@dataclass
class BiogeochemistryConfig:
    """Configuration for biogeochemical simulation"""

    # Grid settings
    nx: int = 50  # Horizontal grid points
    ny: int = 50
    nz: int = 10  # Vertical levels

    # Domain
    Lx: float = 1.0e6  # m (100 km)
    Ly: float = 1.0e6
    H: float = 200.0  # m depth

    # Time stepping
    dt: float = 3600.0  # 1 hour
    days: int = 365

    # NPZD parameters
    # Nutrients
    N_initial: float = 5.0  # mmol N/m^3
    N_deep: float = 15.0  # Deep water nutrient concentration

    # Phytoplankton
    P_initial: float = 0.5  # mmol N/m^3
    P_max_growth: float = 1.0  # /day
    P_half_sat: float = 1.0  # mmol N/m^3
    P_mortality: float = 0.05  # /day

    # Zooplankton
    Z_initial: float = 0.1  # mmol N/m^3
    Z_grazing_max: float = 0.6  # /day
    Z_half_sat: float = 1.0  # mmol N/m^3
    Z_assim_eff: float = 0.3  # Assimilation efficiency
    Z_mortality: float = 0.05  # /day
    Z_excretion: float = 0.1  # /day

    # Detritus
    D_initial: float = 0.1  # mmol N/m^3
    D_remineralization: float = 0.05  # /day
    D_sinking_speed: float = 5.0  # m/day

    # Physical parameters
    diffusivity_h: float = 10.0  # m^2/s
    diffusivity_v: float = 1.0e-4  # m^2/s
    mixed_layer_depth: float = 50.0  # m

    # Light parameters
    I_surface: float = 200.0  # W/m^2
    k_water: float = 0.04  # Light attenuation (1/m)
    k_chl: float = 0.03  # Self-shading (m^2/mg Chl)

    # Carbon parameters
    C_to_N: float = 6.625  # Redfield ratio
    Chl_to_C: float = 0.02  # mg Chl/mmol C

    # Output
    output_interval: int = 24  # Daily output


class BiogeochemistryPattern:
    """
    NPZD biogeochemical model.

    Simulates the cycling of nutrients, phytoplankton, zooplankton,
    and detritus in the ocean. Includes light limitation, nutrient
    uptake, grazing, mortality, and sinking.
    """

    PATTERN_ID = "biogeochemistry"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: BiogeochemistryConfig | None = None) -> None:
        self.config = config or BiogeochemistryConfig()
        self._initialize_grid()
        self._initialize_fields()

    def _initialize_grid(self) -> None:
        """Initialize 3D grid"""
        cfg = self.config

        self.x = np.linspace(0, cfg.Lx, cfg.nx)
        self.y = np.linspace(0, cfg.Ly, cfg.ny)
        self.z = np.linspace(-cfg.H, 0, cfg.nz)

        self.dx = cfg.Lx / cfg.nx
        self.dy = cfg.Ly / cfg.ny
        self.dz = cfg.H / cfg.nz

        self.X, self.Y, self.Z = np.meshgrid(self.x, self.y, self.z, indexing="ij")

    def _initialize_fields(self) -> None:
        """Initialize tracer fields"""
        cfg = self.config

        shape = (cfg.nx, cfg.ny, cfg.nz)

        # Nutrients
        self.N = np.ones(shape) * cfg.N_initial

        # Phytoplankton (higher near surface)
        self.P = np.ones(shape) * cfg.P_initial
        for k in range(cfg.nz):
            depth_factor = np.exp(self.z[k] / 20)  # Decay with depth
            self.P[:, :, k] *= depth_factor

        # Zooplankton
        self.Z = np.ones(shape) * cfg.Z_initial

        # Detritus
        self.D = np.ones(shape) * cfg.D_initial

        # Output storage
        self.history = {  # type: ignore[var-annotated]
            "N": [],
            "P": [],
            "Z": [],
            "D": [],
            "time": [],
            "primary_production": [],
            "export_flux": [],
        }

    def _light_profile(self) -> np.ndarray:
        """Calculate light attenuation with depth"""
        cfg = self.config

        I = np.zeros((cfg.nx, cfg.ny, cfg.nz))

        for k in range(cfg.nz):
            # Self-shading by phytoplankton
            chl = self.P[:, :, k] * cfg.C_to_N * cfg.Chl_to_C  # mg Chl/m^3

            # Attenuation coefficient
            Kd = cfg.k_water + cfg.k_chl * chl

            # Light at depth
            depth = -self.z[k]
            I[:, :, k] = cfg.I_surface * np.exp(-Kd * depth)

        return I

    def _temperature_limitation(self) -> float:
        """Temperature limitation factor (simplified)"""
        return 1.0  # Constant for now

    def _nutrient_uptake(
        self, N: np.ndarray, P: np.ndarray, I: np.ndarray
    ) -> np.ndarray:
        """
        Calculate phytoplankton nutrient uptake.
        Returns growth rate.
        """
        cfg = self.config

        # Light limitation (Monod)
        f_I = I / (I + 50)  # Half-saturation 50 W/m^2

        # Nutrient limitation (Monod)
        f_N = N / (N + cfg.P_half_sat)

        # Temperature limitation
        f_T = self._temperature_limitation()

        # Maximum growth rate (convert from /day to /s)
        mu_max = cfg.P_max_growth / 86400.0

        # Actual growth rate
        mu = mu_max * f_I * f_N * f_T

        return mu * P  # type: ignore[no-any-return]

    def _grazing(self, P: np.ndarray, Z: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """
        Calculate zooplankton grazing on phytoplankton.
        Returns grazing rate on P and assimilation into Z.
        """
        cfg = self.config

        # Holling Type II functional response
        g_max = cfg.Z_grazing_max / 86400.0
        grazing = g_max * Z * P / (P + cfg.Z_half_sat)

        # Assimilation
        assimilation = cfg.Z_assim_eff * grazing

        return grazing, assimilation

    def _mortality(self, P: np.ndarray, Z: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Calculate mortality terms"""
        cfg = self.config

        # Phytoplankton mortality (linear + quadratic)
        m_P = cfg.P_mortality / 86400.0
        P_mortality = m_P * P

        # Zooplankton mortality (linear)
        m_Z = cfg.Z_mortality / 86400.0
        Z_mortality = m_Z * Z

        return P_mortality, Z_mortality

    def _remineralization(self, D: np.ndarray) -> np.ndarray:
        """Calculate detritus remineralization"""
        cfg = self.config

        r_D = cfg.D_remineralization / 86400.0
        return r_D * D

    def _sinking(self, D: np.ndarray) -> np.ndarray:
        """Calculate detritus sinking flux"""
        cfg = self.config

        # Sinking flux (positive = downward)
        w_sink = cfg.D_sinking_speed / 86400.0  # Convert to m/s

        F_sink = np.zeros_like(D)

        for k in range(cfg.nz - 1):
            F_sink[:, :, k] = w_sink * D[:, :, k + 1]

        # Bottom boundary (loss to sediments)
        F_sink[:, :, -1] = w_sink * D[:, :, -1]

        return F_sink

    def _tendencies(self) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Calculate tendencies for all tracers"""
        cfg = self.config

        # Light
        I = self._light_profile()

        # Phytoplankton growth
        growth = self._nutrient_uptake(self.N, self.P, I)

        # Grazing
        grazing, assimilation = self._grazing(self.P, self.Z)

        # Mortality
        P_mort, Z_mort = self._mortality(self.P, self.Z)

        # Excretion
        excretion = (cfg.Z_excretion / 86400.0) * self.Z

        # Remineralization
        remin = self._remineralization(self.D)

        # Sinking
        F_sink = self._sinking(self.D)

        # Nutrient tendency
        dN_dt = -growth + remin + excretion

        # Phytoplankton tendency
        dP_dt = growth - grazing - P_mort

        # Zooplankton tendency
        dZ_dt = assimilation - Z_mort - excretion

        # Detritus tendency
        dD_dt = P_mort + Z_mort + (1 - cfg.Z_assim_eff) * grazing - remin

        # Add sinking divergence
        for k in range(cfg.nz):
            if k == 0:
                dD_dt[:, :, k] -= F_sink[:, :, k] / self.dz
            elif k < cfg.nz - 1:
                dD_dt[:, :, k] += (F_sink[:, :, k - 1] - F_sink[:, :, k]) / self.dz
            else:
                dD_dt[:, :, k] += F_sink[:, :, k - 1] / self.dz

        # Add vertical mixing
        dN_dt += self._vertical_mixing(self.N)
        dP_dt += self._vertical_mixing(self.P)
        dZ_dt += self._vertical_mixing(self.Z)
        dD_dt += self._vertical_mixing(self.D)

        return dN_dt, dP_dt, dZ_dt, dD_dt

    def _vertical_mixing(self, tracer: np.ndarray) -> np.ndarray:
        """Apply vertical mixing"""
        cfg = self.config

        dtracer_dt = np.zeros_like(tracer)

        Kz = cfg.diffusivity_v

        for k in range(1, cfg.nz - 1):
            d2c_dz2 = (
                tracer[:, :, k + 1] - 2 * tracer[:, :, k] + tracer[:, :, k - 1]
            ) / self.dz**2
            dtracer_dt[:, :, k] = Kz * d2c_dz2

        # Surface boundary: restoring to initial value
        dtracer_dt[:, :, 0] = Kz * (tracer[:, :, 1] - tracer[:, :, 0]) / self.dz**2

        # Deep boundary: restoring to deep value
        if tracer is self.N:
            dtracer_dt[:, :, -1] = Kz * (cfg.N_deep - tracer[:, :, -1]) / self.dz**2
        else:
            dtracer_dt[:, :, -1] = (
                Kz * (tracer[:, :, -2] - tracer[:, :, -1]) / self.dz**2
            )

        return dtracer_dt

    def _step(self) -> None:
        """Advance model by one time step"""
        cfg = self.config

        # Get tendencies
        dN_dt, dP_dt, dZ_dt, dD_dt = self._tendencies()

        # Update fields
        self.N += dN_dt * cfg.dt
        self.P += dP_dt * cfg.dt
        self.Z += dZ_dt * cfg.dt
        self.D += dD_dt * cfg.dt

        # Ensure non-negative
        self.N = np.maximum(self.N, 0)
        self.P = np.maximum(self.P, 0)
        self.Z = np.maximum(self.Z, 0)
        self.D = np.maximum(self.D, 0)

    def _calculate_primary_production(self) -> float:
        """Calculate total primary production"""

        I = self._light_profile()
        growth = self._nutrient_uptake(self.N, self.P, I)

        # Integrate over volume and convert to mmol N/m^2/day
        PP = np.sum(growth) * self.dx * self.dy * self.dz * 86400.0

        return PP  # type: ignore[no-any-return]

    def _calculate_export_flux(self) -> float:
        """Calculate carbon export flux at base of euphotic zone"""
        cfg = self.config

        # Find depth index for euphotic zone base (~100 m or max depth)
        z_euphotic = -100.0
        k_euphotic = np.argmin(np.abs(self.z - z_euphotic))

        # Sinking flux at euphotic base
        w_sink = cfg.D_sinking_speed / 86400.0
        export = np.sum(w_sink * self.D[:, :, k_euphotic]) * self.dx * self.dy

        return float(export)

    def run(self, hypothesis: dict[str, Any] = None) -> dict[str, Any]:  # type: ignore[assignment]
        """Run the biogeochemical simulation"""
        cfg = self.config
        n_steps = int(cfg.days * 86400 / cfg.dt)

        logger.info(f"Starting NPZD simulation: {cfg.days} days, {n_steps} steps")

        for step in range(n_steps):
            self._step()

            # Output
            if step % cfg.output_interval == 0:
                day = step * cfg.dt / 86400.0

                # Calculate diagnostics
                PP = self._calculate_primary_production()
                export = self._calculate_export_flux()

                self.history["N"].append(np.mean(self.N))
                self.history["P"].append(np.mean(self.P))
                self.history["Z"].append(np.mean(self.Z))
                self.history["D"].append(np.mean(self.D))
                self.history["time"].append(day)
                self.history["primary_production"].append(PP)
                self.history["export_flux"].append(export)

            if step % (24 * 10) == 0:
                logger.debug(
                    f"Step {step}/{n_steps}, Day {day:.0f}, P: {np.mean(self.P):.3f}"
                )

        return self._format_output()

    def _format_output(self) -> dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        # Carbon conversion
        carbon_biomass = (np.mean(self.P) + np.mean(self.Z)) * cfg.C_to_N  # mmol C/m^3

        return {
            "nutrients": self.history["N"],
            "phytoplankton": self.history["P"],
            "zooplankton": self.history["Z"],
            "detritus": self.history["D"],
            "primary_production": self.history["primary_production"],
            "export_flux": self.history["export_flux"],
            "time_days": self.history["time"],
            "final_state": {
                "mean_N": float(np.mean(self.N)),
                "mean_P": float(np.mean(self.P)),
                "mean_Z": float(np.mean(self.Z)),
                "mean_D": float(np.mean(self.D)),
                "surface_chl": float(
                    np.mean(self.P[:, :, 0] * cfg.C_to_N * cfg.Chl_to_C)
                ),
                "carbon_biomass": float(carbon_biomass),
                "N_P_ratio": float(np.mean(self.N) / np.mean(self.P)),
            },
            "production_stats": {
                "total_PP": float(np.sum(self.history["primary_production"])),
                "mean_export": float(np.mean(self.history["export_flux"])),
                "export_ratio": float(np.mean(self.history["export_flux"]))
                / float(np.mean(self.history["primary_production"]))
                if np.mean(self.history["primary_production"]) > 0
                else 0,
            },
            "grid": {
                "nx": cfg.nx,
                "ny": cfg.ny,
                "nz": cfg.nz,
            },
            "config": {
                "days": cfg.days,
                "P_max_growth": cfg.P_max_growth,
                "Z_grazing_max": cfg.Z_grazing_max,
            },
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Biogeochemistry",
            "category": "ON_DEMAND",
            "domain": ["Marine Biology", "Biogeochemistry"],
            "description": "NPZD ecosystem model for marine biogeochemistry",
            "computational_complexity": "O(N³)",
            "typical_runtime": "minutes to hours",
            "accuracy": "High (ecosystem research)",
            "assumptions": [
                "Redfield stoichiometry",
                "Monod kinetics",
                "Instantaneous equilibrium",
                "Simplified light attenuation",
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
                    "name": "P_max_growth",
                    "type": "float",
                    "default": 1.0,
                    "description": "Max phyto growth rate",
                },
                {
                    "name": "Z_grazing_max",
                    "type": "float",
                    "default": 0.6,
                    "description": "Max grazing rate",
                },
            ],
        }


# Unit tests
import unittest


class TestBiogeochemistry(unittest.TestCase):
    """TestBiogeochemistry."""
    def test_initialization(self) -> None:
        """Test that pattern initializes correctly"""
        config = BiogeochemistryConfig(nx=20, ny=20, nz=5)
        pattern = BiogeochemistryPattern(config)

        self.assertEqual(pattern.N.shape, (20, 20, 5))
        self.assertEqual(pattern.P.shape, (20, 20, 5))
        self.assertEqual(pattern.Z.shape, (20, 20, 5))
        self.assertEqual(pattern.D.shape, (20, 20, 5))

    def test_light_profile(self) -> None:
        """Test light attenuation calculation"""
        config = BiogeochemistryConfig(nx=10, ny=10, nz=5)
        pattern = BiogeochemistryPattern(config)

        I = pattern._light_profile()

        self.assertEqual(I.shape, (10, 10, 5))
        # Light should decrease with depth
        self.assertTrue(np.all(I[:, :, 0] >= I[:, :, -1]))

    def test_nutrient_uptake(self) -> None:
        """Test phytoplankton growth calculation"""
        config = BiogeochemistryConfig()
        pattern = BiogeochemistryPattern(config)

        I = pattern._light_profile()
        growth = pattern._nutrient_uptake(pattern.N, pattern.P, I)

        self.assertEqual(growth.shape, pattern.P.shape)
        self.assertTrue(np.all(growth >= 0))

    def test_grazing(self) -> None:
        """Test zooplankton grazing"""
        config = BiogeochemistryConfig()
        pattern = BiogeochemistryPattern(config)

        grazing, assimilation = pattern._grazing(pattern.P, pattern.Z)

        self.assertEqual(grazing.shape, pattern.P.shape)
        self.assertEqual(assimilation.shape, pattern.Z.shape)
        # Assimilation should be less than grazing
        self.assertTrue(np.all(assimilation <= grazing * config.Z_assim_eff + 1e-10))

    def test_mortality(self) -> None:
        """Test mortality calculation"""
        config = BiogeochemistryConfig()
        pattern = BiogeochemistryPattern(config)

        P_mort, Z_mort = pattern._mortality(pattern.P, pattern.Z)

        self.assertEqual(P_mort.shape, pattern.P.shape)
        self.assertEqual(Z_mort.shape, pattern.Z.shape)
        self.assertTrue(np.all(P_mort >= 0))
        self.assertTrue(np.all(Z_mort >= 0))

    def test_remineralization(self) -> None:
        """Test detritus remineralization"""
        config = BiogeochemistryConfig()
        pattern = BiogeochemistryPattern(config)

        remin = pattern._remineralization(pattern.D)

        self.assertEqual(remin.shape, pattern.D.shape)
        self.assertTrue(np.all(remin >= 0))

    def test_tendencies(self) -> None:
        """Test tendency calculation"""
        config = BiogeochemistryConfig()
        pattern = BiogeochemistryPattern(config)

        dN_dt, dP_dt, dZ_dt, dD_dt = pattern._tendencies()

        self.assertEqual(dN_dt.shape, pattern.N.shape)
        self.assertEqual(dP_dt.shape, pattern.P.shape)
        self.assertTrue(np.all(np.isfinite(dN_dt)))

    def test_vertical_mixing(self) -> None:
        """Test vertical mixing operator"""
        config = BiogeochemistryConfig(nz=5)
        pattern = BiogeochemistryPattern(config)

        dN_dt = pattern._vertical_mixing(pattern.N)

        self.assertEqual(dN_dt.shape, pattern.N.shape)
        self.assertTrue(np.all(np.isfinite(dN_dt)))

    def test_step(self) -> None:
        """Test single time step"""
        config = BiogeochemistryConfig(dt=100)
        pattern = BiogeochemistryPattern(config)

        pattern.N.copy()
        pattern._step()

        # Values should remain non-negative
        self.assertTrue(np.all(pattern.N >= 0))
        self.assertTrue(np.all(pattern.P >= 0))
        self.assertTrue(np.all(pattern.Z >= 0))
        self.assertTrue(np.all(pattern.D >= 0))

    def test_primary_production(self) -> None:
        """Test primary production calculation"""
        config = BiogeochemistryConfig()
        pattern = BiogeochemistryPattern(config)

        PP = pattern._calculate_primary_production()

        self.assertIsInstance(PP, float)
        self.assertGreaterEqual(PP, 0)

    def test_metadata(self) -> None:
        """Test metadata retrieval"""
        metadata = BiogeochemistryPattern.get_metadata()

        self.assertEqual(metadata["id"], "biogeochemistry")
        self.assertIn("parameters", metadata)
        self.assertGreater(len(metadata["assumptions"]), 0)

    def test_short_simulation(self) -> None:
        """Test running a short simulation"""
        config = BiogeochemistryConfig(nx=10, ny=10, nz=3, days=5, dt=3600)
        pattern = BiogeochemistryPattern(config)

        result = pattern.run()

        self.assertIn("nutrients", result)
        self.assertIn("phytoplankton", result)
        self.assertIn("primary_production", result)
        self.assertGreater(len(result["time_days"]), 0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
