"""Tests for src/patterns/library/mantle_convection.py"""
from __future__ import annotations

import numpy as np
import pytest

from patterns.library.mantle_convection import MantleConvectionConfig, MantleConvectionPattern


class TestMantleConvectionConfig:
    def test_defaults(self):
        cfg = MantleConvectionConfig()
        assert cfg.nx == 64
        assert cfg.Ra == 1.0e6
        assert cfg.internal_heating == 10.0

    def test_custom(self):
        cfg = MantleConvectionConfig(nx=32, Ra=1e5)
        assert cfg.nx == 32
        assert cfg.Ra == 1e5


class TestMantleConvectionInit:
    def test_init_default(self):
        pattern = MantleConvectionPattern()
        assert pattern.config is not None
        assert pattern.T.shape == (64, 64, 32)

    def test_init_custom(self):
        cfg = MantleConvectionConfig(nx=16, ny=16, nz=8)
        pattern = MantleConvectionPattern(cfg)
        assert pattern.T.shape == (16, 16, 8)
        assert pattern.u.shape == (15, 16, 8)
        assert pattern.w.shape == (16, 16, 7)


class TestMantleConvectionReferenceState:
    def test_reference_state(self):
        pattern = MantleConvectionPattern()
        assert pattern.rho_ref.shape == pattern.T.shape
        assert pattern.T_ref.shape == pattern.T.shape
        assert np.all(pattern.alpha == 1.0)


class TestMantleConvectionViscosity:
    def test_viscosity_shape(self):
        pattern = MantleConvectionPattern()
        eta = pattern._viscosity()
        assert eta.shape == pattern.T.shape
        assert np.all(eta > 0)

    def test_viscosity_depth_dependence(self):
        pattern = MantleConvectionPattern()
        eta = pattern._viscosity()
        assert np.all(np.isfinite(eta))


class TestMantleConvectionBuoyancy:
    def test_buoyancy_shape(self):
        pattern = MantleConvectionPattern()
        B = pattern._buoyancy()
        assert B.shape == pattern.T.shape


class TestMantleConvectionMomentumTendency:
    def test_momentum_tendency_u_shape(self):
        pattern = MantleConvectionPattern()
        dudt = pattern._momentum_tendency_u()
        assert dudt.shape == pattern.u.shape

    def test_momentum_tendency_v_shape(self):
        pattern = MantleConvectionPattern()
        dvdt = pattern._momentum_tendency_v()
        assert dvdt.shape == pattern.v.shape

    def test_momentum_tendency_w_shape(self):
        pattern = MantleConvectionPattern()
        dwdt = pattern._momentum_tendency_w()
        assert dwdt.shape == pattern.w.shape

    def test_momentum_tendency_w_buoyancy(self):
        pattern = MantleConvectionPattern()
        pattern.T[:, :, :] = 0.5
        dwdt = pattern._momentum_tendency_w()
        assert not np.all(dwdt == 0)


class TestMantleConvectionTracerTendency:
    def test_tracer_tendency_T_shape(self):
        cfg = MantleConvectionConfig(nx=8, ny=8, nz=4)
        pattern = MantleConvectionPattern(cfg)
        dTdt = pattern._temperature_tendency()
        assert dTdt.shape == pattern.T.shape


class TestMantleConvectionContinuity:
    def test_continuity_residual_shape(self):
        cfg = MantleConvectionConfig(nx=8, ny=8, nz=4)
        pattern = MantleConvectionPattern(cfg)
        residual = pattern._continuity_residual()
        assert residual.shape == (cfg.nx, cfg.ny, cfg.nz)

    def test_pressure_projection(self):
        cfg = MantleConvectionConfig(nx=8, ny=8, nz=4)
        pattern = MantleConvectionPattern(cfg)
        # Set non-zero velocities to create non-zero residual
        pattern.u[1:-1, 1:-1, :] = 0.1
        pattern.v[1:-1, 1:-1, :] = 0.1
        pattern.w[1:-1, 1:-1, :] = 0.1
        p_before = pattern.p.copy()
        pattern._pressure_projection()
        assert not np.allclose(pattern.p, p_before)


class TestMantleConvectionBoundaryConditions:
    def test_apply_boundary_conditions(self):
        pattern = MantleConvectionPattern()
        pattern.T[:, :, :] = 0.5
        pattern._apply_boundary_conditions()
        assert np.all(pattern.T[:, :, 0] == pattern.config.bottom_temp)
        assert np.all(pattern.T[:, :, -1] == pattern.config.top_temp)
        assert np.all(pattern.u[0, :, :] == 0)
        assert np.all(pattern.w[:, :, 0] == 0)


class TestMantleConvectionNusselt:
    def test_nusselt_number(self):
        pattern = MantleConvectionPattern()
        Nu = pattern._calculate_nusselt_number()
        assert isinstance(Nu, float)
        assert Nu >= 1.0


class TestMantleConvectionDissipation:
    def test_viscous_dissipation(self):
        pattern = MantleConvectionPattern()
        diss = pattern._calculate_viscous_dissipation()
        assert isinstance(diss, float)
        assert diss >= 0


class TestMantleConvectionStep:
    def test_step_changes_temperature(self):
        pattern = MantleConvectionPattern()
        T_before = pattern.T.copy()
        pattern._step()
        assert not np.allclose(pattern.T, T_before)

    def test_step_finite(self):
        pattern = MantleConvectionPattern()
        pattern._step()
        assert np.all(np.isfinite(pattern.T))
        assert np.all(np.isfinite(pattern.u))


class TestMantleConvectionRun:
    def test_short_run(self):
        cfg = MantleConvectionConfig(nx=16, ny=16, nz=8, max_time=0.001, dt=1e-7, output_interval=10)
        pattern = MantleConvectionPattern(cfg)
        result = pattern.run()
        assert "temperature" in result
        assert "nusselt_number" in result
        assert len(result["time"]) > 0

    def test_run_with_history(self):
        cfg = MantleConvectionConfig(nx=16, ny=16, nz=8, max_time=0.0001, dt=1e-7, output_interval=1)
        pattern = MantleConvectionPattern(cfg)
        result = pattern.run()
        assert "final_state" in result
        assert "parameters" in result


class TestMantleConvectionFormatOutput:
    def test_format_output(self):
        cfg = MantleConvectionConfig(nx=16, ny=16, nz=8)
        pattern = MantleConvectionPattern(cfg)
        pattern.history["T"].append(0.5)
        pattern.history["u_rms"].append(0.1)
        pattern.history["time"].append(0.0)
        pattern.history["nusselt"].append(1.0)
        result = pattern._format_output()
        assert "final_state" in result
        assert "grid" in result


class TestMantleConvectionMetadata:
    def test_get_metadata(self):
        meta = MantleConvectionPattern.get_metadata()
        assert meta["id"] == "mantle_convection"
        assert "parameters" in meta
