"""Tests for groundwater pattern module."""

import numpy as np
import pytest

from src.patterns.library.groundwater import GroundwaterConfig, GroundwaterPattern


class TestGroundwaterConfig:
    def test_default_values(self):
        cfg = GroundwaterConfig()
        assert cfg.nx == 50
        assert cfg.ny == 50
        assert cfg.nz == 20
        assert cfg.Lx == 1000.0
        assert cfg.K_s == 1.0e-4
        assert cfg.water_table_depth == 5.0

    def test_custom_values(self):
        cfg = GroundwaterConfig(nx=20, ny=20, nz=10, days=10)
        assert cfg.nx == 20
        assert cfg.days == 10


class TestGroundwaterPattern:
    @pytest.fixture
    def small_config(self):
        return GroundwaterConfig(nx=15, ny=15, nz=5, days=2, dt=1000)

    @pytest.fixture
    def pattern(self, small_config):
        return GroundwaterPattern(small_config)

    def test_init(self, pattern, small_config):
        assert pattern.config == small_config
        assert pattern.h.shape == (15, 15, 5)
        assert pattern.theta.shape == (15, 15, 5)
        assert pattern.K.shape == (15, 15, 5)

    def test_pattern_id(self):
        assert GroundwaterPattern.PATTERN_ID == "groundwater"
        assert GroundwaterPattern.PATTERN_VERSION == "6.0.0"

    def test_effective_saturation(self, pattern):
        h_test = np.array([-100, -10, -1, 0, 1])
        Se = pattern._effective_saturation(h_test)
        assert Se[3] == 1.0
        assert Se[4] == 1.0
        assert np.all(np.diff(Se[:3]) > 0)
        assert np.all(Se >= 0)
        assert np.all(Se <= 1)

    def test_water_content_update(self, pattern):
        pattern._update_water_content()
        assert np.all(pattern.theta >= pattern.config.theta_r)
        assert np.all(pattern.theta <= pattern.config.theta_s)

    def test_hydraulic_conductivity(self, pattern):
        pattern._update_hydraulic_conductivity()
        assert np.all(pattern.K >= 0)
        assert np.all(pattern.K <= pattern.config.K_s)

    def test_water_capacity(self, pattern):
        h_test = np.array([-10, -5, -1])
        C = pattern._water_capacity(h_test)
        assert np.all(C >= 0)

    def test_darcy_flux_x(self, pattern):
        qx = pattern._darcy_flux_x()
        assert qx.shape == pattern.h.shape
        assert np.all(np.isfinite(qx))

    def test_darcy_flux_y(self, pattern):
        qy = pattern._darcy_flux_y()
        assert qy.shape == pattern.h.shape
        assert np.all(np.isfinite(qy))

    def test_darcy_flux_z(self, pattern):
        qz = pattern._darcy_flux_z()
        assert qz.shape == pattern.h.shape
        assert np.all(np.isfinite(qz))

    def test_richards_tendency(self, pattern):
        rhs = pattern._richards_tendency(0)
        assert rhs.shape == pattern.h.shape
        assert np.all(np.isfinite(rhs))

    def test_water_table(self, pattern):
        wt = pattern._calculate_water_table()
        assert wt.shape == (pattern.config.nx, pattern.config.ny)
        assert np.all(wt >= 0)

    def test_storage(self, pattern):
        storage = pattern._calculate_storage()
        assert isinstance(storage, float)
        assert storage > 0

    def test_drawdown(self, pattern):
        drawdown = pattern._calculate_drawdown()
        assert isinstance(drawdown, float)
        assert drawdown >= 0

    def test_step(self, pattern):
        h_before = pattern.h.copy()
        pattern._step(0)
        assert np.all(np.isfinite(pattern.h))

    def test_boundary_conditions(self, pattern):
        pattern.h[0, :, :] = 10.0
        pattern.h[-1, :, :] = -10.0
        pattern._apply_boundary_conditions()
        assert np.allclose(pattern.h[0, :, :], pattern.h[1, :, :])
        assert np.allclose(pattern.h[-1, :, :], pattern.h[-2, :, :])

    def test_run_short(self):
        config = GroundwaterConfig(nx=10, ny=10, nz=3, days=1, dt=1000, output_interval=1)
        pattern = GroundwaterPattern(config)
        result = pattern.run()
        assert "pressure_head" in result
        assert "water_content" in result
        assert "water_table" in result
        assert "storage" in result
        assert "drawdown" in result
        assert len(result["time_days"]) > 0
        assert "final_state" in result
        assert "saturated_fraction" in result["final_state"]

    def test_metadata(self):
        metadata = GroundwaterPattern.get_metadata()
        assert metadata["id"] == "groundwater"
        assert "parameters" in metadata
        assert len(metadata["assumptions"]) > 0

    def test_pumping_effect(self):
        config = GroundwaterConfig(
            nx=10,
            ny=10,
            nz=3,
            days=2,
            dt=1000,
            pumping_start=0,
            pumping_duration=2,
            pumping_rate=0.1,
        )
        pattern = GroundwaterPattern(config)
        result = pattern.run()
        assert result["final_state"]["final_drawdown"] > 0

    def test_recharge_effect(self):
        config = GroundwaterConfig(nx=10, ny=10, nz=3, days=2, dt=1000, recharge_rate=1.0e-6)
        pattern = GroundwaterPattern(config)
        result = pattern.run()
        assert result["final_state"]["total_storage"] > 0
