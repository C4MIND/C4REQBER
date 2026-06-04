"""
Tests for src/patterns/library/circuit_simulation.py

Covers:
- ComponentType and AnalysisType enums
- Component and CircuitConfig dataclasses
- CircuitSimulationPattern initialization
- can_simulate() keyword matching
- _parse_config()
- _build_circuit() for all circuit types
- _build_rc_filter(), _build_rlc_tank(), _build_amplifier()
- _build_oscillator(), _build_regulator(), _build_generic_circuit()
- _run_fallback_simulation()
- _run_monte_carlo()
- _calculate_confidence()
- estimate_resources()
- run() integration
- get_metadata()
- Edge cases: empty components, zero tolerance, extreme temperatures
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.circuit_simulation import (
    AnalysisType,
    CircuitConfig,
    CircuitSimulationPattern,
    Component,
    ComponentType,
)
from src.patterns.core import Hypothesis, SimulationStatus



# ═══════════════════════════════════════════════════════════════════
# Enums and Dataclasses
# ═══════════════════════════════════════════════════════════════════


class TestComponentType:
    def test_enum_members(self):
        assert ComponentType.RESISTOR.name == "RESISTOR"
        assert ComponentType.CAPACITOR.name == "CAPACITOR"
        assert ComponentType.INDUCTOR.name == "INDUCTOR"
        assert ComponentType.VOLTAGE_SOURCE.name == "VOLTAGE_SOURCE"
        assert ComponentType.CURRENT_SOURCE.name == "CURRENT_SOURCE"
        assert ComponentType.DIODE.name == "DIODE"
        assert ComponentType.TRANSISTOR_NPN.name == "TRANSISTOR_NPN"
        assert ComponentType.TRANSISTOR_PNP.name == "TRANSISTOR_PNP"
        assert ComponentType.MOSFET.name == "MOSFET"
        assert ComponentType.OPAMP.name == "OPAMP"


class TestAnalysisType:
    def test_enum_values(self):
        assert AnalysisType.DC.value == "dc"
        assert AnalysisType.AC.value == "ac"
        assert AnalysisType.TRANSIENT.value == "transient"
        assert AnalysisType.OP.value == "operating_point"
        assert AnalysisType.NOISE.value == "noise"
        assert AnalysisType.DISTORTION.value == "distortion"
        assert AnalysisType.SENSITIVITY.value == "sensitivity"


class TestComponent:
    def test_default_init(self):
        comp = Component(
            name="R1",
            component_type=ComponentType.RESISTOR,
            nodes=["a", "b"],
            value=1000.0,
        )
        assert comp.name == "R1"
        assert comp.component_type == ComponentType.RESISTOR
        assert comp.nodes == ["a", "b"]
        assert comp.value == 1000.0
        assert comp.parameters == {}
        assert comp.model is None

    def test_custom_init(self):
        comp = Component(
            name="Q1",
            component_type=ComponentType.TRANSISTOR_NPN,
            nodes=["c", "b", "e"],
            value=0,
            model="2N2222",
            parameters={"beta": 200},
        )
        assert comp.model == "2N2222"
        assert comp.parameters["beta"] == 200


class TestCircuitConfig:
    def test_default_init(self):
        cfg = CircuitConfig()
        assert cfg.analysis_type == AnalysisType.TRANSIENT
        assert cfg.t_start == 0.0
        assert cfg.t_stop == 1e-3
        assert cfg.t_step == 1e-6
        assert cfg.f_start == 1.0
        assert cfg.f_stop == 1e6
        assert cfg.n_points == 100
        assert cfg.temperature == 27.0
        assert cfg.monte_carlo_runs == 0
        assert cfg.tolerance == 0.05

    def test_custom_init(self):
        cfg = CircuitConfig(
            analysis_type=AnalysisType.AC,
            t_stop=1e-2,
            temperature=85.0,
            monte_carlo_runs=10,
        )
        assert cfg.analysis_type == AnalysisType.AC
        assert cfg.t_stop == 1e-2
        assert cfg.temperature == 85.0
        assert cfg.monte_carlo_runs == 10


# ═══════════════════════════════════════════════════════════════════
# CircuitSimulationPattern Initialization
# ═══════════════════════════════════════════════════════════════════


class TestCircuitSimulationPatternInit:
    def test_init(self):
        pattern = CircuitSimulationPattern()
        assert pattern is not None
        assert pattern.components == []
        assert pattern.results == {}

    def test_parameters_defined(self):
        pattern = CircuitSimulationPattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0
        param_names = [p.name for p in pattern.parameters]
        assert "analysis_type" in param_names
        assert "t_stop" in param_names
        assert "temperature" in param_names


# ═══════════════════════════════════════════════════════════════════
# can_simulate
# ═══════════════════════════════════════════════════════════════════


class TestCanSimulate:
    def test_matches_circuit(self):
        pattern = CircuitSimulationPattern()
        h = Hypothesis(title="RC filter circuit", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_amplifier(self):
        pattern = CircuitSimulationPattern()
        h = Hypothesis(title="Transistor amplifier", description="gain analysis")
        assert pattern.can_simulate(h) is True

    def test_matches_voltage(self):
        pattern = CircuitSimulationPattern()
        h = Hypothesis(title="Voltage regulator", description="power supply")
        assert pattern.can_simulate(h) is True

    def test_matches_filter(self):
        pattern = CircuitSimulationPattern()
        h = Hypothesis(title="Low pass filter", description="frequency response")
        assert pattern.can_simulate(h) is True

    def test_matches_noise(self):
        pattern = CircuitSimulationPattern()
        h = Hypothesis(title="Circuit noise analysis", description="thermal noise")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = CircuitSimulationPattern()
        h = Hypothesis(title="Linear regression", description="statistics")
        assert pattern.can_simulate(h) is False

    def test_empty_hypothesis(self):
        pattern = CircuitSimulationPattern()
        h = Hypothesis()
        assert pattern.can_simulate(h) is False


# ═══════════════════════════════════════════════════════════════════
# Config Parsing
# ═══════════════════════════════════════════════════════════════════


class TestParseConfig:
    def test_default_parsing(self):
        pattern = CircuitSimulationPattern()
        cfg = pattern._parse_config({})
        assert cfg.analysis_type == AnalysisType.TRANSIENT
        assert cfg.t_stop == 1e-3
        assert cfg.temperature == 27.0

    def test_custom_parsing(self):
        pattern = CircuitSimulationPattern()
        cfg = pattern._parse_config({
            "analysis_type": "ac",
            "t_stop": 1e-2,
            "temperature": 85.0,
            "monte_carlo_runs": 10,
        })
        assert cfg.analysis_type == AnalysisType.AC
        assert cfg.t_stop == 1e-2
        assert cfg.temperature == 85.0
        assert cfg.monte_carlo_runs == 10

    def test_random_seed(self):
        pattern = CircuitSimulationPattern()
        cfg = pattern._parse_config({"random_seed": 42})
        assert cfg.random_seed == 42


# ═══════════════════════════════════════════════════════════════════
# Circuit Building
# ═══════════════════════════════════════════════════════════════════


class TestBuildCircuit:
    def test_build_rc_filter(self):
        pattern = CircuitSimulationPattern()
        h = Hypothesis(parameters={"circuit_type": "rc_filter"})
        pattern.builder.build_from_params(h.parameters)
        assert len(pattern.builder.components) == 3
        names = [c.name for c in pattern.builder.components]
        assert "R1" in names
        assert "C1" in names
        assert "V1" in names

    def test_build_rlc_tank(self):
        pattern = CircuitSimulationPattern()
        h = Hypothesis(parameters={"circuit_type": "rlc_tank"})
        pattern.builder.build_from_params(h.parameters)
        assert len(pattern.builder.components) == 4
        names = [c.name for c in pattern.builder.components]
        assert "L1" in names
        assert "C1" in names
        assert "R1" in names

    def test_build_amplifier(self):
        pattern = CircuitSimulationPattern()
        h = Hypothesis(parameters={"circuit_type": "amplifier"})
        pattern.builder.build_from_params(h.parameters)
        assert len(pattern.builder.components) == 7
        names = [c.name for c in pattern.builder.components]
        assert "Q1" in names
        assert "Rc" in names
        assert "Rb" in names

    def test_build_oscillator(self):
        pattern = CircuitSimulationPattern()
        h = Hypothesis(parameters={"circuit_type": "oscillator"})
        pattern.builder.build_from_params(h.parameters)
        assert len(pattern.builder.components) == 3
        names = [c.name for c in pattern.builder.components]
        assert "R1" in names
        assert "C1" in names

    def test_build_regulator(self):
        pattern = CircuitSimulationPattern()
        h = Hypothesis(parameters={"circuit_type": "voltage_regulator"})
        pattern.builder.build_from_params(h.parameters)
        assert len(pattern.builder.components) == 4
        names = [c.name for c in pattern.builder.components]
        assert "R1" in names
        assert "D1" in names
        assert "C1" in names

    def test_build_generic(self):
        pattern = CircuitSimulationPattern()
        h = Hypothesis(parameters={"circuit_type": "generic"})
        pattern.builder.build_from_params(h.parameters)
        assert len(pattern.builder.components) >= 2

    def test_build_from_components_list(self):
        pattern = CircuitSimulationPattern()
        h = Hypothesis(
            parameters={
                "components": [
                    {"name": "R1", "type": "resistor", "value": 1000},
                    {"name": "C1", "type": "capacitor", "value": 1e-6},
                ]
            }
        )
        pattern.builder.build_from_params(h.parameters)
        assert len(pattern.builder.components) == 2
        assert pattern.builder.components[0].name == "R1"
        assert pattern.builder.components[1].name == "C1"


# ═══════════════════════════════════════════════════════════════════
# Fallback Simulation
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestFallbackSimulation:
    async def test_rc_circuit(self):
        pattern = CircuitSimulationPattern()
        pattern.builder.components = [
            Component("R1", ComponentType.RESISTOR, ["in", "out"], 1000.0),
            Component("C1", ComponentType.CAPACITOR, ["out", "ground"], 1e-6),
        ]
        cfg = CircuitConfig(analysis_type=AnalysisType.TRANSIENT)
        result = await pattern.simulator.run(pattern.builder.components, cfg)
        assert "metrics" in result
        assert "logs" in result

    async def test_rlc_circuit(self):
        pattern = CircuitSimulationPattern()
        pattern.builder.components = [
            Component("L1", ComponentType.INDUCTOR, ["node1", "out"], 1e-3),
            Component("C1", ComponentType.CAPACITOR, ["out", "ground"], 1e-9),
            Component("R1", ComponentType.RESISTOR, ["out", "ground"], 100.0),
        ]
        cfg = CircuitConfig()
        result = await pattern.simulator.run(pattern.builder.components, cfg)
        assert "metrics" in result

    async def test_voltage_source_only(self):
        pattern = CircuitSimulationPattern()
        pattern.builder.components = [
            Component("V1", ComponentType.VOLTAGE_SOURCE, ["in", "ground"], 5.0),
        ]
        cfg = CircuitConfig()
        result = await pattern.simulator.run(pattern.builder.components, cfg)
        assert "metrics" in result
        assert "logs" in result

    async def test_empty_components(self):
        pattern = CircuitSimulationPattern()
        pattern.builder.components = []
        cfg = CircuitConfig()
        result = await pattern.simulator.run(pattern.builder.components, cfg)
        assert "metrics" in result
        assert "logs" in result


# ═══════════════════════════════════════════════════════════════════
# Monte Carlo
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestMonteCarlo:
    async def test_monte_carlo_rc(self):
        pattern = CircuitSimulationPattern()
        pattern.rng = np.random.default_rng(42)
        pattern.builder.components = [
            Component("R1", ComponentType.RESISTOR, ["in", "out"], 1000.0),
            Component("C1", ComponentType.CAPACITOR, ["out", "ground"], 1e-6),
        ]
        cfg = CircuitConfig(monte_carlo_runs=5, tolerance=0.05)
        result = await pattern.simulator.run(pattern.builder.components, cfg)
        assert "metrics" in result

    async def test_zero_runs(self):
        pattern = CircuitSimulationPattern()
        pattern.builder.components = [
            Component("R1", ComponentType.RESISTOR, ["in", "out"], 1000.0),
        ]
        cfg = CircuitConfig(monte_carlo_runs=0)
        result = await pattern.simulator.run(pattern.builder.components, cfg)
        assert "metrics" in result


# ═══════════════════════════════════════════════════════════════════
# Confidence Calculation
# ═══════════════════════════════════════════════════════════════════


class TestCalculateConfidence:
    def test_with_components(self):
        pattern = CircuitSimulationPattern()
        pattern.builder.components = [
            Component("R1", ComponentType.RESISTOR, ["a", "b"], 1000.0),
            Component("C1", ComponentType.CAPACITOR, ["b", "ground"], 1e-6),
        ]
        results = {"metrics": {"rc_time_constant": 0.001}}
        cfg = CircuitConfig(temperature=50.0)
        confidence = pattern._calculate_confidence(results, cfg)
        assert confidence > 0.3

    def test_no_components(self):
        pattern = CircuitSimulationPattern()
        pattern.builder.components = []
        results = {"metrics": {}}
        cfg = CircuitConfig()
        confidence = pattern._calculate_confidence(results, cfg)
        assert confidence < 0.5

    def test_monte_carlo_boost(self):
        pattern = CircuitSimulationPattern()
        pattern.builder.components = [
            Component("R1", ComponentType.RESISTOR, ["a", "b"], 1000.0),
        ]
        results = {"metrics": {"rc_time_constant": 0.001}}
        cfg = CircuitConfig(monte_carlo_runs=20)
        confidence = pattern._calculate_confidence(results, cfg)
        assert confidence > 0.3


# ═══════════════════════════════════════════════════════════════════
# Resource Estimation
# ═══════════════════════════════════════════════════════════════════


class TestEstimateResources:
    def test_default_params(self):
        pattern = CircuitSimulationPattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert "gpu_required" in resources
        assert "estimated_time_seconds" in resources
        assert resources["gpu_required"] is False

    def test_with_components(self):
        pattern = CircuitSimulationPattern()
        h = Hypothesis(parameters={"components": [{}, {}, {}]})
        resources = pattern.estimate_resources(h)
        assert resources["estimated_time_seconds"] > 0

    def test_with_monte_carlo(self):
        pattern = CircuitSimulationPattern()
        h = Hypothesis(parameters={"monte_carlo_runs": 10})
        resources = pattern.estimate_resources(h)
        assert resources["estimated_time_seconds"] > 0


# ═══════════════════════════════════════════════════════════════════
# run() Integration
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRun:
    async def test_run_transient(self):
        pattern = CircuitSimulationPattern()
        h = Hypothesis(title="RC filter", description="test")
        config = {"circuit_type": "rc_filter", "t_stop": 1e-4}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("ckt_")
        assert len(result.logs) > 0

    async def test_run_ac(self):
        pattern = CircuitSimulationPattern()
        h = Hypothesis(title="Filter frequency response", description="test")
        config = {"circuit_type": "rc_filter", "analysis_type": "ac"}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_with_seed(self):
        pattern = CircuitSimulationPattern()
        h = Hypothesis(title="RC filter", description="test")
        config = {"circuit_type": "rc_filter", "random_seed": 42}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_monte_carlo(self):
        pattern = CircuitSimulationPattern()
        h = Hypothesis(title="RC filter", description="test")
        config = {"circuit_type": "rc_filter", "monte_carlo_runs": 3}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert "monte_carlo" in result.data or result.metrics

    async def test_run_logs_present(self):
        pattern = CircuitSimulationPattern()
        h = Hypothesis(title="Circuit", description="test")
        config = {"circuit_type": "rc_filter"}
        result = await pattern.run(h, config)
        assert len(result.logs) > 0

    async def test_run_failure_handling(self):
        pattern = CircuitSimulationPattern()
        h = Hypothesis(title="Circuit", description="test")
        with patch.object(pattern.builder, "build_from_params", side_effect=ValueError("test error")):
            result = await pattern.run(h, {"circuit_type": "rc_filter"})
            assert result.status == SimulationStatus.FAILED
            assert "test error" in result.error_message


# ═══════════════════════════════════════════════════════════════════
# get_metadata
# ═══════════════════════════════════════════════════════════════════


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = CircuitSimulationPattern.get_metadata()
        assert meta["id"] == "circuit_simulation"
        assert meta["name"] == "CircuitSimulationPattern"
        assert meta["category"] == "physical"


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestEdgeCases:
    async def test_extreme_temperature(self):
        pattern = CircuitSimulationPattern()
        h = Hypothesis(title="Circuit", description="test")
        config = {"circuit_type": "rc_filter", "temperature": 150.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_negative_temperature(self):
        pattern = CircuitSimulationPattern()
        h = Hypothesis(title="Circuit", description="test")
        config = {"circuit_type": "rc_filter", "temperature": -40.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_zero_tolerance(self):
        pattern = CircuitSimulationPattern()
        h = Hypothesis(title="Circuit", description="test")
        config = {"circuit_type": "rc_filter", "tolerance": 0.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_empty_hypothesis(self):
        pattern = CircuitSimulationPattern()
        h = Hypothesis()
        config = {}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_very_small_time_step(self):
        pattern = CircuitSimulationPattern()
        h = Hypothesis(title="Circuit", description="test")
        config = {"circuit_type": "rc_filter", "t_step": 1e-12, "t_stop": 1e-9}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
