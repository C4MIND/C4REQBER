"""
Tests for air_quality pattern module.
"""

import numpy as np
import pytest

from src.patterns.library.air_quality import AirQualityConfig, AirQualityPattern


class TestConfig:
    def test_default_config(self):
        cfg = AirQualityConfig()
        assert cfg.nx == 50
        assert cfg.ny == 50
        assert cfg.nz == 10
        assert cfg.hours == 72

    def test_custom_config(self):
        cfg = AirQualityConfig(nx=20, ny=20, nz=5, hours=2)
        assert cfg.nx == 20
        assert cfg.hours == 2


class TestInit:
    def test_pattern_init_default(self):
        pattern = AirQualityPattern()
        assert pattern.config is not None
        assert len(pattern.conc) == len(pattern.config.species)

    def test_pattern_init_custom(self):
        cfg = AirQualityConfig(nx=20, ny=20, nz=5)
        pattern = AirQualityPattern(cfg)
        for sp in cfg.species:
            assert pattern.conc[sp].shape == (20, 20, 5)


class TestPhotolysis:
    def test_photolysis_noon(self):
        pattern = AirQualityPattern()
        j_noon = pattern._photolysis_rate(12)
        assert j_noon > 0
        assert j_noon <= pattern.config.j_no2_max

    def test_photolysis_midnight(self):
        pattern = AirQualityPattern()
        j_midnight = pattern._photolysis_rate(0)
        assert j_midnight == 0

    def test_photolysis_morning(self):
        pattern = AirQualityPattern()
        j_morning = pattern._photolysis_rate(6)
        j_noon = pattern._photolysis_rate(12)
        assert j_morning < j_noon


class TestEmissions:
    def test_emissions_shape(self):
        pattern = AirQualityPattern()
        emissions = pattern._emissions(12)
        assert "NO" in emissions
        assert emissions["NO"].shape == (pattern.config.nx, pattern.config.ny, pattern.config.nz)

    def test_rush_hour_higher(self):
        pattern = AirQualityPattern()
        emissions_rush = pattern._emissions(8)
        emissions_night = pattern._emissions(2)
        assert np.sum(emissions_rush["NO"]) > np.sum(emissions_night["NO"])


class TestDeposition:
    def test_deposition_negative(self):
        pattern = AirQualityPattern()
        deposition = pattern._deposition()
        assert "O3" in deposition
        assert np.all(deposition["O3"][:, :, 0] <= 0)


class TestChemistry:
    def test_gas_chemistry(self):
        pattern = AirQualityPattern()
        chemistry = pattern._gas_chemistry(12)
        assert "NO" in chemistry
        assert "NO2" in chemistry
        assert "O3" in chemistry


class TestTransport:
    def test_transport_shape(self):
        pattern = AirQualityPattern()
        transport = pattern._transport("O3")
        assert transport.shape == (pattern.config.nx, pattern.config.ny, pattern.config.nz)
        assert np.all(np.isfinite(transport))


class TestBoundaryConditions:
    def test_bc_inflow(self):
        pattern = AirQualityPattern()
        pattern.conc["O3"][0, :, :] = 1000
        pattern._apply_boundary_conditions()
        assert np.all(pattern.conc["O3"][0, :, :] < 1000)


class TestAQI:
    def test_aqi_calculation(self):
        pattern = AirQualityPattern()
        aqi = pattern._calculate_aqi()
        assert isinstance(aqi, float)
        assert aqi >= 0


class TestStep:
    def test_single_step(self):
        pattern = AirQualityPattern()
        o3_before = pattern.conc["O3"].copy()
        pattern._step(12)
        assert not np.allclose(pattern.conc["O3"], o3_before)


class TestRun:
    def test_short_simulation(self):
        cfg = AirQualityConfig(nx=20, ny=20, nz=5, hours=2, dt=600)
        pattern = AirQualityPattern(cfg)
        result = pattern.run()
        assert "aqi" in result
        assert "final_concentrations" in result
        assert len(result["time_hours"]) > 0

    def test_metadata(self):
        meta = AirQualityPattern.get_metadata()
        assert meta["id"] == "air_quality"
        assert "parameters" in meta


class TestEdgeCases:
    def test_zero_wind(self):
        cfg = AirQualityConfig(wind_speed=0.0)
        pattern = AirQualityPattern(cfg)
        assert np.all(pattern.u == 0)

    def test_negative_concentration_clipped(self):
        pattern = AirQualityPattern()
        pattern.conc["NO"][:, :, :] = -1.0
        pattern._step(12)
        assert np.all(pattern.conc["NO"] >= 0)

    def test_aqi_categories(self):
        pattern = AirQualityPattern()
        result = pattern.run()
        assert result["aqi_summary"]["category"] in [
            "Good",
            "Moderate",
            "Unhealthy for Sensitive",
            "Unhealthy",
            "Very Unhealthy",
        ]
