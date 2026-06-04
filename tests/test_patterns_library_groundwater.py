"""Tests for src/patterns/library/groundwater.py"""
from __future__ import annotations

import numpy as np
import pytest

from patterns.library.groundwater import GroundwaterConfig, GroundwaterPattern


class TestGroundwaterConfig:
    def test_defaults(self):
        cfg = GroundwaterConfig()
        assert cfg.nx == 50
        assert cfg.K_s == 1.0e-4
        assert cfg.alpha == 0.036

    def test_custom(self):
        cfg = GroundwaterConfig(nx=20, K_s=1e-3)
        assert cfg.nx == 20
        assert cfg.K_s == 1e-3


class TestGroundwaterInit:
    def test_init_default(self):
        pattern = GroundwaterPattern()
        assert pattern.h.shape == (50, 50, 20)
        assert pattern.theta.shape == pattern.h.shape
        assert pattern.K.shape == pattern.h.shape

    def test_init_custom(self):
        cfg = GroundwaterConfig(nx=20, ny=20, nz=10)
        pattern = GroundwaterPattern(cfg)
        assert pattern.h.shape == (20, 20, 10)

    def test_initial_hydrostatic(self):
        pattern = GroundwaterPattern()
        assert np.all(np.isfinite(pattern.h))


class TestGroundwaterEffectiveSaturation:
    def test_effective_saturation_saturated(self):
        pattern = GroundwaterPattern()
        h_test = np.array([0, 1, 10])
        Se = pattern._effective_saturation(h_test)
        assert np.all(Se == 1.0)

    def test_effective_saturation_unsaturated(self):
        pattern = GroundwaterPattern()
        h_test = np.array([-100, -10, -1])
        Se = pattern._effective_saturation(h_test)
        assert np.all(np.diff(Se) > 0)


class TestGroundwaterWaterContent:
    def test_update_water_content(self):
        pattern = GroundwaterPattern()
        pattern._update_water_content()
        assert np.all(pattern.theta >= pattern.config.theta_r)
        assert np.all(pattern.theta <= pattern.config.theta_s)


class TestGroundwaterHydraulicConductivity:
    def test_update_hydraulic_conductivity(self):
        pattern = GroundwaterPattern()
        pattern._update_hydraulic_conductivity()
        assert np.all(pattern.K >= 0)
        assert np.all(pattern.K <= pattern.config.K_s)

    def test_K_saturated(self):
        pattern = GroundwaterPattern()
        pattern.h[:, :, :] = 1.0
        pattern._update_hydraulic_conductivity()
        assert np.all(pattern.K == pattern.config.K_s)


class TestGroundwaterWaterCapacity:
    def test_water_capacity_unsaturated(self):
        pattern = GroundwaterPattern()
        h_test = np.array([-10, -5, -1])
        C = pattern._water_capacity(h_test)
        assert np.all(C >= 0)

    def test_water_capacity_saturated(self):
        pattern = GroundwaterPattern()
        h_test = np.array([0, 1, 10])
        C = pattern._water_capacity(h_test)
        assert np.all(C == 0)


class TestGroundwaterDarcyFlux:
    def test_darcy_flux_x_shape(self):
        pattern = GroundwaterPattern()
        qx = pattern._darcy_flux_x()
        assert qx.shape == pattern.h.shape

    def test_darcy_flux_y_shape(self):
        pattern = GroundwaterPattern()
        qy = pattern._darcy_flux_y()
        assert qy.shape == pattern.h.shape

    def test_darcy_flux_z_shape(self):
        pattern = GroundwaterPattern()
        qz = pattern._darcy_flux_z()
        assert qz.shape == pattern.h.shape


class TestGroundwaterRichardsTendency:
    def test_richards_tendency_shape(self):
        pattern = GroundwaterPattern()
        rhs = pattern._richards_tendency(0)
        assert rhs.shape == pattern.h.shape

    def test_richards_tendency_with_pumping(self):
        pattern = GroundwaterPattern()
        rhs = pattern._richards_tendency(86400 * 10)
        assert np.all(np.isfinite(rhs))


class TestGroundwaterBoundaryConditions:
    def test_apply_boundary_conditions(self):
        pattern = GroundwaterPattern()
        pattern.h[:, :, :] = 1.0
        pattern._apply_boundary_conditions()
        assert np.allclose(pattern.h[0, :, :], pattern.h[1, :, :])


class TestGroundwaterWaterTable:
    def test_calculate_water_table_shape(self):
        pattern = GroundwaterPattern()
        wt = pattern._calculate_water_table()
        assert wt.shape == (pattern.config.nx, pattern.config.ny)
        assert np.all(wt >= 0)


class TestGroundwaterStorage:
    def test_calculate_storage(self):
        pattern = GroundwaterPattern()
        storage = pattern._calculate_storage()
        assert isinstance(storage, float)
        assert storage > 0


class TestGroundwaterDrawdown:
    def test_calculate_drawdown(self):
        pattern = GroundwaterPattern()
        drawdown = pattern._calculate_drawdown()
        assert isinstance(drawdown, float)
        assert drawdown >= 0


class TestGroundwaterStep:
    def test_step_finite(self):
        pattern = GroundwaterPattern()
        pattern._step(0)
        assert np.all(np.isfinite(pattern.h))


class TestGroundwaterRun:
    def test_short_run(self):
        cfg = GroundwaterConfig(nx=15, ny=15, nz=5, days=1, dt=1000)
        pattern = GroundwaterPattern(cfg)
        result = pattern.run()
        assert "water_content" in result
        assert "water_table" in result
        assert len(result["time_days"]) > 0

    def test_run_output(self):
        cfg = GroundwaterConfig(nx=15, ny=15, nz=5, days=1, dt=1000)
        pattern = GroundwaterPattern(cfg)
        result = pattern.run()
        assert "final_state" in result
        assert "hydraulics" in result


class TestGroundwaterFormatOutput:
    def test_format_output(self):
        cfg = GroundwaterConfig(nx=15, ny=15, nz=5)
        pattern = GroundwaterPattern(cfg)
        pattern.history["h"].append(-5.0)
        pattern.history["theta"].append(0.3)
        pattern.history["time"].append(0.0)
        pattern.history["storage"].append(1e6)
        pattern.history["drawdown"].append(0.5)
        result = pattern._format_output()
        assert "final_state" in result
        assert "saturated_fraction" in result["final_state"]


class TestGroundwaterMetadata:
    def test_get_metadata(self):
        meta = GroundwaterPattern.get_metadata()
        assert meta["id"] == "groundwater"
        assert "parameters" in meta
