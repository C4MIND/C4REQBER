"""
Tests for src/patterns/library/opinion_dynamics.py (Opinion Dynamics pattern)

Covers:
- OpinionModel enum
- OpinionDynamicsConfig dataclass
- _build_network() for different network types
- OpinionDynamicsPattern initialization
- _degroot_step(), _hk_step(), _fj_step()
- _add_noise()
- run() integration
- get_metadata()
- Edge cases: different models, network structures, stubborn agents
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.opinion_dynamics import (

    OpinionDynamicsPattern,
    OpinionDynamicsConfig,
    OpinionModel,
    _build_network,
)


# ═══════════════════════════════════════════════════════════════════
# Enum and Config Tests
# ═══════════════════════════════════════════════════════════════════


class TestOpinionModel:
    def test_enum_values(self):
        assert OpinionModel.DEGROOT.value == "degroot"
        assert OpinionModel.HEGSELMANN_KRAUSE.value == "hk"
        assert OpinionModel.FRIEDKIN_JOHNSEN.value == "fj"


class TestOpinionDynamicsConfig:
    def test_default_init(self):
        cfg = OpinionDynamicsConfig()
        assert cfg.model == OpinionModel.HEGSELMANN_KRAUSE
        assert cfg.n_agents == 100
        assert cfg.n_issues == 1
        assert cfg.opinion_range == (-1.0, 1.0)
        assert cfg.network_type == "complete"
        assert cfg.confidence_bound == 0.2

    def test_custom_init(self):
        cfg = OpinionDynamicsConfig(
            model=OpinionModel.DEGROOT,
            n_agents=50,
            n_issues=2,
            network_type="ring"
        )
        assert cfg.model == OpinionModel.DEGROOT
        assert cfg.n_agents == 50
        assert cfg.n_issues == 2
        assert cfg.network_type == "ring"


# ═══════════════════════════════════════════════════════════════════
# Network Building Tests
# ═══════════════════════════════════════════════════════════════════


class TestBuildNetwork:
    def test_complete_network(self):
        adj = _build_network(5, "complete", 0.0)
        assert adj.shape == (5, 5)
        # Complete graph: all off-diagonal should be 1
        assert np.sum(adj) == 5 * 4  # n*(n-1)
        assert np.all(np.diag(adj) == 0)

    def test_ring_network(self):
        adj = _build_network(5, "ring", 0.0)
        assert adj.shape == (5, 5)
        # Ring: each node has 2 neighbors
        assert np.all(np.sum(adj, axis=1) == 2)

    def test_random_network_shape(self):
        adj = _build_network(10, "random", 0.3)
        assert adj.shape == (10, 10)
        # Symmetric
        assert np.allclose(adj, adj.T)
        # No self-loops
        assert np.all(np.diag(adj) == 0)

    def test_scale_free_network(self):
        adj = _build_network(10, "scale_free", 2.0)
        assert adj.shape == (10, 10)
        assert np.allclose(adj, adj.T)

    def test_small_world_network(self):
        adj = _build_network(10, "small_world", 0.3)
        assert adj.shape == (10, 10)
        assert np.allclose(adj, adj.T)


# ═══════════════════════════════════════════════════════════════════
# Initialization Tests
# ═══════════════════════════════════════════════════════════════════


class TestOpinionDynamicsPatternInit:
    def test_default_init(self):
        pattern = OpinionDynamicsPattern()
        assert pattern.PATTERN_ID == "opinion_dynamics"
        assert pattern.opinions is not None
        assert pattern.history is not None
        assert pattern.network is not None

    def test_opinions_shape(self):
        cfg = OpinionDynamicsConfig(n_agents=50, n_issues=2)
        pattern = OpinionDynamicsPattern(cfg)
        assert pattern.opinions.shape == (50, 2)

    def test_opinions_in_range(self):
        cfg = OpinionDynamicsConfig(opinion_range=(-1.0, 1.0))
        pattern = OpinionDynamicsPattern(cfg)
        assert np.all(pattern.opinions >= -1.0)
        assert np.all(pattern.opinions <= 1.0)

    def test_network_normalized(self):
        pattern = OpinionDynamicsPattern()
        # Row sums of influence matrix should be 1 (or 0 for isolated)
        row_sums = np.sum(pattern.influence_matrix, axis=1)
        assert np.all((row_sums > 0.99) | (row_sums == 0))

    def test_polarized_initial(self):
        cfg = OpinionDynamicsConfig(initial_distribution="polarized", n_agents=100)
        pattern = OpinionDynamicsPattern(cfg)
        # Should have roughly half negative, half positive
        assert np.sum(pattern.opinions < 0) > 30
        assert np.sum(pattern.opinions > 0) > 30


# ═══════════════════════════════════════════════════════════════════
# Step Function Tests
# ═══════════════════════════════════════════════════════════════════


class TestDegrootStep:
    def test_decreasing_variance(self):
        """DeGroot should reduce opinion variance"""
        cfg = OpinionDynamicsConfig(model=OpinionModel.DEGROOT, n_agents=50)
        pattern = OpinionDynamicsPattern(cfg)
        var_before = np.var(pattern.opinions)

        for _ in range(50):
            pattern.opinions = pattern._degroot_step()

        var_after = np.var(pattern.opinions)
        assert var_after < var_before

    def test_opinions_stay_in_range(self):
        cfg = OpinionDynamicsConfig(model=OpinionModel.DEGROOT)
        pattern = OpinionDynamicsPattern(cfg)

        for _ in range(10):
            pattern.opinions = pattern._degroot_step()

        assert np.all(pattern.opinions >= -1.0)
        assert np.all(pattern.opinions <= 1.0)


class TestHKStep:
    def test_bounded_confidence(self):
        """HK model respects confidence bound"""
        cfg = OpinionDynamicsConfig(
            model=OpinionModel.HEGSELMANN_KRAUSE,
            n_agents=50,
            confidence_bound=0.3
        )
        pattern = OpinionDynamicsPattern(cfg)

        opinions_before = pattern.opinions.copy()
        pattern.opinions = pattern._hk_step()

        # Opinions should change
        assert not np.allclose(pattern.opinions, opinions_before)

    def test_no_interaction_when_far(self):
        """Agents beyond confidence bound don't interact"""
        cfg = OpinionDynamicsConfig(
            model=OpinionModel.HEGSELMANN_KRAUSE,
            n_agents=2,
            confidence_bound=0.1,
            initial_distribution="uniform"
        )
        pattern = OpinionDynamicsPattern(cfg)
        # Force far apart opinions
        pattern.opinions[0] = -0.9
        pattern.opinions[1] = 0.9

        opinions_before = pattern.opinions.copy()
        pattern.opinions = pattern._hk_step()

        # No change since opinions are far apart
        assert np.allclose(pattern.opinions, opinions_before, atol=0.01)


