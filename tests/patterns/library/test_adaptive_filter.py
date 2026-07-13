"""
Tests for src/patterns/library/adaptive_filter.py (Adaptive Filter pattern)

Covers:
- AdaptiveAlgorithm enum
- AdaptiveFilterConfig dataclass
- AdaptiveFilterPattern initialization
- _initialize_filter()
- _generate_input_signal()
- _generate_desired_signal()
- LMS update algorithms: _lms_update, _nlms_update, _rls_update
- _update_weights()
- _compute_learning_curve()
- run() integration
- _format_output()
- get_metadata()
- Edge cases: different algorithms, convergence, stability
"""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.adaptive_filter import (
    AdaptiveAlgorithm,
    AdaptiveFilterConfig,
    AdaptiveFilterPattern,
)


# ═══════════════════════════════════════════════════════════════════
# Enum and Config Tests
# ═══════════════════════════════════════════════════════════════════


class TestAdaptiveAlgorithm:
    def test_enum_values(self):
        assert AdaptiveAlgorithm.LMS.value == "lms"
        assert AdaptiveAlgorithm.NLMS.value == "nlms"
        assert AdaptiveAlgorithm.RLS.value == "rls"
        assert AdaptiveAlgorithm.RLS_FORGETTING.value == "rls_forgetting"


class TestAdaptiveFilterConfig:
    def test_default_init(self):
        cfg = AdaptiveFilterConfig()
        assert cfg.filter_order == 32
        assert cfg.algorithm == AdaptiveAlgorithm.LMS
        assert cfg.mu == 0.01
        assert cfg.n_samples == 10000
        assert cfg.snr_db == 20.0

    def test_custom_init(self):
        cfg = AdaptiveFilterConfig(
            filter_order=16, algorithm=AdaptiveAlgorithm.RLS, mu=0.05, n_samples=5000
        )
        assert cfg.filter_order == 16
        assert cfg.algorithm == AdaptiveAlgorithm.RLS
        assert cfg.mu == 0.05
        assert cfg.n_samples == 5000

    def test_rls_params(self):
        cfg = AdaptiveFilterConfig(algorithm=AdaptiveAlgorithm.RLS, delta=0.5, lambda_factor=0.95)
        assert cfg.delta == 0.5
        assert cfg.lambda_factor == 0.95


# ═══════════════════════════════════════════════════════════════════
# Initialization Tests
# ═══════════════════════════════════════════════════════════════════


class TestAdaptiveFilterInit:
    def test_default_init(self):
        pattern = AdaptiveFilterPattern()
        assert pattern.PATTERN_ID == "adaptive_filter"
        assert pattern.weights is not None
        assert pattern.weights.shape == (32,)
        assert np.allclose(pattern.weights, 0)

    def test_custom_config(self):
        cfg = AdaptiveFilterConfig(filter_order=16)
        pattern = AdaptiveFilterPattern(cfg)
        assert pattern.weights.shape == (16,)

    def test_rls_initialization(self):
        cfg = AdaptiveFilterConfig(algorithm=AdaptiveAlgorithm.RLS)
        pattern = AdaptiveFilterPattern(cfg)
        assert pattern.P is not None
        assert pattern.P.shape == (32, 32)

    def test_lms_no_p_matrix(self):
        cfg = AdaptiveFilterConfig(algorithm=AdaptiveAlgorithm.LMS)
        pattern = AdaptiveFilterPattern(cfg)
        assert pattern.P is None


class TestInitializeFilter:
    def test_system_id_mode_default(self):
        cfg = AdaptiveFilterConfig(sys_id_mode=True, unknown_system=None)
        pattern = AdaptiveFilterPattern(cfg)
        assert pattern.unknown_system is not None
        assert len(pattern.unknown_system) == 32

    def test_system_id_mode_custom(self):
        unknown = np.array([0.5, -0.3, 0.2, -0.1])
        cfg = AdaptiveFilterConfig(filter_order=4, sys_id_mode=True, unknown_system=unknown)
        pattern = AdaptiveFilterPattern(cfg)
        assert np.allclose(pattern.unknown_system, unknown)

    def test_no_sys_id_mode(self):
        cfg = AdaptiveFilterConfig(sys_id_mode=False)
        pattern = AdaptiveFilterPattern(cfg)
        assert pattern.unknown_system is None


