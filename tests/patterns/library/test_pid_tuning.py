"""
Tests for src/patterns/library/pid_tuning.py

Covers:
- TuningMethod and PIDStructure enums
- PIDConfig default and custom initialization
- PIDController init, update, reset, anti-windup, output limits, structures
- PIDTuningPattern init, manual tuning, ZN tuning, Cohen-Coon tuning,
  auto-tune step, run(), get_metadata()
- Edge cases: zero dt, negative gains
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.pid_tuning import (

    PIDConfig,
    PIDController,
    PIDStructure,
    PIDTuningPattern,
    TuningMethod,
)


# ═══════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════


class TestTuningMethod:
    def test_enum_values(self):
        assert TuningMethod.MANUAL.value == "manual"
        assert TuningMethod.ZIEGLER_NICHOLS.value == "ziegler_nichols"
        assert TuningMethod.AUTO_TUNE_RELAY.value == "auto_tune_relay"
        assert TuningMethod.AUTO_TUNE_STEP.value == "auto_tune_step"
        assert TuningMethod.COHEN_COON.value == "cohen_coon"


class TestPIDStructure:
    def test_enum_values(self):
        assert PIDStructure.PARALLEL.value == "parallel"
        assert PIDStructure.SERIES.value == "series"
        assert PIDStructure.IDEAL.value == "ideal"


# ═══════════════════════════════════════════════════════════════════
# PIDConfig
# ═══════════════════════════════════════════════════════════════════


class TestPIDConfig:
    def test_default_init(self):
        cfg = PIDConfig()
        assert cfg.Kp == 1.0
        assert cfg.Ki == 0.1
        assert cfg.Kd == 0.01
        assert cfg.tuning_method == TuningMethod.ZIEGLER_NICHOLS
        assert cfg.pid_structure == PIDStructure.PARALLEL
        assert cfg.auto_tune_steps == 2000
        assert cfg.auto_tune_setpoint == 1.0
        assert cfg.relay_amplitude == 1.0
        assert cfg.dt == 0.01
        assert cfg.simulation_steps == 5000
        assert cfg.process_gain == 1.0
        assert cfg.time_constant == 1.0
        assert cfg.dead_time == 0.1
        assert cfg.settling_time_weight == 1.0
        assert cfg.overshoot_weight == 1.0
        assert cfg.rise_time_weight == 0.5
        assert cfg.output_interval == 10
        assert cfg.enable_anti_windup is True
        assert cfg.output_limits == (-10.0, 10.0)

    def test_custom_init(self):
        cfg = PIDConfig(
            Kp=2.5,
            Ki=0.5,
            Kd=0.05,
            tuning_method=TuningMethod.MANUAL,
            pid_structure=PIDStructure.SERIES,
            auto_tune_steps=1000,
            auto_tune_setpoint=5.0,
            relay_amplitude=2.0,
            dt=0.05,
            simulation_steps=2000,
            process_gain=2.0,
            time_constant=0.5,
            dead_time=0.2,
            settling_time_weight=2.0,
            overshoot_weight=0.5,
            rise_time_weight=1.0,
            output_interval=5,
            enable_anti_windup=False,
            output_limits=(-5.0, 5.0),
        )
        assert cfg.Kp == 2.5
        assert cfg.Ki == 0.5
        assert cfg.Kd == 0.05
        assert cfg.tuning_method == TuningMethod.MANUAL
        assert cfg.pid_structure == PIDStructure.SERIES
        assert cfg.auto_tune_steps == 1000
        assert cfg.auto_tune_setpoint == 5.0
        assert cfg.relay_amplitude == 2.0
        assert cfg.dt == 0.05
        assert cfg.simulation_steps == 2000
        assert cfg.process_gain == 2.0
        assert cfg.time_constant == 0.5
        assert cfg.dead_time == 0.2
        assert cfg.settling_time_weight == 2.0
        assert cfg.overshoot_weight == 0.5
        assert cfg.rise_time_weight == 1.0
        assert cfg.output_interval == 5
        assert cfg.enable_anti_windup is False
        assert cfg.output_limits == (-5.0, 5.0)


# ═══════════════════════════════════════════════════════════════════
# PIDController
# ═══════════════════════════════════════════════════════════════════


class TestPIDController:
    def test_initialization_defaults(self):
        pid = PIDController(Kp=1.0, Ki=0.1, Kd=0.01)
        assert pid.Kp == 1.0
        assert pid.Ki == 0.1
        assert pid.Kd == 0.01
        assert pid.dt == 0.01
        assert pid.structure == PIDStructure.PARALLEL
        assert pid.output_limits == (-np.inf, np.inf)
        assert pid.enable_anti_windup is True
        assert pid.integral == 0.0
        assert pid.prev_error == 0.0
        assert pid.prev_measurement == 0.0

    def test_initialization_custom(self):
        pid = PIDController(
            Kp=2.0,
            Ki=0.5,
            Kd=0.1,
            dt=0.05,
            structure=PIDStructure.SERIES,
            output_limits=(-5.0, 5.0),
            enable_anti_windup=False,
        )
        assert pid.Kp == 2.0
        assert pid.Ki == 0.5
        assert pid.Kd == 0.1
        assert pid.dt == 0.05
        assert pid.structure == PIDStructure.SERIES
        assert pid.output_limits == (-5.0, 5.0)
        assert pid.enable_anti_windup is False

    def test_update_constant_error(self):
        pid = PIDController(Kp=1.0, Ki=0.0, Kd=0.0, dt=0.1)
        output = pid.update(setpoint=5.0, measurement=0.0)
        assert output == pytest.approx(5.0)

        # Same error → same P output, no I or D contribution
        output2 = pid.update(setpoint=5.0, measurement=0.0)
        assert output2 == pytest.approx(5.0)

    def test_update_integral_accumulation(self):
        pid = PIDController(Kp=0.0, Ki=1.0, Kd=0.0, dt=0.1)
        output = pid.update(setpoint=1.0, measurement=0.0)
        assert output == pytest.approx(0.1)  # Ki * error * dt

        output2 = pid.update(setpoint=1.0, measurement=0.0)
        assert output2 == pytest.approx(0.2)  # Ki * 2 * error * dt

    def test_update_derivative_on_measurement(self):
        pid = PIDController(Kp=0.0, Ki=0.0, Kd=1.0, dt=0.1)
        # First update: prev_measurement=0, measurement=0 → d_meas=0
        output1 = pid.update(setpoint=1.0, measurement=0.0)
        assert output1 == pytest.approx(0.0)

        # Measurement increases → negative derivative contribution
        output2 = pid.update(setpoint=1.0, measurement=0.5)
        assert output2 < 0.0

    def test_update_series_structure(self):
        pid = PIDController(
            Kp=1.0, Ki=1.0, Kd=0.0, dt=0.1, structure=PIDStructure.SERIES
        )
        output = pid.update(setpoint=1.0, measurement=0.0)
        # Series: Kp * (error + Ki * integral)
        expected = 1.0 * (1.0 + 1.0 * 0.1)
        assert output == pytest.approx(expected)

    def test_update_ideal_structure(self):
        pid = PIDController(
            Kp=1.0, Ki=0.1, Kd=0.01, dt=0.1, structure=PIDStructure.IDEAL
        )
        output = pid.update(setpoint=1.0, measurement=0.0)
        # Ideal behaves same as parallel in this implementation
        expected = 1.0 * 1.0 + 0.1 * 0.1 + 0.0  # P + I + D
        assert output == pytest.approx(expected)

    def test_reset(self):
        pid = PIDController(Kp=1.0, Ki=0.1, Kd=0.01)
        for _ in range(5):
            pid.update(setpoint=1.0, measurement=0.5)

        assert pid.integral != 0.0
        assert pid.prev_error != 0.0
        assert pid.prev_measurement != 0.0

        pid.reset()
        assert pid.integral == 0.0
        assert pid.prev_error == 0.0
        assert pid.prev_measurement == 0.0

    def test_anti_windup_enabled(self):
        pid = PIDController(
            Kp=1.0,
            Ki=1.0,
            Kd=0.0,
            dt=0.01,
            output_limits=(-1.0, 1.0),
            enable_anti_windup=True,
        )

        # Saturate with large error
        for _ in range(100):
            output = pid.update(setpoint=100.0, measurement=0.0)

        assert output == 1.0
        # Integral should be clamped, not grow indefinitely
        assert abs(pid.integral) < 1000.0
        integral_clamped = pid.integral

        # Additional updates should not change integral much
        for _ in range(10):
            pid.update(setpoint=100.0, measurement=0.0)
        assert abs(pid.integral - integral_clamped) < 1e-6

    def test_anti_windup_disabled(self):
        pid = PIDController(
            Kp=1.0,
            Ki=1.0,
            Kd=0.0,
            dt=0.01,
            output_limits=(-1.0, 1.0),
            enable_anti_windup=False,
        )

        for _ in range(100):
            output = pid.update(setpoint=100.0, measurement=0.0)

        assert output == 1.0
        # Integral should grow without clamping
        assert pid.integral > 10.0

    def test_output_limits(self):
        pid = PIDController(
            Kp=10.0, Ki=0.0, Kd=0.0, dt=0.1, output_limits=(-2.0, 2.0)
        )
        output = pid.update(setpoint=1.0, measurement=0.0)
        assert output == 2.0  # Clamped to upper limit

        output2 = pid.update(setpoint=-1.0, measurement=0.0)
        assert output2 == -2.0  # Clamped to lower limit

    def test_output_limits_infinite(self):
        pid = PIDController(Kp=10.0, Ki=0.0, Kd=0.0, dt=0.1)
        output = pid.update(setpoint=1.0, measurement=0.0)
        assert output == 10.0  # Not clamped

    def test_zero_dt(self):
        pid = PIDController(Kp=1.0, Ki=1.0, Kd=1.0, dt=0.0)
        # Division by dt in derivative term → inf, but numpy handles it
        output = pid.update(setpoint=1.0, measurement=0.0)
        # With dt=0, integral doesn't accumulate, derivative is inf → clipped
        assert np.isfinite(output) or output == 0.0

    def test_negative_gains(self):
        pid = PIDController(Kp=-1.0, Ki=-0.1, Kd=-0.01, dt=0.1)
        output = pid.update(setpoint=1.0, measurement=0.0)
        # Negative P gain should produce negative output for positive error
        assert output < 0.0


# ═══════════════════════════════════════════════════════════════════
# PIDTuningPattern
# ═══════════════════════════════════════════════════════════════════


class TestPIDTuningPattern:
    def test_initialization_default(self):
        pattern = PIDTuningPattern()
        assert pattern.config is not None
        assert pattern.config.tuning_method == TuningMethod.ZIEGLER_NICHOLS
        assert pattern.controller is None
        assert "time" in pattern.history
        assert "setpoint" in pattern.history
        assert "measurement" in pattern.history
        assert "control" in pattern.history
        assert "error" in pattern.history

    def test_initialization_custom_config(self):
        cfg = PIDConfig(tuning_method=TuningMethod.MANUAL, Kp=3.0)
        pattern = PIDTuningPattern(config=cfg)
        assert pattern.config.tuning_method == TuningMethod.MANUAL
        assert pattern.config.Kp == 3.0

    def test_manual_tuning(self):
        cfg = PIDConfig(
            tuning_method=TuningMethod.MANUAL,
            Kp=2.0,
            Ki=0.5,
            Kd=0.1,
            simulation_steps=100,
        )
        pattern = PIDTuningPattern(cfg)
        result = pattern.run()

        assert result["tuning_method"] == "manual"
        assert result["controller_parameters"]["Kp"] == 2.0
        assert result["controller_parameters"]["Ki"] == 0.5
        assert result["controller_parameters"]["Kd"] == 0.1
        assert "performance_metrics" in result
        assert "history" in result
        assert "config" in result

    def test_ziegler_nichols_tuning(self):
        cfg = PIDConfig(
            tuning_method=TuningMethod.ZIEGLER_NICHOLS,
            auto_tune_steps=500,
            simulation_steps=500,
        )
        pattern = PIDTuningPattern(cfg)
        result = pattern.run()

        assert result["tuning_method"] == "ziegler_nichols"
        assert "ultimate_gain" in result["tuning_results"]
        assert "ultimate_period" in result["tuning_results"]
        assert "Kp" in result["tuning_results"]
        assert "Ki" in result["tuning_results"]
        assert "Kd" in result["tuning_results"]
        assert result["tuning_results"]["Kp"] > 0
        assert result["tuning_results"]["Ki"] >= 0
        assert result["tuning_results"]["Kd"] >= 0

    def test_cohen_coon_tuning(self):
        cfg = PIDConfig(
            tuning_method=TuningMethod.COHEN_COON,
            simulation_steps=500,
        )
        pattern = PIDTuningPattern(cfg)
        result = pattern.run()

        assert result["tuning_method"] == "cohen_coon"
        assert "Kp" in result["tuning_results"]
        assert "Ki" in result["tuning_results"]
        assert "Kd" in result["tuning_results"]
        assert result["tuning_results"]["Kp"] > 0

    def test_auto_tune_step(self):
        cfg = PIDConfig(
            tuning_method=TuningMethod.AUTO_TUNE_STEP,
            auto_tune_steps=500,
            simulation_steps=500,
        )
        pattern = PIDTuningPattern(cfg)
        result = pattern.run()

        assert result["tuning_method"] == "auto_tune_step"
        assert "estimated_gain" in result["tuning_results"]
        assert "estimated_tau" in result["tuning_results"]
        assert "estimated_theta" in result["tuning_results"]
        assert "Kp" in result["tuning_results"]

    def test_auto_tune_relay(self):
        cfg = PIDConfig(
            tuning_method=TuningMethod.AUTO_TUNE_RELAY,
            auto_tune_steps=500,
            simulation_steps=500,
        )
        pattern = PIDTuningPattern(cfg)
        result = pattern.run()

        assert result["tuning_method"] == "auto_tune_relay"
        assert "Kp" in result["tuning_results"]
        assert result["tuning_results"].get("notes") == "Refined ZN with improved robustness"

    def test_run_output_structure(self):
        cfg = PIDConfig(
            tuning_method=TuningMethod.MANUAL,
            simulation_steps=100,
        )
        pattern = PIDTuningPattern(cfg)
        result = pattern.run()

        assert "tuning_method" in result
        assert "tuning_results" in result
        assert "controller_parameters" in result
        assert "performance_metrics" in result
        assert "history" in result
        assert "config" in result

        # Check performance metrics
        metrics = result["performance_metrics"]
        assert "rise_time" in metrics
        assert "settling_time" in metrics
        assert "overshoot_percent" in metrics
        assert "iae" in metrics
        assert "ise" in metrics
        assert "max_error" in metrics
        assert "mean_error" in metrics

    def test_run_history_lengths(self):
        cfg = PIDConfig(
            tuning_method=TuningMethod.MANUAL,
            simulation_steps=100,
            output_interval=10,
        )
        pattern = PIDTuningPattern(cfg)
        result = pattern.run()

        hist = result["history"]
        assert len(hist["time"]) == len(hist["setpoint"])
        assert len(hist["time"]) == len(hist["measurement"])
        assert len(hist["time"]) == len(hist["control"])
        assert len(hist["time"]) == len(hist["error"])
        # 100 steps / 10 interval = ~10 records
        assert len(hist["time"]) > 0

    def test_run_with_hypothesis(self):
        cfg = PIDConfig(
            tuning_method=TuningMethod.MANUAL,
            simulation_steps=100,
        )
        pattern = PIDTuningPattern(cfg)
        hypothesis = {"text": "test hypothesis"}
        result = pattern.run(hypothesis)
        assert "performance_metrics" in result

    def test_tune_returns_parameters(self):
        cfg = PIDConfig(tuning_method=TuningMethod.ZIEGLER_NICHOLS)
        pattern = PIDTuningPattern(cfg)
        Kp, Ki, Kd = pattern.tune()
        assert Kp > 0
        assert Ki >= 0
        assert Kd >= 0
        assert pattern.controller is not None
        assert pattern.controller.Kp == Kp
        assert pattern.controller.Ki == Ki
        assert pattern.controller.Kd == Kd

    def test_simulate_process(self):
        cfg = PIDConfig(process_gain=1.0, time_constant=1.0, dead_time=0.1)
        pattern = PIDTuningPattern(cfg)
        state = {}
        output = pattern._simulate_process(control_signal=1.0, state=state)
        assert isinstance(output, float)
        assert "y" in state
        assert "y_delayed" in state

    def test_calculate_metrics(self):
        cfg = PIDConfig()
        pattern = PIDTuningPattern(cfg)
        time = np.linspace(0, 1, 100)
        setpoint = np.ones(100)
        measurement = np.linspace(0, 1, 100)
        metrics = pattern._calculate_metrics(setpoint, measurement, time)

        assert "rise_time" in metrics
        assert "settling_time" in metrics
        assert "overshoot_percent" in metrics
        assert "iae" in metrics
        assert "ise" in metrics
        assert "max_error" in metrics
        assert "mean_error" in metrics
        assert all(np.isfinite(v) for v in metrics.values())

    def test_get_metadata(self):
        metadata = PIDTuningPattern.get_metadata()
        assert metadata["id"] == "pid_tuning"
        assert metadata["version"] == "6.0.0"
        assert metadata["name"] == "PID Tuning"
        assert metadata["category"] == "EXTENDED"
        assert "Control Systems" in metadata["domain"]
        assert "parameters" in metadata
        assert isinstance(metadata["parameters"], list)


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_zero_dead_time_cohen_coon(self):
        """Cohen-Coon with zero dead time should handle division safely."""
        cfg = PIDConfig(
            tuning_method=TuningMethod.COHEN_COON,
            dead_time=0.0,
            simulation_steps=100,
        )
        pattern = PIDTuningPattern(cfg)
        result = pattern.run()
        assert result["tuning_method"] == "cohen_coon"
        assert result["tuning_results"]["Kp"] > 0

    def test_very_small_dt(self):
        cfg = PIDConfig(
            tuning_method=TuningMethod.MANUAL,
            dt=1e-6,
            simulation_steps=10,
        )
        pattern = PIDTuningPattern(cfg)
        result = pattern.run()
        assert result["config"]["dt"] == 1e-6

    def test_negative_output_limits(self):
        pid = PIDController(
            Kp=1.0,
            Ki=0.0,
            Kd=0.0,
            dt=0.1,
            output_limits=(-5.0, -1.0),
        )
        output = pid.update(setpoint=10.0, measurement=0.0)
        assert output == -1.0  # Clamped to upper (less negative) limit

        output2 = pid.update(setpoint=-10.0, measurement=0.0)
        assert output2 == -5.0  # Clamped to lower limit

    def test_reversed_output_limits(self):
        """Test behavior when limits are reversed (min > max)."""
        pid = PIDController(
            Kp=1.0,
            Ki=0.0,
            Kd=0.0,
            dt=0.1,
            output_limits=(5.0, -5.0),
        )
        output = pid.update(setpoint=1.0, measurement=0.0)
        # Reversed limits are normalized to (-5.0, 5.0), so 1.0 is within range
        assert output == 1.0

    def test_all_zero_gains(self):
        pid = PIDController(Kp=0.0, Ki=0.0, Kd=0.0, dt=0.1)
        output = pid.update(setpoint=10.0, measurement=0.0)
        assert output == 0.0

    def test_large_simulation_steps(self):
        cfg = PIDConfig(
            tuning_method=TuningMethod.MANUAL,
            simulation_steps=10000,
            output_interval=100,
        )
        pattern = PIDTuningPattern(cfg)
        result = pattern.run()
        assert len(result["history"]["time"]) > 0

    def test_different_pid_structures_run(self):
        for structure in [PIDStructure.PARALLEL, PIDStructure.SERIES, PIDStructure.IDEAL]:
            cfg = PIDConfig(
                tuning_method=TuningMethod.MANUAL,
                pid_structure=structure,
                simulation_steps=100,
            )
            pattern = PIDTuningPattern(cfg)
            result = pattern.run()
            assert result["config"]["pid_structure"] == structure.value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
