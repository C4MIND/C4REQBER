"""
Tests for metapopulation pattern module.
"""

import asyncio

import numpy as np
import pytest

from src.patterns.library.metapopulation import (
    MetapopulationConfig,
    MetapopulationModel,
    MetapopulationPattern,
    Patch,
)


class TestEnums:
    def test_model_values(self):
        assert MetapopulationModel.LEVINS.value == "levins"
        assert MetapopulationModel.LEVINS_Hanski.value == "levins_hanski"
        assert MetapopulationModel.INCIDENCE_FUNCTION.value == "incidence_function"
        assert MetapopulationModel.SPATIAL.value == "spatial"


class TestPatch:
    def test_distance_to(self):
        p1 = Patch(0, 10.0, 0.0, 0.0)
        p2 = Patch(1, 10.0, 3.0, 4.0)
        assert p1.distance_to(p2) == 5.0


class TestConfig:
    def test_default_config(self):
        cfg = MetapopulationConfig()
        assert cfg.model == MetapopulationModel.LEVINS
        assert cfg.c == 0.1
        assert cfg.e == 0.05
        assert cfg.num_patches == 20

    def test_to_dict(self):
        cfg = MetapopulationConfig()
        d = cfg.to_dict()
        assert d["model"] == "levins"
        assert "c" in d
        assert "e" in d


class TestInit:
    def test_pattern_init(self):
        pattern = MetapopulationPattern()
        assert pattern.config is not None
        assert len(pattern.patches) == 0


class TestCanSimulate:
    def test_can_simulate_fragmentation(self):
        pattern = MetapopulationPattern()
        from src.patterns.core import Hypothesis

        h = Hypothesis(title="fragmentation effects", description="patch dynamics")
        assert pattern.can_simulate(h) is True

    def test_can_simulate_no_match(self):
        pattern = MetapopulationPattern()
        from src.patterns.core import Hypothesis

        h = Hypothesis(title="quantum mechanics", description="wave function")
        assert pattern.can_simulate(h) is False


class TestParseConfig:
    def test_parse_config(self):
        pattern = MetapopulationPattern()
        cfg = pattern._parse_config({"c": 0.2, "e": 0.1, "num_patches": 10})
        assert cfg.c == 0.2
        assert cfg.e == 0.1
        assert cfg.num_patches == 10


class TestLandscape:
    def test_generate_landscape(self):
        pattern = MetapopulationPattern()
        pattern.config = MetapopulationConfig(num_patches=10)
        pattern._generate_landscape()
        assert len(pattern.patches) == 10


class TestLevins:
    @pytest.mark.asyncio
    async def test_levins_simulation(self):
        pattern = MetapopulationPattern()
        pattern.config = MetapopulationConfig(
            model=MetapopulationModel.LEVINS,
            years=20,
            c=0.2,
            e=0.05,
        )
        pattern._generate_landscape()
        result = await pattern._levins_simulation()
        assert "metrics" in result
        assert "logs" in result
        assert "occupancy" in result
        assert result["metrics"]["model"] == "levins"

    @pytest.mark.asyncio
    async def test_levins_persistence(self):
        pattern = MetapopulationPattern()
        pattern.config = MetapopulationConfig(
            model=MetapopulationModel.LEVINS,
            years=50,
            c=0.2,
            e=0.05,
        )
        pattern._generate_landscape()
        result = await pattern._levins_simulation()
        assert "persistence" in result["metrics"]


class TestHanski:
    @pytest.mark.asyncio
    async def test_hanski_simulation(self):
        pattern = MetapopulationPattern()
        pattern.config = MetapopulationConfig(
            model=MetapopulationModel.LEVINS_Hanski,
            years=20,
            rescue_effect=True,
        )
        pattern._generate_landscape()
        result = await pattern._levins_hanski_simulation()
        assert result["metrics"]["model"] == "levins_hanski"
        assert result["metrics"]["rescue_effect"] is True


class TestIncidence:
    @pytest.mark.asyncio
    async def test_incidence_simulation(self):
        pattern = MetapopulationPattern()
        pattern.config = MetapopulationConfig(
            model=MetapopulationModel.INCIDENCE_FUNCTION,
            num_patches=10,
            years=20,
        )
        pattern._generate_landscape()
        result = await pattern._incidence_function_simulation()
        assert result["metrics"]["model"] == "incidence_function"
        assert "patch_occupancy" in result


class TestSpatial:
    @pytest.mark.asyncio
    async def test_spatial_simulation(self):
        pattern = MetapopulationPattern()
        pattern.config = MetapopulationConfig(
            model=MetapopulationModel.SPATIAL,
            num_patches=10,
            years=20,
        )
        pattern._generate_landscape()
        result = await pattern._spatial_simulation()
        assert result["metrics"]["model"] == "spatial"


class TestRun:
    @pytest.mark.asyncio
    async def test_run_levins(self):
        pattern = MetapopulationPattern()
        result = await pattern.run(
            hypothesis=None,
            config={"model": "levins", "years": 20, "num_patches": 10},
        )
        assert result.status.name == "COMPLETED"
        assert "metrics" in result.__dict__

    @pytest.mark.asyncio
    async def test_run_spatial(self):
        pattern = MetapopulationPattern()
        result = await pattern.run(
            hypothesis=None,
            config={"model": "spatial", "years": 20, "num_patches": 10},
        )
        assert result.status.name == "COMPLETED"


class TestEdgeCases:
    def test_confidence(self):
        pattern = MetapopulationPattern()
        results = {"metrics": {"final_occupancy": 0.5, "persistence": True, "c_e_ratio": 2.0}}
        score = pattern._calculate_confidence(results)
        assert 0 <= score <= 0.95

    def test_estimate_resources(self):
        pattern = MetapopulationPattern()
        from src.patterns.core import Hypothesis

        h = Hypothesis(
            title="test", description="test", parameters={"num_patches": 20, "years": 100}
        )
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources

    def test_get_metadata(self):
        meta = MetapopulationPattern.get_metadata()
        assert "id" in meta
        assert "parameters" in meta