class TestFJStep:
    def test_stubbornness_effect(self):
        """Stubborn agents resist change"""
        cfg = OpinionDynamicsConfig(
            model=OpinionModel.FRIEDKIN_JOHNSEN,
            n_agents=10,
            stubbornness=[0.9] * 10  # Very stubborn
        )
        pattern = OpinionDynamicsPattern(cfg)
        initial = pattern.initial_opinions.copy()

        for _ in range(10):
            pattern.opinions = pattern._fj_step()

        # Opinions should stay close to initial
        assert np.allclose(pattern.opinions, initial, atol=0.3)


# ═══════════════════════════════════════════════════════════════════
# Noise Tests
# ═══════════════════════════════════════════════════════════════════


class TestAddNoise:
    def test_noise_changes_opinions(self):
        cfg = OpinionDynamicsConfig(noise_level=0.1)
        pattern = OpinionDynamicsPattern(cfg)
        opinions = np.zeros((10, 1))

        noisy = pattern._add_noise(opinions)
        assert not np.allclose(noisy, opinions)

    def test_opinions_clipped(self):
        cfg = OpinionDynamicsConfig(noise_level=1.0, opinion_range=(-1.0, 1.0))
        pattern = OpinionDynamicsPattern(cfg)
        opinions = np.ones((10, 1)) * 0.9

        for _ in range(10):
            opinions = pattern._add_noise(opinions)

        assert np.all(opinions >= -1.0)
        assert np.all(opinions <= 1.0)

    def test_no_noise(self):
        cfg = OpinionDynamicsConfig(noise_level=0.0)
        pattern = OpinionDynamicsPattern(cfg)
        opinions = np.ones((10, 1))

        noisy = pattern._add_noise(opinions)
        assert np.allclose(noisy, opinions)


# ═══════════════════════════════════════════════════════════════════
# Run Integration Tests
# ═══════════════════════════════════════════════════════════════════


