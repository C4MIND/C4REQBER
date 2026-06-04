"""Tests for cloud_microphysics pattern module."""

import numpy as np
import pytest

from src.patterns.library.cloud_microphysics import CloudMicrophysicsConfig, CloudMicrophysicsPattern



class TestCloudMicrophysicsConfig:
    def test_default_values(self):
        cfg = CloudMicrophysicsConfig()
        assert cfg.nx == 50
        assert cfg.ny == 50
        assert cfg.nz == 30
        assert cfg.T_surface == 288.0
        assert cfg.dt == 60.0
        assert cfg.minutes == 180

    def test_custom_values(self):
        cfg = CloudMicrophysicsConfig(nx=20, ny=20, nz=10, minutes=30)
        assert cfg.nx == 20
        assert cfg.minutes == 30


class TestCloudMicrophysicsPattern:
    @pytest.fixture
    def small_config(self):
        return CloudMicrophysicsConfig(nx=10, ny=10, nz=5, minutes=10, dt=30)

    @pytest.fixture
    def pattern(self, small_config):
        return CloudMicrophysicsPattern(small_config)

    def test_init(self, pattern, small_config):
        assert pattern.config == small_config
        assert pattern.qv.shape == (10, 10, 5)
        assert pattern.qc.shape == (10, 10, 5)
        assert pattern.qr.shape == (10, 10, 5)
        assert pattern.T.shape == (10, 10, 5)

    def test_pattern_id(self):
        assert CloudMicrophysicsPattern.PATTERN_ID == "cloud_microphysics"
        assert CloudMicrophysicsPattern.PATTERN_VERSION == "6.0.0"

    def test_saturation_vapor_pressure(self, pattern):
        T = np.array([273.15, 283.15, 293.15])
        es = pattern._saturation_vapor_pressure(T)
        assert len(es) == 3
        assert np.all(np.diff(es) > 0)
        assert np.all(es > 0)

    def test_saturation_mixing_ratio(self, pattern):
        T = 288.0
        p = 100000.0
        qs = pattern._saturation_mixing_ratio(np.array([[T]]), p)
        assert qs[0, 0] > 0
        assert qs[0, 0] < 0.1

    def test_saturation_adjustment(self, pattern):
        dqc_dt, dT_dt = pattern._saturation_adjustment()
        assert dqc_dt.shape == pattern.qc.shape
        assert dT_dt.shape == pattern.T.shape
        assert np.all(np.isfinite(dqc_dt))

    def test_autoconversion(self, pattern):
        pattern.qc[:, :, 2] = 2.0e-3
        dqr_dt = pattern._autoconversion()
        assert dqr_dt.shape == pattern.qr.shape
        assert np.all(dqr_dt >= 0)

    def test_accretion(self, pattern):
        pattern.qc[:, :, 2] = 1.0e-3
        pattern.qr[:, :, 2] = 1.0e-3
        dqr_dt = pattern._accretion()
        assert np.all(dqr_dt >= 0)

    def test_evaporation(self, pattern):
        pattern.qr[:, :, 2] = 1.0e-3
        dqr_dt = pattern._evaporation()
        assert np.all(dqr_dt <= 0)

    def test_sedimentation(self, pattern):
        pattern.qr[:, :, 2] = 1.0e-3
        dqc_dt, dqr_dt = pattern._sedimentation()
        assert dqr_dt.shape == pattern.qr.shape
        assert np.all(np.isfinite(dqr_dt))

    def test_tendencies(self, pattern):
        dqv_dt, dqc_dt, dqr_dt, dT_dt = pattern._tendencies()
        assert dqv_dt.shape == pattern.qv.shape
        assert dqc_dt.shape == pattern.qc.shape
        assert dqr_dt.shape == pattern.qr.shape
        assert dT_dt.shape == pattern.T.shape
        assert np.all(np.isfinite(dqv_dt))

    def test_precipitation_rate(self, pattern):
        pattern.qr[:, :, -1] = 1.0e-3
        precip = pattern._calculate_precipitation_rate()
        assert isinstance(precip, float)
        assert precip >= 0

    def test_cloud_cover(self, pattern):
        cover = pattern._calculate_cloud_cover()
        assert isinstance(cover, float)
        assert 0 <= cover <= 1

    def test_step(self, pattern):
        pattern._step()
        assert np.all(pattern.qv >= 0)
        assert np.all(pattern.qc >= 0)
        assert np.all(pattern.qr >= 0)

    def test_run_short(self):
        config = CloudMicrophysicsConfig(nx=8, ny=8, nz=4, minutes=5, dt=30, output_interval=1)
        pattern = CloudMicrophysicsPattern(config)
        result = pattern.run()
        assert "vapor" in result
        assert "cloud_water" in result
        assert "rain_water" in result
        assert "precipitation_rate" in result
        assert "cloud_cover" in result
        assert len(result["time_minutes"]) > 0
        assert "final_state" in result

    def test_metadata(self):
        metadata = CloudMicrophysicsPattern.get_metadata()
        assert metadata["id"] == "cloud_microphysics"
        assert "parameters" in metadata
        assert len(metadata["assumptions"]) > 0

    def test_temperature_profile(self, pattern):
        assert np.all(pattern.T[:, :, 0] > pattern.T[:, :, -1])

    def test_moisture_profile(self, pattern):
        assert np.all(pattern.qv[:, :, 0] >= pattern.qv[:, :, -1])
