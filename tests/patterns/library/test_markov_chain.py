"""
Tests for src/patterns/library/markov_chain.py
"""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.core import Hypothesis, SimulationStatus
from src.patterns.library.markov_chain import (
    MarkovChainConfig,
    MarkovChainPattern,
)


class TestMarkovChainConfig:
    def test_default_init(self):
        cfg = MarkovChainConfig()
        assert cfg.n_states == 3
        assert cfg.n_steps == 1000
        assert cfg.n_simulations == 100

    def test_custom_init(self):
        cfg = MarkovChainConfig(n_states=5, n_steps=500, n_simulations=50)
        assert cfg.n_states == 5
        assert cfg.n_steps == 500


class TestMarkovChainPatternInit:
    def test_init(self):
        pattern = MarkovChainPattern()
        assert pattern is not None

    def test_parameters_defined(self):
        pattern = MarkovChainPattern()
        param_names = [p.name for p in pattern.parameters]
        assert "n_states" in param_names
        assert "n_steps" in param_names


class TestCanSimulate:
    def test_matches_markov(self):
        pattern = MarkovChainPattern()
        h = Hypothesis(title="Markov chain", description="state transition")
        assert pattern.can_simulate(h) is True

    def test_matches_stationary(self):
        pattern = MarkovChainPattern()
        h = Hypothesis(title="Stationary distribution", description="steady state")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = MarkovChainPattern()
        h = Hypothesis(title="Stock market", description="trading")
        assert pattern.can_simulate(h) is False


class TestParseConfig:
    def test_default_parsing(self):
        pattern = MarkovChainPattern()
        cfg = pattern._parse_config({})
        assert cfg.n_states == 3

    def test_custom_parsing(self):
        pattern = MarkovChainPattern()
        cfg = pattern._parse_config({"n_states": 5, "n_steps": 500})
        assert cfg.n_states == 5
        assert cfg.n_steps == 500


@pytest.mark.asyncio
class TestSimulateMarkov:
    async def test_simulation_completes(self):
        pattern = MarkovChainPattern()
        pattern.config = MarkovChainConfig(n_states=3, n_steps=100, n_simulations=10)
        result = await pattern._simulate_markov()
        assert "metrics" in result
        assert "logs" in result
        assert "stationary_distribution" in result

    async def test_stationary_distribution(self):
        pattern = MarkovChainPattern()
        pattern.config = MarkovChainConfig(n_states=3, n_steps=100, n_simulations=10)
        result = await pattern._simulate_markov()
        stationary = np.array(result["stationary_distribution"])
        assert np.allclose(np.sum(stationary), 1.0)
        assert np.all(stationary >= 0)

    async def test_transition_matrix_stochastic(self):
        pattern = MarkovChainPattern()
        pattern.config = MarkovChainConfig(n_states=3, n_steps=100, n_simulations=10)
        result = await pattern._simulate_markov()
        P = np.array(result["transition_matrix"])
        assert np.allclose(np.sum(P, axis=1), 1.0)
        assert np.all(P >= 0)

    async def test_irreducibility(self):
        pattern = MarkovChainPattern()
        pattern.config = MarkovChainConfig(n_states=3, n_steps=100, n_simulations=10)
        result = await pattern._simulate_markov()
        assert "is_irreducible" in result["metrics"]

    async def test_spectral_gap(self):
        pattern = MarkovChainPattern()
        pattern.config = MarkovChainConfig(n_states=3, n_steps=100, n_simulations=10)
        result = await pattern._simulate_markov()
        assert result["metrics"]["spectral_gap"] >= 0

    async def test_mixing_time(self):
        pattern = MarkovChainPattern()
        pattern.config = MarkovChainConfig(n_states=3, n_steps=1000, n_simulations=10)
        result = await pattern._simulate_markov()
        assert result["metrics"]["mixing_time"] >= 0

    async def test_empirical_vs_stationary(self):
        pattern = MarkovChainPattern()
        pattern.config = MarkovChainConfig(n_states=3, n_steps=1000, n_simulations=100)
        result = await pattern._simulate_markov()
        tv = result["metrics"]["tv_distance_final"]
        assert tv < 0.5  # Should be somewhat close


class TestCalculateConfidence:
    def test_high_confidence(self):
        pattern = MarkovChainPattern()
        results = {
            "metrics": {
                "is_irreducible": True,
                "mixing_time": 10,
                "spectral_gap": 0.5,
                "tv_distance_final": 0.1,
            }
        }
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5


@pytest.mark.asyncio
class TestRun:
    async def test_run_default(self):
        pattern = MarkovChainPattern()
        h = Hypothesis(title="Markov chain", description="state transitions")
        config = {"n_states": 3, "n_steps": 100, "n_simulations": 10}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = MarkovChainPattern.get_metadata()
        assert meta["id"] == "markov_chain"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
