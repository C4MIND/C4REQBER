"""
Tests for src/patterns/library/hodgkin_huxley.py (Hodgkin-Huxley Neuron Model)

Covers:
- StimulusType enum
- HHConfig dataclass
- HodgkinHuxleyPattern initialization
- can_simulate() keyword matching
- _parse_config()
- _simulate_hh() simulation
- Gating variable rate functions (_alpha_m, _beta_m, _alpha_h, _beta_h, _alpha_n, _beta_n)
- _get_stimulus() for different stimulus types
- _detect_spikes()
- _calculate_metrics()
- _calculate_confidence()
- estimate_resources()
- run() integration
- get_metadata()
- Edge cases: zero stimulus, various stimulus types, edge voltages
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.hodgkin_huxley import (
    HodgkinHuxleyPattern,
    HHConfig,
    StimulusType,
)
from src.patterns.core import Hypothesis, SimulationStatus



# ═══════════════════════════════════════════════════════════════════
# Enums and Dataclasses
# ═══════════════════════════════════════════════════════════════════


class TestStimulusType:
    def test_enum_values(self):
        assert StimulusType.STEP.value == "step"
        assert StimulusType.RAMP.value == "ramp"
        assert StimulusType.PULSE.value == "pulse"
        assert StimulusType.SINUSOIDAL.value == "sinusoidal"


class TestHHConfig:
    def test_default_init(self):
        cfg = HHConfig()
        assert cfg.C_m == 1.0
        assert cfg.g_Na == 120.0
        assert cfg.g_K == 36.0
        assert cfg.g_L == 0.3
        assert cfg.E_Na == 50.0
        assert cfg.E_K == -77.0
        assert cfg.E_L == -54.387
        assert cfg.t_max == 50.0
        assert cfg.dt == 0.01
        assert cfg.I_inj == 10.0
        assert cfg.stim_start == 5.0
        assert cfg.stim_end == 30.0
        assert cfg.stim_type == StimulusType.STEP
        assert cfg.V0 == -65.0

    def test_custom_params(self):
        cfg = HHConfig(C_m=2.0, g_Na=100.0, I_inj=20.0, stim_type=StimulusType.RAMP)
        assert cfg.C_m == 2.0
        assert cfg.g_Na == 100.0
        assert cfg.I_inj == 20.0
        assert cfg.stim_type == StimulusType.RAMP

    def test_to_dict(self):
        cfg = HHConfig()
        d = cfg.to_dict()
        assert d["C_m"] == 1.0
        assert d["g_Na"] == 120.0
        assert d["stim_type"] == "step"


# ═══════════════════════════════════════════════════════════════════
# HodgkinHuxleyPattern Initialization
# ═══════════════════════════════════════════════════════════════════


class TestHodgkinHuxleyPatternInit:
    def test_init(self):
        pattern = HodgkinHuxleyPattern()
        assert pattern is not None
        assert hasattr(pattern, "config")
        assert pattern.config is not None

    def test_parameters_defined(self):
        pattern = HodgkinHuxleyPattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0
        param_names = [p.name for p in pattern.parameters]
        assert "C_m" in param_names
        assert "g_Na" in param_names
        assert "g_K" in param_names
        assert "I_inj" in param_names
        assert "t_max" in param_names
        assert "stim_type" in param_names


# ═══════════════════════════════════════════════════════════════════
# can_simulate
# ═══════════════════════════════════════════════════════════════════


class TestCanSimulate:
    def test_matches_hodgkin_huxley(self):
        pattern = HodgkinHuxleyPattern()
        h = Hypothesis(title="Hodgkin-Huxley model", description="action potential")
        assert pattern.can_simulate(h) is True

    def test_matches_action_potential(self):
        pattern = HodgkinHuxleyPattern()
        h = Hypothesis(title="Neuron spike", description="action potential generation")
        assert pattern.can_simulate(h) is True

    def test_matches_ion_channel(self):
        pattern = HodgkinHuxleyPattern()
        h = Hypothesis(title="Ion channel dynamics", description="voltage-gated channels")
        assert pattern.can_simulate(h) is True

    def test_matches_neuron(self):
        pattern = HodgkinHuxleyPattern()
        h = Hypothesis(title="Neuron membrane", description="biophysical model")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = HodgkinHuxleyPattern()
        h = Hypothesis(title="Stock market", description="price prediction")
        assert pattern.can_simulate(h) is False

    def test_empty_hypothesis(self):
        pattern = HodgkinHuxleyPattern()
        h = Hypothesis()
        assert pattern.can_simulate(h) is False


# ═══════════════════════════════════════════════════════════════════
# Config Parsing
# ═══════════════════════════════════════════════════════════════════


class TestParseConfig:
    def test_default_parsing(self):
        pattern = HodgkinHuxleyPattern()
        cfg = pattern._parse_config({})
        assert cfg.C_m == 1.0
        assert cfg.g_Na == 120.0

    def test_custom_parsing(self):
        pattern = HodgkinHuxleyPattern()
        cfg = pattern._parse_config({"C_m": 2.0, "g_Na": 100.0, "I_inj": 20.0, "stim_type": "ramp"})
        assert cfg.C_m == 2.0
        assert cfg.g_Na == 100.0
        assert cfg.I_inj == 20.0
        assert cfg.stim_type == StimulusType.RAMP

    def test_all_stimulus_types(self):
        pattern = HodgkinHuxleyPattern()
        for stim_type in ["step", "ramp", "pulse", "sinusoidal"]:
            cfg = pattern._parse_config({"stim_type": stim_type})
            assert cfg.stim_type.value == stim_type


# ═══════════════════════════════════════════════════════════════════
# Gating Variable Rate Functions
# ═══════════════════════════════════════════════════════════════════


class TestGatingRates:
    def test_alpha_m_returns_positive(self):
        pattern = HodgkinHuxleyPattern()
        for V in [-80, -65, -40, -20, 0, 20]:
            result = pattern._alpha_m(V)
            assert result >= 0

    def test_beta_m_returns_positive(self):
        pattern = HodgkinHuxleyPattern()
        for V in [-80, -65, -40, -20, 0, 20]:
            result = pattern._beta_m(V)
            assert result > 0

    def test_alpha_h_returns_positive(self):
        pattern = HodgkinHuxleyPattern()
        for V in [-80, -65, -40, -20, 0, 20]:
            result = pattern._alpha_h(V)
            assert result >= 0

    def test_beta_h_returns_positive(self):
        pattern = HodgkinHuxleyPattern()
        for V in [-80, -65, -40, -20, 0, 20]:
            result = pattern._beta_h(V)
            assert result > 0

    def test_alpha_n_returns_positive(self):
        pattern = HodgkinHuxleyPattern()
        for V in [-80, -65, -40, -20, 0, 20]:
            result = pattern._alpha_n(V)
            assert result >= 0

    def test_beta_n_returns_positive(self):
        pattern = HodgkinHuxleyPattern()
        for V in [-80, -65, -40, -20, 0, 20]:
            result = pattern._beta_n(V)
            assert result > 0


# ═══════════════════════════════════════════════════════════════════
# Stimulus Functions
# ═══════════════════════════════════════════════════════════════════


class TestGetStimulus:
    def test_step_stimulus(self):
        pattern = HodgkinHuxleyPattern()
        pattern.config = HHConfig(stim_type=StimulusType.STEP, stim_start=5.0, stim_end=30.0, I_inj=10.0)
        assert pattern._get_stimulus(0.0) == 0.0
        assert pattern._get_stimulus(5.0) == 10.0
        assert pattern._get_stimulus(15.0) == 10.0
        assert pattern._get_stimulus(30.0) == 0.0

    def test_ramp_stimulus(self):
        pattern = HodgkinHuxleyPattern()
        pattern.config = HHConfig(stim_type=StimulusType.RAMP, stim_start=5.0, stim_end=25.0, I_inj=10.0)
        assert pattern._get_stimulus(0.0) == 0.0
        assert pattern._get_stimulus(5.0) == pytest.approx(0.0, abs=0.01)
        assert pattern._get_stimulus(15.0) == pytest.approx(5.0, abs=0.01)

    def test_pulse_stimulus(self):
        pattern = HodgkinHuxleyPattern()
        pattern.config = HHConfig(stim_type=StimulusType.PULSE, stim_start=5.0, stim_end=30.0, I_inj=10.0)
        assert pattern._get_stimulus(0.0) == 0.0
        assert pattern._get_stimulus(5.5) == 10.0  # During 1ms pulse
        assert pattern._get_stimulus(6.0) == 0.0  # After 1ms pulse ends

    def test_sinusoidal_stimulus(self):
        pattern = HodgkinHuxleyPattern()
        pattern.config = HHConfig(stim_type=StimulusType.SINUSOIDAL, stim_start=5.0, stim_end=30.0, I_inj=10.0)
        stim = pattern._get_stimulus(10.0)
        assert -10.0 <= stim <= 10.0


# ═══════════════════════════════════════════════════════════════════
# Spike Detection
# ═══════════════════════════════════════════════════════════════════


class TestDetectSpikes:
    def test_no_spikes(self):
        pattern = HodgkinHuxleyPattern()
        t = np.array([0, 1, 2, 3, 4])
        V = np.array([-65, -64, -63, -62, -61])
        spikes = pattern._detect_spikes(t, V, -20.0)
        assert len(spikes) == 0

    def test_single_spike(self):
        pattern = HodgkinHuxleyPattern()
        t = np.array([0, 1, 2, 3, 4])
        V = np.array([-65, -30, 10, -50, -65])
        spikes = pattern._detect_spikes(t, V, -20.0)
        assert len(spikes) == 1

    def test_multiple_spikes(self):
        pattern = HodgkinHuxleyPattern()
        t = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8])
        V = np.array([-65, -30, 10, -50, -65, -30, 10, -50, -65])
        spikes = pattern._detect_spikes(t, V, -20.0)
        assert len(spikes) == 2


# ═══════════════════════════════════════════════════════════════════
# Simulation
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestSimulateHH:
    async def test_simulation_completes(self):
        pattern = HodgkinHuxleyPattern()
        pattern.config = HHConfig(t_max=10.0, dt=0.01, I_inj=10.0)
        result = await pattern._simulate_hh()
        assert "metrics" in result
        assert "logs" in result
        assert "time" in result
        assert "voltage" in result

    async def test_step_stimulus_generates_spikes(self):
        pattern = HodgkinHuxleyPattern()
        pattern.config = HHConfig(t_max=50.0, dt=0.01, I_inj=10.0, stim_type=StimulusType.STEP)
        result = await pattern._simulate_hh()
        assert result["metrics"]["num_spikes"] >= 1

    async def test_metrics_structure(self):
        pattern = HodgkinHuxleyPattern()
        pattern.config = HHConfig(t_max=20.0, dt=0.01)
        result = await pattern._simulate_hh()
        metrics = result["metrics"]
        assert "resting_V" in metrics
        assert "max_V" in metrics
        assert "min_V" in metrics
        assert "num_spikes" in metrics
        assert "spike_frequency" in metrics


# ═══════════════════════════════════════════════════════════════════
# Results Analysis
# ═══════════════════════════════════════════════════════════════════


class TestCalculateMetrics:
    def test_metrics_calculation(self):
        pattern = HodgkinHuxleyPattern()
        pattern.config = HHConfig()
        t = np.linspace(0, 50, 5000)
        V = np.sin(t) * 50  # Fake voltage trace
        m = np.ones(5000) * 0.5
        h = np.ones(5000) * 0.5
        n = np.ones(5000) * 0.5
        I_Na = np.ones(5000)
        I_K = np.ones(5000)
        spike_times = [10.0, 20.0]

        metrics = pattern._calculate_metrics(t, V, m, h, n, I_Na, I_K, spike_times)
        assert "resting_V" in metrics
        assert "max_V" in metrics
        assert "num_spikes" in metrics
        assert metrics["num_spikes"] == 2


# ═══════════════════════════════════════════════════════════════════
# Confidence Calculation
# ═══════════════════════════════════════════════════════════════════


class TestCalculateConfidence:
    def test_high_confidence(self):
        pattern = HodgkinHuxleyPattern()
        pattern.config = HHConfig(g_Na=120.0, g_K=36.0)
        results = {"metrics": {"resting_V": -65.0, "ap_amplitude": 100.0, "spike_frequency": 50.0}}
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5

    def test_low_confidence(self):
        pattern = HodgkinHuxleyPattern()
        pattern.config = HHConfig()
        results = {"metrics": {"resting_V": -30.0, "ap_amplitude": 20.0}}
        confidence = pattern._calculate_confidence(results)
        assert confidence < 0.9


# ═══════════════════════════════════════════════════════════════════
# Resource Estimation
# ═══════════════════════════════════════════════════════════════════


class TestEstimateResources:
    def test_default_params(self):
        pattern = HodgkinHuxleyPattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert "gpu_required" in resources
        assert "estimated_time_seconds" in resources
        assert resources["gpu_required"] is False

    def test_long_simulation(self):
        pattern = HodgkinHuxleyPattern()
        h = Hypothesis(parameters={"t_max": 500.0, "dt": 0.001})
        resources = pattern.estimate_resources(h)
        assert resources["estimated_time_seconds"] > 0


# ═══════════════════════════════════════════════════════════════════
# run() Integration
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRun:
    async def test_run_default(self):
        pattern = HodgkinHuxleyPattern()
        h = Hypothesis(title="Hodgkin-Huxley", description="action potential")
        config = {"t_max": 20.0, "dt": 0.01}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("hh_")

    async def test_run_with_step(self):
        pattern = HodgkinHuxleyPattern()
        h = Hypothesis(title="Neuron", description="spike")
        config = {"t_max": 30.0, "I_inj": 15.0, "stim_type": "step"}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert "num_spikes" in result.metrics or "spike_frequency" in result.metrics

    async def test_run_logs_present(self):
        pattern = HodgkinHuxleyPattern()
        h = Hypothesis(title="Neuron", description="spike")
        config = {"t_max": 20.0}
        result = await pattern.run(h, config)
        assert len(result.logs) > 0


# ═══════════════════════════════════════════════════════════════════
# get_metadata
# ═══════════════════════════════════════════════════════════════════


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = HodgkinHuxleyPattern.get_metadata()
        assert meta["id"] == "hodgkin_huxley"
        assert meta["name"] == "Hodgkin-Huxley Neuron Model"
        assert "category" in meta
        assert "parameters" in meta


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
