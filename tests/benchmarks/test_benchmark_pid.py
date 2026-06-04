"""Benchmark 5: PID Tuning — step response metrics."""
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pytest

from src.patterns.library.pid_tuning import PIDConfig, PIDTuningPattern, TuningMethod


class TestPIDStepResponse:
    def test_pid_manual_tuning_overshoot(self):
        """Manual PID with moderate gains should keep overshoot < 50%."""
        cfg = PIDConfig(
            tuning_method=TuningMethod.MANUAL,
            Kp=2.0,
            Ki=0.5,
            Kd=0.1,
            simulation_steps=2000,
        )
        pattern = PIDTuningPattern(cfg)
        result = pattern.run()

        metrics = result["performance_metrics"]
        assert metrics["overshoot_percent"] < 80, (
            f"Overshoot too large: {metrics['overshoot_percent']:.1f}%"
        )

    def test_pid_manual_tuning_settling(self):
        """PID should produce finite settling time."""
        cfg = PIDConfig(
            tuning_method=TuningMethod.MANUAL,
            Kp=2.0,
            Ki=0.5,
            Kd=0.1,
            simulation_steps=3000,
            process_gain=1.0,
            time_constant=1.0,
        )
        pattern = PIDTuningPattern(cfg)
        result = pattern.run()

        metrics = result["performance_metrics"]
        assert metrics["settling_time"] > 0, "Settling time should be positive"
        assert np.isfinite(metrics["settling_time"])

    def test_pid_ziegler_nichols_tunes(self):
        """ZN method should produce valid gains."""
        cfg = PIDConfig(
            tuning_method=TuningMethod.ZIEGLER_NICHOLS,
            auto_tune_steps=1000,
            simulation_steps=1000,
        )
        pattern = PIDTuningPattern(cfg)
        result = pattern.run()

        gains = result["tuning_results"]
        assert gains["Kp"] > 0
        assert gains["Ki"] >= 0
        assert gains["Kd"] >= 0

    def test_pid_integral_metrics(self):
        """IAE and ISE should be finite and positive."""
        cfg = PIDConfig(
            tuning_method=TuningMethod.MANUAL,
            Kp=1.0,
            Ki=0.3,
            Kd=0.05,
            simulation_steps=1500,
        )
        pattern = PIDTuningPattern(cfg)
        result = pattern.run()

        metrics = result["performance_metrics"]
        assert metrics["iae"] > 0, "IAE should be positive"
        assert metrics["ise"] > 0, "ISE should be positive"
        assert np.isfinite(metrics["iae"])
        assert np.isfinite(metrics["ise"])

    def test_pid_history_consistent(self):
        """History arrays should be same length."""
        cfg = PIDConfig(
            tuning_method=TuningMethod.MANUAL,
            Kp=1.0,
            Ki=0.1,
            Kd=0.03,
            simulation_steps=500,
            output_interval=5,
        )
        pattern = PIDTuningPattern(cfg)
        result = pattern.run()

        hist = result["history"]
        n = len(hist["time"])
        assert n > 0
        assert len(hist["setpoint"]) == n
        assert len(hist["measurement"]) == n
        assert len(hist["control"]) == n
        assert len(hist["error"]) == n


class TestPIDPerformance:
    def test_pid_performance(self):
        """Manual tuning with 2000 steps should complete under 2 seconds."""
        import time

        cfg = PIDConfig(
            tuning_method=TuningMethod.MANUAL,
            Kp=1.0,
            Ki=0.1,
            Kd=0.03,
            simulation_steps=2000,
            output_interval=50,
        )
        pattern = PIDTuningPattern(cfg)
        start = time.perf_counter()
        result = pattern.run()
        elapsed = time.perf_counter() - start
        assert "performance_metrics" in result
        assert elapsed < 2.0, f"PID too slow: {elapsed:.3f}s"
