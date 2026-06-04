"""Tests for src/patterns/library/ocean_circulation.py"""
from __future__ import annotations

import numpy as np
import pytest

from patterns.library.ocean_circulation import OceanCirculationConfig, OceanCirculationPattern


class TestOceanCirculationConfig:
    def test_defaults(self):
        cfg = OceanCirculationConfig()
        assert cfg.nx == 128
        assert cfg.days == 365
        assert cfg.f0 == 1.0e-4

    def test_custom(self):
        cfg = OceanCirculationConfig(nx=32, days=30)
        assert cfg.nx == 32
        assert cfg.days == 30


class TestOceanCirculationInit:
    def test_init_default(self):
        pattern = OceanCirculationPattern()
        assert pattern.u.shape == (127, 64, 20)
        assert pattern.T.shape == (128, 64, 20)
        assert pattern.eta.shape == (128, 64)

    def test_init_custom(self):
        cfg = OceanCirculationConfig(nx=32, ny=16, nz=5)
        pattern = OceanCirculationPattern(cfg)
        assert pattern.u.shape == (31, 16, 5)
        assert pattern.T.shape == (32, 16, 5)


class TestOceanCirculationGrid:
    def test_grid_spacing(self):
        cfg = OceanCirculationConfig(Lx=1e6, Ly=5e5, nx=51, ny=26)
        pattern = OceanCirculationPattern(cfg)
        assert abs(pattern.dx - 20000.0) < 1.0
        assert abs(pattern.dy - 20000.0) < 1.0

    def test_coriolis_parameter(self):
        cfg = OceanCirculationConfig(f0=1e-4, beta=2e-11, Ly=1e6)
        pattern = OceanCirculationPattern(cfg)
        mid_idx = len(pattern.f) // 2
        assert abs(pattern.f[mid_idx] - cfg.f0) < 1e-5


class TestOceanCirculationForcing:
    def test_wind_stress(self):
        pattern = OceanCirculationPattern()
        assert np.all(np.isfinite(pattern.taux))

    def test_heat_flux(self):
        pattern = OceanCirculationPattern()
        assert np.all(np.isfinite(pattern.Q))


class TestOceanCirculationPressure:
    def test_update_pressure(self):
        pattern = OceanCirculationPattern()
        pattern._update_pressure()
        assert np.all(np.isfinite(pattern.p))


class TestOceanCirculationMomentum:
    def test_momentum_tendency_u_shape(self):
        pattern = OceanCirculationPattern()
        du_dt = pattern._momentum_tendency_u()
        assert du_dt.shape == pattern.u.shape

    def test_momentum_tendency_v_shape(self):
        pattern = OceanCirculationPattern()
        dv_dt = pattern._momentum_tendency_v()
        assert dv_dt.shape == pattern.v.shape


class TestOceanCirculationTracer:
    def test_tracer_tendency_T_shape(self):
        pattern = OceanCirculationPattern()
        dT_dt = pattern._tracer_tendency_T()
        assert dT_dt.shape == pattern.T.shape

    def test_tracer_tendency_S_shape(self):
        pattern = OceanCirculationPattern()
        dS_dt = pattern._tracer_tendency_S()
        assert dS_dt.shape == pattern.S.shape


class TestOceanCirculationLaplacian:
    def test_laplacian_h_shape(self):
        pattern = OceanCirculationPattern()
        field = np.random.randn(pattern.config.nx, pattern.config.ny)
        lapl = pattern._laplacian_h(field)
        assert lapl.shape == field.shape


class TestOceanCirculationContinuity:
    def test_continuity(self):
        pattern = OceanCirculationPattern()
        pattern._continuity()
        assert np.allclose(pattern.w[:, :, -1], 0)


class TestOceanCirculationMOC:
    def test_calculate_moc_shape(self):
        pattern = OceanCirculationPattern()
        moc = pattern._calculate_moc()
        assert moc.shape == (pattern.config.ny, pattern.config.nz)


class TestOceanCirculationBoundaryConditions:
    def test_apply_boundary_conditions(self):
        pattern = OceanCirculationPattern()
        pattern.u[0, :, :] = 1.0
        pattern.u[-1, :, :] = 1.0
        pattern._apply_boundary_conditions()
        assert np.allclose(pattern.u[0, :, :], 0)
        assert np.allclose(pattern.u[-1, :, :], 0)


class TestOceanCirculationStep:
    def test_step_changes_fields(self):
        pattern = OceanCirculationPattern()
        T_before = pattern.T.copy()
        pattern._step()
        assert not np.allclose(pattern.T, T_before)

    def test_step_finite(self):
        pattern = OceanCirculationPattern()
        pattern._step()
        assert np.all(np.isfinite(pattern.T))
        assert np.all(np.isfinite(pattern.u))


class TestOceanCirculationRun:
    def test_short_run(self):
        cfg = OceanCirculationConfig(nx=16, ny=8, nz=3, days=1, dt=3600)
        pattern = OceanCirculationPattern(cfg)
        result = pattern.run()
        assert "mean_surface_temperature" in result
        assert "kinetic_energy" in result
        assert len(result["time_days"]) > 0

    def test_run_output(self):
        cfg = OceanCirculationConfig(nx=16, ny=8, nz=3, days=1, dt=3600)
        pattern = OceanCirculationPattern(cfg)
        result = pattern.run()
        assert "final_state" in result
        assert "overturning" in result


class TestOceanCirculationFormatOutput:
    def test_format_output(self):
        cfg = OceanCirculationConfig(nx=16, ny=8, nz=3)
        pattern = OceanCirculationPattern(cfg)
        pattern.history["T"].append(pattern.T.copy())
        pattern.history["time"].append(0.0)
        pattern.history["ke"].append(0.1)
        pattern.history["moc"].append(np.zeros((8, 3)))
        result = pattern._format_output()
        assert "final_state" in result
        assert "grid" in result


class TestOceanCirculationMetadata:
    def test_get_metadata(self):
        meta = OceanCirculationPattern.get_metadata()
        assert meta["id"] == "ocean_circulation"
        assert "parameters" in meta
        assert len(meta["assumptions"]) > 0
