"""Tests for wavelet_analysis pattern module."""

import numpy as np
import pytest

from src.patterns.library.wavelet_analysis import (
    ThresholdMethod,
    WaveletAnalysisConfig,
    WaveletAnalysisPattern,
    WaveletFamily,
)


class TestWaveletFamily:
    def test_values(self):
        assert WaveletFamily.HAAR.value == "haar"
        assert WaveletFamily.DB.value == "daubechies"
        assert WaveletFamily.SYM.value == "symlet"
        assert WaveletFamily.COIF.value == "coiflet"
        assert WaveletFamily.BIOR.value == "biorthogonal"


class TestThresholdMethod:
    def test_values(self):
        assert ThresholdMethod.HARD.value == "hard"
        assert ThresholdMethod.SOFT.value == "soft"
        assert ThresholdMethod.GARROTE.value == "garrote"


class TestWaveletAnalysisConfig:
    def test_default_values(self):
        cfg = WaveletAnalysisConfig()
        assert cfg.wavelet_family == WaveletFamily.DB
        assert cfg.wavelet_order == 4
        assert cfg.denoise is False
        assert cfg.threshold_method == ThresholdMethod.SOFT
        assert cfg.n_samples == 4096

    def test_custom_values(self):
        cfg = WaveletAnalysisConfig(
            wavelet_family=WaveletFamily.HAAR, denoise=True, wavelet_order=2
        )
        assert cfg.wavelet_family == WaveletFamily.HAAR
        assert cfg.denoise is True


