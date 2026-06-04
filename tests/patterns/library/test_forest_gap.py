"""Tests for forest_gap pattern module."""

import numpy as np
import pytest
import asyncio

from src.patterns.library.forest_gap import (
    ForestGapConfig,
    ForestGapPattern,
    GapState,
)
from src.patterns.core import Hypothesis



class TestGapState:
    def test_values(self):
        assert GapState.EMPTY.value == 0
        assert GapState.JUVENILE.value == 1
        assert GapState.MATURE.value == 2
        assert GapState.OLD_GROWTH.value == 3
        assert GapState.DISTURBED.value == 4


class TestForestGapConfig:
    def test_default_values(self):
        cfg = ForestGapConfig()
        assert cfg.grid_size == 50
        assert cfg.num_species == 3
        assert cfg.disturbance_rate == 0.01
        assert cfg.years == 500
        assert cfg.initial_cover == 0.7

    def test_to_dict(self):
        cfg = ForestGapConfig(grid_size=30, years=100)
        d = cfg.to_dict()
        assert d["grid_size"] == 30
        assert d["years"] == 100
        assert "mortality_rates" in d


class TestForestGapPattern:
    @pytest.fixture
    def pattern(self):
        return ForestGapPattern()

    @pytest.fixture
    def hypothesis(self):
        return Hypothesis(
            title="Forest gap dynamics",
            description="Simulate forest succession and disturbance regimes",
        )

    def test_init(self, pattern):
        assert pattern.config.grid_size == 50
        assert pattern.rng is not None
        assert pattern.grid is None

    def test_can_simulate_matching(self, pattern, hypothesis):
        assert pattern.can_simulate(hypothesis) is True

    def test_can_simulate_non_matching(self, pattern):
        h = Hypothesis(title="Quantum mechanics", description="Particle physics")
        assert pattern.can_simulate(h) is False

    def test_can_simulate_keywords(self, pattern):
        keywords = ["forest", "gap", "succession", "disturbance", "canopy"]
        for kw in keywords:
            h = Hypothesis(title=kw, description="test")
            assert pattern.can_simulate(h) is True

    def test_parse_config(self, pattern):
        pattern.config = pattern._parse_config({"grid_size": 30, "years": 100, "disturbance_rate": 0.05})
        assert pattern.config.grid_size == 30
        assert pattern.config.years == 100
        assert pattern.config.disturbance_rate == 0.05

    def test_initialize_grid(self, pattern):
        pattern.config = ForestGapConfig(grid_size=20, initial_cover=0.5)
        pattern._initialize_grid()
        assert pattern.grid.shape == (20, 20)
        assert pattern.species_grid.shape == (20, 20)
        assert pattern.age_grid.shape == (20, 20)
        cover = np.sum(pattern.grid > 0) / (20 * 20)
        assert 0.3 < cover < 0.7  # Approximate due to randomness

    def test_has_mature_neighbor(self, pattern):
        pattern.config = ForestGapConfig(grid_size=10)
        pattern._initialize_grid()
        # Force a mature neighbor
        pattern.grid[1, 0] = 2
        assert pattern._has_mature_neighbor(0, 0) is True
        pattern.grid[:, :] = 0
        assert pattern._has_mature_neighbor(0, 0) is False

    def test_choose_species(self, pattern):
        pattern.config = ForestGapConfig(grid_size=10, num_species=3)
        pattern._initialize_grid()
        species = pattern._choose_species(0, 0)
        assert 0 <= species < 3

    def test_apply_disturbance(self, pattern):
        pattern.config = ForestGapConfig(grid_size=10, disturbance_rate=1.0)
        pattern._initialize_grid()
        pattern._apply_disturbance()
        assert np.sum(pattern.grid == 0) > 0

    def test_apply_succession(self, pattern):
        pattern.config = ForestGapConfig(grid_size=10, recruitment_rate=1.0)
        pattern._initialize_grid()
        pattern.grid[:] = 0
        pattern.species_grid[:] = -1
        pattern._apply_succession()
        assert np.sum(pattern.grid > 0) > 0

    def test_calculate_metrics(self, pattern):
        pattern.config = ForestGapConfig(grid_size=10)
        pattern._initialize_grid()
        cover_hist = [0.5, 0.6, 0.7]
        species_hist = [2, 2, 3]
        gap_hist = [0.3, 0.2, 0.1]
        snapshots = [pattern.grid.copy()]
        metrics = pattern._calculate_metrics(cover_hist, species_hist, gap_hist, snapshots)
        assert "final_cover" in metrics
        assert "final_species_richness" in metrics
        assert "shannon_diversity" in metrics
        assert "stage_distribution" in metrics
        assert metrics["years_simulated"] == 500

    def test_count_clusters(self, pattern):
        binary = np.array([[1, 1, 0], [1, 0, 0], [0, 0, 1]])
        n = pattern._count_clusters(binary)
        assert n >= 1

    def test_calculate_confidence(self, pattern):
        results = {"metrics": {"final_cover": 0.5, "final_species_richness": 2, "shannon_diversity": 0.5, "cover_stability": 0.6}}
        score = pattern._calculate_confidence(results)
        assert 0 <= score <= 0.95

    def test_estimate_resources(self, pattern):
        h = Hypothesis(title="test", description="test")
        h.parameters = {"grid_size": 50, "years": 500}
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert resources["gpu_required"] is False

    @pytest.mark.asyncio
    async def test_run(self, pattern, hypothesis):
        result = await pattern.run(hypothesis, {"grid_size": 10, "years": 10, "record_interval": 5})
        assert result.status.value == "completed"
        assert result.metrics
        assert len(result.logs) > 0

    @pytest.mark.asyncio
    async def test_run_low_disturbance(self, pattern, hypothesis):
        result = await pattern.run(
            hypothesis, {"grid_size": 10, "years": 10, "disturbance_rate": 0.0}
        )
        assert result.status.value == "completed"

    def test_get_metadata(self):
        metadata = ForestGapPattern.get_metadata()
        assert metadata["id"] == "forest_gap"
        assert "parameters" in metadata
        assert len(metadata["references"]) > 0
