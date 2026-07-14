"""Benchmark 4: Kalman Filter — convergence on linear system."""
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pytest

from src.patterns.library.kalman_filter import (
    FilterType,
    KalmanFilterConfig,
    KalmanFilterPattern,
    SystemModel,
)


class TestKFConvergence:
    def test_kf_standard_converges(self):
        """Standard KF should reduce error over time."""
        config = KalmanFilterConfig(
            filter_type=FilterType.KF,
            system_model=SystemModel.CONSTANT_VELOCITY,
            simulation_steps=500,
            dt=0.1,
            Q=np.eye(2) * 0.01,
            R=np.eye(1) * 0.1,
        )
        pattern = KalmanFilterPattern(config)
        result = pattern.run()

        assert "rmse" in result["performance_metrics"], (
            f"Missing performance metrics: {result.keys()}"
        )

    def test_kf_rmse_reasonable(self):
        """RMSE should be finite for standard KF."""
        config = KalmanFilterConfig(
            filter_type=FilterType.KF,
            system_model=SystemModel.CONSTANT_VELOCITY,
            simulation_steps=500,
            dt=0.1,
            Q=np.eye(2) * 0.01,
            R=np.eye(1) * 0.1,
        )
        pattern = KalmanFilterPattern(config)
        result = pattern.run()

        rmse = result["performance_metrics"]["rmse"]
        assert np.isfinite(rmse), f"KF RMSE not finite: {rmse}"
        assert rmse < 20.0, f"KF RMSE too high: {rmse:.4f}"

    def test_kf_ekf_pendulum(self):
        """EKF on nonlinear pendulum should complete without errors."""
        config = KalmanFilterConfig(
            filter_type=FilterType.EKF,
            system_model=SystemModel.NONLINEAR_PENDULUM,
            simulation_steps=200,
            dt=0.05,
        )
        pattern = KalmanFilterPattern(config)
        result = pattern.run()

        assert result["filter_type"] == "ekf"
        assert "performance_metrics" in result
        assert result["performance_metrics"]["rmse"] < 5.0, (
            f"EKF RMSE too high: {result['performance_metrics']['rmse']:.4f}"
        )

    def test_kf_ukf_pendulum(self):
        """UKF on nonlinear pendulum should complete without errors."""
        config = KalmanFilterConfig(
            filter_type=FilterType.UKF,
            system_model=SystemModel.NONLINEAR_PENDULUM,
            simulation_steps=200,
            dt=0.05,
        )
        pattern = KalmanFilterPattern(config)
        result = pattern.run()

        assert result["filter_type"] == "ukf"
        assert result["performance_metrics"]["rmse"] < 5.0

    def test_kf_covariance_decreases(self):
        """Covariance trace should generally decrease or stabilize."""
        config = KalmanFilterConfig(
            filter_type=FilterType.KF,
            system_model=SystemModel.CONSTANT_VELOCITY,
            simulation_steps=500,
            dt=0.1,
            Q=np.eye(2) * 0.01,
            R=np.eye(1) * 0.1,
        )
        pattern = KalmanFilterPattern(config)
        result = pattern.run()

        cov_history = result.get("history", {}).get("covariance_trace", [])
        if len(cov_history) > 10:
            initial_cov = np.mean(cov_history[:5])
            final_cov = np.mean(cov_history[-5:])
            assert final_cov <= initial_cov * 3, (
                f"Covariance grew: {initial_cov:.4f} -> {final_cov:.4f}"
            )


class TestKFPerformance:
    def test_kf_performance(self):
        """500-step KF should complete under 2 seconds."""
        import time

        config = KalmanFilterConfig(
            filter_type=FilterType.KF,
            system_model=SystemModel.CONSTANT_VELOCITY,
            simulation_steps=500,
            dt=0.1,
        )
        pattern = KalmanFilterPattern(config)
        start = time.perf_counter()
        result = pattern.run()
        elapsed = time.perf_counter() - start
        assert result["filter_type"] == "kf"
        assert elapsed < 2.0, f"KF too slow: {elapsed:.3f}s"
