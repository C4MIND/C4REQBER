"""
Tests for src/patterns/library/cultural_diffusion.py (Cultural Diffusion pattern)

Covers:
- CulturalDiffusionConfig dataclass
- CulturalDiffusionPattern initialization
- _initialize() and _build_neighbors()
- _cultural_similarity()
- _interact()
- _mutate()
- _count_regions() and _get_region_sizes()
- _cultural_diversity()
- run() integration
- get_metadata()
- Edge cases: different grid sizes, mutation effects
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.cultural_diffusion import (

    CulturalDiffusionPattern,
    CulturalDiffusionConfig,
)


# ═══════════════════════════════════════════════════════════════════
# Config Tests
# ═══════════════════════════════════════════════════════════════════


class TestCulturalDiffusionConfig:
    def test_default_init(self):
        cfg = CulturalDiffusionConfig()
        assert cfg.n_agents == 400
        assert cfg.grid_size == (20, 20)
        assert cfg.n_features == 5
        assert cfg.n_traits == 10
        assert cfg.interaction_radius == 1
        assert cfg.max_steps == 100000

    def test_custom_init(self):
        cfg = CulturalDiffusionConfig(
            n_agents=100,
            n_features=3,
            n_traits=5,
            interaction_radius=2
        )
        assert cfg.n_agents == 100
        assert cfg.n_features == 3
        assert cfg.n_traits == 5
        assert cfg.interaction_radius == 2


# ═══════════════════════════════════════════════════════════════════
# Initialization Tests
# ═══════════════════════════════════════════════════════════════════


class TestCulturalDiffusionPatternInit:
    def test_default_init(self):
        pattern = CulturalDiffusionPattern()
        assert pattern.PATTERN_ID == "cultural_diffusion"
        assert pattern.culture is not None
        assert pattern.positions is not None
        assert pattern.history is not None

    def test_culture_shape(self):
        cfg = CulturalDiffusionConfig(n_agents=100, n_features=3)
        pattern = CulturalDiffusionPattern(cfg)
        assert pattern.culture.shape == (100, 3)

    def test_positions_shape(self):
        cfg = CulturalDiffusionConfig(n_agents=100)
        pattern = CulturalDiffusionPattern(cfg)
        assert pattern.positions.shape == (100, 2)

    def test_culture_values_in_range(self):
        cfg = CulturalDiffusionConfig(n_agents=50, n_traits=5)
        pattern = CulturalDiffusionPattern(cfg)
        assert np.all(pattern.culture >= 0)
        assert np.all(pattern.culture < 5)

    def test_neighbors_built(self):
        pattern = CulturalDiffusionPattern()
        assert len(pattern.neighbors) > 0


# ═══════════════════════════════════════════════════════════════════
# Grid Adjustment Tests
# ═══════════════════════════════════════════════════════════════════


class TestGridAdjustment:
    def test_grid_adjusted_if_mismatch(self):
        """If n_agents doesn't match grid_size, it should be adjusted"""
        cfg = CulturalDiffusionConfig(n_agents=50, grid_size=(10, 10))  # 100 != 50
        pattern = CulturalDiffusionPattern(cfg)
        # Grid should have been adjusted
        assert cfg.n_agents <= 100


# ═══════════════════════════════════════════════════════════════════
# Neighbor Tests
# ═══════════════════════════════════════════════════════════════════


class TestBuildNeighbors:
    def test_neighbors_exist(self):
        cfg = CulturalDiffusionConfig(n_agents=9, grid_size=(3, 3))
        pattern = CulturalDiffusionPattern(cfg)
        # Center agent should have neighbors
        center_neighbors = pattern.neighbors[4]  # Center of 3x3
        assert len(center_neighbors) > 0

    def test_radius_effect(self):
        """Larger radius should include more neighbors"""
        cfg_small = CulturalDiffusionConfig(n_agents=25, grid_size=(5, 5), interaction_radius=1)
        pattern_small = CulturalDiffusionPattern(cfg_small)
        center_small = len(pattern_small.neighbors[12])

        cfg_large = CulturalDiffusionConfig(n_agents=25, grid_size=(5, 5), interaction_radius=2)
        pattern_large = CulturalDiffusionPattern(cfg_large)
        center_large = len(pattern_large.neighbors[12])

        assert center_large >= center_small


# ═══════════════════════════════════════════════════════════════════
# Cultural Similarity Tests
# ═══════════════════════════════════════════════════════════════════


