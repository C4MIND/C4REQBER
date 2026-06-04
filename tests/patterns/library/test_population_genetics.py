"""
Tests for src/patterns/library/population_genetics.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.population_genetics import (
    PopulationGeneticsPattern,
    PopulationGeneticsConfig,
)
from src.patterns.core import Hypothesis, SimulationStatus



class TestPopulationGeneticsConfig:
    def test_default_init(self):
        cfg = PopulationGeneticsConfig()
        assert cfg.N == 100
        assert cfg.p0 == 0.5
        assert cfg.n_generations == 100

    def test_custom_init(self):
        cfg = PopulationGeneticsConfig(N=200, p0=0.3, selection_coefficient=0.1)
        assert cfg.N == 200
        assert cfg.p0 == 0.3


class TestPopulationGeneticsPatternInit:
    def test_init(self):
        pattern = PopulationGeneticsPattern()
        assert pattern is not None

    def test_parameters_defined(self):
        pattern = PopulationGeneticsPattern()
        param_names = [p.name for p in pattern.parameters]
        assert "N" in param_names
        assert "p0" in param_names


class TestCanSimulate:
    def test_matches_genetics(self):
        pattern = PopulationGeneticsPattern()
        h = Hypothesis(title="Genetic drift", description="wright fisher")
        assert pattern.can_simulate(h) is True

    def test_matches_fixation(self):
        pattern = PopulationGeneticsPattern()
        h = Hypothesis(title="Fixation probability", description="allele frequency")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = PopulationGeneticsPattern()
        h = Hypothesis(title="Stock market", description="trading")
        assert pattern.can_simulate(h) is False


class TestParseConfig:
    def test_default_parsing(self):
        pattern = PopulationGeneticsPattern()
        cfg = pattern._parse_config({})
        assert cfg.N == 100

    def test_custom_parsing(self):
        pattern = PopulationGeneticsPattern()
        cfg = pattern._parse_config({"N": 200, "p0": 0.3, "selection_coefficient": 0.1})
        assert cfg.N == 200
        assert cfg.p0 == 0.3


@pytest.mark.asyncio
class TestSimulateGenetics:
    async def test_simulation_completes(self):
        pattern = PopulationGeneticsPattern()
        pattern.config = PopulationGeneticsConfig(N=50, n_generations=50, n_replicates=20)
        result = await pattern._simulate_genetics()
        assert "metrics" in result
        assert "logs" in result
        assert "frequencies" in result

    async def test_fixation_probability(self):
        np.random.seed(42)
        pattern = PopulationGeneticsPattern()
        pattern.config = PopulationGeneticsConfig(N=50, p0=0.5, n_generations=100, n_replicates=50)
        result = await pattern._simulate_genetics()
        # With p0=0.5 and no selection, fixation prob should be ~0.5
        if result["metrics"]["selection_coefficient"] == 0:
            assert 0.2 <= result["metrics"]["fixation_probability"] <= 0.8

    async def test_heterozygosity_decay(self):
        pattern = PopulationGeneticsPattern()
        pattern.config = PopulationGeneticsConfig(N=50, n_generations=100, n_replicates=20)
        result = await pattern._simulate_genetics()
        assert result["metrics"]["final_heterozygosity"] <= result["metrics"]["initial_heterozygosity"]

    async def test_counts_sum(self):
        pattern = PopulationGeneticsPattern()
        pattern.config = PopulationGeneticsConfig(N=50, n_generations=50, n_replicates=20)
        result = await pattern._simulate_genetics()
        total = result["metrics"]["fixed_count"] + result["metrics"]["lost_count"] + result["metrics"]["polymorphic_count"]
        assert total == 20

    async def test_selection_increases_fixation(self):
        pattern = PopulationGeneticsPattern()
        pattern.config = PopulationGeneticsConfig(N=50, p0=0.1, n_generations=100, n_replicates=50, selection_coefficient=0.1)
        result = await pattern._simulate_genetics()
        # With positive selection, fixation prob should be higher than neutral
        assert result["metrics"]["fixation_probability"] > result["metrics"]["expected_fixation_prob"] * 0.5


class TestCalculateConfidence:
    def test_high_confidence(self):
        pattern = PopulationGeneticsPattern()
        results = {"metrics": {"fixation_probability": 0.5, "expected_fixation_prob": 0.5, "final_heterozygosity": 0.1, "initial_heterozygosity": 0.5, "effective_population": 100}}
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5


@pytest.mark.asyncio
class TestRun:
    async def test_run_default(self):
        pattern = PopulationGeneticsPattern()
        h = Hypothesis(title="Genetic drift", description="wright fisher")
        config = {"N": 50, "n_generations": 50, "n_replicates": 20}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = PopulationGeneticsPattern.get_metadata()
        assert meta["id"] == "population_genetics"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
