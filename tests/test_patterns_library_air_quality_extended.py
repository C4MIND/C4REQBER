"""Extended tests for src/patterns/library/air_quality.py - covering missed paths"""
from __future__ import annotations

import numpy as np
import pytest

from patterns.library.air_quality import AirQualityConfig, AirQualityPattern


class TestAirQualityTransportExtended:
    def test_transport_upwind_positive_u(self):
        cfg = AirQualityConfig(nx=10, ny=10, nz=5, wind_speed=5.0, wind_dir=270.0)
        pattern = AirQualityPattern(cfg)
        pattern.conc["NO"][5, 5, 2] = 100.0
        transport = pattern._transport("NO")
        assert transport.shape == (10, 10, 5)
        assert np.all(np.isfinite(transport))

    def test_transport_upwind_negative_u(self):
        cfg = AirQualityConfig(nx=10, ny=10, nz=5, wind_speed=5.0, wind_dir=90.0)
        pattern = AirQualityPattern(cfg)
        transport = pattern._transport("NO")
        assert transport.shape == (10, 10, 5)

    def test_transport_vertical_diffusion(self):
        cfg = AirQualityConfig(nx=10, ny=10, nz=5)
        pattern = AirQualityPattern(cfg)
        pattern.conc["O3"][:, :, 1] = 50.0
        pattern.conc["O3"][:, :, 3] = 50.0
        transport = pattern._transport("O3")
        assert transport.shape == (10, 10, 5)


class TestAirQualityBoundaryConditionsExtended:
    def test_bc_inflow_west(self):
        cfg = AirQualityConfig(nx=10, ny=10, nz=5, wind_speed=5.0, wind_dir=270.0)
        pattern = AirQualityPattern(cfg)
        pattern.conc["O3"][0, :, :] = 1000.0
        pattern._apply_boundary_conditions()
        assert np.all(pattern.conc["O3"][0, :, :] < 1000.0)

    def test_bc_outflow_east(self):
        cfg = AirQualityConfig(nx=10, ny=10, nz=5, wind_speed=5.0, wind_dir=90.0)
        pattern = AirQualityPattern(cfg)
        pattern.conc["O3"][-1, :, :] = 1000.0
        pattern._apply_boundary_conditions()
        assert np.all(pattern.conc["O3"][-1, :, :] < 1000.0)

    def test_bc_top(self):
        cfg = AirQualityConfig(nx=10, ny=10, nz=5)
        pattern = AirQualityPattern(cfg)
        pattern.conc["O3"][:, :, -1] = 1000.0
        pattern._apply_boundary_conditions()
        assert np.all(pattern.conc["O3"][:, :, -1] < 1000.0)


class TestAirQualityAQIExtended:
    def test_aqi_good(self):
        cfg = AirQualityConfig(nx=10, ny=10, nz=5)
        pattern = AirQualityPattern(cfg)
        pattern.conc["O3"][:, :, :] = 30.0
        pattern.conc["PM25"][:, :, :] = 5.0
        aqi = pattern._calculate_aqi()
        assert aqi <= 50

    def test_aqi_moderate(self):
        cfg = AirQualityConfig(nx=10, ny=10, nz=5)
        pattern = AirQualityPattern(cfg)
        pattern.conc["O3"][:, :, :] = 60.0
        pattern.conc["PM25"][:, :, :] = 5.0
        aqi = pattern._calculate_aqi()
        assert 50 < aqi <= 100

    def test_aqi_unhealthy(self):
        cfg = AirQualityConfig(nx=10, ny=10, nz=5)
        pattern = AirQualityPattern(cfg)
        pattern.conc["O3"][:, :, :] = 100.0
        pattern.conc["PM25"][:, :, :] = 50.0
        aqi = pattern._calculate_aqi()
        assert aqi > 100


class TestAirQualityChemistryExtended:
    def test_gas_chemistry_night(self):
        cfg = AirQualityConfig()
        pattern = AirQualityPattern(cfg)
        chemistry = pattern._gas_chemistry(0)
        assert "NO" in chemistry
        assert "NO2" in chemistry

    def test_gas_chemistry_day(self):
        cfg = AirQualityConfig()
        pattern = AirQualityPattern(cfg)
        chemistry = pattern._gas_chemistry(12)
        assert "NO" in chemistry
        assert "NO2" in chemistry


class TestAirQualityEmissionsExtended:
    def test_emissions_rush_hour(self):
        cfg = AirQualityConfig()
        pattern = AirQualityPattern(cfg)
        emissions = pattern._emissions(8)
        assert np.sum(emissions["NO"]) > 0

    def test_emissions_night(self):
        cfg = AirQualityConfig()
        pattern = AirQualityPattern(cfg)
        emissions = pattern._emissions(2)
        assert np.sum(emissions["NO"]) >= 0


class TestAirQualityDepositionExtended:
    def test_deposition_negative(self):
        cfg = AirQualityConfig()
        pattern = AirQualityPattern(cfg)
        deposition = pattern._deposition()
        assert np.all(deposition["O3"][:, :, 0] <= 0)


class TestAirQualityStepExtended:
    def test_step_changes_concentration(self):
        cfg = AirQualityConfig(nx=10, ny=10, nz=5)
        pattern = AirQualityPattern(cfg)
        o3_before = pattern.conc["O3"].copy()
        pattern._step(12)
        assert not np.allclose(pattern.conc["O3"], o3_before)

    def test_step_nonnegative(self):
        cfg = AirQualityConfig(nx=10, ny=10, nz=5)
        pattern = AirQualityPattern(cfg)
        pattern._step(12)
        for sp in cfg.species:
            assert np.all(pattern.conc[sp] >= 0)


class TestAirQualityRunExtended:
    def test_short_run(self):
        cfg = AirQualityConfig(nx=10, ny=10, nz=5, hours=1, dt=600)
        pattern = AirQualityPattern(cfg)
        result = pattern.run()
        assert "aqi" in result
        assert "final_concentrations" in result
        assert len(result["time_hours"]) > 0

    def test_run_aqi_categories(self):
        cfg = AirQualityConfig(nx=10, ny=10, nz=5, hours=1, dt=600)
        pattern = AirQualityPattern(cfg)
        result = pattern.run()
        assert "aqi_summary" in result
        assert "category" in result["aqi_summary"]
        assert result["aqi_summary"]["category"] in ["Good", "Moderate", "Unhealthy for Sensitive", "Unhealthy", "Very Unhealthy"]


class TestAirQualityFormatOutputExtended:
    def test_format_output_empty(self):
        cfg = AirQualityConfig(nx=10, ny=10, nz=5)
        pattern = AirQualityPattern(cfg)
        result = pattern._format_output()
        assert "aqi_summary" in result
        assert result["aqi_summary"]["max_aqi"] == 0

    def test_format_output_with_data(self):
        cfg = AirQualityConfig(nx=10, ny=10, nz=5)
        pattern = AirQualityPattern(cfg)
        pattern.history["time"].append(0.0)
        pattern.history["aqi"].append(75.0)
        pattern.history["max_o3"].append(60.0)
        pattern.history["max_pm25"].append(20.0)
        result = pattern._format_output()
        assert result["aqi_summary"]["category"] == "Moderate"


class TestAirQualityMetadataExtended:
    def test_get_metadata(self):
        meta = AirQualityPattern.get_metadata()
        assert meta["id"] == "air_quality"
        assert "parameters" in meta
        assert "assumptions" in meta
