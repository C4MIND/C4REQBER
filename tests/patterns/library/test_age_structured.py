"""
Tests for src/patterns/library/age_structured.py (Age-Structured Population pattern)

Covers:
- AgeStructuredConfig dataclass
- AgeStructuredPattern initialization
- can_simulate() keyword matching
- _parse_config()
- _get_survival_curve() for different types
- _get_fertility_rates()
- _initial_population()
- _update_population()
- _record()
- _analyze_results()
- _calculate_confidence()
- estimate_resources()
- run() async integration
- Edge cases: different survival types, demographic transitions
"""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import asyncio

import numpy as np
import pytest

from src.patterns.core import Hypothesis, SimulationStatus
from src.patterns.library.age_structured import AgeStructuredConfig, AgeStructuredPattern


# ═══════════════════════════════════════════════════════════════════
# Config Tests
# ═══════════════════════════════════════════════════════════════════


class TestAgeStructuredConfig:
    def test_default_init(self):
        cfg = AgeStructuredConfig()
        assert cfg.max_age == 100
        assert cfg.age_groups == 20
        assert cfg.t_max == 100.0
        assert cfg.dt == 0.1
        assert cfg.birth_rate == 0.025
        assert cfg.carrying_capacity == 1000000
        assert cfg.survival_type == "type1"

    def test_custom_init(self):
        cfg = AgeStructuredConfig(max_age=80, age_groups=16, t_max=50.0, birth_rate=0.03)
        assert cfg.max_age == 80
        assert cfg.age_groups == 16
        assert cfg.t_max == 50.0
        assert cfg.birth_rate == 0.03


# ═══════════════════════════════════════════════════════════════════
# Initialization Tests
# ═══════════════════════════════════════════════════════════════════


class TestAgeStructuredPatternInit:
    def test_init(self):
        pattern = AgeStructuredPattern()
        assert pattern is not None
        assert pattern.rng is not None
        assert pattern.config is None  # Set during run

    def test_parameters_defined(self):
        pattern = AgeStructuredPattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0
        param_names = [p.name for p in pattern.parameters]
        assert "max_age" in param_names
        assert "age_groups" in param_names
        assert "birth_rate" in param_names


# ═══════════════════════════════════════════════════════════════════
# can_simulate Tests
# ═══════════════════════════════════════════════════════════════════


