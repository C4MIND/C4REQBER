"""Extended tests for src/patterns/library/seismic_waves.py - covering missed paths"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from patterns.library.seismic_waves import SeismicWavesConfig, SeismicWavesPattern


class TestSeismicWavesSourceExtended:
    def test_source_time_function_negative_time(self):
        pattern = SeismicWavesPattern()
        stf = pattern._source_time_function(-1.0)
        assert stf == 0.0

    def test_source_time_function_zero_time(self):
        pattern = SeismicWavesPattern()
        stf = pattern._source_time_function(0.0)
        assert stf == 0.0


class TestSeismicWavesStepExtended:
    def test_step_with_source(self):
        cfg = SeismicWavesConfig(nx=10, ny=10, nz=5)
        pattern = SeismicWavesPattern(cfg)
        pattern._step(0.1)
        assert np.all(np.isfinite(pattern.ux))

    def test_step_with_source_active(self):
        cfg = SeismicWavesConfig(nx=10, ny=10, nz=5)
        pattern = SeismicWavesPattern(cfg)
        pattern._step(5.0)
        assert np.all(np.isfinite(pattern.ux))


class TestSeismicWavesRunExtended:
    def test_run_fallback_no_newton(self):
        cfg = SeismicWavesConfig(nx=15, ny=15, nz=8, duration=0.1, dt=0.001, output_interval=50)
        pattern = SeismicWavesPattern(cfg)
        with patch("src.simulations.newton_bridge.NewtonBridge") as mock_cls:
            mock_bridge = MagicMock()
            mock_bridge.available = False
            mock_cls.return_value = mock_bridge
            result = pattern.run()
        assert "time" in result
        assert "max_displacement" in result

    def test_run_with_newton_success(self):
        cfg = SeismicWavesConfig(nx=15, ny=15, nz=8, duration=0.1, dt=0.001, output_interval=50)
        pattern = SeismicWavesPattern(cfg)
        with patch("src.simulations.newton_bridge.NewtonBridge") as mock_cls:
            mock_bridge = MagicMock()
            mock_bridge.available = True
            mock_bridge.run_simulation.return_value = {"status": "success", "data": []}
            mock_cls.return_value = mock_bridge
            result = pattern.run()
            assert result.get("status") == "success"

    def test_run_with_newton_error_fallback(self):
        cfg = SeismicWavesConfig(nx=15, ny=15, nz=8, duration=0.1, dt=0.001, output_interval=50)
        pattern = SeismicWavesPattern(cfg)
        with patch("src.simulations.newton_bridge.NewtonBridge") as mock_cls:
            mock_bridge = MagicMock()
            mock_bridge.available = True
            mock_bridge.run_simulation.return_value = {"status": "error"}
            mock_cls.return_value = mock_bridge
            result = pattern.run()
            assert "time" in result

    def test_run_with_hypothesis(self):
        cfg = SeismicWavesConfig(nx=15, ny=15, nz=8, duration=0.1, dt=0.001, output_interval=50)
        pattern = SeismicWavesPattern(cfg)
        with patch("src.simulations.newton_bridge.NewtonBridge") as mock_cls:
            mock_bridge = MagicMock()
            mock_bridge.available = False
            mock_cls.return_value = mock_bridge
            result = pattern.run(hypothesis={"test": "value"})
            assert "time" in result


class TestSeismicWavesCFLExtended:
    def test_cfl_positive(self):
        pattern = SeismicWavesPattern()
        cfl = pattern._calculate_cfl()
        assert cfl > 0


class TestSeismicWavesEnergyExtended:
    def test_energy_with_velocity(self):
        pattern = SeismicWavesPattern()
        pattern.vx[:, :, :] = 1.0
        pattern.vy[:, :, :] = 2.0
        pattern.vz[:, :, :] = 3.0
        ke = pattern._calculate_energy()
        assert ke > 0


class TestSeismicWavesFormatOutputExtended:
    def test_format_output_empty_history(self):
        cfg = SeismicWavesConfig(nx=15, ny=15, nz=8)
        pattern = SeismicWavesPattern(cfg)
        result = pattern._format_output()
        assert "time" in result
        assert "final_state" in result
        assert "materials" in result