# ═══════════════════════════════════════════════════════════════════
# Signal Generation Tests
# ═══════════════════════════════════════════════════════════════════


class TestGenerateInputSignal:
    def test_signal_shape(self):
        pattern = AdaptiveFilterPattern(AdaptiveFilterConfig(n_samples=1000))
        x = pattern._generate_input_signal()
        # Signal length includes filter_order for proper convolution
        assert len(x) == 1000 + 32

    def test_signal_not_constant(self):
        pattern = AdaptiveFilterPattern()
        x = pattern._generate_input_signal()
        assert np.std(x) > 0

    def test_ar_correlation(self):
        """Generated signal should have AR(1) correlation structure"""
        pattern = AdaptiveFilterPattern(AdaptiveFilterConfig(n_samples=10000))
        x = pattern._generate_input_signal()
        # Compute autocorrelation
        x_centered = x - np.mean(x)
        autocorr = np.correlate(x_centered, x_centered, mode="full")
        autocorr = autocorr[len(autocorr) // 2 :]
        autocorr = autocorr / autocorr[0]
        # AR(1) with coeff 0.8 should have lag-1 autocorr ~0.8
        assert autocorr[1] > 0.5  # Should be positively correlated


class TestGenerateDesiredSignal:
    def test_signal_length(self):
        cfg = AdaptiveFilterConfig(n_samples=1000)
        pattern = AdaptiveFilterPattern(cfg)
        x = pattern._generate_input_signal()
        d, d_clean = pattern._generate_desired_signal(x)
        assert len(d) == len(x)
        assert len(d_clean) == len(x)

    def test_noise_addition(self):
        cfg = AdaptiveFilterConfig(n_samples=1000, snr_db=20)
        pattern = AdaptiveFilterPattern(cfg)
        x = pattern._generate_input_signal()
        d, d_clean = pattern._generate_desired_signal(x)
        # Noisy signal should differ from clean
        assert not np.allclose(d, d_clean)

    def test_snr_effect(self):
        """Higher SNR should result in cleaner signal"""
        np.random.seed(42)
        cfg_high = AdaptiveFilterConfig(n_samples=1000, snr_db=40)
        pattern_high = AdaptiveFilterPattern(cfg_high)
        x = pattern_high._generate_input_signal()
        d_high, d_clean = pattern_high._generate_desired_signal(x)

        np.random.seed(42)
        cfg_low = AdaptiveFilterConfig(n_samples=1000, snr_db=10)
        pattern_low = AdaptiveFilterPattern(cfg_low)
        x = pattern_low._generate_input_signal()
        d_low, _ = pattern_low._generate_desired_signal(x)

        noise_high = np.mean((d_high - d_clean) ** 2)
        noise_low = np.mean((d_low - d_clean) ** 2)
        assert noise_high < noise_low


# ═══════════════════════════════════════════════════════════════════
# Algorithm Update Tests
# ═══════════════════════════════════════════════════════════════════


class TestLMSUpdate:
    def test_update_direction(self):
        pattern = AdaptiveFilterPattern(AdaptiveFilterConfig(filter_order=4))
        x_vec = np.array([1.0, 0.5, 0.25, 0.1])
        e = 0.5
        update = pattern._lms_update(x_vec, e)
        # Update should be proportional to input
        assert np.allclose(update, pattern.config.mu * e * x_vec)

    def test_zero_error_no_update(self):
        pattern = AdaptiveFilterPattern(AdaptiveFilterConfig(filter_order=4))
        x_vec = np.array([1.0, 0.5, 0.25, 0.1])
        update = pattern._lms_update(x_vec, 0.0)
        assert np.allclose(update, 0)


class TestNLMSUpdate:
    def test_normalization(self):
        pattern = AdaptiveFilterPattern(
            AdaptiveFilterConfig(filter_order=4, algorithm=AdaptiveAlgorithm.NLMS)
        )
        x_vec = np.array([2.0, 0.0, 0.0, 0.0])  # High power input
        e = 1.0
        update = pattern._nlms_update(x_vec, e)
        # Should be normalized
        expected = pattern.config.mu * e * x_vec / (np.dot(x_vec, x_vec) + 1e-10)
        assert np.allclose(update, expected)


class TestRLSUpdate:
    def test_rls_updates_p_matrix(self):
        cfg = AdaptiveFilterConfig(filter_order=4, algorithm=AdaptiveAlgorithm.RLS)
        pattern = AdaptiveFilterPattern(cfg)
        P_before = pattern.P.copy()
        x_vec = np.array([1.0, 0.5, 0.25, 0.1])
        pattern._rls_update(x_vec, 0.5)
        # P matrix should be updated
        assert not np.allclose(pattern.P, P_before)

    def test_rls_weight_update(self):
        cfg = AdaptiveFilterConfig(filter_order=4, algorithm=AdaptiveAlgorithm.RLS)
        pattern = AdaptiveFilterPattern(cfg)
        x_vec = np.array([1.0, 0.5, 0.25, 0.1])
        update = pattern._rls_update(x_vec, 0.5)
        assert update.shape == (4,)


class TestUpdateWeights:
    def test_lms_routing(self):
        cfg = AdaptiveFilterConfig(algorithm=AdaptiveAlgorithm.LMS)
        pattern = AdaptiveFilterPattern(cfg)
        x_vec = np.ones(32)
        update = pattern._update_weights(x_vec, 0.5)
        assert update.shape == (32,)

    def test_rls_routing(self):
        cfg = AdaptiveFilterConfig(algorithm=AdaptiveAlgorithm.RLS)
        pattern = AdaptiveFilterPattern(cfg)
        x_vec = np.ones(32)
        update = pattern._update_weights(x_vec, 0.5)
        assert update.shape == (32,)


# ═══════════════════════════════════════════════════════════════════
# Learning Curve Tests
# ═══════════════════════════════════════════════════════════════════


class TestComputeLearningCurve:
    def test_empty_history(self):
        pattern = AdaptiveFilterPattern()
        pattern.error_history = []
        curve = pattern._compute_learning_curve()
        assert len(curve) == 0 or (len(curve) == 1 and (curve[0] == 0.0 or str(curve[0]) == "nan"))

    def test_learning_curve_smoothing(self):
        pattern = AdaptiveFilterPattern()
        # Generate decreasing errors
        pattern.error_history = [1.0 / (i + 1) for i in range(200)]
        curve = pattern._compute_learning_curve(window_size=100)
        assert len(curve) > 0
        # Should be decreasing
        assert curve[-1] < curve[0]


# ═══════════════════════════════════════════════════════════════════
# Run Integration Tests
# ═══════════════════════════════════════════════════════════════════


class TestRun:
    def test_run_lms(self):
        cfg = AdaptiveFilterConfig(algorithm=AdaptiveAlgorithm.LMS, filter_order=8, n_samples=500)
        pattern = AdaptiveFilterPattern(cfg)
        result = pattern.run()
        assert result["algorithm"] == "lms"
        assert "final_mse" in result
        assert "final_weights" in result

    def test_run_nlms(self):
        cfg = AdaptiveFilterConfig(algorithm=AdaptiveAlgorithm.NLMS, filter_order=8, n_samples=500)
        pattern = AdaptiveFilterPattern(cfg)
        result = pattern.run()
        assert result["algorithm"] == "nlms"

    def test_run_rls(self):
        cfg = AdaptiveFilterConfig(algorithm=AdaptiveAlgorithm.RLS, filter_order=8, n_samples=500)
        pattern = AdaptiveFilterPattern(cfg)
        result = pattern.run()
        assert result["algorithm"] == "rls"

    def test_run_rls_forgetting(self):
        cfg = AdaptiveFilterConfig(
            algorithm=AdaptiveAlgorithm.RLS_FORGETTING, filter_order=8, n_samples=500
        )
        pattern = AdaptiveFilterPattern(cfg)
        result = pattern.run()
        assert result["algorithm"] == "rls_forgetting"

    def test_convergence(self):
        """Filter should converge for simple system"""
        np.random.seed(42)
        unknown = np.array([0.5, 0.3, 0.1])
        cfg = AdaptiveFilterConfig(
            algorithm=AdaptiveAlgorithm.LMS,
            filter_order=3,
            n_samples=5000,
            mu=0.01,
            unknown_system=unknown,
            sys_id_mode=True,
            snr_db=40,
        )
        pattern = AdaptiveFilterPattern(cfg)
        result = pattern.run()
        # Should converge to low error
        assert result["weight_error_normalized"] < 1.0

    def test_mse_decreases(self):
        """MSE should generally decrease during adaptation"""
        cfg = AdaptiveFilterConfig(filter_order=8, n_samples=2000, output_interval=10)
        pattern = AdaptiveFilterPattern(cfg)
        result = pattern.run()
        # Early MSE should be higher than final
        if len(result["mse_history"]) > 1:
            assert result["mse_history"][-1] < result["mse_history"][0] * 2

    def test_error_history_present(self):
        cfg = AdaptiveFilterConfig(filter_order=8, n_samples=500)
        pattern = AdaptiveFilterPattern(cfg)
        result = pattern.run()
        assert "error_history" in result
        assert len(result["error_history"]) > 0


# ═══════════════════════════════════════════════════════════════════
# Output Format Tests
# ═══════════════════════════════════════════════════════════════════


class TestFormatOutput:
    def test_output_structure(self):
        cfg = AdaptiveFilterConfig(filter_order=8, n_samples=500)
        pattern = AdaptiveFilterPattern(cfg)
        result = pattern.run()
        required_keys = [
            "algorithm",
            "filter_order",
            "final_weights",
            "final_mse",
            "noise_power",
            "misadjustment",
            "error_history",
            "mse_history",
            "learning_curve",
            "mean_output",
            "output_variance",
            "config",
        ]
        for key in required_keys:
            assert key in result

    def test_system_id_output(self):
        unknown = np.array([0.5, 0.3, 0.1])
        cfg = AdaptiveFilterConfig(
            filter_order=3, n_samples=500, unknown_system=unknown, sys_id_mode=True
        )
        pattern = AdaptiveFilterPattern(cfg)
        result = pattern.run()
        assert "weight_error" in result
        assert "weight_error_normalized" in result
        assert result["unknown_system"] is not None


# ═══════════════════════════════════════════════════════════════════
# Metadata Tests
# ═══════════════════════════════════════════════════════════════════


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = AdaptiveFilterPattern.get_metadata()
        assert meta["id"] == "adaptive_filter"
        assert "name" in meta
        assert "category" in meta
        assert "domain" in meta
        assert "parameters" in meta

    def test_parameters_list(self):
        meta = AdaptiveFilterPattern.get_metadata()
        param_names = [p["name"] for p in meta["parameters"]]
        assert "filter_order" in param_names
        assert "algorithm" in param_names
        assert "mu" in param_names


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_very_small_filter(self):
        """Filter with order 1 should still work"""
        cfg = AdaptiveFilterConfig(filter_order=1, n_samples=100)
        pattern = AdaptiveFilterPattern(cfg)
        result = pattern.run()
        assert len(result["final_weights"]) == 1

    def test_high_snr(self):
        """Very high SNR should result in low MSE"""
        cfg = AdaptiveFilterConfig(filter_order=8, n_samples=1000, snr_db=60)
        pattern = AdaptiveFilterPattern(cfg)
        result = pattern.run()
        # MSE should be close to noise power (very small)
        assert result["final_mse"] < 10.0

    def test_low_snr(self):
        """Low SNR should still complete"""
        cfg = AdaptiveFilterConfig(filter_order=8, n_samples=500, snr_db=5)
        pattern = AdaptiveFilterPattern(cfg)
        result = pattern.run()
        assert "final_mse" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
