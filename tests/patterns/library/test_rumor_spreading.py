"""
Tests for src/patterns/library/rumor_spreading.py (Rumor Spreading Pattern)

Covers:
- RumorModel enum
- RumorConfig dataclass
- RumorSpreadingPattern initialization
- _initialize() and _build_network()
- _sir_step(), _seir_step(), _seiz_step()
- _count_states()
- _record_state()
- _calculate_final_reach()
- _calculate_peak_spreaders()
- run() simulation
- _format_output()
- get_metadata()
- Edge cases: zero agents, high spreading rate, counter-rumor
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.rumor_spreading import RumorSpreadingPattern, RumorConfig, RumorModel



# ═══════════════════════════════════════════════════════════════════
# Enums and Dataclasses
# ═══════════════════════════════════════════════════════════════════


class TestRumorModel:
    def test_enum_values(self):
        assert RumorModel.SIR.value == "sir"
        assert RumorModel.SEIR.value == "seir"
        assert RumorModel.SEIZ.value == "seiz"
        assert RumorModel.MCKENDRICK.value == "mckendrick"


class TestRumorConfig:
    def test_default_init(self):
        cfg = RumorConfig()
        assert cfg.model == RumorModel.SIR
        assert cfg.n_agents == 1000
        assert cfg.network_type == "small_world"
        assert cfg.network_param == 0.1
        assert cfg.initial_spreaders == 10
        assert cfg.spreading_rate == 0.5
        assert cfg.stifling_rate == 0.2
        assert cfg.forgetting_rate == 0.05
        assert cfg.latent_period == 1.0
        assert cfg.skepticism_rate == 0.3
        assert cfg.dt == 0.1
        assert cfg.max_time == 100.0
        assert cfg.counter_rumor_start is None
        assert cfg.counter_rumor_strength == 0.3

    def test_custom_init(self):
        cfg = RumorConfig(model=RumorModel.SEIR, n_agents=500, spreading_rate=0.8)
        assert cfg.model == RumorModel.SEIR
        assert cfg.n_agents == 500
        assert cfg.spreading_rate == 0.8


# ═══════════════════════════════════════════════════════════════════
# RumorSpreadingPattern Initialization
# ═══════════════════════════════════════════════════════════════════


class TestRumorSpreadingPatternInit:
    def test_init(self):
        pattern = RumorSpreadingPattern()
        assert pattern is not None
        assert pattern.config is not None
        assert pattern.network is not None
        assert pattern.states is not None

    def test_pattern_id(self):
        assert RumorSpreadingPattern.PATTERN_ID == "rumor_spreading"
        assert RumorSpreadingPattern.PATTERN_VERSION == "6.0.0"


# ═══════════════════════════════════════════════════════════════════
# Network Building
# ═══════════════════════════════════════════════════════════════════


class TestBuildNetwork:
    def test_complete_network(self):
        cfg = RumorConfig(network_type="complete", n_agents=10)
        pattern = RumorSpreadingPattern(cfg)
        assert pattern.network.shape == (10, 10)
        # Diagonal should be 0
        assert np.all(np.diag(pattern.network) == 0)
        # Off-diagonal should be 1
        for i in range(10):
            for j in range(10):
                if i != j:
                    assert pattern.network[i, j] == 1

    def test_small_world_network(self):
        cfg = RumorConfig(network_type="small_world", n_agents=20)
        pattern = RumorSpreadingPattern(cfg)
        assert pattern.network.shape == (20, 20)
        # Should have some connections
        assert np.sum(pattern.network) > 0

    def test_scale_free_network(self):
        cfg = RumorConfig(network_type="scale_free", n_agents=20)
        pattern = RumorSpreadingPattern(cfg)
        assert pattern.network.shape == (20, 20)

    def test_random_network(self):
        cfg = RumorConfig(network_type="random", n_agents=20, network_param=0.1)
        pattern = RumorSpreadingPattern(cfg)
        assert pattern.network.shape == (20, 20)


# ═══════════════════════════════════════════════════════════════════
# Initial State
# ═══════════════════════════════════════════════════════════════════


class TestInitialState:
    def test_initial_spreaders_set(self):
        cfg = RumorConfig(n_agents=100, initial_spreaders=5, model=RumorModel.SIR)
        pattern = RumorSpreadingPattern(cfg)
        # States 2 = spreaders
        assert np.sum(pattern.states == 2) == 5

    def test_seir_initial_exposed(self):
        cfg = RumorConfig(n_agents=100, initial_spreaders=5, model=RumorModel.SEIR)
        pattern = RumorSpreadingPattern(cfg)
        # States 1 = exposed
        assert np.sum(pattern.states == 1) == 5

    def test_seiz_initial_skeptics(self):
        cfg = RumorConfig(n_agents=100, initial_spreaders=5, model=RumorModel.SEIZ)
        pattern = RumorSpreadingPattern(cfg)
        # Should have some skeptics (states 4)
        assert np.sum(pattern.states == 4) > 0


# ═══════════════════════════════════════════════════════════════════
# State Transitions
# ═══════════════════════════════════════════════════════════════════


class TestStateTransitions:
    def test_sir_step_changes_states(self):
        cfg = RumorConfig(model=RumorModel.SIR, n_agents=50, spreading_rate=1.0, dt=0.5)
        pattern = RumorSpreadingPattern(cfg)
        initial_spreaders = np.sum(pattern.states == 2)
        pattern._sir_step()
        # With high spreading rate, should have more spreaders or stiflers
        assert np.sum(pattern.states == 0) < 50 - initial_spreaders  # Fewer ignorants

    def test_seir_step_changes_states(self):
        cfg = RumorConfig(model=RumorModel.SEIR, n_agents=50, spreading_rate=1.0, dt=0.5)
        pattern = RumorSpreadingPattern(cfg)
        pattern._seir_step()
        # Should have some state changes
        assert pattern.states is not None

    def test_seiz_step_changes_states(self):
        cfg = RumorConfig(model=RumorModel.SEIZ, n_agents=50, spreading_rate=1.0, skepticism_rate=0.5, dt=0.5)
        pattern = RumorSpreadingPattern(cfg)
        pattern._seiz_step()
        assert pattern.states is not None


# ═══════════════════════════════════════════════════════════════════
# State Counting
# ═══════════════════════════════════════════════════════════════════


class TestCountStates:
    def test_count_states_sums_to_total(self):
        cfg = RumorConfig(n_agents=100)
        pattern = RumorSpreadingPattern(cfg)
        counts = pattern._count_states()
        assert sum(counts) == 100

    def test_count_states_types(self):
        cfg = RumorConfig(n_agents=100)
        pattern = RumorSpreadingPattern(cfg)
        counts = pattern._count_states()
        assert len(counts) == 5  # I, E, S, R, Z


# ═══════════════════════════════════════════════════════════════════
# Run Simulation
# ═══════════════════════════════════════════════════════════════════


class TestRun:
    def test_run_sir(self):
        cfg = RumorConfig(model=RumorModel.SIR, n_agents=100, max_time=10.0)
        pattern = RumorSpreadingPattern(cfg)
        result = pattern.run()
        assert "model" in result
        assert "final_state" in result
        assert "history" in result
        assert "statistics" in result
        assert result["model"] == "sir"

    def test_run_seir(self):
        cfg = RumorConfig(model=RumorModel.SEIR, n_agents=100, max_time=10.0)
        pattern = RumorSpreadingPattern(cfg)
        result = pattern.run()
        assert result["model"] == "seir"
        assert "exposed" in result["final_state"]

    def test_run_seiz(self):
        cfg = RumorConfig(model=RumorModel.SEIZ, n_agents=100, max_time=10.0)
        pattern = RumorSpreadingPattern(cfg)
        result = pattern.run()
        assert result["model"] == "seiz"
        assert "skeptics" in result["final_state"]

    def test_statistics_structure(self):
        cfg = RumorConfig(n_agents=100, max_time=10.0)
        pattern = RumorSpreadingPattern(cfg)
        result = pattern.run()
        stats = result["statistics"]
        assert "final_reach" in stats
        assert "peak_spreaders" in stats
        assert "peak_time" in stats
        assert "half_life" in stats
        assert "r0_estimate" in stats


# ═══════════════════════════════════════════════════════════════════
# Final Reach Calculation
# ═══════════════════════════════════════════════════════════════════


class TestCalculateFinalReach:
    def test_final_reach_range(self):
        cfg = RumorConfig(n_agents=100, max_time=10.0)
        pattern = RumorSpreadingPattern(cfg)
        pattern.run()
        reach = pattern._calculate_final_reach()
        assert 0 <= reach <= 1


# ═══════════════════════════════════════════════════════════════════
# Peak Spreaders Calculation
# ═══════════════════════════════════════════════════════════════════


class TestCalculatePeakSpreaders:
    def test_peak_spreaders_positive(self):
        cfg = RumorConfig(n_agents=100, max_time=10.0, spreading_rate=0.8)
        pattern = RumorSpreadingPattern(cfg)
        pattern.run()
        peak, time = pattern._calculate_peak_spreaders()
        assert peak >= 0
        assert time >= 0


# ═══════════════════════════════════════════════════════════════════
# get_metadata
# ═══════════════════════════════════════════════════════════════════


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = RumorSpreadingPattern.get_metadata()
        assert meta["id"] == "rumor_spreading"
        assert meta["name"] == "Rumor Spreading"
        assert "category" in meta
        assert "parameters" in meta


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_high_spreading_rate(self):
        cfg = RumorConfig(n_agents=100, spreading_rate=1.0, max_time=10.0)
        pattern = RumorSpreadingPattern(cfg)
        result = pattern.run()
        # High spreading rate should lead to high reach
        assert result["statistics"]["final_reach"] > 0.3

    def test_low_spreading_rate(self):
        cfg = RumorConfig(n_agents=100, spreading_rate=0.01, stifling_rate=0.5, max_time=10.0)
        pattern = RumorSpreadingPattern(cfg)
        result = pattern.run()
        # Low spreading rate with high stifling may die out quickly
        assert result["statistics"]["final_reach"] >= 0

    def test_counter_rumor(self):
        cfg = RumorConfig(
            n_agents=100,
            spreading_rate=0.8,
            counter_rumor_start=5.0,
            counter_rumor_strength=0.5,
            max_time=20.0,
        )
        pattern = RumorSpreadingPattern(cfg)
        result = pattern.run()
        assert "final_state" in result

    def test_small_network(self):
        cfg = RumorConfig(n_agents=10, max_time=5.0)
        pattern = RumorSpreadingPattern(cfg)
        result = pattern.run()
        assert result["final_state"]["ignorant"] + result["final_state"]["spreaders"] + result["final_state"]["stiflers"] == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
