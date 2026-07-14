"""
Tests for src/patterns/library/ising_model.py (Ising Model Pattern)

Covers:
- Algorithm enum
- IsingConfig dataclass
- IsingModelPattern initialization
- can_simulate() keyword matching
- _parse_config()
- _simulate() with different algorithms
- _metropolis() single-spin flip
- _wolff() cluster algorithm
- _swendsen_wang() cluster algorithm
- _measure() observables
- _analyze_results()
- _calculate_confidence()
- estimate_resources()
- run() integration
- get_metadata()
- Edge cases: single lattice site, high/low temperature, zero field
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.core import Hypothesis, SimulationStatus
from src.patterns.library.ising_model import Algorithm, IsingConfig, IsingModelPattern


# ═══════════════════════════════════════════════════════════════════
# Enums and Dataclasses
# ═══════════════════════════════════════════════════════════════════


class TestAlgorithm:
    def test_enum_values(self):
        assert Algorithm.METROPOLIS.value == "metropolis"
        assert Algorithm.WOLFF.value == "wolff"
        assert Algorithm.SWENDSEN_WANG.value == "swendsen_wang"


class TestIsingConfig:
    def test_default_init(self):
        cfg = IsingConfig()
        assert cfg.lattice_size == 32
        assert cfg.temperature == 2.27
        assert cfg.J == 1.0
        assert cfg.h == 0.0
        assert cfg.n_sweeps == 10000
        assert cfg.thermalization == 1000
        assert cfg.algorithm == "metropolis"
        assert cfg.measure_every == 10
        assert cfg.random_seed is None

    def test_custom_init(self):
        cfg = IsingConfig(lattice_size=16, temperature=3.0, J=-1.0, h=0.5)
        assert cfg.lattice_size == 16
        assert cfg.temperature == 3.0
        assert cfg.J == -1.0
        assert cfg.h == 0.5

    def test_post_init_validation(self):
        cfg = IsingConfig(algorithm="invalid")
        assert cfg.algorithm == "metropolis"  # Should default to metropolis


# ═══════════════════════════════════════════════════════════════════
# IsingModelPattern Initialization
# ═══════════════════════════════════════════════════════════════════


class TestIsingModelPatternInit:
    def test_init(self):
        pattern = IsingModelPattern()
        assert pattern is not None
        assert pattern.rng is not None
        assert pattern.lattice.size == 0  # Not initialized yet
        assert pattern.config is None

    def test_parameters_defined(self):
        pattern = IsingModelPattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0
        param_names = [p.name for p in pattern.parameters]
        assert "lattice_size" in param_names
        assert "temperature" in param_names
        assert "J" in param_names
        assert "h" in param_names
        assert "algorithm" in param_names


# ═══════════════════════════════════════════════════════════════════
# can_simulate
# ═══════════════════════════════════════════════════════════════════


class TestCanSimulate:
    def test_matches_ising(self):
        pattern = IsingModelPattern()
        h = Hypothesis(title="Ising model", description="ferromagnetism")
        assert pattern.can_simulate(h) is True

    def test_matches_magnet(self):
        pattern = IsingModelPattern()
        h = Hypothesis(title="Magnetic phase transition", description="spontaneous symmetry")
        assert pattern.can_simulate(h) is True

    def test_matches_phase_transition(self):
        pattern = IsingModelPattern()
        h = Hypothesis(title="Critical phenomena", description="phase transition")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = IsingModelPattern()
        h = Hypothesis(title="Neural network", description="deep learning")
        assert pattern.can_simulate(h) is False

    def test_empty_hypothesis(self):
        pattern = IsingModelPattern()
        h = Hypothesis()
        assert pattern.can_simulate(h) is False


# ═══════════════════════════════════════════════════════════════════
# Config Parsing
# ═══════════════════════════════════════════════════════════════════


class TestParseConfig:
    def test_default_parsing(self):
        pattern = IsingModelPattern()
        cfg = pattern._parse_config({})
        assert cfg.lattice_size == 32
        assert cfg.temperature == 2.27

    def test_custom_parsing(self):
        pattern = IsingModelPattern()
        cfg = pattern._parse_config({"lattice_size": 16, "temperature": 3.0, "algorithm": "wolff"})
        assert cfg.lattice_size == 16
        assert cfg.temperature == 3.0
        assert cfg.algorithm == "wolff"


# ═══════════════════════════════════════════════════════════════════
# Simulation
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestSimulate:
    async def test_metropolis_simulation(self):
        pattern = IsingModelPattern()
        pattern.config = IsingConfig(
            lattice_size=8, n_sweeps=100, thermalization=10, algorithm="metropolis"
        )
        h = Hypothesis()
        result = await pattern._simulate(h)
        assert "metrics" in result
        assert "logs" in result

    async def test_wolff_simulation(self):
        pattern = IsingModelPattern()
        pattern.config = IsingConfig(
            lattice_size=8, n_sweeps=100, thermalization=10, algorithm="wolff"
        )
        h = Hypothesis()
        result = await pattern._simulate(h)
        assert "metrics" in result

    async def test_swendsen_wang_simulation(self):
        pattern = IsingModelPattern()
        pattern.config = IsingConfig(
            lattice_size=8, n_sweeps=100, thermalization=10, algorithm="swendsen_wang"
        )
        h = Hypothesis()
        result = await pattern._simulate(h)
        assert "metrics" in result

    async def test_lattice_initialized(self):
        pattern = IsingModelPattern()
        pattern.config = IsingConfig(lattice_size=8, n_sweeps=10, thermalization=5)
        h = Hypothesis()
        await pattern._simulate(h)
        assert pattern.lattice.shape == (8, 8)
        assert np.all(np.abs(pattern.lattice) == 1)  # Spins should be +/- 1


# ═══════════════════════════════════════════════════════════════════
# Measurements
# ═══════════════════════════════════════════════════════════════════


class TestMeasure:
    def test_measure_stores_values(self):
        pattern = IsingModelPattern()
        pattern.config = IsingConfig(lattice_size=8)
        pattern.lattice = np.ones((8, 8))
        pattern._measure()
        assert len(pattern.measurements["magnetization"]) == 1
        assert len(pattern.measurements["energy"]) == 1

    def test_measure_all_spins_up(self):
        pattern = IsingModelPattern()
        pattern.config = IsingConfig(lattice_size=8)
        pattern.lattice = np.ones((8, 8))
        pattern._measure()
        assert pattern.measurements["magnetization"][0] == 1.0
        assert pattern.measurements["abs_magnetization"][0] == 1.0


# ═══════════════════════════════════════════════════════════════════
# Results Analysis
# ═══════════════════════════════════════════════════════════════════


class TestAnalyzeResults:
    def test_empty_measurements(self):
        pattern = IsingModelPattern()
        result = pattern._analyze_results()
        assert result["metrics"] == {}
        assert "No measurements taken" in result["logs"]

    def test_basic_metrics(self):
        pattern = IsingModelPattern()
        pattern.config = IsingConfig(lattice_size=8, temperature=2.27)
        pattern.measurements = {
            "magnetization": [0.5, 0.6, 0.55],
            "abs_magnetization": [0.5, 0.6, 0.55],
            "magnetization_squared": [0.25, 0.36, 0.3025],
            "energy": [-1.0, -1.2, -1.1],
            "energy_squared": [1.0, 1.44, 1.21],
        }
        result = pattern._analyze_results()
        assert "temperature" in result["metrics"]
        assert "magnetization" in result["metrics"]
        assert "susceptibility" in result["metrics"]
        assert "energy" in result["metrics"]
        assert "specific_heat" in result["metrics"]
        assert "binder_cumulant" in result["metrics"]


# ═══════════════════════════════════════════════════════════════════
# Confidence Calculation
# ═══════════════════════════════════════════════════════════════════


class TestCalculateConfidence:
    def test_high_confidence(self):
        pattern = IsingModelPattern()
        pattern.config = IsingConfig(lattice_size=64)
        results = {"metrics": {"n_measurements": 200, "autocorrelation": 0.05, "lattice_size": 64}}
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5

    def test_low_confidence(self):
        pattern = IsingModelPattern()
        results = {"metrics": {"n_measurements": 10, "autocorrelation": 0.9}}
        confidence = pattern._calculate_confidence(results)
        assert confidence < 0.5


# ═══════════════════════════════════════════════════════════════════
# Resource Estimation
# ═══════════════════════════════════════════════════════════════════


class TestEstimateResources:
    def test_default_params(self):
        pattern = IsingModelPattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert "gpu_required" in resources
        assert "estimated_time_seconds" in resources
        assert resources["gpu_required"] is False

    def test_large_lattice(self):
        pattern = IsingModelPattern()
        h = Hypothesis(parameters={"lattice_size": 128, "n_sweeps": 100000})
        resources = pattern.estimate_resources(h)
        assert resources["memory_gb"] > 0.1


# ═══════════════════════════════════════════════════════════════════
# run() Integration
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRun:
    async def test_run_default(self):
        pattern = IsingModelPattern()
        h = Hypothesis(title="Ising model", description="phase transition")
        config = {"lattice_size": 8, "n_sweeps": 100, "thermalization": 10}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("ising_")

    async def test_run_wolff(self):
        pattern = IsingModelPattern()
        h = Hypothesis(title="Ising model", description="cluster algorithm")
        config = {"lattice_size": 8, "n_sweeps": 100, "algorithm": "wolff"}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_with_seed(self):
        pattern = IsingModelPattern()
        h = Hypothesis(title="Ising model", description="test")
        config = {"lattice_size": 8, "n_sweeps": 100, "random_seed": 42}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_failure_handling(self):
        pattern = IsingModelPattern()
        h = Hypothesis(title="Ising model", description="test")
        with patch.object(pattern, "_simulate", side_effect=ValueError("test error")):
            result = await pattern.run(h, {"lattice_size": 8})
            assert result.status == SimulationStatus.FAILED


# ═══════════════════════════════════════════════════════════════════
# get_metadata
# ═══════════════════════════════════════════════════════════════════


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = IsingModelPattern.get_metadata()
        assert meta["id"] == "ising_model"
        assert meta["name"] == "IsingModelPattern"
        assert "category" in meta


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestEdgeCases:
    async def test_high_temperature(self):
        pattern = IsingModelPattern()
        h = Hypothesis(title="Ising model", description="high T")
        config = {"lattice_size": 8, "temperature": 10.0, "n_sweeps": 100}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        # High T should result in low magnetization
        assert result.metrics.get("magnetization", 0) < 0.5

    async def test_low_temperature(self):
        pattern = IsingModelPattern()
        h = Hypothesis(title="Ising model", description="low T")
        config = {"lattice_size": 8, "temperature": 1.0, "n_sweeps": 100}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        # Low T should result in high magnetization
        assert result.metrics.get("magnetization", 0) > 0.5

    async def test_external_field(self):
        pattern = IsingModelPattern()
        h = Hypothesis(title="Ising model", description="with field")
        config = {"lattice_size": 8, "h": 1.0, "n_sweeps": 100}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_antiferromagnetic(self):
        pattern = IsingModelPattern()
        h = Hypothesis(title="Ising model", description="antiferro")
        config = {"lattice_size": 8, "J": -1.0, "n_sweeps": 100}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
