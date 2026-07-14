"""Tests for sea_ice pattern module."""

import numpy as np
import pytest

from src.patterns.library.sea_ice import SeaIceConfig, SeaIcePattern


class TestSeaIceConfig:
    def test_default_values(self):
        cfg = SeaIceConfig()
        assert cfg.nx == 100
        assert cfg.ny == 100
        assert cfg.Lx == 4.0e6
        assert cfg.albedo_ice == 0.65
        assert cfg.T_freeze == -1.8

    def test_custom_values(self):
        cfg = SeaIceConfig(nx=50, ny=50, days=10)
        assert cfg.nx == 50
        assert cfg.days == 10


class TestSeaIcePattern:
    @pytest.fixture
    def small_config(self):
        return SeaIceConfig(nx=20, ny=20, days=5)

    @pytest.fixture
    def pattern(self, small_config):
        return SeaIcePattern(small_config)

    def test_init(self, pattern, small_config):
        assert pattern.config == small_config
        assert pattern.a_ice.shape == (20, 20)
        assert pattern.h_ice.shape == (20, 20)
        assert pattern.T_ice.shape == (20, 20)
        assert pattern.u.shape == (20, 20)
        assert pattern.v.shape == (20, 20)

    def test_pattern_id(self):
        assert SeaIcePattern.PATTERN_ID == "sea_ice"
        assert SeaIcePattern.PATTERN_VERSION == "6.0.0"

    def test_initial_ice_in_center(self, pattern):
        assert np.sum(pattern.a_ice > 0) > 0
        assert np.sum(pattern.h_ice > 0) > 0

    def test_calculate_albedo(self, pattern):
        albedo = pattern._calculate_albedo()
        assert albedo.shape == (20, 20)
        assert np.all(albedo >= pattern.config.albedo_water)
        assert np.all(albedo <= pattern.config.albedo_ice)

    def test_surface_energy_balance(self, pattern):
        Q_net, T_surf = pattern._surface_energy_balance()
        assert Q_net.shape == (20, 20)
        assert T_surf.shape == (20, 20)
        assert np.all(np.isfinite(Q_net))

    def test_thermodynamics(self, pattern):
        dh_dt, da_dt = pattern._thermodynamics()
        assert dh_dt.shape == (20, 20)
        assert da_dt.shape == (20, 20)
        assert np.all(np.isfinite(dh_dt))
        assert np.all(np.isfinite(da_dt))

    def test_dynamics(self, pattern):
        du_dt, dv_dt = pattern._dynamics()
        assert du_dt.shape == (20, 20)
        assert dv_dt.shape == (20, 20)
        assert np.all(np.isfinite(du_dt))

    def test_advection_bounds(self, pattern):
        h_before = pattern.h_ice.copy()
        pattern._advect_ice()
        assert np.all(pattern.h_ice >= 0)
        assert np.all(pattern.h_ice <= pattern.config.h_max)
        assert np.all(pattern.a_ice >= 0)
        assert np.all(pattern.a_ice <= 1)

    def test_step(self, pattern):
        h_before = pattern.h_ice.copy()
        pattern._step(0)
        assert np.all(pattern.h_ice >= 0)
        assert np.all(pattern.a_ice >= 0)
        assert np.all(pattern.a_ice <= 1)
        assert np.all(pattern.T_ice >= -50)
        assert np.all(pattern.T_ice <= 10)

    def test_forcing_update(self, pattern):
        pattern._update_atmospheric_forcing(0)
        T_winter = pattern.T_atm.copy()
        pattern._update_atmospheric_forcing(180)
        T_summer = pattern.T_atm.copy()
        # Day 0: sin(pi/2) = 1 (peak), day 180: sin(3.7) ~ -0.5 (near minimum)
        assert np.mean(T_winter) > np.mean(T_summer)

    def test_run_short(self):
        config = SeaIceConfig(nx=10, ny=10, days=3, output_interval=1)
        pattern = SeaIcePattern(config)
        result = pattern.run()
        assert "ice_volume" in result
        assert "ice_extent" in result
        assert "final_state" in result
        assert len(result["time_days"]) > 0
        assert "mean_concentration" in result["final_state"]

    def test_metadata(self):
        metadata = SeaIcePattern.get_metadata()
        assert metadata["id"] == "sea_ice"
        assert "parameters" in metadata
        assert len(metadata["assumptions"]) > 0

    def test_edge_case_single_day(self):
        config = SeaIceConfig(nx=10, ny=10, days=2, output_interval=1)
        pattern = SeaIcePattern(config)
        result = pattern.run()
        assert len(result["time_days"]) == 2

    def test_edge_case_no_initial_ice(self):
        config = SeaIceConfig(nx=10, ny=10, days=2)
        pattern = SeaIcePattern(config)
        pattern.a_ice[:] = 0
        pattern.h_ice[:] = 0
        result = pattern.run()
        assert "ice_volume" in result