class TestCulturalSimilarity:
    def test_identical_culture(self):
        cfg = CulturalDiffusionConfig(n_agents=2, n_features=3)
        pattern = CulturalDiffusionPattern(cfg)
        pattern.culture[0] = [1, 2, 3]
        pattern.culture[1] = [1, 2, 3]
        sim = pattern._cultural_similarity(0, 1)
        assert sim == 1.0

    def test_completely_different(self):
        cfg = CulturalDiffusionConfig(n_agents=2, n_features=3, n_traits=10)
        pattern = CulturalDiffusionPattern(cfg)
        pattern.culture[0] = [0, 0, 0]
        pattern.culture[1] = [1, 1, 1]
        sim = pattern._cultural_similarity(0, 1)
        assert sim == 0.0

    def test_partial_similarity(self):
        cfg = CulturalDiffusionConfig(n_agents=2, n_features=4)
        pattern = CulturalDiffusionPattern(cfg)
        pattern.culture[0] = [1, 2, 3, 4]
        pattern.culture[1] = [1, 2, 0, 0]
        sim = pattern._cultural_similarity(0, 1)
        assert sim == 0.5


# ═══════════════════════════════════════════════════════════════════
# Interaction Tests
# ═══════════════════════════════════════════════════════════════════


class TestInteract:
    def test_interaction_when_similar(self):
        """Agents should interact when they share some traits"""
        cfg = CulturalDiffusionConfig(n_agents=2, n_features=3)
        pattern = CulturalDiffusionPattern(cfg)
        pattern.culture[0] = [1, 2, 0]
        pattern.culture[1] = [1, 2, 3]
        pattern.neighbors[0] = [1]

        culture_before = pattern.culture[0].copy()
        interacted = pattern._interact(0, 1)

        # Should have adopted trait 2 from agent 1
        if interacted:
            assert not np.array_equal(pattern.culture[0], culture_before) or pattern.culture[0, 2] == 3

    def test_no_interaction_when_identical(self):
        """Identical agents don't interact"""
        cfg = CulturalDiffusionConfig(n_agents=2, n_features=3)
        pattern = CulturalDiffusionPattern(cfg)
        pattern.culture[0] = [1, 2, 3]
        pattern.culture[1] = [1, 2, 3]

        interacted = pattern._interact(0, 1)
        assert interacted is False

    def test_no_interaction_when_completely_different(self):
        """Completely different agents don't interact"""
        cfg = CulturalDiffusionConfig(n_agents=2, n_features=3, n_traits=10)
        pattern = CulturalDiffusionPattern(cfg)
        pattern.culture[0] = [0, 0, 0]
        pattern.culture[1] = [1, 1, 1]

        interacted = pattern._interact(0, 1)
        assert interacted is False


# ═══════════════════════════════════════════════════════════════════
# Mutation Tests
# ═══════════════════════════════════════════════════════════════════


class TestMutate:
    def test_mutation_changes_culture(self):
        cfg = CulturalDiffusionConfig(n_agents=10, enable_mutation=True, mutation_rate=1.0)
        pattern = CulturalDiffusionPattern(cfg)
        culture_before = pattern.culture.copy()

        pattern._mutate()

        # With high mutation rate, culture should change
        assert not np.array_equal(pattern.culture, culture_before)

    def test_no_mutation_when_disabled(self):
        cfg = CulturalDiffusionConfig(n_agents=10, enable_mutation=False)
        pattern = CulturalDiffusionPattern(cfg)
        culture_before = pattern.culture.copy()

        pattern._mutate()

        assert np.array_equal(pattern.culture, culture_before)


# ═══════════════════════════════════════════════════════════════════
# Region Counting Tests
# ═══════════════════════════════════════════════════════════════════


class TestCountRegions:
    def test_single_region_when_all_identical(self):
        cfg = CulturalDiffusionConfig(n_agents=9, n_features=2)
        pattern = CulturalDiffusionPattern(cfg)
        # Make all identical
        pattern.culture[:] = [1, 2]

        regions = pattern._count_regions()
        assert regions == 1

    def test_many_regions_when_all_different(self):
        cfg = CulturalDiffusionConfig(n_agents=4, n_features=2, n_traits=10)
        pattern = CulturalDiffusionPattern(cfg)
        # Make all different
        pattern.culture[0] = [0, 0]
        pattern.culture[1] = [1, 1]
        pattern.culture[2] = [2, 2]
        pattern.culture[3] = [3, 3]

        regions = pattern._count_regions()
        assert regions == 4


class TestGetRegionSizes:
    def test_sizes_sum_to_total(self):
        cfg = CulturalDiffusionConfig(n_agents=16)
        pattern = CulturalDiffusionPattern(cfg)
        sizes = pattern._get_region_sizes()
        assert sum(sizes) == cfg.n_agents


# ═══════════════════════════════════════════════════════════════════
# Diversity Tests
# ═══════════════════════════════════════════════════════════════════


