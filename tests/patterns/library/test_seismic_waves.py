"""
Tests for seismic_waves pattern module.
"""

import numpy as np
import pytest

from src.patterns.library.seismic_waves import SeismicWavesConfig, SeismicWavesPattern


class TestConfig:
    def test_default_config(self):
        cfg = SeismicWavesConfig()
        assert cfg.nx == 100
        assert cfg.ny == 100
        assert cfg.nz == 50
        assert cfg.ngll == 4
        assert cfg.dt == 0.001
        assert cfg.duration == 20.0

    def test_custom_config(self):
        cfg = SeismicWavesConfig(nx=20, ny=20, nz=10, duration=1.0)
        assert cfg.nx == 20
        assert cfg.duration == 1.0


class TestInit:
    def test_pattern_init_default(self):
        pattern = SeismicWavesPattern()
        assert pattern.config is not None
        assert pattern.ux is not None
        assert pattern.vp is not None

    def test_pattern_init_custom_grid(self):
        cfg = SeismicWavesConfig(nx=20, ny=20, nz=10, ngll=3)
        pattern = SeismicWavesPattern(cfg)
        assert pattern.nx_total == 20 * (3 - 1) + 1


class TestGLL:
    def test_gll_points_n2(self):
        cfg = SeismicWavesConfig(ngll=2)
        pattern = SeismicWavesPattern(cfg)
        xi, w = pattern._gll_points(2)
        assert len(xi) == 2
        assert len(w) == 2
        assert xi[0] == -1.0
        assert xi[-1] == 1.0

    def test_gll_points_n4(self):
        cfg = SeismicWavesConfig(ngll=4)
        pattern = SeismicWavesPattern(cfg)
        xi, w = pattern._gll_points(4)
        assert len(xi) == 4
        assert len(w) == 4
        assert np.isclose(xi[0], -1.0)
        assert np.isclose(xi[-1], 1.0)

    def test_gll_points_n5(self):
        cfg = SeismicWavesConfig(ngll=5)
        pattern = SeismicWavesPattern(cfg)
        xi, w = pattern._gll_points(5)
        assert len(xi) == 5
        assert np.isclose(sum(w), 2.0, atol=0.1)


class TestSource:
    def test_source_time_function_zero(self):
        pattern = SeismicWavesPattern()
        stf = pattern._source_time_function(0.0)
        assert stf == 0.0

    def test_source_time_function_peak(self):
        pattern = SeismicWavesPattern()
        stf = pattern._source_time_function(0.5)
        assert stf != 0.0

    def test_source_time_function_late(self):
        pattern = SeismicWavesPattern()
        stf = pattern._source_time_function(5.0)
        assert abs(stf) < 0.01


class TestStrainStress:
    def test_strain_tensor_shape(self):
        cfg = SeismicWavesConfig(nx=10, ny=10, nz=5)
        pattern = SeismicWavesPattern(cfg)
        pattern.ux[:, :, :] = 1.0
        exx, eyy, ezz, exy, exz, eyz = pattern._strain_tensor()
        assert exx.shape == pattern.ux.shape

    def test_stress_tensor_shape(self):
        cfg = SeismicWavesConfig(nx=10, ny=10, nz=5)
        pattern = SeismicWavesPattern(cfg)
        sxx, syy, szz, sxy, sxz, syz = pattern._stress_tensor()
        assert sxx.shape == pattern.ux.shape


class TestAbsorbing:
    def test_absorbing_boundary(self):
        cfg = SeismicWavesConfig(abs_width=100)
        pattern = SeismicWavesPattern(cfg)
        field = np.ones_like(pattern.ux)
        damped = pattern._absorbing_boundary(field)
        assert np.mean(damped[0, :, :]) < 1.0


class TestEnergy:
    def test_cfl(self):
        pattern = SeismicWavesPattern()
        cfl = pattern._calculate_cfl()
        assert isinstance(cfl, float)
        assert cfl > 0

    def test_energy(self):
        pattern = SeismicWavesPattern()
        pattern.vx[:, :, :] = 1.0
        ke = pattern._calculate_energy()
        assert isinstance(ke, float)
        assert ke > 0


class TestStep:
    def test_single_step(self):
        pattern = SeismicWavesPattern()
        pattern._step(0.1)
        assert np.all(np.isfinite(pattern.ux))
        assert np.all(np.isfinite(pattern.vx))


class TestRun:
    def test_short_simulation(self):
        cfg = SeismicWavesConfig(nx=15, ny=15, nz=8, duration=0.1, dt=0.001, output_interval=50)
        pattern = SeismicWavesPattern(cfg)
        result = pattern.run()
        assert "time" in result
        assert "seismograms" in result
        assert len(result["time"]) > 0

    def test_metadata(self):
        meta = SeismicWavesPattern.get_metadata()
        assert meta["id"] == "seismic_waves"
        assert "parameters" in meta


class TestEdgeCases:
    def test_zero_velocity(self):
        cfg = SeismicWavesConfig(vp_surf=0.0)
        pattern = SeismicWavesPattern(cfg)
        assert np.all(pattern.vp >= 0)

    def test_very_small_grid(self):
        cfg = SeismicWavesConfig(nx=5, ny=5, nz=3, ngll=2)
        pattern = SeismicWavesPattern(cfg)
        assert pattern.ux.shape == (pattern.nx_total, pattern.ny_total, pattern.nz_total)
