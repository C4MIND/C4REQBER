"""Tests for src/patterns/library/seismic_waves.py"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from patterns.library.seismic_waves import SeismicWavesConfig, SeismicWavesPattern


class TestSeismicWavesConfig:
    def test_defaults(self):
        cfg = SeismicWavesConfig()
        assert cfg.nx == 100
        assert cfg.ny == 100
        assert cfg.nz == 50
        assert cfg.ngll == 4
        assert cfg.duration == 20.0

    def test_custom(self):
        cfg = SeismicWavesConfig(nx=50, ny=50, nz=20, duration=5.0)
        assert cfg.nx == 50
        assert cfg.ny == 50
        assert cfg.nz == 20
        assert cfg.duration == 5.0


class TestSeismicWavesPatternInit:
    def test_init_default(self):
        pattern = SeismicWavesPattern()
        assert pattern.config is not None
        assert pattern.ux.shape == (pattern.nx_total, pattern.ny_total, pattern.nz_total)
        assert pattern.vp.shape == pattern.ux.shape

    def test_init_custom(self):
        cfg = SeismicWavesConfig(nx=20, ny=20, nz=10, ngll=3)
        pattern = SeismicWavesPattern(cfg)
        assert pattern.ux.shape == (pattern.nx_total, pattern.ny_total, pattern.nz_total)


class TestSeismicWavesGLL:
    def test_gll_points_n2(self):
        pattern = SeismicWavesPattern()
        xi, w = pattern._gll_points(2)
        assert len(xi) == 2
        assert len(w) == 2

    def test_gll_points_n3(self):
        pattern = SeismicWavesPattern()
        xi, w = pattern._gll_points(3)
        assert len(xi) == 3
        assert len(w) == 3

    def test_gll_points_n4(self):
        pattern = SeismicWavesPattern()
        xi, w = pattern._gll_points(4)
        assert len(xi) == 4
        assert len(w) == 4

    def test_gll_points_n5(self):
        pattern = SeismicWavesPattern()
        xi, w = pattern._gll_points(5)
        assert len(xi) == 5
        assert len(w) == 5

    def test_gll_points_default(self):
        pattern = SeismicWavesPattern()
        xi, w = pattern._gll_points(10)
        assert len(xi) == 4
        assert len(w) == 10


class TestSeismicWavesLagrange:
    def test_lagrange_derivative(self):
        pattern = SeismicWavesPattern()
        xi = np.array([-1.0, 0.0, 1.0])
        dL = pattern._lagrange_derivative(xi, 0, 0.0)
        assert isinstance(dL, float)


class TestSeismicWavesSource:
    def test_source_time_function_zero(self):
        pattern = SeismicWavesPattern()
        stf = pattern._source_time_function(0)
        assert stf == 0.0

    def test_source_time_function_peak(self):
        pattern = SeismicWavesPattern()
        stf = pattern._source_time_function(0.5)
        assert stf != 0.0

    def test_source_time_function_late(self):
        pattern = SeismicWavesPattern()
        stf = pattern._source_time_function(10.0)
        assert abs(stf) < 1e-3


class TestSeismicWavesStrain:
    def test_strain_tensor_shape(self):
        cfg = SeismicWavesConfig(nx=10, ny=10, nz=5)
        pattern = SeismicWavesPattern(cfg)
        pattern.ux[:, :, :] = 1.0
        exx, eyy, ezz, exy, exz, eyz = pattern._strain_tensor()
        assert exx.shape == pattern.ux.shape
        assert np.all(np.isfinite(exx))

    def test_strain_tensor_zero(self):
        cfg = SeismicWavesConfig(nx=10, ny=10, nz=5)
        pattern = SeismicWavesPattern(cfg)
        exx, eyy, ezz, exy, exz, eyz = pattern._strain_tensor()
        assert np.all(exx == 0)
        assert np.all(eyy == 0)


class TestSeismicWavesStress:
    def test_stress_tensor_shape(self):
        cfg = SeismicWavesConfig(nx=10, ny=10, nz=5)
        pattern = SeismicWavesPattern(cfg)
        sxx, syy, szz, sxy, sxz, syz = pattern._stress_tensor()
        assert sxx.shape == pattern.ux.shape
        assert np.all(np.isfinite(sxx))


class TestSeismicWavesInternalForces:
    def test_internal_forces_shape(self):
        cfg = SeismicWavesConfig(nx=10, ny=10, nz=5)
        pattern = SeismicWavesPattern(cfg)
        fx, fy, fz = pattern._internal_forces()
        assert fx.shape == pattern.ux.shape
        assert np.all(np.isfinite(fx))


class TestSeismicWavesAbsorbing:
    def test_absorbing_boundary_damps(self):
        cfg = SeismicWavesConfig(abs_width=100)
        pattern = SeismicWavesPattern(cfg)
        field = np.ones_like(pattern.ux)
        damped = pattern._absorbing_boundary(field)
        assert np.mean(damped[0, :, :]) < 1.0
        assert np.mean(damped[-1, :, :]) < 1.0

    def test_absorbing_boundary_bottom(self):
        cfg = SeismicWavesConfig(abs_width=100)
        pattern = SeismicWavesPattern(cfg)
        field = np.ones_like(pattern.ux)
        damped = pattern._absorbing_boundary(field)
        assert np.mean(damped[:, :, 0]) < 1.0


class TestSeismicWavesCFL:
    def test_cfl_calculation(self):
        pattern = SeismicWavesPattern()
        cfl = pattern._calculate_cfl()
        assert isinstance(cfl, float)
        assert cfl > 0


class TestSeismicWavesEnergy:
    def test_energy_zero_velocity(self):
        pattern = SeismicWavesPattern()
        ke = pattern._calculate_energy()
        assert ke == 0.0

    def test_energy_nonzero(self):
        pattern = SeismicWavesPattern()
        pattern.vx[:, :, :] = 1.0
        ke = pattern._calculate_energy()
        assert ke > 0


class TestSeismicWavesStep:
    def test_step_updates_fields(self):
        pattern = SeismicWavesPattern()
        before_ux = pattern.ux.copy()
        pattern._step(0.1)
        assert not np.allclose(pattern.ux, before_ux)

    def test_step_finite(self):
        pattern = SeismicWavesPattern()
        pattern._step(0.1)
        assert np.all(np.isfinite(pattern.ux))
        assert np.all(np.isfinite(pattern.vx))


class TestSeismicWavesRun:
    def test_short_run(self):
        cfg = SeismicWavesConfig(nx=15, ny=15, nz=8, duration=0.1, dt=0.001, output_interval=50)
        pattern = SeismicWavesPattern(cfg)
        with patch("src.simulations.newton_bridge.NewtonBridge") as mock_cls:
            mock_bridge = MagicMock()
            mock_bridge.available = False
            mock_cls.return_value = mock_bridge
            result = pattern.run()
        assert "time" in result
        assert "seismograms" in result
        assert "final_state" in result

    def test_run_with_newton_bridge(self):
        cfg = SeismicWavesConfig(nx=15, ny=15, nz=8, duration=0.1, dt=0.001, output_interval=50)
        pattern = SeismicWavesPattern(cfg)
        with patch("src.simulations.newton_bridge.NewtonBridge") as mock_cls:
            mock_bridge = MagicMock()
            mock_bridge.available = True
            mock_bridge.run_simulation = MagicMock(return_value={"status": "success", "data": []})
            mock_cls.return_value = mock_bridge
            result = pattern.run()
            assert result.get("status") == "success"

    def test_run_with_newton_bridge_fallback(self):
        cfg = SeismicWavesConfig(nx=15, ny=15, nz=8, duration=0.1, dt=0.001, output_interval=50)
        pattern = SeismicWavesPattern(cfg)
        with patch("src.simulations.newton_bridge.NewtonBridge") as mock_cls:
            mock_bridge = MagicMock()
            mock_bridge.available = True
            mock_bridge.run_simulation = MagicMock(return_value={"status": "error"})
            mock_cls.return_value = mock_bridge
            result = pattern.run()
            assert "time" in result

    def test_run_no_newton(self):
        cfg = SeismicWavesConfig(nx=15, ny=15, nz=8, duration=0.1, dt=0.001, output_interval=50)
        pattern = SeismicWavesPattern(cfg)
        with patch("src.simulations.newton_bridge.NewtonBridge") as mock_cls:
            mock_bridge = MagicMock()
            mock_bridge.available = False
            mock_cls.return_value = mock_bridge
            result = pattern.run()
            assert "time" in result


class TestSeismicWavesFormatOutput:
    def test_format_output(self):
        cfg = SeismicWavesConfig(nx=15, ny=15, nz=8, duration=0.1, dt=0.001, output_interval=50)
        pattern = SeismicWavesPattern(cfg)
        pattern.history["time"].append(0.0)
        pattern.history["max_displacement"].append(0.0)
        pattern.history["kinetic_energy"].append(0.0)
        result = pattern._format_output()
        assert "materials" in result
        assert "grid" in result
        assert "config" in result
        assert "final_state" in result


class TestSeismicWavesMetadata:
    def test_get_metadata(self):
        meta = SeismicWavesPattern.get_metadata()
        assert meta["id"] == "seismic_waves"
        assert "parameters" in meta
        assert "assumptions" in meta


class TestSeismicWavesReceivers:
    def test_receivers_created(self):
        cfg = SeismicWavesConfig(n_receivers=5)
        pattern = SeismicWavesPattern(cfg)
        assert len(pattern.receivers) == 5
        assert len(pattern.seismograms["ux"]) == 5

    def test_seismograms_recorded(self):
        cfg = SeismicWavesConfig(n_receivers=3)
        pattern = SeismicWavesPattern(cfg)
        pattern._step(0.1)
        for i in range(3):
            assert len(pattern.seismograms["ux"][i]) == 1
