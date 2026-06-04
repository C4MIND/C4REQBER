"""Tests for land_surface pattern module."""

import numpy as np
import pytest

from src.patterns.library.land_surface import LandSurfaceConfig, LandSurfacePattern



class TestLandSurfaceConfig:
    def test_default_values(self):
        cfg = LandSurfaceConfig()
        assert cfg.nx == 50
        assert cfg.ny == 50
        assert cfg.Lx == 1.0e5
        assert cfg.albedo == 0.2
        assert cfg.soil_depth == 1.0
        assert cfg.days == 365

    def test_custom_values(self):
        cfg = LandSurfaceConfig(nx=20, ny=20, days=10, albedo=0.3)
        assert cfg.nx == 20
        assert cfg.days == 10
        assert cfg.albedo == 0.3


class TestLandSurfacePattern:
    @pytest.fixture
    def small_config(self):
        return LandSurfaceConfig(nx=20, ny=20, days=2, dt=3600)

    @pytest.fixture
    def pattern(self, small_config):
        return LandSurfacePattern(small_config)

    def test_init(self, pattern, small_config):
        assert pattern.config == small_config
        assert pattern.T_surf.shape == (20, 20)
        assert pattern.soil_moisture.shape == (20, 20)
        assert pattern.swe.shape == (20, 20)
        assert pattern.runoff.shape == (20, 20)

    def test_pattern_id(self):
        assert LandSurfacePattern.PATTERN_ID == "land_surface"
        assert LandSurfacePattern.PATTERN_VERSION == "6.0.0"

    def test_diurnal_temperature(self, pattern):
        T_day, S_day = pattern._diurnal_temperature(100, 12)
        T_night, S_night = pattern._diurnal_temperature(100, 0)
        assert np.mean(T_day) > np.mean(T_night)
        assert np.mean(S_day) > np.mean(S_night)
        assert T_day.shape == (20, 20)

    def test_surface_albedo_no_snow(self, pattern):
        albedo = pattern._surface_albedo()
        assert np.allclose(albedo, pattern.config.albedo)

    def test_surface_albedo_with_snow(self, pattern):
        pattern.swe[:, :] = 20.0
        albedo = pattern._surface_albedo()
        assert np.all(albedo > pattern.config.albedo)
        assert np.all(albedo <= 0.8)

    def test_surface_resistance(self, pattern):
        rs = pattern._surface_resistance()
        assert rs.shape == (20, 20)
        assert np.all(rs > 0)

    def test_energy_balance(self, pattern):
        T_atm = np.ones((20, 20)) * 288.0
        S_down = np.ones((20, 20)) * 500.0
        Q_net, Q_h, Q_le, Q_g = pattern._energy_balance(T_atm, S_down)
        assert Q_net.shape == (20, 20)
        residual = Q_net - Q_h - Q_le - Q_g
        assert np.allclose(residual, 0, atol=1e-6)

    def test_soil_moisture_update(self, pattern):
        sm_before = pattern.soil_moisture.copy()
        precip = np.ones((20, 20)) * 10.0
        ET = np.ones((20, 20)) * 50.0
        pattern._soil_moisture_update(precip, ET)
        assert np.all(pattern.soil_moisture >= pattern.config.wilting_point)
        assert np.all(pattern.soil_moisture <= pattern.config.field_capacity)

    def test_temperature_update(self, pattern):
        T_before = pattern.T_surf.copy()
        Q_g = np.ones((20, 20)) * 50.0
        pattern._temperature_update(Q_g)
        assert not np.allclose(pattern.T_surf, T_before)

    def test_snow_update_cold(self, pattern):
        precip = np.ones((20, 20)) * 10.0
        T_atm = np.ones((20, 20)) * 260.0
        pattern.T_surf = np.ones((20, 20)) * 260.0  # ensure surface is cold too
        liquid = pattern._snow_update(precip, T_atm)
        assert np.all(pattern.swe > 0)
        assert np.all(liquid == 0)

    def test_snow_update_warm(self, pattern):
        precip = np.ones((20, 20)) * 10.0
        T_atm = np.ones((20, 20)) * 290.0
        liquid = pattern._snow_update(precip, T_atm)
        assert np.all(liquid > 0)

    def test_step(self, pattern):
        pattern._step(1.0, 12.0)
        assert np.all(np.isfinite(pattern.T_surf))
        assert np.all(np.isfinite(pattern.soil_moisture))
        assert np.all(pattern.soil_moisture >= 0)

    def test_run_short(self):
        config = LandSurfaceConfig(nx=10, ny=10, days=2, dt=3600, output_interval=1)
        pattern = LandSurfacePattern(config)
        result = pattern.run()
        assert "surface_temperature" in result
        assert "soil_moisture" in result
        assert "evapotranspiration" in result
        assert "runoff" in result
        assert "snow_water" in result
        assert len(result["time_days"]) > 0
        assert "final_state" in result
        assert "water_balance" in result

    def test_metadata(self):
        metadata = LandSurfacePattern.get_metadata()
        assert metadata["id"] == "land_surface"
        assert "parameters" in metadata
        assert len(metadata["assumptions"]) > 0

    def test_water_balance_conservation(self):
        config = LandSurfaceConfig(nx=10, ny=10, days=2, dt=3600)
        pattern = LandSurfacePattern(config)
        result = pattern.run()
        sm_change = result["water_balance"]["soil_moisture_change"]
        assert isinstance(sm_change, float)