class TestCanSimulate:
    def test_matches_age_structure(self):
        pattern = AgeStructuredPattern()
        h = Hypothesis(title="Age structure analysis", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_demography(self):
        pattern = AgeStructuredPattern()
        h = Hypothesis(title="Population dynamics", description="demographic transition")
        assert pattern.can_simulate(h) is True

    def test_matches_leslie(self):
        pattern = AgeStructuredPattern()
        h = Hypothesis(title="Leslie matrix model", description="population projection")
        assert pattern.can_simulate(h) is True

    def test_matches_fertility(self):
        pattern = AgeStructuredPattern()
        h = Hypothesis(title="Fertility analysis", description="birth rates")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = AgeStructuredPattern()
        h = Hypothesis(title="Chemical reaction", description="kinetics")
        assert pattern.can_simulate(h) is False


# ═══════════════════════════════════════════════════════════════════
# Config Parsing Tests
# ═══════════════════════════════════════════════════════════════════


class TestParseConfig:
    def test_default_parsing(self):
        pattern = AgeStructuredPattern()
        cfg = pattern._parse_config({})
        assert cfg.max_age == 100
        assert cfg.age_groups == 20

    def test_custom_parsing(self):
        pattern = AgeStructuredPattern()
        cfg = pattern._parse_config({"max_age": 80, "age_groups": 16, "birth_rate": 0.03})
        assert cfg.max_age == 80
        assert cfg.age_groups == 16
        assert cfg.birth_rate == 0.03

    def test_survival_type_parsing(self):
        pattern = AgeStructuredPattern()
        cfg = pattern._parse_config({"survival_type": "type2"})
        assert cfg.survival_type == "type2"


# ═══════════════════════════════════════════════════════════════════
# Survival Curve Tests
# ═══════════════════════════════════════════════════════════════════


class TestGetSurvivalCurve:
    def test_type1_survival(self):
        pattern = AgeStructuredPattern()
        pattern.config = AgeStructuredConfig(survival_type="type1", age_groups=20, max_age=100)
        survival = pattern._get_survival_curve()
        assert len(survival) == 20
        # Type 1: high survival early
        assert survival[0] > 0.9
        # Declining with age
        assert survival[5] > survival[15]
        # No survival past max age
        assert survival[-1] == 0

    def test_type2_survival(self):
        pattern = AgeStructuredPattern()
        pattern.config = AgeStructuredConfig(survival_type="type2", age_groups=20, max_age=100)
        survival = pattern._get_survival_curve()
        assert len(survival) == 20
        # Type 2: constant mortality
        # Should be roughly exponential
        assert survival[0] < 1.0
        assert survival[-1] == 0

    def test_type3_survival(self):
        pattern = AgeStructuredPattern()
        pattern.config = AgeStructuredConfig(survival_type="type3", age_groups=20, max_age=100)
        survival = pattern._get_survival_curve()
        assert len(survival) == 20
        # Type 3: high mortality early
        assert survival[0] < 0.9
        # Should decline faster initially
        assert survival[-1] == 0

    def test_survival_probs_in_range(self):
        pattern = AgeStructuredPattern()
        for stype in ["type1", "type2", "type3"]:
            pattern.config = AgeStructuredConfig(survival_type=stype, age_groups=10)
            survival = pattern._get_survival_curve()
            assert np.all((survival >= 0) & (survival <= 1))


# ═══════════════════════════════════════════════════════════════════
# Fertility Tests
# ═══════════════════════════════════════════════════════════════════


class TestGetFertilityRates:
    def test_fertility_shape(self):
        pattern = AgeStructuredPattern()
        pattern.config = AgeStructuredConfig(age_groups=20, max_age=100)
        fertility = pattern._get_fertility_rates()
        assert len(fertility) == 20

    def test_fertility_zero_outside_reproductive(self):
        pattern = AgeStructuredPattern()
        pattern.config = AgeStructuredConfig(age_groups=20, max_age=100)
        fertility = pattern._get_fertility_rates()
        # Very young and very old should have near-zero fertility
        assert fertility[0] == 0
        assert fertility[1] == 0  # 0-5 years
        assert fertility[-1] == 0  # 95-100 years

    def test_fertility_peak_middle(self):
        pattern = AgeStructuredPattern()
        pattern.config = AgeStructuredConfig(age_groups=20, max_age=100)
        fertility = pattern._get_fertility_rates()
        # Peak should be around ages 25-35 (groups 5-7)
        peak_idx = np.argmax(fertility)
        assert 4 <= peak_idx <= 8


# ═══════════════════════════════════════════════════════════════════
# Population Tests
# ═══════════════════════════════════════════════════════════════════


class TestInitialPopulation:
    def test_population_shape(self):
        pattern = AgeStructuredPattern()
        pattern.config = AgeStructuredConfig(age_groups=10)
        pop = pattern._initial_population()
        assert len(pop) == 10

    def test_population_positive(self):
        pattern = AgeStructuredPattern()
        pattern.config = AgeStructuredConfig(age_groups=10)
        pop = pattern._initial_population()
        assert np.all(pop > 0)

    def test_population_sum(self):
        pattern = AgeStructuredPattern()
        pattern.config = AgeStructuredConfig(age_groups=10, carrying_capacity=1000)
        pop = pattern._initial_population()
        # Should be less than carrying capacity initially
        assert np.sum(pop) < pattern.config.carrying_capacity


class TestUpdatePopulation:
    def test_population_updates(self):
        pattern = AgeStructuredPattern()
        pattern.config = AgeStructuredConfig(age_groups=5, max_age=25, birth_rate=0.02)
        pattern.population = np.array([100, 80, 60, 40, 20], dtype=float)
        pattern.fertility_rates = np.array([0, 0.1, 0.2, 0.05, 0])
        pattern.survival_probs = np.array([0.95, 0.9, 0.85, 0.7, 0])

        pop_before = pattern.population.copy()
        pattern._update_population(da=5.0)

        # Population should change
        assert not np.allclose(pattern.population, pop_before)

    def test_age_progression(self):
        pattern = AgeStructuredPattern()
        pattern.config = AgeStructuredConfig(age_groups=5)
        pattern.population = np.array([100, 80, 60, 40, 20], dtype=float)
        pattern.fertility_rates = np.zeros(5)
        pattern.survival_probs = np.ones(5)  # Perfect survival

        pattern._update_population(da=1.0)

        # Ages should progress (shifted)
        assert pattern.population[1] == 100  # Previous group 0
        assert pattern.population[2] == 80  # Previous group 1

    def test_carrying_capacity_regulation(self):
        pattern = AgeStructuredPattern()
        pattern.config = AgeStructuredConfig(age_groups=5, carrying_capacity=100, birth_rate=0.1)
        # Start at carrying capacity
        pattern.population = np.array([50, 30, 15, 4, 1], dtype=float)
        pattern.fertility_rates = np.array([0, 0.5, 0.5, 0.1, 0])
        pattern.survival_probs = np.ones(5)

        pop_before = np.sum(pattern.population)
        pattern._update_population(da=1.0)
        pop_after = np.sum(pattern.population)

        # Regulation should limit growth
        assert pop_after <= pop_before * 1.5  # Not exploding


# ═══════════════════════════════════════════════════════════════════
# Recording and Analysis Tests
# ═══════════════════════════════════════════════════════════════════


class TestRecord:
    def test_record_structure(self):
        pattern = AgeStructuredPattern()
        pattern.config = AgeStructuredConfig(age_groups=5)
        pattern.population = np.array([100, 80, 60, 40, 20], dtype=float)
        pattern.survival_probs = np.ones(5, dtype=float)
        pattern.history = []

        pattern._record(t=0.0)

        assert len(pattern.history) == 1
        record = pattern.history[0]
        assert "time" in record
        assert "total_population" in record
        assert "mean_age" in record
        assert "dependency_ratio" in record

    def test_total_population_calculation(self):
        pattern = AgeStructuredPattern()
        pattern.config = AgeStructuredConfig(age_groups=3)
        pattern.population = np.array([100, 50, 25], dtype=float)
        pattern.survival_probs = np.ones(3, dtype=float)
        pattern.history = []

        pattern._record(t=0.0)

        assert pattern.history[0]["total_population"] == 175


class TestAnalyzeResults:
    def test_empty_history(self):
        pattern = AgeStructuredPattern()
        pattern.history = []
        result = pattern._analyze_results()
        assert result["metrics"] == {}
        assert "No simulation data" in result["logs"]

    def test_with_history(self):
        pattern = AgeStructuredPattern()
        pattern.config = AgeStructuredConfig(max_age=100)
        pattern.history = [
            {
                "time": 0,
                "total_population": 1000,
                "mean_age": 30,
                "dependency_ratio": 0.5,
                "young": 300,
                "working": 600,
                "old": 100,
            },
            {
                "time": 50,
                "total_population": 1500,
                "mean_age": 35,
                "dependency_ratio": 0.6,
                "young": 400,
                "working": 700,
                "old": 200,
            },
        ]

        result = pattern._analyze_results()

        assert "initial_population" in result["metrics"]
        assert "final_population" in result["metrics"]
        assert "growth_rate" in result["metrics"]
        assert result["metrics"]["initial_population"] == 1000
        assert result["metrics"]["final_population"] == 1500

    def test_growth_rate_calculation(self):
        pattern = AgeStructuredPattern()
        pattern.config = AgeStructuredConfig(max_age=100)
        pattern.history = [
            {
                "time": 0,
                "total_population": 1000,
                "mean_age": 30,
                "dependency_ratio": 0.5,
                "young": 300,
                "working": 600,
                "old": 100,
            },
            {
                "time": 50,
                "total_population": 2000,
                "mean_age": 35,
                "dependency_ratio": 0.6,
                "young": 400,
                "working": 700,
                "old": 200,
            },
        ]

        result = pattern._analyze_results()

        # r = ln(2000/1000) / 50 = ln(2) / 50 ≈ 0.0139
        assert result["metrics"]["growth_rate"] > 0
        assert result["metrics"]["doubling_time"] > 0


# ═══════════════════════════════════════════════════════════════════
# Confidence Calculation Tests
# ═══════════════════════════════════════════════════════════════════


class TestCalculateConfidence:
    def test_high_confidence(self):
        pattern = AgeStructuredPattern()
        pattern.config = AgeStructuredConfig(t_max=100, age_groups=20)
        results = {"metrics": {"growth_rate": 0.01, "young_pct_change": 5.0}}
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5

    def test_low_confidence(self):
        pattern = AgeStructuredPattern()
        pattern.config = AgeStructuredConfig(t_max=10, age_groups=5)
        results = {"metrics": {}}
        confidence = pattern._calculate_confidence(results)
        assert confidence < 0.5

    def test_empty_metrics(self):
        pattern = AgeStructuredPattern()
        pattern.config = AgeStructuredConfig(t_max=10, age_groups=5)
        results = {"metrics": {}}
        confidence = pattern._calculate_confidence(results)
        assert confidence == 0.0


# ═══════════════════════════════════════════════════════════════════
# Resource Estimation Tests
# ═══════════════════════════════════════════════════════════════════


class TestEstimateResources:
    def test_default_params(self):
        pattern = AgeStructuredPattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert "gpu_required" in resources
        assert "estimated_time_seconds" in resources
        assert resources["gpu_required"] is False

    def test_custom_params(self):
        pattern = AgeStructuredPattern()
        h = Hypothesis(parameters={"age_groups": 50, "t_max": 200.0})
        resources = pattern.estimate_resources(h)
        assert resources["estimated_time_seconds"] > 0


# ═══════════════════════════════════════════════════════════════════
# Run Integration Tests
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRun:
    async def test_run_default(self):
        pattern = AgeStructuredPattern()
        h = Hypothesis(title="Age structure", description="test")
        result = await pattern.run(h, {"age_groups": 10, "t_max": 10.0})
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("age_struct_")

    async def test_run_type1(self):
        pattern = AgeStructuredPattern()
        h = Hypothesis(title="Age structure", description="test")
        result = await pattern.run(h, {"survival_type": "type1", "t_max": 10.0})
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_type2(self):
        pattern = AgeStructuredPattern()
        h = Hypothesis(title="Age structure", description="test")
        result = await pattern.run(h, {"survival_type": "type2", "t_max": 10.0})
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_type3(self):
        pattern = AgeStructuredPattern()
        h = Hypothesis(title="Age structure", description="test")
        result = await pattern.run(h, {"survival_type": "type3", "t_max": 10.0})
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_with_seed(self):
        pattern = AgeStructuredPattern()
        h = Hypothesis(title="Age structure", description="test")
        result = await pattern.run(h, {"random_seed": 42, "t_max": 10.0})
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_logs_present(self):
        pattern = AgeStructuredPattern()
        h = Hypothesis(title="Age structure", description="test")
        result = await pattern.run(h, {"t_max": 10.0})
        assert len(result.logs) > 0


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestEdgeCases:
    async def test_short_simulation(self):
        pattern = AgeStructuredPattern()
        h = Hypothesis(title="Age structure", description="test")
        result = await pattern.run(h, {"t_max": 1.0, "dt": 0.1})
        assert result.status == SimulationStatus.COMPLETED

    async def test_few_age_groups(self):
        pattern = AgeStructuredPattern()
        h = Hypothesis(title="Age structure", description="test")
        result = await pattern.run(h, {"age_groups": 5, "t_max": 5.0})
        assert result.status == SimulationStatus.COMPLETED

    async def test_high_birth_rate(self):
        pattern = AgeStructuredPattern()
        h = Hypothesis(title="Age structure", description="test")
        result = await pattern.run(h, {"birth_rate": 0.05, "t_max": 10.0})
        assert result.status == SimulationStatus.COMPLETED
        # Should show growth
        metrics = result.metrics
        if "growth_rate" in metrics:
            assert metrics["growth_rate"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
