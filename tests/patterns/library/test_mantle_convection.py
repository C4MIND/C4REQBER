"""
Tests for mantle_convection pattern module.
"""
import numpy as np
import pytest

from src.patterns.library.mantle_convection import MantleConvectionConfig, MantleConvectionPattern



class TestConfig:
    def test_default_config(self):
        cfg = MantleConvectionConfig()
        assert cfg.nx == 64
        assert cfg.ny == 64
        assert cfg.nz == 32
        assert cfg.Ra == 1.0e6

    def test_custom_config(self):
        cfg = MantleConvectionConfig(nx=32, ny=32, nz=16)
        assert cfg.nx == 32


class TestInit:
    def test_pattern_init_default(self):
        pattern = MantleConvectionPattern()
        assert pattern.config is not None
        assert pattern.T is not None

    def test_pattern_init_custom(self):
        cfg = MantleConvectionConfig(nx=32, ny=32, nz=16)
        pattern = MantleConvectionPattern(cfg)
        assert pattern.T.shape == (32, 32, 16)


class TestViscosity:
    def test_viscosity_shape(self):
        pattern = MantleConvectionPattern()
        eta = pattern._viscosity()
        assert eta.shape == pattern.T.shape
        assert np.all(eta > 0)


class TestBuoyancy:
    def test_buoyancy_shape(self):
        pattern = MantleConvectionPattern()
        B = pattern._buoyancy()
        assert B.shape == pattern.T.shape
        assert np.all(np.isfinite(B))


class TestMomentum:
    def test_momentum_tendency_u(self):
        pattern = MantleConvectionPattern()
        dudt = pattern._momentum_tendency_u()
        assert dudt.shape == pattern.u.shape

    def test_momentum_tendency_v(self):
        pattern = MantleConvectionPattern()
        dvdt = pattern._momentum_tendency_v()
        assert dvdt.shape == pattern.v.shape

    def test_momentum_tendency_w(self):
        pattern = MantleConvectionPattern()
        dwdt = pattern._momentum_tendency_w()
        assert dwdt.shape == pattern.w.shape


class TestTemperature:
    def test_temperature_tendency(self):
        pattern = MantleConvectionPattern()
        dTdt = pattern._temperature_tendency()
        assert dTdt.shape == pattern.T.shape
        assert np.all(np.isfinite(dTdt))


class TestContinuity:
    def test_continuity_residual(self):
        pattern = MantleConvectionPattern()
        residual = pattern._continuity_residual()
        assert residual.shape == (pattern.config.nx, pattern.config.ny, pattern.config.nz)


class TestNusselt:
    def test_nusselt_number(self):
        pattern = MantleConvectionPattern()
        Nu = pattern._calculate_nusselt_number()
        assert isinstance(Nu, float)
        assert Nu >= 1.0

    def test_viscous_dissipation(self):
        pattern = MantleConvectionPattern()
        diss = pattern._calculate_viscous_dissipation()
        assert isinstance(diss, float)
        assert diss >= 0


class TestStep:
    def test_single_step(self):
        pattern = MantleConvectionPattern()
        T_before = pattern.T.copy()
        pattern._step()
        assert not np.allclose(pattern.T, T_before)


class TestBoundaryConditions:
    def test_bc_temperature(self):
        pattern = MantleConvectionPattern()
        pattern.T[:, :, :] = 0.5
        pattern._apply_boundary_conditions()
        assert np.all(pattern.T[:, :, 0] == pattern.config.bottom_temp)
        assert np.all(pattern.T[:, :, -1] == pattern.config.top_temp)


class TestRun:
    def test_short_simulation(self):
        cfg = MantleConvectionConfig(
            nx=16, ny=16, nz=8, max_time=0.001, dt=1e-7, output_interval=10
        )
        pattern = MantleConvectionPattern(cfg)
        result = pattern.run()
        assert "temperature" in result
        assert "nusselt_number" in result
        assert len(result["time"]) > 0

    def test_metadata(self):
        meta = MantleConvectionPattern.get_metadata()
        assert meta["id"] == "mantle_convection"
        assert "parameters" in meta


class TestEdgeCases:
    def test_zero_velocity_kinetic_energy(self):
        pattern = MantleConvectionPattern()
        pattern.u[:, :, :] = 0
        pattern.v[:, :, :] = 0
        pattern.w[:, :, :] = 0
        diss = pattern._calculate_viscous_dissipation()
        assert diss == 0

    def test_pressure_projection(self):
        pattern = MantleConvectionPattern()
        pattern._pressure_projection()
        assert np.all(np.isfinite(pattern.p))

    def test_small_grid(self):
        cfg = MantleConvectionConfig(nx=8, ny=8, nz=4, max_time=0.0001, dt=1e-7)
        pattern = MantleConvectionPattern(cfg)
        result = pattern.run()
        assert "final_state" in result
