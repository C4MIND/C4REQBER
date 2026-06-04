"""
Tests for src/patterns/library/evolutionary.py (Evolutionary Dynamics Pattern)

Covers:
- EvolutionaryConfig dataclass
- EvolutionaryPattern initialization
- can_simulate() keyword matching
- _parse_config()
- _simulate() with different models
- _run_moran() Moran process
- _run_wright_fisher() Wright-Fisher model
- _run_replicator() replicator dynamics
- _analyze_results()
- _calculate_confidence()
- estimate_resources()
- run() integration
- Edge cases: neutral evolution, strong selection, small population
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.evolutionary import EvolutionaryPattern, EvolutionaryConfig
from src.patterns.core import Hypothesis, SimulationStatus



# ═══════════════════════════════════════════════════════════════════
# Dataclass
# ═══════════════════════════════════════════════════════════════════


class TestEvolutionaryConfig:
    def test_default_init(self):
        cfg = EvolutionaryConfig()
        assert cfg.model_type == "moran"
        assert cfg.N == 100
        assert cfg.n_generations == 1000
        assert cfg.selection_strength == 1.0
        assert cfg.mutation_rate == 0.001
        assert cfg.initial_frequency == 0.5
        assert cfg.n_types == 2
        assert cfg.n_realizations == 100
        assert cfg.random_seed is None

    def test_custom_init(self):
        cfg = EvolutionaryConfig(
            model_type="wright_fisher",
            N=200,
            selection_strength=2.0,
            mutation_rate=0.01,
        )
        assert cfg.model_type == "wright_fisher"
        assert cfg.N == 200
        assert cfg.selection_strength == 2.0
        assert cfg.mutation_rate == 0.01


# ═══════════════════════════════════════════════════════════════════
# EvolutionaryPattern Initialization
# ═══════════════════════════════════════════════════════════════════


class TestEvolutionaryPatternInit:
    def test_init(self):
        pattern = EvolutionaryPattern()
        assert pattern is not None
        assert pattern.rng is not None
        assert pattern.config is None
        assert pattern.trajectories == []

    def test_parameters_defined(self):
        pattern = EvolutionaryPattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0
        param_names = [p.name for p in pattern.parameters]
        assert "model_type" in param_names
        assert "N" in param_names
        assert "selection_strength" in param_names


# ═══════════════════════════════════════════════════════════════════
# can_simulate
# ═══════════════════════════════════════════════════════════════════


class TestCanSimulate:
    def test_matches_evolution(self):
        pattern = EvolutionaryPattern()
        h = Hypothesis(title="Evolutionary dynamics", description="natural selection")
        assert pattern.can_simulate(h) is True

    def test_matches_moran(self):
        pattern = EvolutionaryPattern()
        h = Hypothesis(title="Moran process", description="genetic drift")
        assert pattern.can_simulate(h) is True

    def test_matches_fixation(self):
        pattern = EvolutionaryPattern()
        h = Hypothesis(title="Fixation probability", description="allele frequency")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = EvolutionaryPattern()
        h = Hypothesis(title="Neural network", description="deep learning")
        assert pattern.can_simulate(h) is False


# ═══════════════════════════════════════════════════════════════════
# Config Parsing
# ═══════════════════════════════════════════════════════════════════


class TestParseConfig:
    def test_default_parsing(self):
        pattern = EvolutionaryPattern()
        cfg = pattern._parse_config({})
        assert cfg.model_type == "moran"
        assert cfg.N == 100

    def test_custom_parsing(self):
        pattern = EvolutionaryPattern()
        cfg = pattern._parse_config({"model_type": "wright_fisher", "N": 200, "selection_strength": 2.0})
        assert cfg.model_type == "wright_fisher"
        assert cfg.N == 200
        assert cfg.selection_strength == 2.0


# ═══════════════════════════════════════════════════════════════════
# Simulation Models
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestSimulate:
    async def test_moran_simulation(self):
        pattern = EvolutionaryPattern()
        pattern.config = EvolutionaryConfig(model_type="moran", N=50, n_generations=100, n_realizations=10)
        pattern.rng = np.random.default_rng(42)
        h = Hypothesis()
        result = await pattern._simulate(h)
        assert "metrics" in result
        assert "logs" in result

    async def test_wright_fisher_simulation(self):
        pattern = EvolutionaryPattern()
        pattern.config = EvolutionaryConfig(model_type="wright_fisher", N=50, n_generations=100, n_realizations=10)
        pattern.rng = np.random.default_rng(42)
        h = Hypothesis()
        result = await pattern._simulate(h)
        assert "metrics" in result

    async def test_replicator_simulation(self):
        pattern = EvolutionaryPattern()
        pattern.config = EvolutionaryConfig(model_type="replicator", n_generations=100, n_realizations=10)
        pattern.rng = np.random.default_rng(42)
        h = Hypothesis()
        result = await pattern._simulate(h)
        assert "metrics" in result


# ═══════════════════════════════════════════════════════════════════
# Moran Process
# ═══════════════════════════════════════════════════════════════════


class TestRunMoran:
    def test_moran_trajectory_length(self):
        pattern = EvolutionaryPattern()
        pattern.rng = np.random.default_rng(42)
        pattern.config = EvolutionaryConfig(model_type="moran", N=50, n_generations=100, mutation_rate=0)
        trajectory, fix_data = pattern._run_moran()
        assert len(trajectory) <= 101  # n_generations + 1
        assert "fixation_time" in fix_data
        assert "fixation_type" in fix_data

    def test_moran_with_mutation(self):
        pattern = EvolutionaryPattern()
        pattern.rng = np.random.default_rng(42)
        pattern.config = EvolutionaryConfig(model_type="moran", N=50, n_generations=100, mutation_rate=0.01)
        trajectory, fix_data = pattern._run_moran()
        # With mutation, may not fix
        assert len(trajectory) > 0


# ═══════════════════════════════════════════════════════════════════
# Wright-Fisher Model
# ═══════════════════════════════════════════════════════════════════


class TestRunWrightFisher:
    def test_wf_trajectory_length(self):
        pattern = EvolutionaryPattern()
        pattern.rng = np.random.default_rng(42)
        pattern.config = EvolutionaryConfig(model_type="wright_fisher", N=50, n_generations=100, mutation_rate=0)
        trajectory, fix_data = pattern._run_wright_fisher()
        assert len(trajectory) <= 101
        assert "fixation_time" in fix_data


# ═══════════════════════════════════════════════════════════════════
# Replicator Dynamics
# ═══════════════════════════════════════════════════════════════════


class TestRunReplicator:
    def test_replicator_trajectory_length(self):
        pattern = EvolutionaryPattern()
        pattern.config = EvolutionaryConfig(model_type="replicator", n_generations=100)
        trajectory, fix_data = pattern._run_replicator()
        assert len(trajectory) == 101
        assert "final_frequency" in fix_data

    def test_replicator_converges(self):
        pattern = EvolutionaryPattern()
        pattern.config = EvolutionaryConfig(
            model_type="replicator", n_generations=1000, selection_strength=2.0
        )
        trajectory, fix_data = pattern._run_replicator()
        # With strong selection, should converge
        assert fix_data["final_frequency"] > 0.9 or fix_data["final_frequency"] < 0.1


# ═══════════════════════════════════════════════════════════════════
# Results Analysis
# ═══════════════════════════════════════════════════════════════════


class TestAnalyzeResults:
    def test_basic_metrics(self):
        pattern = EvolutionaryPattern()
        pattern.config = EvolutionaryConfig(N=100, selection_strength=1.0)
        pattern.trajectories = [np.array([0.5, 0.6, 0.7]), np.array([0.5, 0.4, 0.3])]
        pattern.fixation_data = [
            {"fixation_time": 50, "fixation_type": "A", "final_frequency": 1.0},
            {"fixation_time": 60, "fixation_type": "B", "final_frequency": 0.0},
        ]
        result = pattern._analyze_results()
        assert "fixation_prob_A" in result["metrics"]
        assert "fixation_prob_B" in result["metrics"]
        assert "fixation_prob_theory" in result["metrics"]

    def test_empty_data(self):
        pattern = EvolutionaryPattern()
        pattern.trajectories = []
        result = pattern._analyze_results()
        assert result["metrics"] == {}
        assert "No simulation data" in result["logs"]


# ═══════════════════════════════════════════════════════════════════
# Confidence Calculation
# ═══════════════════════════════════════════════════════════════════


class TestCalculateConfidence:
    def test_high_confidence(self):
        pattern = EvolutionaryPattern()
        pattern.config = EvolutionaryConfig(n_realizations=100)
        results = {"metrics": {"n_realizations": 100, "fixation_error": 0.02, "mean_fixation_time": 50.0}}
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5

    def test_low_confidence(self):
        pattern = EvolutionaryPattern()
        results = {"metrics": {"n_realizations": 10}}
        confidence = pattern._calculate_confidence(results)
        assert confidence < 0.5


# ═══════════════════════════════════════════════════════════════════
# Resource Estimation
# ═══════════════════════════════════════════════════════════════════


class TestEstimateResources:
    def test_default_params(self):
        pattern = EvolutionaryPattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert "gpu_required" in resources
        assert "estimated_time_seconds" in resources
        assert resources["gpu_required"] is False


# ═══════════════════════════════════════════════════════════════════
# run() Integration
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRun:
    async def test_run_moran(self):
        pattern = EvolutionaryPattern()
        h = Hypothesis(title="Evolution", description="Moran process")
        config = {"model_type": "moran", "N": 50, "n_generations": 100, "n_realizations": 10}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("evo_")

    async def test_run_wright_fisher(self):
        pattern = EvolutionaryPattern()
        h = Hypothesis(title="Evolution", description="Wright-Fisher")
        config = {"model_type": "wright_fisher", "N": 50, "n_generations": 100, "n_realizations": 10}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_with_seed(self):
        pattern = EvolutionaryPattern()
        h = Hypothesis(title="Evolution", description="test")
        config = {"N": 50, "n_generations": 100, "random_seed": 42}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_failure_handling(self):
        pattern = EvolutionaryPattern()
        h = Hypothesis(title="Evolution", description="test")
        with patch.object(pattern, "_simulate", side_effect=ValueError("test error")):
            result = await pattern.run(h, {"N": 50})
            assert result.status == SimulationStatus.FAILED


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestEdgeCases:
    async def test_neutral_evolution(self):
        pattern = EvolutionaryPattern()
        h = Hypothesis(title="Evolution", description="neutral")
        config = {"model_type": "moran", "N": 50, "selection_strength": 0.0, "n_realizations": 20}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        # Fixation probability should be close to 1/N = 0.02
        # With 0 selection, drift dominates

    async def test_strong_selection(self):
        pattern = EvolutionaryPattern()
        h = Hypothesis(title="Evolution", description="strong selection")
        config = {"model_type": "moran", "N": 50, "selection_strength": 5.0, "n_realizations": 20}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_small_population(self):
        pattern = EvolutionaryPattern()
        h = Hypothesis(title="Evolution", description="small pop")
        config = {"model_type": "moran", "N": 10, "n_generations": 50, "n_realizations": 10}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_high_mutation(self):
        pattern = EvolutionaryPattern()
        h = Hypothesis(title="Evolution", description="high mutation")
        config = {"model_type": "moran", "N": 50, "mutation_rate": 0.1, "n_realizations": 10}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
