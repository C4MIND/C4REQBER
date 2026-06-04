"""
Tests for src/patterns/library/innovation_diffusion.py (Innovation Diffusion Pattern)

Covers:
- DiffusionModel enum
- InnovationDiffusionConfig dataclass
- InnovationDiffusionPattern initialization
- _initialize() and _build_network()
- _bass_derivative()
- _generalized_bass_derivative()
- _network_step()
- _calculate_t_star() and _calculate_m_peak()
- run() simulation for different models
- _format_output()
- get_metadata()
- Edge cases: zero innovation, high imitation, network effects
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.innovation_diffusion import (

    InnovationDiffusionPattern,
    InnovationDiffusionConfig,
    DiffusionModel,
)


# ═══════════════════════════════════════════════════════════════════
# Enums and Dataclasses
# ═══════════════════════════════════════════════════════════════════


class TestDiffusionModel:
    def test_enum_values(self):
        assert DiffusionModel.BASS.value == "bass"
        assert DiffusionModel.GENERALIZED_BASS.value == "generalized_bass"
        assert DiffusionModel.MULTIGENERATION.value == "multigen"
        assert DiffusionModel.NETWORK.value == "network"


class TestInnovationDiffusionConfig:
    def test_default_init(self):
        cfg = InnovationDiffusionConfig()
        assert cfg.model == DiffusionModel.BASS
        assert cfg.market_size == 1000000.0
        assert cfg.p == 0.03
        assert cfg.q == 0.38
        assert cfg.price_coefficient == -1.5
        assert cfg.advertising_coefficient == 0.1
        assert cfg.n_generations == 1
        assert cfg.n_agents == 1000
        assert cfg.network_type == "small_world"
        assert cfg.seed_nodes == 10
        assert cfg.dt == 0.1
        assert cfg.max_time == 10.0

    def test_custom_init(self):
        cfg = InnovationDiffusionConfig(
            model=DiffusionModel.NETWORK,
            market_size=500000.0,
            p=0.05,
            q=0.5,
            n_agents=500,
        )
        assert cfg.model == DiffusionModel.NETWORK
        assert cfg.market_size == 500000.0
        assert cfg.p == 0.05
        assert cfg.q == 0.5
        assert cfg.n_agents == 500


# ═══════════════════════════════════════════════════════════════════
# InnovationDiffusionPattern Initialization
# ═══════════════════════════════════════════════════════════════════


class TestInnovationDiffusionPatternInit:
    def test_init(self):
        pattern = InnovationDiffusionPattern()
        assert pattern is not None
        assert pattern.config is not None
        assert pattern.cumulative_adopters == 0.0
        assert pattern.time == 0.0

    def test_pattern_id(self):
        assert InnovationDiffusionPattern.PATTERN_ID == "innovation_diffusion"
        assert InnovationDiffusionPattern.PATTERN_VERSION == "6.0.0"


# ═══════════════════════════════════════════════════════════════════
# Network Building
# ═══════════════════════════════════════════════════════════════════


class TestBuildNetwork:
    def test_complete_network(self):
        cfg = InnovationDiffusionConfig(model=DiffusionModel.NETWORK, network_type="complete", n_agents=10)
        pattern = InnovationDiffusionPattern(cfg)
        assert pattern.network is not None
        assert pattern.network.shape == (10, 10)

    def test_small_world_network(self):
        cfg = InnovationDiffusionConfig(model=DiffusionModel.NETWORK, network_type="small_world", n_agents=20)
        pattern = InnovationDiffusionPattern(cfg)
        assert pattern.network is not None
        assert pattern.network.shape == (20, 20)

    def test_scale_free_network(self):
        cfg = InnovationDiffusionConfig(model=DiffusionModel.NETWORK, network_type="scale_free", n_agents=20)
        pattern = InnovationDiffusionPattern(cfg)
        assert pattern.network is not None

    def test_random_network(self):
        cfg = InnovationDiffusionConfig(model=DiffusionModel.NETWORK, network_type="random", n_agents=20)
        pattern = InnovationDiffusionPattern(cfg)
        assert pattern.network is not None


# ═══════════════════════════════════════════════════════════════════
# Derivative Calculations
# ═══════════════════════════════════════════════════════════════════


class TestBassDerivative:
    def test_bass_derivative_positive(self):
        cfg = InnovationDiffusionConfig(p=0.03, q=0.38)
        pattern = InnovationDiffusionPattern(cfg)
        # At f=0, derivative should be p
        assert pattern._bass_derivative(0.0) == pytest.approx(0.03)

    def test_bass_derivative_zero_at_full_adoption(self):
        cfg = InnovationDiffusionConfig()
        pattern = InnovationDiffusionPattern(cfg)
        # At f=1, derivative should be 0
        assert pattern._bass_derivative(1.0) == 0.0

    def test_bass_derivative_increases_with_f(self):
        cfg = InnovationDiffusionConfig(p=0.03, q=0.38)
        pattern = InnovationDiffusionPattern(cfg)
        # Derivative should be higher at f=0.5 than f=0
        assert pattern._bass_derivative(0.5) > pattern._bass_derivative(0.0)


class TestGeneralizedBassDerivative:
    def test_generalized_bass_with_marketing(self):
        cfg = InnovationDiffusionConfig(
            marketing_mix=[(0, 1.0, 0), (3, 0.8, 100)],
            advertising_coefficient=0.002,
        )
        pattern = InnovationDiffusionPattern(cfg)
        # Should not raise error
        deriv = pattern._generalized_bass_derivative(0.5, 1.0)
        assert deriv >= 0


# ═══════════════════════════════════════════════════════════════════
# Theoretical Calculations
# ═══════════════════════════════════════════════════════════════════


class TestTheoreticalCalculations:
    def test_t_star_positive(self):
        cfg = InnovationDiffusionConfig(p=0.03, q=0.38)
        pattern = InnovationDiffusionPattern(cfg)
        t_star = pattern._calculate_t_star()
        assert t_star > 0

    def test_m_peak_positive(self):
        cfg = InnovationDiffusionConfig(p=0.03, q=0.38)
        pattern = InnovationDiffusionPattern(cfg)
        m_peak = pattern._calculate_m_peak()
        assert m_peak > 0


# ═══════════════════════════════════════════════════════════════════
# Network Step
# ═══════════════════════════════════════════════════════════════════


class TestNetworkStep:
    def test_network_step_changes_state(self):
        cfg = InnovationDiffusionConfig(
            model=DiffusionModel.NETWORK,
            n_agents=50,
            p=0.1,
            q=0.4,
        )
        pattern = InnovationDiffusionPattern(cfg)
        initial_adopters = np.sum(pattern.adopted)
        new_adoptions = pattern._network_step()
        assert new_adoptions >= 0
        # With high p and q, should have some adoptions
        assert np.sum(pattern.adopted) >= initial_adopters


# ═══════════════════════════════════════════════════════════════════
# Run Simulation
# ═══════════════════════════════════════════════════════════════════


class TestRun:
    def test_run_bass(self):
        cfg = InnovationDiffusionConfig(model=DiffusionModel.BASS, market_size=10000, max_time=5.0)
        pattern = InnovationDiffusionPattern(cfg)
        result = pattern.run()
        assert "model" in result
        assert "final_adopters" in result
        assert "final_penetration" in result
        assert "peak" in result
        assert result["model"] == "bass"

    def test_run_generalized_bass(self):
        cfg = InnovationDiffusionConfig(
            model=DiffusionModel.GENERALIZED_BASS,
            market_size=10000,
            max_time=5.0,
        )
        pattern = InnovationDiffusionPattern(cfg)
        result = pattern.run()
        assert result["model"] == "generalized_bass"

    def test_run_network(self):
        cfg = InnovationDiffusionConfig(
            model=DiffusionModel.NETWORK,
            n_agents=100,
            max_time=5.0,
        )
        pattern = InnovationDiffusionPattern(cfg)
        result = pattern.run()
        assert result["model"] == "network"

    def test_results_structure(self):
        cfg = InnovationDiffusionConfig(market_size=10000, max_time=5.0)
        pattern = InnovationDiffusionPattern(cfg)
        result = pattern.run()
        assert "history" in result
        assert "peak" in result
        assert "theoretical" in result
        assert "bass_parameters" in result
        assert "config" in result
        assert "p" in result["bass_parameters"]
        assert "q" in result["bass_parameters"]
        assert "q_p_ratio" in result["bass_parameters"]
        assert "interpretation" in result["bass_parameters"]

    def test_history_recorded(self):
        cfg = InnovationDiffusionConfig(market_size=10000, max_time=5.0)
        pattern = InnovationDiffusionPattern(cfg)
        result = pattern.run()
        assert "time" in result["history"]
        assert "cumulative" in result["history"]
        assert "fraction" in result["history"]
        assert "adoption_rate" in result["history"]


# ═══════════════════════════════════════════════════════════════════
# Parameter Interpretation
# ═══════════════════════════════════════════════════════════════════


class TestInterpretParameters:
    def test_innovation_dominated(self):
        cfg = InnovationDiffusionConfig(p=0.1, q=0.01)
        pattern = InnovationDiffusionPattern(cfg)
        interpretation = pattern._interpret_parameters()
        assert "Innovation-dominated" in interpretation

    def test_imitation_dominated(self):
        cfg = InnovationDiffusionConfig(p=0.01, q=0.5)
        pattern = InnovationDiffusionPattern(cfg)
        interpretation = pattern._interpret_parameters()
        assert "Imitation-dominated" in interpretation or "Balanced" in interpretation


# ═══════════════════════════════════════════════════════════════════
# get_metadata
# ═══════════════════════════════════════════════════════════════════


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = InnovationDiffusionPattern.get_metadata()
        assert meta["id"] == "innovation_diffusion"
        assert meta["name"] == "Innovation Diffusion"
        assert "category" in meta
        assert "parameters" in meta


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_zero_innovation(self):
        cfg = InnovationDiffusionConfig(p=0.001, q=0.1, max_time=5.0)
        pattern = InnovationDiffusionPattern(cfg)
        result = pattern.run()
        # Low p should lead to slow adoption
        assert result["final_penetration"] >= 0

    def test_high_imitation(self):
        cfg = InnovationDiffusionConfig(p=0.01, q=1.0, max_time=5.0)
        pattern = InnovationDiffusionPattern(cfg)
        result = pattern.run()
        # High q should lead to fast adoption once started
        assert result["final_penetration"] > 0.1

    def test_small_market(self):
        cfg = InnovationDiffusionConfig(market_size=100, max_time=2.0)
        pattern = InnovationDiffusionPattern(cfg)
        result = pattern.run()
        assert result["config"]["market_size"] == 100

    def test_short_time(self):
        cfg = InnovationDiffusionConfig(max_time=1.0)
        pattern = InnovationDiffusionPattern(cfg)
        result = pattern.run()
        assert result["peak"]["time"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
