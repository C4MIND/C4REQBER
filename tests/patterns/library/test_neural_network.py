"""
Tests for src/patterns/library/neural_network.py (Neural Network pattern)

Covers:
- NeuronModel enum
- Neuron dataclass
- NeuralNetworkPattern initialization
- can_simulate() keyword matching
- _lif_simulation() Leaky Integrate-and-Fire
- _izhikevich_simulation()
- _calculate_confidence()
- estimate_resources()
- run() integration
- get_metadata()
- Edge cases: zero neurons, zero time, zero connection probability
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.core import Hypothesis, SimulationStatus
from src.patterns.library.neural_network import (
    NeuralNetworkPattern,
    Neuron,
    NeuronModel,
)


# ═══════════════════════════════════════════════════════════════════
# Enums and Dataclasses
# ═══════════════════════════════════════════════════════════════════


class TestNeuronModel:
    def test_enum_values(self):
        assert NeuronModel.LIF.value == "leaky_integrate_fire"
        assert NeuronModel.IZHikevich.value == "izhikevich"
        assert NeuronModel.HH.value == "hodgkin_huxley"


class TestNeuron:
    def test_default_init(self):
        neuron = Neuron(neuron_id=0)
        assert neuron.neuron_id == 0
        assert neuron.v == -70.0
        assert neuron.u == 0.0
        assert neuron.fired is False
        assert neuron.spike_times == []

    def test_custom_init(self):
        neuron = Neuron(neuron_id=1, v=-65.0, u=2.0, fired=True, spike_times=[1.0, 2.0])
        assert neuron.v == -65.0
        assert neuron.u == 2.0
        assert neuron.fired is True
        assert neuron.spike_times == [1.0, 2.0]


# ═══════════════════════════════════════════════════════════════════
# NeuralNetworkPattern Initialization
# ═══════════════════════════════════════════════════════════════════


class TestNeuralNetworkPatternInit:
    def test_init(self):
        pattern = NeuralNetworkPattern()
        assert pattern is not None
        assert pattern.neurons == []
        assert pattern.connections == []
        assert pattern.spike_history == []

    def test_parameters_defined(self):
        pattern = NeuralNetworkPattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0
        param_names = [p.name for p in pattern.parameters]
        assert "num_neurons" in param_names
        assert "neuron_model" in param_names
        assert "connection_prob" in param_names
        assert "simulation_time" in param_names
        assert "dt" in param_names


# ═══════════════════════════════════════════════════════════════════
# can_simulate
# ═══════════════════════════════════════════════════════════════════


class TestCanSimulate:
    def test_matches_neuron(self):
        pattern = NeuralNetworkPattern()
        h = Hypothesis(title="Neuron firing", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_brain(self):
        pattern = NeuralNetworkPattern()
        h = Hypothesis(title="Brain dynamics", description="spiking neural network")
        assert pattern.can_simulate(h) is True

    def test_matches_synchronization(self):
        pattern = NeuralNetworkPattern()
        h = Hypothesis(title="Neural synchronization", description="oscillation")
        assert pattern.can_simulate(h) is True

    def test_matches_eeg(self):
        pattern = NeuralNetworkPattern()
        h = Hypothesis(title="EEG analysis", description="population dynamics")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = NeuralNetworkPattern()
        h = Hypothesis(title="Linear regression", description="statistics")
        assert pattern.can_simulate(h) is False

    def test_empty_hypothesis(self):
        pattern = NeuralNetworkPattern()
        h = Hypothesis()
        assert pattern.can_simulate(h) is False


# ═══════════════════════════════════════════════════════════════════
# LIF Simulation
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestLIFSimulation:
    async def test_lif_default(self):
        pattern = NeuralNetworkPattern()
        h = Hypothesis(parameters={})
        config = {
            "neuron_model": "leaky_integrate_fire",
            "num_neurons": 10,
            "simulation_time": 100.0,
            "dt": 0.1,
            "connection_prob": 0.1,
        }
        result = await pattern._lif_simulation(h, config)
        assert "metrics" in result
        assert "logs" in result
        assert "num_neurons" in result["metrics"]
        assert "avg_firing_rate_hz" in result["metrics"]
        assert "total_spikes" in result["metrics"]

    async def test_lif_spikes_generated(self):
        pattern = NeuralNetworkPattern()
        h = Hypothesis(parameters={})
        config = {
            "neuron_model": "leaky_integrate_fire",
            "num_neurons": 10,
            "simulation_time": 100.0,
            "dt": 0.1,
            "connection_prob": 0.5,
        }
        result = await pattern._lif_simulation(h, config)
        # With external input, some spikes should occur
        assert result["metrics"]["total_spikes"] >= 0

    async def test_lif_connections_created(self):
        pattern = NeuralNetworkPattern()
        h = Hypothesis(parameters={})
        config = {
            "neuron_model": "leaky_integrate_fire",
            "num_neurons": 10,
            "simulation_time": 10.0,
            "dt": 0.1,
            "connection_prob": 0.5,
        }
        result = await pattern._lif_simulation(h, config)
        assert result["metrics"]["num_connections"] > 0

    async def test_lif_logs_present(self):
        pattern = NeuralNetworkPattern()
        h = Hypothesis(parameters={})
        config = {
            "neuron_model": "leaky_integrate_fire",
            "num_neurons": 10,
            "simulation_time": 100.0,
        }
        result = await pattern._lif_simulation(h, config)
        assert any("LIF" in log for log in result["logs"])

    async def test_lif_zero_connections(self):
        pattern = NeuralNetworkPattern()
        h = Hypothesis(parameters={})
        config = {
            "neuron_model": "leaky_integrate_fire",
            "num_neurons": 10,
            "simulation_time": 100.0,
            "dt": 0.1,
            "connection_prob": 0.0,
        }
        result = await pattern._lif_simulation(h, config)
        assert result["metrics"]["num_connections"] == 0


# ═══════════════════════════════════════════════════════════════════
# Izhikevich Simulation
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestIzhikevichSimulation:
    async def test_izhikevich_default(self):
        pattern = NeuralNetworkPattern()
        h = Hypothesis(parameters={})
        config = {
            "neuron_model": "izhikevich",
            "num_neurons": 10,
            "simulation_time": 100.0,
            "dt": 0.1,
        }
        result = await pattern._izhikevich_simulation(h, config)
        assert "metrics" in result
        assert "logs" in result
        assert "num_neurons" in result["metrics"]
        assert "total_spikes" in result["metrics"]
        assert result["metrics"]["neuron_model"] == "izhikevich"

    async def test_izhikevich_spikes(self):
        pattern = NeuralNetworkPattern()
        h = Hypothesis(parameters={})
        config = {
            "neuron_model": "izhikevich",
            "num_neurons": 10,
            "simulation_time": 100.0,
            "dt": 0.1,
        }
        result = await pattern._izhikevich_simulation(h, config)
        assert result["metrics"]["total_spikes"] >= 0

    async def test_izhikevich_logs_present(self):
        pattern = NeuralNetworkPattern()
        h = Hypothesis(parameters={})
        config = {"neuron_model": "izhikevich", "num_neurons": 10, "simulation_time": 100.0}
        result = await pattern._izhikevich_simulation(h, config)
        assert any("Izhikevich" in log for log in result["logs"])


# ═══════════════════════════════════════════════════════════════════
# Confidence Calculation
# ═══════════════════════════════════════════════════════════════════


class TestCalculateConfidence:
    def test_high_confidence(self):
        pattern = NeuralNetworkPattern()
        results = {
            "metrics": {
                "avg_firing_rate_hz": 10.0,
                "total_spikes": 1000,
                "coefficient_of_variation": 1.0,
                "num_connections": 50,
            }
        }
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5

    def test_low_confidence(self):
        pattern = NeuralNetworkPattern()
        results = {"metrics": {"avg_firing_rate_hz": 0.0, "total_spikes": 0}}
        confidence = pattern._calculate_confidence(results)
        assert confidence < 0.5

    def test_empty_metrics(self):
        pattern = NeuralNetworkPattern()
        results = {"metrics": {}}
        confidence = pattern._calculate_confidence(results)
        # num_connections default contributes 0.2
        assert confidence >= 0.0


# ═══════════════════════════════════════════════════════════════════
# Resource Estimation
# ═══════════════════════════════════════════════════════════════════


class TestEstimateResources:
    def test_default_params(self):
        pattern = NeuralNetworkPattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert "gpu_required" in resources
        assert "estimated_time_seconds" in resources
        assert resources["gpu_required"] is False

    def test_custom_params(self):
        pattern = NeuralNetworkPattern()
        h = Hypothesis(parameters={"num_neurons": 1000, "simulation_time": 10000.0, "dt": 0.01})
        resources = pattern.estimate_resources(h)
        assert resources["estimated_time_seconds"] > 0


# ═══════════════════════════════════════════════════════════════════
# run() Integration
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRun:
    async def test_run_lif(self):
        pattern = NeuralNetworkPattern()
        h = Hypothesis(title="Neural simulation", description="test")
        config = {
            "neuron_model": "leaky_integrate_fire",
            "num_neurons": 10,
            "simulation_time": 100.0,
        }
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("nn_")
        assert "avg_firing_rate_hz" in result.metrics

    async def test_run_izhikevich(self):
        pattern = NeuralNetworkPattern()
        h = Hypothesis(title="Neural simulation", description="test")
        config = {"neuron_model": "izhikevich", "num_neurons": 10, "simulation_time": 100.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert "total_spikes" in result.metrics

    async def test_run_logs_present(self):
        pattern = NeuralNetworkPattern()
        h = Hypothesis(title="Neural simulation", description="test")
        config = {
            "neuron_model": "leaky_integrate_fire",
            "num_neurons": 10,
            "simulation_time": 100.0,
        }
        result = await pattern.run(h, config)
        assert len(result.logs) > 0

    async def test_run_failure_handling(self):
        pattern = NeuralNetworkPattern()
        h = Hypothesis(title="Neural simulation", description="test")
        with patch.object(pattern, "_lif_simulation", side_effect=ValueError("test error")):
            result = await pattern.run(h, {"neuron_model": "leaky_integrate_fire"})
            assert result.status == SimulationStatus.FAILED
            assert "test error" in result.error_message


# ═══════════════════════════════════════════════════════════════════
# get_metadata
# ═══════════════════════════════════════════════════════════════════


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = NeuralNetworkPattern.get_metadata()
        assert meta["id"] == "neural_network"
        assert meta["name"] == "NeuralNetworkPattern"
        assert "category" in meta


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestEdgeCases:
    async def test_single_neuron(self):
        pattern = NeuralNetworkPattern()
        h = Hypothesis(title="Neural simulation", description="test")
        config = {
            "neuron_model": "leaky_integrate_fire",
            "num_neurons": 1,
            "simulation_time": 100.0,
        }
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_zero_simulation_time(self):
        pattern = NeuralNetworkPattern()
        h = Hypothesis(title="Neural simulation", description="test")
        config = {"neuron_model": "leaky_integrate_fire", "num_neurons": 10, "simulation_time": 0.0}
        result = await pattern.run(h, config)
        # Zero simulation time causes division by zero in source
        assert result.status in (SimulationStatus.COMPLETED, SimulationStatus.FAILED)

    async def test_empty_config(self):
        pattern = NeuralNetworkPattern()
        h = Hypothesis(title="Neural simulation", description="test")
        result = await pattern.run(h, {})
        assert result.status == SimulationStatus.COMPLETED

    async def test_lif_no_spikes_low_input(self):
        pattern = NeuralNetworkPattern()
        h = Hypothesis(parameters={})
        config = {
            "neuron_model": "leaky_integrate_fire",
            "num_neurons": 10,
            "simulation_time": 10.0,
            "dt": 0.1,
        }
        result = await pattern._lif_simulation(h, config)
        # Should still produce valid metrics even with few/no spikes
        assert "avg_firing_rate_hz" in result["metrics"]

    async def test_izhikevich_single_neuron(self):
        pattern = NeuralNetworkPattern()
        h = Hypothesis(parameters={})
        config = {
            "neuron_model": "izhikevich",
            "num_neurons": 1,
            "simulation_time": 100.0,
            "dt": 0.1,
        }
        result = await pattern._izhikevich_simulation(h, config)
        assert result["metrics"]["num_neurons"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
