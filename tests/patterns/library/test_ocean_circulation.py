"""Tests for ocean_circulation pattern module."""

import numpy as np
import pytest

from src.patterns.library.ocean_circulation import OceanCirculationConfig, OceanCirculationPattern



class TestOceanCirculationConfig:
    def test_default_values(self):
        cfg = OceanCirculationConfig()
        assert cfg.nx == 128
        assert cfg.ny == 64
        assert cfg.nz == 20
        assert cfg.Lx == 5.0e6
        assert cfg.dt == 3600.0

    def test_custom_values(self):
        cfg = OceanCirculationConfig(nx=32, ny=16, nz=5, days=10)
        assert cfg.nx == 32
        assert cfg.days == 10


class TestOceanCirculationPattern:
    @pytest.fixture
    def small_config(self):
        return OceanCirculationConfig(nx=16, ny=8, nz=3, days=1, dt=3600)

    @pytest.fixture
    def pattern(self, small_config):
        return OceanCirculationPattern(small_config)

    def test_init(self, pattern, small_config):
        assert pattern.config == small_config
        assert pattern.u.shape == (15, 8, 3)
        assert pattern.T.shape == (16, 8, 3)
        assert pattern.eta.shape == (16, 8)

    def test_pattern_id(self):
        assert OceanCirculationPattern.PATTERN_ID == "ocean_circulation"
        assert OceanCirculationPattern.PATTERN_VERSION == "6.0.0"

    def test_grid_spacing(self):
        config = OceanCirculationConfig(Lx=1e6, Ly=5e5, nx=51, ny=26)
        pattern = OceanCirculationPattern(config)
        assert pattern.dx == pytest.approx(20000.0, abs=1.0)
        assert pattern.dy == pytest.approx(20000.0, abs=1.0)

    def test_coriolis_parameter(self):
        config = OceanCirculationConfig(f0=1e-4, beta=2e-11, Ly=1e6, ny=8)
        pattern = OceanCirculationPattern(config)
        assert pattern.f[0] != pattern.f[-1]
        mid_idx = len(pattern.f) // 2
        assert pattern.f[mid_idx] == pytest.approx(config.f0, abs=1e-5)

    def test_momentum_tendency_u(self, pattern):
        du_dt = pattern._momentum_tendency_u()
        assert du_dt.shape == pattern.u.shape
        assert np.all(np.isfinite(du_dt))

    def test_momentum_tendency_v(self, pattern):
        dv_dt = pattern._momentum_tendency_v()
        assert dv_dt.shape == pattern.v.shape
        assert np.all(np.isfinite(dv_dt))

    def test_tracer_tendency_T(self, pattern):
        dT_dt = pattern._tracer_tendency_T()
        assert dT_dt.shape == pattern.T.shape
        assert np.all(np.isfinite(dT_dt))

    def test_tracer_tendency_S(self, pattern):
        dS_dt = pattern._tracer_tendency_S()
        assert dS_dt.shape == pattern.S.shape
        assert np.all(np.isfinite(dS_dt))

    def test_pressure_update(self, pattern):
        pattern._update_pressure()
        cfg = pattern.config
        # z[0] = -H (bottom), z[-1] = 0 (surface)
        # Pressure should increase with depth (decrease with k index)
        for j in range(cfg.ny):
            for i in range(cfg.nx):
                p_profile = pattern.p[i, j, :]
                assert np.all(np.diff(p_profile) <= 1e-6)  # Decreases toward surface

    def test_continuity(self, pattern):
        pattern._continuity()
        assert np.allclose(pattern.w[:, :, -1], 0)

    def test_boundary_conditions(self):
        config = OceanCirculationConfig(nx=16, ny=8, nz=3)
        pattern = OceanCirculationPattern(config)
        pattern.u[0, :, :] = 1.0
        pattern.u[-1, :, :] = 1.0
        pattern._apply_boundary_conditions()
        assert np.allclose(pattern.u[0, :, :], 0)
        assert np.allclose(pattern.u[-1, :, :], 0)

    def test_moc_calculation(self, pattern):
        moc = pattern._calculate_moc()
        assert moc.shape == (pattern.config.ny, pattern.config.nz)
        assert np.all(np.isfinite(moc))

    def test_laplacian_h(self, pattern):
        field = np.ones((10, 10))
        lapl = pattern._laplacian_h(field)
        assert lapl.shape == (10, 10)
        assert np.allclose(lapl[1:-1, 1:-1], 0, atol=1e-10)

    def test_step(self, pattern):
        pattern._step()
        assert np.all(np.isfinite(pattern.u))
        assert np.all(np.isfinite(pattern.T))

    def test_run_short(self):
        config = OceanCirculationConfig(nx=8, ny=4, nz=2, days=1, dt=3600, output_interval=1)
        pattern = OceanCirculationPattern(config)
        result = pattern.run()
        assert "mean_surface_temperature" in result
        assert "kinetic_energy" in result
        assert "final_state" in result
        assert len(result["time_days"]) > 0

    def test_metadata(self):
        metadata = OceanCirculationPattern.get_metadata()
        assert metadata["id"] == "ocean_circulation"
        assert "parameters" in metadata
        assert len(metadata["assumptions"]) > 0

    def test_stratification_initialization(self, pattern):
        # z[0] = -H (bottom), z[-1] = 0 (surface), so T[:,:,-1] is surface (warmest)
        assert np.all(pattern.T[:, :, -1] > pattern.T[:, :, 0])