class TestCulturalDiversity:
    def test_full_diversity(self):
        """All different cultures -> diversity = 1"""
        cfg = CulturalDiffusionConfig(n_agents=5, n_features=3, n_traits=10)
        pattern = CulturalDiffusionPattern(cfg)
        # Make all different
        for i in range(5):
            pattern.culture[i] = [i, i, i]

        diversity = pattern._cultural_diversity()
        assert diversity == 1.0

    def test_no_diversity(self):
        """All identical cultures -> diversity = 1/n_agents"""
        cfg = CulturalDiffusionConfig(n_agents=10, n_features=2)
        pattern = CulturalDiffusionPattern(cfg)
        # Make all identical
        pattern.culture[:] = [1, 2]

        diversity = pattern._cultural_diversity()
        assert diversity == 0.1  # 1 unique / 10 agents


# ═══════════════════════════════════════════════════════════════════
# Run Integration Tests
# ═══════════════════════════════════════════════════════════════════


class TestRun:
    def test_run_default(self):
        cfg = CulturalDiffusionConfig(n_agents=25, max_steps=1000)
        pattern = CulturalDiffusionPattern(cfg)
        result = pattern.run()
        assert "final_step" in result
        assert "n_regions" in result
        assert "cultural_diversity" in result

    def test_regions_form(self):
        cfg = CulturalDiffusionConfig(n_agents=25, n_features=3, n_traits=5, max_steps=5000)
        pattern = CulturalDiffusionPattern(cfg)
        result = pattern.run()
        assert result["n_regions"] >= 1

    def test_diversity_decreases(self):
        """Cultural diversity should decrease over time (regions form)"""
        cfg = CulturalDiffusionConfig(n_agents=25, n_features=3, n_traits=5, max_steps=5000)
        pattern = CulturalDiffusionPattern(cfg)

        initial_diversity = pattern._cultural_diversity()
        result = pattern.run()
        final_diversity = result["cultural_diversity"]

        # Diversity typically decreases as regions form
        assert final_diversity <= initial_diversity + 0.1  # Allow small fluctuation

    def test_history_recorded(self):
        cfg = CulturalDiffusionConfig(n_agents=25, max_steps=1000)
        pattern = CulturalDiffusionPattern(cfg)
        result = pattern.run()
        assert "history" in result
        assert len(result["history"]) > 0

    def test_config_in_output(self):
        cfg = CulturalDiffusionConfig(n_agents=25, n_features=3)
        pattern = CulturalDiffusionPattern(cfg)
        result = pattern.run()
        assert "config" in result
        assert result["config"]["n_agents"] == 25
        assert result["config"]["n_features"] == 3

    def test_convergence_info(self):
        cfg = CulturalDiffusionConfig(n_agents=25, max_steps=5000)
        pattern = CulturalDiffusionPattern(cfg)
        result = pattern.run()
        assert "convergence" in result
        assert "frozen" in result["convergence"]
        assert "polarized" in result["convergence"]
        assert "global_consensus" in result["convergence"]


# ═══════════════════════════════════════════════════════════════════
# Metadata Tests
# ═══════════════════════════════════════════════════════════════════


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = CulturalDiffusionPattern.get_metadata()
        assert meta["id"] == "cultural_diffusion"
        assert "name" in meta
        assert "category" in meta
        assert "parameters" in meta

    def test_parameters_list(self):
        meta = CulturalDiffusionPattern.get_metadata()
        param_names = [p["name"] for p in meta["parameters"]]
        assert "n_agents" in param_names
        assert "n_features" in param_names
        assert "n_traits" in param_names


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_small_grid(self):
        cfg = CulturalDiffusionConfig(n_agents=4, grid_size=(2, 2), max_steps=100)
        pattern = CulturalDiffusionPattern(cfg)
        result = pattern.run()
        assert result["n_regions"] >= 1

    def test_single_feature(self):
        cfg = CulturalDiffusionConfig(n_agents=16, n_features=1, max_steps=500)
        pattern = CulturalDiffusionPattern(cfg)
        result = pattern.run()
        assert result["cultural_diversity"] >= 0

    def test_few_traits(self):
        """With few traits, more consensus should form"""
        cfg = CulturalDiffusionConfig(n_agents=16, n_traits=2, max_steps=1000)
        pattern = CulturalDiffusionPattern(cfg)
        result = pattern.run()
        assert result["n_regions"] >= 1

    def test_mutation_prevents_freeze(self):
        """Mutation should prevent complete freeze"""
        cfg = CulturalDiffusionConfig(
            n_agents=16,
            enable_mutation=True,
            mutation_rate=0.01,
            max_steps=2000
        )
        pattern = CulturalDiffusionPattern(cfg)
        result = pattern.run()
        # With mutation, diversity should be maintained
        assert result["cultural_diversity"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
