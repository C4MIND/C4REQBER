"""
Tests for src/patterns/library/epidemic_seir.py

Covers:
- SEIRConfig initialization and defaults
- EpidemicSEIRPattern initialization
- can_simulate() keyword matching
- _parse_config()
- _simulate_deterministic() for SIR, SEIR, SEIRS
- _simulate_stochastic()
- _analyze_results()
- _calculate_confidence()
- estimate_resources()
- run() integration
- Edge cases: R0 < 1, zero population, zero initial infected
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.core import Hypothesis, SimulationStatus
from src.patterns.library.epidemic_seir import EpidemicSEIRPattern, SEIRConfig


# ═══════════════════════════════════════════════════════════════════
# SEIRConfig
# ═══════════════════════════════════════════════════════════════════


class TestSEIRConfig:
    def test_default_init(self):
        cfg = SEIRConfig()
        assert cfg.model_type == "seir"
        assert cfg.N == 100000
        assert cfg.I0 == 10
        assert cfg.t_max == 200.0
        assert cfg.beta == 0.5
        assert cfg.sigma == 0.2
        assert cfg.gamma == 0.1
        assert cfg.stochastic is False

    def test_custom_params(self):
        cfg = SEIRConfig(N=50000, I0=5, beta=0.3, gamma=0.05)
        assert cfg.N == 50000
        assert cfg.I0 == 5
        assert cfg.beta == 0.3
        assert cfg.gamma == 0.05

    def test_stochastic_config(self):
        cfg = SEIRConfig(stochastic=True, n_realizations=50)
        assert cfg.stochastic is True
        assert cfg.n_realizations == 50

    def test_random_seed(self):
        cfg = SEIRConfig(random_seed=42)
        assert cfg.random_seed == 42


# ═══════════════════════════════════════════════════════════════════
# EpidemicSEIRPattern Initialization
# ═══════════════════════════════════════════════════════════════════


class TestEpidemicSEIRPatternInit:
    def test_init(self):
        pattern = EpidemicSEIRPattern()
        assert pattern is not None
        assert pattern.config is None

    def test_parameters_defined(self):
        pattern = EpidemicSEIRPattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0


# ═══════════════════════════════════════════════════════════════════
# can_simulate
# ═══════════════════════════════════════════════════════════════════


class TestCanSimulate:
    def test_matches_epidemic(self):
        pattern = EpidemicSEIRPattern()
        h = Hypothesis(title="Epidemic spread", description="disease transmission")
        assert pattern.can_simulate(h) is True

    def test_matches_sir(self):
        pattern = EpidemicSEIRPattern()
        h = Hypothesis(title="SIR model analysis", description="compartmental model")
        assert pattern.can_simulate(h) is True

    def test_matches_herd_immunity(self):
        pattern = EpidemicSEIRPattern()
        h = Hypothesis(title="Herd immunity threshold", description="vaccination strategy")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = EpidemicSEIRPattern()
        h = Hypothesis(title="Neural network", description="deep learning")
        assert pattern.can_simulate(h) is False

    def test_empty_hypothesis(self):
        pattern = EpidemicSEIRPattern()
        h = Hypothesis()
        assert pattern.can_simulate(h) is False


# ═══════════════════════════════════════════════════════════════════
# Config Parsing
# ═══════════════════════════════════════════════════════════════════


class TestParseConfig:
    def test_default_parsing(self):
        pattern = EpidemicSEIRPattern()
        cfg = pattern._parse_config({})
        assert cfg.N == 100000
        assert cfg.I0 == 10
        assert cfg.beta == 0.5

    def test_custom_parsing(self):
        pattern = EpidemicSEIRPattern()
        cfg = pattern._parse_config({"N": 50000, "beta": 0.3, "stochastic": True})
        assert cfg.N == 50000
        assert cfg.beta == 0.3
        assert cfg.stochastic is True


# ═══════════════════════════════════════════════════════════════════
# Deterministic Simulation
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestSimulateDeterministic:
    async def test_sir_model(self):
        pattern = EpidemicSEIRPattern()
        pattern.config = SEIRConfig(model_type="sir", N=10000, I0=10, t_max=50.0)
        h = Hypothesis()
        result = await pattern._simulate_deterministic(h)
        assert "metrics" in result
        assert "logs" in result
        assert "R0" in result["metrics"]

    async def test_seir_model(self):
        pattern = EpidemicSEIRPattern()
        pattern.config = SEIRConfig(model_type="seir", N=10000, I0=10, t_max=50.0)
        h = Hypothesis()
        result = await pattern._simulate_deterministic(h)
        assert "R0" in result["metrics"]
        assert "peak_time" in result["metrics"]
        assert "peak_infections" in result["metrics"]

    async def test_seirs_model(self):
        pattern = EpidemicSEIRPattern()
        pattern.config = SEIRConfig(model_type="seirs", N=10000, I0=10, t_max=50.0, omega=0.01)
        h = Hypothesis()
        result = await pattern._simulate_deterministic(h)
        assert "R0" in result["metrics"]

    async def test_trajectories_stored(self):
        pattern = EpidemicSEIRPattern()
        pattern.config = SEIRConfig(model_type="seir", N=10000, I0=10, t_max=50.0)
        h = Hypothesis()
        await pattern._simulate_deterministic(h)
        assert "S" in pattern.trajectories
        assert "E" in pattern.trajectories
        assert "I" in pattern.trajectories
        assert "R" in pattern.trajectories
        assert len(pattern.time_points) > 0

    async def test_sir_trajectories(self):
        pattern = EpidemicSEIRPattern()
        pattern.config = SEIRConfig(model_type="sir", N=10000, I0=10, t_max=50.0)
        h = Hypothesis()
        await pattern._simulate_deterministic(h)
        assert "S" in pattern.trajectories
        assert "I" in pattern.trajectories
        assert "R" in pattern.trajectories
        assert "E" not in pattern.trajectories


# ═══════════════════════════════════════════════════════════════════
# Stochastic Simulation
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestSimulateStochastic:
    async def test_stochastic_sir(self):
        pattern = EpidemicSEIRPattern()
        pattern.config = SEIRConfig(
            model_type="sir", N=1000, I0=5, t_max=30.0, stochastic=True, n_realizations=10
        )
        pattern.rng = np.random.default_rng(42)
        h = Hypothesis()
        result = await pattern._simulate_stochastic(h)
        assert "metrics" in result
        assert "R0" in result["metrics"]

    async def test_stochastic_seir(self):
        pattern = EpidemicSEIRPattern()
        pattern.config = SEIRConfig(
            model_type="seir", N=1000, I0=5, t_max=30.0, stochastic=True, n_realizations=10
        )
        pattern.rng = np.random.default_rng(42)
        h = Hypothesis()
        result = await pattern._simulate_stochastic(h)
        assert "metrics" in result

    async def test_stochastic_with_seed(self):
        pattern = EpidemicSEIRPattern()
        pattern.config = SEIRConfig(
            model_type="sir",
            N=1000,
            I0=5,
            t_max=30.0,
            stochastic=True,
            n_realizations=5,
            random_seed=42,
        )
        pattern.rng = np.random.default_rng(42)
        h = Hypothesis()
        result = await pattern._simulate_stochastic(h)
        assert "metrics" in result


# ═══════════════════════════════════════════════════════════════════
# Results Analysis
# ═══════════════════════════════════════════════════════════════════


class TestAnalyzeResults:
    def test_peak_infection(self):
        pattern = EpidemicSEIRPattern()
        pattern.config = SEIRConfig(N=10000, beta=0.5, gamma=0.1)
        pattern.time_points = np.array([0, 1, 2, 3, 4, 5])
        pattern.trajectories = {
            "S": np.array([9990, 9950, 9800, 9500, 9200, 9000]),
            "E": np.array([0, 20, 100, 200, 150, 100]),
            "I": np.array([10, 30, 100, 300, 280, 200]),
            "R": np.array([0, 0, 0, 0, 370, 700]),
        }
        result = pattern._analyze_results()
        assert result["metrics"]["peak_infections"] == 300.0
        assert result["metrics"]["peak_time"] == 3.0

    def test_r0_calculation(self):
        pattern = EpidemicSEIRPattern()
        pattern.config = SEIRConfig(beta=0.5, gamma=0.1)
        pattern.time_points = np.array([0, 1])
        pattern.trajectories = {
            "S": np.array([1000, 900]),
            "I": np.array([10, 100]),
            "R": np.array([0, 10]),
        }
        result = pattern._analyze_results()
        assert result["metrics"]["R0"] == pytest.approx(5.0)

    def test_herd_immunity(self):
        pattern = EpidemicSEIRPattern()
        pattern.config = SEIRConfig(beta=0.5, gamma=0.1)
        pattern.time_points = np.array([0, 1])
        pattern.trajectories = {
            "S": np.array([1000, 900]),
            "I": np.array([10, 100]),
            "R": np.array([0, 10]),
        }
        result = pattern._analyze_results()
        assert result["metrics"]["herd_immunity_threshold"] == pytest.approx(0.8, abs=0.01)

    def test_attack_rate(self):
        pattern = EpidemicSEIRPattern()
        pattern.config = SEIRConfig(N=1000)
        pattern.time_points = np.array([0, 1])
        pattern.trajectories = {
            "S": np.array([990, 500]),
            "I": np.array([10, 100]),
            "R": np.array([0, 400]),
        }
        result = pattern._analyze_results()
        assert result["metrics"]["attack_rate"] == pytest.approx(0.4)

    def test_empty_trajectories(self):
        pattern = EpidemicSEIRPattern()
        pattern.trajectories = {}
        result = pattern._analyze_results()
        assert result["metrics"] == {}
        assert "No simulation data" in result["logs"]

    def test_doubling_time(self):
        pattern = EpidemicSEIRPattern()
        pattern.config = SEIRConfig()
        pattern.time_points = np.array([0, 1, 2, 3, 4, 5])
        pattern.trajectories = {
            "S": np.array([1000, 990, 970, 930, 850, 700]),
            "I": np.array([10, 20, 40, 80, 160, 300]),
            "R": np.array([0, 0, 0, 0, 0, 0]),
        }
        result = pattern._analyze_results()
        assert "doubling_time" in result["metrics"]
        assert result["metrics"]["doubling_time"] > 0

    def test_generation_time_seir(self):
        pattern = EpidemicSEIRPattern()
        pattern.config = SEIRConfig(model_type="seir", sigma=0.2, gamma=0.1)
        pattern.time_points = np.array([0, 1])
        pattern.trajectories = {
            "S": np.array([1000, 900]),
            "E": np.array([0, 50]),
            "I": np.array([10, 50]),
            "R": np.array([0, 0]),
        }
        result = pattern._analyze_results()
        # T_incubation = 1/0.2 = 5, T_infectious = 1/0.1 = 10
        # generation_time = 5 + 10/2 = 10
        assert result["metrics"]["generation_time"] == pytest.approx(10.0)

    def test_generation_time_sir(self):
        pattern = EpidemicSEIRPattern()
        pattern.config = SEIRConfig(model_type="sir", gamma=0.1)
        pattern.time_points = np.array([0, 1])
        pattern.trajectories = {
            "S": np.array([1000, 900]),
            "I": np.array([10, 100]),
            "R": np.array([0, 10]),
        }
        result = pattern._analyze_results()
        assert result["metrics"]["generation_time"] == pytest.approx(10.0)


# ═══════════════════════════════════════════════════════════════════
# Confidence Calculation
# ═══════════════════════════════════════════════════════════════════


class TestCalculateConfidence:
    def test_high_confidence(self):
        pattern = EpidemicSEIRPattern()
        pattern.config = SEIRConfig(stochastic=True, n_realizations=100)
        results = {"metrics": {"R0": 2.5, "peak_infections": 5000, "final_epidemic_size": 8000}}
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5

    def test_low_confidence(self):
        pattern = EpidemicSEIRPattern()
        pattern.config = SEIRConfig()
        results = {"metrics": {"R0": 0.5, "peak_infections": 0}}
        confidence = pattern._calculate_confidence(results)
        assert confidence < 0.5

    def test_r0_out_of_range(self):
        pattern = EpidemicSEIRPattern()
        pattern.config = SEIRConfig()
        results = {"metrics": {"R0": 15.0, "peak_infections": 100}}
        confidence = pattern._calculate_confidence(results)
        # R0 > 10 doesn't contribute
        assert confidence < 0.9


# ═══════════════════════════════════════════════════════════════════
# Resource Estimation
# ═══════════════════════════════════════════════════════════════════


class TestEstimateResources:
    def test_default_params(self):
        pattern = EpidemicSEIRPattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert "gpu_required" in resources
        assert "estimated_time_seconds" in resources

    def test_stochastic_params(self):
        pattern = EpidemicSEIRPattern()
        h = Hypothesis(parameters={"stochastic": True, "n_realizations": 200})
        resources = pattern.estimate_resources(h)
        assert resources["estimated_time_seconds"] > 0


# ═══════════════════════════════════════════════════════════════════
# run() Integration
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRun:
    async def test_run_deterministic(self):
        pattern = EpidemicSEIRPattern()
        h = Hypothesis(title="Epidemic model", description="test")
        config = {"model_type": "seir", "N": 10000, "I0": 10, "t_max": 50.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("seir_")
        assert "R0" in result.metrics

    async def test_run_sir(self):
        pattern = EpidemicSEIRPattern()
        h = Hypothesis(title="SIR model", description="test")
        config = {"model_type": "sir", "N": 10000, "I0": 10, "t_max": 50.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_with_seed(self):
        pattern = EpidemicSEIRPattern()
        h = Hypothesis(title="Epidemic", description="test")
        config = {"model_type": "seir", "N": 10000, "random_seed": 42}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_logs_present(self):
        pattern = EpidemicSEIRPattern()
        h = Hypothesis(title="Epidemic", description="test")
        config = {"model_type": "seir", "N": 10000}
        result = await pattern.run(h, config)
        assert len(result.logs) > 0

    async def test_run_failure_handling(self):
        pattern = EpidemicSEIRPattern()
        h = Hypothesis(title="Epidemic", description="test")
        with patch.object(pattern, "_simulate_deterministic", side_effect=ValueError("test error")):
            result = await pattern.run(h, {"model_type": "seir"})
            assert result.status == SimulationStatus.FAILED
            assert "test error" in result.error_message


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestEdgeCases:
    async def test_r0_less_than_one(self):
        pattern = EpidemicSEIRPattern()
        h = Hypothesis(title="Epidemic", description="test")
        config = {"model_type": "sir", "N": 10000, "beta": 0.05, "gamma": 0.1, "t_max": 50.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert result.metrics["R0"] == pytest.approx(0.5)
        # Herd immunity should be 0 when R0 < 1
        assert result.metrics["herd_immunity_threshold"] == 0.0

    async def test_small_population(self):
        pattern = EpidemicSEIRPattern()
        h = Hypothesis(title="Epidemic", description="test")
        config = {"model_type": "seir", "N": 100, "I0": 1, "t_max": 30.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_zero_initial_infected(self):
        pattern = EpidemicSEIRPattern()
        h = Hypothesis(title="Epidemic", description="test")
        config = {"model_type": "sir", "N": 10000, "I0": 0, "t_max": 30.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_empty_config(self):
        pattern = EpidemicSEIRPattern()
        h = Hypothesis(title="Epidemic", description="test")
        result = await pattern.run(h, {})
        assert result.status == SimulationStatus.COMPLETED

    async def test_seirs_waning_immunity(self):
        pattern = EpidemicSEIRPattern()
        h = Hypothesis(title="Epidemic", description="test")
        config = {"model_type": "seirs", "N": 10000, "omega": 0.01, "t_max": 50.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
