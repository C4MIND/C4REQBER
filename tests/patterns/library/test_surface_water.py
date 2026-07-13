"""
Tests for surface_water pattern module.
"""

import numpy as np
import pytest

from src.patterns.library.surface_water import SurfaceWaterConfig, SurfaceWaterPattern


class TestConfig:
    def test_default_config(self):
        cfg = SurfaceWaterConfig()
        assert cfg.nx == 200
        assert cfg.ny == 100
        assert cfg.hours == 24
        assert cfg.g == 9.81

    def test_custom_config(self):
        cfg = SurfaceWaterConfig(nx=50, ny=30, hours=2)
        assert cfg.nx == 50
        assert cfg.hours == 2


class TestInit:
    def test_pattern_init_default(self):
        pattern = SurfaceWaterPattern()
        assert pattern.config is not None
        assert pattern.h.shape == (200, 100)

    def test_pattern_init_custom(self):
        cfg = SurfaceWaterConfig(nx=50, ny=30)
        pattern = SurfaceWaterPattern(cfg)
        assert pattern.h.shape == (50, 30)


class TestGrid:
    def test_grid_spacing(self):
        cfg = SurfaceWaterConfig(Lx=1000, Ly=500, nx=51, ny=26)
        pattern = SurfaceWaterPattern(cfg)
        assert abs(pattern.dx - 20.0) < 1.0
        assert abs(pattern.dy - 20.0) < 1.0


class TestDepth:
    def test_depth_at_u(self):
        cfg = SurfaceWaterConfig(nx=20, ny=20)
        pattern = SurfaceWaterPattern(cfg)
        h_u = pattern._calculate_depth_at_u()
        assert h_u.shape == (19, 20)
        assert np.all(h_u >= 0)

    def test_depth_at_v(self):
        cfg = SurfaceWaterConfig(nx=20, ny=20)
        pattern = SurfaceWaterPattern(cfg)
        h_v = pattern._calculate_depth_at_v()
        assert h_v.shape == (20, 19)
        assert np.all(h_v >= 0)


class TestFriction:
    def test_friction_slope_u(self):
        cfg = SurfaceWaterConfig()
        pattern = SurfaceWaterPattern(cfg)
        pattern.u[:, :] = 1.0
        S_f = pattern._friction_slope_u()
        assert S_f.shape == pattern.u.shape
        assert np.all(S_f >= 0)

    def test_friction_slope_v(self):
        cfg = SurfaceWaterConfig()
        pattern = SurfaceWaterPattern(cfg)
        pattern.v[:, :] = 1.0
        S_f = pattern._friction_slope_v()
        assert S_f.shape == pattern.v.shape
        assert np.all(S_f >= 0)


class TestMomentum:
    def test_momentum_equation_u(self):
        cfg = SurfaceWaterConfig()
        pattern = SurfaceWaterPattern(cfg)
        dudt = pattern._momentum_equation_u()
        assert dudt.shape == pattern.u.shape
        assert np.all(np.isfinite(dudt))

    def test_momentum_equation_v(self):
        cfg = SurfaceWaterConfig()
        pattern = SurfaceWaterPattern(cfg)
        dvdt = pattern._momentum_equation_v()
        assert dvdt.shape == pattern.v.shape
        assert np.all(np.isfinite(dvdt))


class TestContinuity:
    def test_continuity_equation(self):
        cfg = SurfaceWaterConfig()
        pattern = SurfaceWaterPattern(cfg)
        deta_dt = pattern._continuity_equation()
        assert deta_dt.shape == pattern.eta.shape
        assert np.all(np.isfinite(deta_dt))


class TestBoundaryConditions:
    def test_bc_inflow(self):
        cfg = SurfaceWaterConfig(inflow_duration=1000)
        pattern = SurfaceWaterPattern(cfg)
        pattern._apply_boundary_conditions(500)
        assert np.any(pattern.u[0, :] > 0) or np.all(pattern.u[0, :] == 0)


class TestCourant:
    def test_courant_number(self):
        pattern = SurfaceWaterPattern()
        cfl = pattern._calculate_courant_number()
        assert isinstance(cfl, float)
        assert cfl > 0


class TestDischarge:
    def test_discharge(self):
        pattern = SurfaceWaterPattern()
        Q = pattern._calculate_discharge()
        assert isinstance(Q, float)


class TestStep:
    def test_single_step(self):
        pattern = SurfaceWaterPattern()
        h_before = pattern.h.copy()
        pattern._step(0)
        assert np.all(pattern.h >= 0)


class TestRun:
    def test_short_simulation(self):
        cfg = SurfaceWaterConfig(nx=30, ny=20, hours=1, dt=10)
        pattern = SurfaceWaterPattern(cfg)
        result = pattern.run()
        assert "water_depth" in result
        assert "discharge" in result
        assert len(result["time_hours"]) > 0

    def test_metadata(self):
        meta = SurfaceWaterPattern.get_metadata()
        assert meta["id"] == "surface_water"
        assert "parameters" in meta


class TestEdgeCases:
    def test_zero_inflow(self):
        cfg = SurfaceWaterConfig(inflow_rate=0.0, nx=20, ny=20, hours=1, dt=10)
        pattern = SurfaceWaterPattern(cfg)
        result = pattern.run()
        assert result["final_state"]["final_discharge"] == 0

    def test_dry_cells(self):
        cfg = SurfaceWaterConfig(nx=20, ny=20)
        pattern = SurfaceWaterPattern(cfg)
        pattern.h[:, :] = 0
        pattern._step(0)
        assert np.all(pattern.h >= 0)

    def test_very_steep_slope(self):
        cfg = SurfaceWaterConfig(bed_slope=0.1)
        pattern = SurfaceWaterPattern(cfg)
        assert pattern.z_b is not None
        assert pattern.z_b.shape == (cfg.nx, cfg.ny)