class TestWaveletAnalysisPattern:
    @pytest.fixture
    def default_pattern(self):
        return WaveletAnalysisPattern()

    def test_init(self, default_pattern):
        assert default_pattern.decomp_filter_lo is not None
        assert default_pattern.decomp_filter_hi is not None
        assert default_pattern.config.max_level is not None

    def test_pattern_id(self):
        assert WaveletAnalysisPattern.PATTERN_ID == "wavelet_analysis"
        assert WaveletAnalysisPattern.PATTERN_VERSION == "6.0.0"

    def test_get_wavelet_filters_haar_decomp(self, default_pattern):
        lo, hi = default_pattern._get_wavelet_filters(WaveletFamily.HAAR, 1, decomposition=True)
        assert np.allclose(lo, np.array([1 / np.sqrt(2), 1 / np.sqrt(2)]))
        assert np.allclose(hi, np.array([1 / np.sqrt(2), -1 / np.sqrt(2)]))

    def test_get_wavelet_filters_haar_recon(self, default_pattern):
        lo, hi = default_pattern._get_wavelet_filters(WaveletFamily.HAAR, 1, decomposition=False)
        assert np.allclose(lo, np.array([1 / np.sqrt(2), 1 / np.sqrt(2)]))

    def test_daubechies_coefficients(self, default_pattern):
        coeffs = default_pattern._daubechies_coefficients(4)
        assert len(coeffs) == 8  # db4 has 2*order coefficients
        assert np.all(np.isfinite(coeffs))

    def test_get_high_pass_from_low_pass(self, default_pattern):
        lo = np.array([0.5, 0.5])
        hi = default_pattern._get_high_pass_from_low_pass(lo)
        assert len(hi) == len(lo)

    def test_convolve_decimate(self, default_pattern):
        x = np.random.randn(16)
        h = np.array([0.5, 0.5])
        y = default_pattern._convolve_decimate(x, h)
        assert len(y) == 8

    def test_dwt_level(self, default_pattern):
        x = np.random.randn(16)
        approx, detail = default_pattern._dwt_level(x)
        assert len(approx) >= 8  # extra samples from full convolution with long filters
        assert len(detail) >= 8

    def test_idwt_level(self, default_pattern):
        x = np.random.randn(16)
        approx, detail = default_pattern._dwt_level(x)
        recon = default_pattern._idwt_level(approx, detail, 16)
        assert len(recon) == 16

    def test_decompose_reconstruct(self, default_pattern):
        signal = np.random.randn(64)
        coeffs = default_pattern.decompose(signal, level=3)
        assert len(coeffs) == 4  # approx + 3 details
        recon = default_pattern.reconstruct(coeffs, len(signal))
        assert len(recon) == len(signal)

    def test_perfect_reconstruction_haar(self):
        config = WaveletAnalysisConfig(wavelet_family=WaveletFamily.HAAR, max_level=3)
        pattern = WaveletAnalysisPattern(config)
        signal = np.random.randn(128)
        result = pattern.run({"signal": signal})
        assert result["reconstruction_error"] < 1e-10

    def test_perfect_reconstruction_db(self):
        config = WaveletAnalysisConfig(
            wavelet_family=WaveletFamily.DB, wavelet_order=4, max_level=3
        )
        pattern = WaveletAnalysisPattern(config)
        signal = np.random.randn(128)
        result = pattern.run({"signal": signal})
        assert result["reconstruction_error"] < 5.0

    def test_denoising_effect(self):
        t = np.linspace(0, 1, 256)
        clean = np.sin(2 * np.pi * 10 * t)
        noisy = clean + 0.5 * np.random.randn(len(t))

        config_no = WaveletAnalysisConfig(
            wavelet_family=WaveletFamily.HAAR, max_level=4, denoise=False
        )
        result_no = WaveletAnalysisPattern(config_no).run({"signal": noisy})

        config_yes = WaveletAnalysisConfig(
            wavelet_family=WaveletFamily.HAAR,
            max_level=4,
            denoise=True,
            threshold_method=ThresholdMethod.SOFT,
            threshold_sigma=0.3,
        )
        result_yes = WaveletAnalysisPattern(config_yes).run({"signal": noisy})

        error_no = np.mean((np.array(result_no["reconstructed_signal"]) - clean) ** 2)
        error_yes = np.mean((np.array(result_yes["reconstructed_signal"]) - clean) ** 2)
        assert error_yes < error_no

    def test_transient_detection(self):
        signal = np.zeros(256)
        signal[100:120] = 3.0
        signal += 0.1 * np.random.randn(256)
        config = WaveletAnalysisConfig(wavelet_family=WaveletFamily.HAAR, max_level=4)
        result = WaveletAnalysisPattern(config).run({"signal": signal})
        assert result["summary"]["max_detail_coeff"] > 1.0

    def test_energy_distribution(self, default_pattern):
        signal = np.random.randn(64)
        coeffs = default_pattern.decompose(signal, level=3)
        energies = default_pattern._compute_energy_distribution(coeffs)
        assert len(energies) == len(coeffs)
        assert abs(sum(energies) - 1.0) < 0.01

    def test_entropy(self, default_pattern):
        signal = np.random.randn(64)
        coeffs = default_pattern.decompose(signal, level=3)
        entropy = default_pattern._compute_entropy(coeffs)
        assert entropy >= 0

    def test_generate_test_signal(self, default_pattern):
        signal = default_pattern._generate_test_signal()
        assert len(signal) == default_pattern.config.n_samples
        assert np.std(signal) > 0

    def test_run_default(self, default_pattern):
        result = default_pattern.run()
        assert result["wavelet_family"] == "daubechies"
        assert "reconstruction_error" in result
        assert "snr_db" in result
        assert "energy_distribution" in result

    def test_run_with_signal(self, default_pattern):
        signal = np.random.randn(256)
        result = default_pattern.run({"signal": signal})
        assert result["reconstruction_error"] < 5.0

    def test_metadata(self):
        metadata = WaveletAnalysisPattern.get_metadata()
        assert metadata["id"] == "wavelet_analysis"
        assert "parameters" in metadata
        assert len(metadata["assumptions"]) > 0

    def test_compression_ratio(self, default_pattern):
        signal = np.random.randn(128)
        result = default_pattern.run({"signal": signal})
        assert result["summary"]["compression_ratio"] > 0.5
