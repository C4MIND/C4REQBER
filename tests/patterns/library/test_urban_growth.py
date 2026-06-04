"""
Tests for urban_growth pattern module.
"""
import numpy as np
import pytest

from src.patterns.library.urban_growth import UrbanGrowthConfig, UrbanGrowthPattern



class TestConfig:
    def test_default_config(self):
        cfg = UrbanGrowthConfig()
        assert cfg.width == 100
        assert cfg.height == 100
        assert cfg.n_steps == 50
        assert cfg.n_agents == 1000

    def test_custom_config(self):
        cfg = UrbanGrowthConfig(width=50, height=50, n_steps=20)
        assert cfg.width == 50
        assert cfg.height == 50
        assert cfg.n_steps == 20


class TestInit:
    def test_pattern_init_default(self):
        pattern = UrbanGrowthPattern()
        assert pattern.config is not None
        assert pattern.grid is not None
        assert pattern.grid.shape == (100, 100)

    def test_pattern_init_custom(self):
        cfg = UrbanGrowthConfig(width=50, height=50)
        pattern = UrbanGrowthPattern(cfg)
        assert pattern.grid.shape == (50, 50)


class TestRoads:
    def test_roads_created(self):
        pattern = UrbanGrowthPattern()
        road_cells = np.sum(pattern.grid == 2)
        assert road_cells > 0

    def test_road_count(self):
        cfg = UrbanGrowthConfig(width=50, height=50, n_roads=5)
        pattern = UrbanGrowthPattern(cfg)
        road_cells = np.sum(pattern.grid == 2)
        assert road_cells > 0


class TestAgents:
    def test_agents_created(self):
        pattern = UrbanGrowthPattern()
        assert len(pattern.agents) > 0

    def test_agent_types(self):
        pattern = UrbanGrowthPattern()
        types = [a["type"] for a in pattern.agents]
        assert "resident" in types or "business" in types


class TestSuitability:
    def test_suitability_urban_zero(self):
        pattern = UrbanGrowthPattern()
        # Find an urban cell
        urban_cells = np.where(pattern.grid == 1)
        if len(urban_cells[0]) > 0:
            y, x = urban_cells[0][0], urban_cells[1][0]
            suit = pattern._calculate_suitability(y, x)
            assert suit == 0.0

    def test_suitability_empty_positive(self):
        pattern = UrbanGrowthPattern()
        # Find an empty cell
        empty_cells = np.where(pattern.grid == 0)
        if len(empty_cells[0]) > 0:
            y, x = empty_cells[0][0], empty_cells[1][0]
            suit = pattern._calculate_suitability(y, x)
            assert suit >= 0.0


class TestCAGrowth:
    def test_spontaneous_growth(self):
        pattern = UrbanGrowthPattern()
        urban_before = np.sum(pattern.grid == 1)
        pattern._ca_spontaneous_growth()
        urban_after = np.sum(pattern.grid == 1)
        assert urban_after >= urban_before

    def test_diffusion(self):
        pattern = UrbanGrowthPattern()
        urban_before = np.sum(pattern.grid == 1)
        pattern._ca_diffusion()
        urban_after = np.sum(pattern.grid == 1)
        assert urban_after >= urban_before


class TestLandUse:
    def test_land_use_transition(self):
        pattern = UrbanGrowthPattern()
        pattern._land_use_transition()
        assert pattern.land_use is not None


class TestPatches:
    def test_count_patches(self):
        pattern = UrbanGrowthPattern()
        n_patches = pattern._count_patches()
        assert isinstance(n_patches, int)
        assert n_patches >= 0


class TestRun:
    def test_short_simulation(self):
        cfg = UrbanGrowthConfig(width=40, height=40, n_steps=10)
        pattern = UrbanGrowthPattern(cfg)
        result = pattern.run()
        assert "statistics" in result
        assert result["statistics"]["final_urban"] >= result["statistics"]["initial_urban"]

    def test_metadata(self):
        meta = UrbanGrowthPattern.get_metadata()
        assert meta["id"] == "urban_growth"
        assert "parameters" in meta


class TestEdgeCases:
    def test_zero_steps(self):
        cfg = UrbanGrowthConfig(width=20, height=20, n_steps=0)
        pattern = UrbanGrowthPattern(cfg)
        result = pattern.run()
        assert result["statistics"]["urban_growth"] == 0

    def test_high_diffusion(self):
        cfg = UrbanGrowthConfig(width=30, height=30, n_steps=5, diffusion_coefficient=5.0)
        pattern = UrbanGrowthPattern(cfg)
        result = pattern.run()
        assert result["statistics"]["final_urban"] > result["statistics"]["initial_urban"]

    def test_seed_location(self):
        cfg = UrbanGrowthConfig(width=30, height=30, seed_location=(15, 15))
        pattern = UrbanGrowthPattern(cfg)
        assert pattern.grid is not None