class TestRun:
    def test_run_degroot(self):
        cfg = OpinionDynamicsConfig(model=OpinionModel.DEGROOT, n_agents=50)
        pattern = OpinionDynamicsPattern(cfg)
        result = pattern.run()
        assert result["model"] == "degroot"
        assert result["consensus_reached"] is True

    def test_run_hk(self):
        cfg = OpinionDynamicsConfig(model=OpinionModel.HEGSELMANN_KRAUSE, n_agents=50)
        pattern = OpinionDynamicsPattern(cfg)
        result = pattern.run()
        assert result["model"] == "hk"

    def test_run_fj(self):
        cfg = OpinionDynamicsConfig(model=OpinionModel.FRIEDKIN_JOHNSEN, n_agents=50)
        pattern = OpinionDynamicsPattern(cfg)
        result = pattern.run()
        assert result["model"] == "fj"

    def test_consensus_degroot_complete(self):
        """DeGroot on complete graph should reach consensus"""
        cfg = OpinionDynamicsConfig(
            model=OpinionModel.DEGROOT,
            n_agents=50,
            network_type="complete",
            max_iterations=500
        )
        pattern = OpinionDynamicsPattern(cfg)
        result = pattern.run()
        assert result["consensus_reached"] is True
        assert result["statistics"]["opinion_variance"] < 0.01

    def test_polarization_hk(self):
        """HK with polarized initial can lead to clusters"""
        cfg = OpinionDynamicsConfig(
            model=OpinionModel.HEGSELMANN_KRAUSE,
            n_agents=100,
            initial_distribution="polarized",
            confidence_bound=0.3,
            max_iterations=500
        )
        pattern = OpinionDynamicsPattern(cfg)
        result = pattern.run()
        assert result["statistics"]["n_clusters"] >= 1

    def test_statistics_present(self):
        cfg = OpinionDynamicsConfig(n_agents=50)
        pattern = OpinionDynamicsPattern(cfg)
        result = pattern.run()
        stats = result["statistics"]
        assert "mean_opinion" in stats
        assert "opinion_variance" in stats
        assert "n_clusters" in stats
        assert "polarization_index" in stats

    def test_network_info_present(self):
        cfg = OpinionDynamicsConfig(n_agents=20)
        pattern = OpinionDynamicsPattern(cfg)
        result = pattern.run()
        assert "network" in result
        assert "density" in result["network"]
        assert "type" in result["network"]

    def test_opinion_history_recorded(self):
        cfg = OpinionDynamicsConfig(n_agents=50, max_iterations=100)
        pattern = OpinionDynamicsPattern(cfg)
        result = pattern.run()
        assert "opinion_history" in result
        assert len(result["opinion_history"]) > 0


# ═══════════════════════════════════════════════════════════════════
# Metadata Tests
# ═══════════════════════════════════════════════════════════════════


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = OpinionDynamicsPattern.get_metadata()
        assert meta["id"] == "opinion_dynamics"
        assert "name" in meta
        assert "category" in meta
        assert "parameters" in meta

    def test_model_parameter(self):
        meta = OpinionDynamicsPattern.get_metadata()
        model_param = next(p for p in meta["parameters"] if p["name"] == "model")
        assert "degroot" in model_param["options"]
        assert "hk" in model_param["options"]


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_single_agent(self):
        cfg = OpinionDynamicsConfig(n_agents=1)
        pattern = OpinionDynamicsPattern(cfg)
        result = pattern.run()
        assert result["consensus_reached"] is True

    def test_zero_iterations(self):
        cfg = OpinionDynamicsConfig(n_agents=10, max_iterations=0)
        pattern = OpinionDynamicsPattern(cfg)
        result = pattern.run()
        assert result["iterations"] == 0

    def test_very_high_confidence(self):
        """Very high confidence bound allows all interactions"""
        cfg = OpinionDynamicsConfig(
            model=OpinionModel.HEGSELMANN_KRAUSE,
            n_agents=50,
            confidence_bound=10.0  # Larger than opinion range
        )
        pattern = OpinionDynamicsPattern(cfg)
        result = pattern.run()
        # Should reach consensus since everyone interacts
        assert result["statistics"]["opinion_variance"] < 0.1

    def test_very_low_confidence(self):
        """Very low confidence bound prevents most interactions"""
        cfg = OpinionDynamicsConfig(
            model=OpinionModel.HEGSELMANN_KRAUSE,
            n_agents=50,
            confidence_bound=0.01  # Very small
        )
        pattern = OpinionDynamicsPattern(cfg)
        result = pattern.run()
        # Should maintain clusters or not converge
        assert result["statistics"]["n_clusters"] >= 1

    def test_different_network_types(self):
        for net_type in ["complete", "ring", "random", "scale_free", "small_world"]:
            cfg = OpinionDynamicsConfig(
                model=OpinionModel.DEGROOT,
                n_agents=30,
                network_type=net_type,
                max_iterations=50
            )
            pattern = OpinionDynamicsPattern(cfg)
            result = pattern.run()
            assert result["iterations"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
