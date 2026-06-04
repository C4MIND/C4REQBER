"""Tests for src/patterns/library/air_quality.py"""
from __future__ import annotations

import numpy as np
import pytest

from patterns.library.air_quality import AirQualityConfig, AirQualityPattern


class TestAirQualityConfig:
    def test_defaults(self):
        cfg = AirQualityConfig()
        assert cfg.nx == 50
        assert cfg.ny == 50
        assert cfg.nz == 10
        assert cfg.hours == 72
        assert "NO" in cfg.species
        assert "O3" in cfg.species

    def test_custom_grid(self):
        cfg = AirQualityConfig(nx=20, ny=20, nz=5, hours=24)
        assert cfg.nx == 20
        assert cfg.ny == 20
        assert cfg.nz == 5
        assert cfg.hours == 24

    def test_initial_conc(self):
        cfg = AirQualityConfig()
        assert cfg.initial_conc["O3"] == 30.0
        assert cfg.initial_conc["PM25"] == 15.0


class TestAirQualityPatternInit:
    def test_init_default(self):
        pattern = AirQualityPattern()
        assert pattern.config is not None
        assert len(pattern.conc) == len(pattern.config.species)
        assert "NO" in pattern.conc

    def test_init_custom(self):
        cfg = AirQualityConfig(nx=20, ny=20, nz=5)
        pattern = AirQualityPattern(cfg)
        assert pattern.conc["NO"].shape == (20, 20, 5)


class TestAirQualityGrid:
    def test_grid_coordinates(self):
        cfg = AirQualityConfig(nx=20, ny=20, nz=5)
        pattern = AirQualityPattern(cfg)
        assert len(pattern.x) == 20
        assert len(pattern.y) == 20
        assert len(pattern.z) == 5
        assert pattern.dx > 0
        assert pattern.dy > 0
        assert pattern.dz > 0

    def test_wind_components(self):
        cfg = AirQualityConfig(wind_speed=5.0, wind_dir=270.0)
        pattern = AirQualityPattern(cfg)
        assert pattern.u.shape == (cfg.nx, cfg.ny, cfg.nz)
        assert pattern.v.shape == (cfg.nx, cfg.ny, cfg.nz)
        assert pattern.w.shape == (cfg.nx, cfg.ny, cfg.nz)


class TestAirQualityPhotolysis:
    def test_photolysis_noon(self):
        pattern = AirQualityPattern()
        j = pattern._photolysis_rate(12)
        assert j > 0
        assert j <= pattern.config.j_no2_max

    def test_photolysis_midnight(self):
        pattern = AirQualityPattern()
        j = pattern._photolysis_rate(0)
        assert j == 0

    def test_photolysis_morning(self):
        pattern = AirQualityPattern()
        j6 = pattern._photolysis_rate(6)
        j12 = pattern._photolysis_rate(12)
        assert j12 >= j6

    def test_photolysis_night(self):
        pattern = AirQualityPattern()
        j = pattern._photolysis_rate(22)
        assert j == 0


class TestAirQualityEmissions:
    def test_emissions_shape(self):
        pattern = AirQualityPattern()
        emissions = pattern._emissions(12)
        assert "NO" in emissions
        assert emissions["NO"].shape == (pattern.config.nx, pattern.config.ny, pattern.config.nz)

    def test_emissions_rush_hour(self):
        pattern = AirQualityPattern()
        rush = pattern._emissions(8)
        night = pattern._emissions(2)
        assert np.sum(rush["NO"]) > np.sum(night["NO"])

    def test_emissions_night_low(self):
        pattern = AirQualityPattern()
        night = pattern._emissions(2)
        day = pattern._emissions(12)
        assert np.sum(night["NO"]) < np.sum(day["NO"])

    def test_emissions_urban_mask(self):
        pattern = AirQualityPattern()
        emissions = pattern._emissions(12)
        center = emissions["NO"][
            pattern.config.nx // 2, pattern.config.ny // 2, 0
        ]
        edge = emissions["NO"][0, 0, 0]
        assert center >= edge


class TestAirQualityDeposition:
    def test_deposition_shape(self):
        pattern = AirQualityPattern()
        dep = pattern._deposition()
        assert "O3" in dep
        assert dep["O3"].shape == (pattern.config.nx, pattern.config.ny, pattern.config.nz)

    def test_deposition_negative(self):
        pattern = AirQualityPattern()
        dep = pattern._deposition()
        assert np.all(dep["O3"][:, :, 0] <= 0)

    def test_deposition_surface_only(self):
        pattern = AirQualityPattern()
        dep = pattern._deposition()
        assert np.all(dep["NO"][:, :, 1:] == 0)


