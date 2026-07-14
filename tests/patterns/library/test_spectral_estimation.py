"""Tests for spectral_estimation pattern module."""

import numpy as np
import pytest

from src.patterns.library.spectral_estimation import (
    SpectralEstimationConfig,
    SpectralEstimationPattern,
    SpectralMethod,
)


class TestSpectralMethod:
    def test_values(self):
        assert SpectralMethod.PERIODOGRAM.value == "periodogram"
        assert SpectralMethod.WELCH.value == "welch"
        assert SpectralMethod.MTM.value == "multitaper"
        assert SpectralMethod.BARTLETT.value == "bartlett"


class TestSpectralEstimationConfig:
    def test_default_values(self):
        cfg = SpectralEstimationConfig()
        assert cfg.method == SpectralMethod.WELCH
        assert cfg.n_samples == 4096
        assert cfg.sampling_rate == 1000.0
        assert cfg.nperseg == 256
        assert cfg.noverlap == 128

    def test_custom_values(self):
        cfg = SpectralEstimationConfig(method=SpectralMethod.MTM, n_samples=2048)
        assert cfg.method == SpectralMethod.MTM
        assert cfg.n_samples == 2048


class TestSpectralEstimationPattern:
    @pytest.fixture
    def default_pattern(self):
        return SpectralEstimationPattern()

    def test_init(self, default_pattern):
        assert default_pattern.frequencies is None
        assert default_pattern.psd is None
        assert default_pattern.config.nfft == default_pattern.config.nperseg

    def test_pattern_id(self):
        assert SpectralEstimationPattern.PATTERN_ID == "spectral_estimation"
        assert SpectralEstimationPattern.PATTERN_VERSION == "6.0.0"

    def test_generate_test_signal(self, default_pattern):
        signal = default_pattern._generate_test_signal()
        assert len(signal) == default_pattern.config.n_samples
        assert np.std(signal) > 0

    def test_get_window_hann(self, default_pattern):
        w = default_pattern._get_window(64)
        assert len(w) == 64
        assert w[0] == 0.0
        assert w[32] == pytest.approx(1.0, abs=0.01)

    def test_get_window_hamming(self):
        config = SpectralEstimationConfig(window="hamming")
        pattern = SpectralEstimationPattern(config)
        w = pattern._get_window(64)
        assert len(w) == 64

    def test_detrend_constant(self, default_pattern):
        x = np.ones(100) * 5.0
        y = default_pattern._detrend(x)
        assert np.allclose(y, 0, atol=1e-10)

    def test_detrend_linear(self):
        config = SpectralEstimationConfig(detrend="linear")
        pattern = SpectralEstimationPattern(config)
        x = np.arange(100)
        y = pattern._detrend(x)
        assert np.allclose(y, 0, atol=1e-10)

    def test_periodogram(self, default_pattern):
        x = np.sin(2 * np.pi * 50 * np.arange(256) / 1000)
        freqs, psd = default_pattern._periodogram(x)
        assert len(freqs) == len(psd)
        assert np.all(psd >= 0)

    def test_welch(self, default_pattern):
        x = np.sin(2 * np.pi * 50 * np.arange(512) / 1000)
        freqs, psd = default_pattern._welch(x)
        assert len(freqs) == len(psd)
        assert np.all(psd >= 0)

    def test_bartlett(self, default_pattern):
        x = np.sin(2 * np.pi * 50 * np.arange(512) / 1000)
        freqs, psd = default_pattern._bartlett(x)
        assert len(freqs) == len(psd)
        assert np.all(psd >= 0)

    def test_multitaper(self, default_pattern):
        x = np.sin(2 * np.pi * 50 * np.arange(512) / 1000)
        freqs, psd = default_pattern._multitaper(x)
        assert len(freqs) == len(psd)
        assert np.all(psd >= 0)

    def test_dpss_tapers(self, default_pattern):
        tapers = default_pattern._dpss_tapers(64, 4.0, 8)
        assert tapers.shape == (8, 64)
        for i in range(8):
            assert np.isclose(np.linalg.norm(tapers[i]), 1.0)

    def test_peak_detection(self):
        fs = 1000
        t = np.arange(4096) / fs
        signal = np.sin(2 * np.pi * 100 * t)
        config = SpectralEstimationConfig(
            method=SpectralMethod.PERIODOGRAM, sampling_rate=fs, n_samples=len(signal)
        )
        pattern = SpectralEstimationPattern(config)
        result = pattern.run({"signal": signal})
        peaks = result["peak_frequencies"]
        assert any(95 < p < 105 for p in peaks)

    def test_welch_variance_reduction(self):
        np.random.seed(42)
        fs = 1000
        t = np.arange(4096) / fs
        signal = np.sin(2 * np.pi * 50 * t) + 0.5 * np.random.randn(len(t))

        config_per = SpectralEstimationConfig(
            method=SpectralMethod.PERIODOGRAM, sampling_rate=fs, n_samples=len(signal)
        )
        result_per = SpectralEstimationPattern(config_per).run({"signal": signal})

        config_welch = SpectralEstimationConfig(
            method=SpectralMethod.WELCH, sampling_rate=fs, n_samples=len(signal), nperseg=512
        )
        result_welch = SpectralEstimationPattern(config_welch).run({"signal": signal})

        var_per = np.var(result_per["psd"])
        var_welch = np.var(result_welch["psd"])
        assert var_welch < var_per

    def test_run_default(self, default_pattern):
        result = default_pattern.run()
        assert result["method"] == "welch"
        assert "frequencies" in result
        assert "psd" in result
        assert "peak_frequencies" in result
        assert "total_power" in result
        assert "spectral_centroid" in result

    def test_run_with_signal(self, default_pattern):
        signal = np.random.randn(512)
        result = default_pattern.run({"signal": signal})
        assert len(result["psd"]) > 0

    def test_run_periodogram(self):
        config = SpectralEstimationConfig(method=SpectralMethod.PERIODOGRAM)
        pattern = SpectralEstimationPattern(config)
        result = pattern.run()
        assert result["method"] == "periodogram"

    def test_run_mtm(self):
        config = SpectralEstimationConfig(method=SpectralMethod.MTM)
        pattern = SpectralEstimationPattern(config)
        result = pattern.run()
        assert result["method"] == "multitaper"

    def test_run_bartlett(self):
        config = SpectralEstimationConfig(method=SpectralMethod.BARTLETT)
        pattern = SpectralEstimationPattern(config)
        result = pattern.run()
        assert result["method"] == "bartlett"

    def test_spectral_centroid(self):
        fs = 1000
        t = np.arange(1024) / fs
        signal = np.sin(2 * np.pi * 100 * t)
        config = SpectralEstimationConfig(sampling_rate=fs, n_samples=len(signal))
        pattern = SpectralEstimationPattern(config)
        result = pattern.run({"signal": signal})
        assert result["spectral_centroid"] > 50

    def test_metadata(self):
        metadata = SpectralEstimationPattern.get_metadata()
        assert metadata["id"] == "spectral_estimation"
        assert "parameters" in metadata
        assert len(metadata["assumptions"]) > 0

    def test_frequency_resolution(self):
        config = SpectralEstimationConfig(sampling_rate=1000, nfft=256)
        pattern = SpectralEstimationPattern(config)
        assert pattern.config.nfft == 256
        result = pattern.run()
        assert result["frequency_resolution"] == pytest.approx(1000 / 256)