class TestAirQualityChemistry:
    def test_chemistry_shape(self):
        pattern = AirQualityPattern()
        chem = pattern._gas_chemistry(12)
        assert "NO" in chem
        assert chem["NO"].shape == (pattern.config.nx, pattern.config.ny, pattern.config.nz)

    def test_chemistry_night_no_photo(self):
        pattern = AirQualityPattern()
        chem_night = pattern._gas_chemistry(0)
        chem_day = pattern._gas_chemistry(12)
        assert not np.array_equal(chem_night["NO2"], chem_day["NO2"])

    def test_chemistry_voc(self):
        pattern = AirQualityPattern()
        chem = pattern._gas_chemistry(12)
        assert np.all(chem["VOC"] <= 0)


class TestAirQualityTransport:
    def test_transport_shape(self):
        pattern = AirQualityPattern()
        transport = pattern._transport("O3")
        assert transport.shape == (pattern.config.nx, pattern.config.ny, pattern.config.nz)

    def test_transport_finite(self):
        pattern = AirQualityPattern()
        transport = pattern._transport("O3")
        assert np.all(np.isfinite(transport))


class TestAirQualityBoundaryConditions:
    def test_apply_bc(self):
        pattern = AirQualityPattern()
        pattern.conc["O3"][0, :, :] = 999
        pattern._apply_boundary_conditions()
        assert np.all(pattern.conc["O3"][0, :, :] < 999)

    def test_top_boundary(self):
        pattern = AirQualityPattern()
        pattern._apply_boundary_conditions()
        assert np.all(pattern.conc["O3"][:, :, -1] <= pattern.config.bc_conc["O3"])


class TestAirQualityAQI:
    def test_aqi_calculation(self):
        pattern = AirQualityPattern()
        aqi = pattern._calculate_aqi()
        assert isinstance(aqi, float)
        assert aqi >= 0

    def test_aqi_high_ozone(self):
        pattern = AirQualityPattern()
        pattern.conc["O3"][:, :, :] = 100.0
        aqi = pattern._calculate_aqi()
        assert aqi > 50

    def test_aqi_high_pm25(self):
        pattern = AirQualityPattern()
        pattern.conc["PM25"][:, :, :] = 50.0
        aqi = pattern._calculate_aqi()
        assert aqi > 50


class TestAirQualityStep:
    def test_step_changes_concentration(self):
        pattern = AirQualityPattern()
        before = pattern.conc["O3"].copy()
        pattern._step(12)
        assert not np.allclose(pattern.conc["O3"], before)

    def test_step_non_negative(self):
        pattern = AirQualityPattern()
        pattern.conc["O3"][:, :, :] = 0.1
        pattern._step(12)
        assert np.all(pattern.conc["O3"] >= 0)


class TestAirQualityRun:
    def test_short_run(self):
        cfg = AirQualityConfig(nx=20, ny=20, nz=5, hours=2, dt=600)
        pattern = AirQualityPattern(cfg)
        result = pattern.run()
        assert "aqi" in result
        assert "final_concentrations" in result
        assert "aqi_summary" in result
        assert len(result["time_hours"]) > 0

    def test_run_aqi_categories(self):
        cfg = AirQualityConfig(nx=20, ny=20, nz=5, hours=1, dt=600)
        pattern = AirQualityPattern(cfg)
        result = pattern.run()
        category = result["aqi_summary"]["category"]
        assert category in ["Good", "Moderate", "Unhealthy for Sensitive", "Unhealthy", "Very Unhealthy"]

    def test_run_peak_concentrations(self):
        cfg = AirQualityConfig(nx=20, ny=20, nz=5, hours=1, dt=600)
        pattern = AirQualityPattern(cfg)
        result = pattern.run()
        assert "peak_concentrations" in result
        assert "NO" in result["peak_concentrations"]

    def test_run_grid_info(self):
        cfg = AirQualityConfig(nx=20, ny=20, nz=5, hours=1, dt=600)
        pattern = AirQualityPattern(cfg)
        result = pattern.run()
        assert result["grid"]["nx"] == 20
        assert result["grid"]["ny"] == 20
        assert result["grid"]["nz"] == 5


class TestAirQualityMetadata:
    def test_get_metadata(self):
        meta = AirQualityPattern.get_metadata()
        assert meta["id"] == "air_quality"
        assert "parameters" in meta
        assert "assumptions" in meta
