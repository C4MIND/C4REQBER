"""
Tests for src/patterns/library/reaction_diffusion.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.reaction_diffusion import (
    ReactionDiffusionPattern,
    ReactionDiffusionConfig,
)
from src.patterns.core import Hypothesis, SimulationStatus



class TestReactionDiffusionConfig:
    def test_default_init(self):
        cfg = ReactionDiffusionConfig()
        assert cfg.model == "gray_scott"
        assert cfg.nx == 128
        assert cfg.Du == 0.16

    def test_custom_init(self):
        cfg = ReactionDiffusionConfig(model="turing", nx=64, F=0.04)
        assert cfg.model == "turing"
        assert cfg.nx == 64


class TestReactionDiffusionPatternInit:
    def test_init(self):
        pattern = ReactionDiffusionPattern()
        assert pattern is not None

    def test_parameters_defined(self):
        pattern = ReactionDiffusionPattern()
        param_names = [p.name for p in pattern.parameters]
        assert "model" in param_names
        assert "F" in param_names


class TestCanSimulate:
    def test_matches_gray_scott(self):
        pattern = ReactionDiffusionPattern()
        h = Hypothesis(title="Gray-Scott model", description="pattern formation")
        assert pattern.can_simulate(h) is True

    def test_matches_turing(self):
        pattern = ReactionDiffusionPattern()
        h = Hypothesis(title="Turing pattern", description="morphogenesis")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = ReactionDiffusionPattern()
        h = Hypothesis(title="Stock market", description="trading")
        assert pattern.can_simulate(h) is False


class TestParseConfig:
    def test_default_parsing(self):
        pattern = ReactionDiffusionPattern()
        cfg = pattern._parse_config({})
        assert cfg.model == "gray_scott"

    def test_custom_parsing(self):
        pattern = ReactionDiffusionPattern()
        cfg = pattern._parse_config({"model": "turing", "nx": 64, "F": 0.04})
        assert cfg.model == "turing"
        assert cfg.nx == 64


@pytest.mark.asyncio
class TestSimulateGrayScott:
    async def test_simulation_completes(self):
        pattern = ReactionDiffusionPattern()
        pattern.config = ReactionDiffusionConfig(model="gray_scott", nx=32, n_steps=1000)
        result = await pattern._simulate_gray_scott()
        assert "metrics" in result
        assert "logs" in result
        assert "V_final" in result

    async def test_pattern_classified(self):
        pattern = ReactionDiffusionPattern()
        pattern.config = ReactionDiffusionConfig(model="gray_scott", nx=32, n_steps=1000)
        result = await pattern._simulate_gray_scott()
        assert result["metrics"]["pattern_type"] in ["homogeneous", "spots", "stripes", "waves", "chaotic"]

    async def test_final_v_in_range(self):
        pattern = ReactionDiffusionPattern()
        pattern.config = ReactionDiffusionConfig(model="gray_scott", nx=32, n_steps=1000)
        result = await pattern._simulate_gray_scott()
        assert 0 <= result["metrics"]["final_V_mean"] <= 1


@pytest.mark.asyncio
class TestSimulateTuring:
    async def test_simulation_completes(self):
        pattern = ReactionDiffusionPattern()
        pattern.config = ReactionDiffusionConfig(model="turing", nx=32, n_steps=1000)
        result = await pattern._simulate_turing()
        assert "metrics" in result
        assert "logs" in result


class TestCalculateConfidence:
    def test_high_confidence(self):
        pattern = ReactionDiffusionPattern()
        results = {"metrics": {"V_variance": 0.01, "F": 0.035, "pattern_type": "spots", "n_steps": 5000}}
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5


@pytest.mark.asyncio
class TestRun:
    async def test_run_gray_scott(self):
        pattern = ReactionDiffusionPattern()
        h = Hypothesis(title="Gray-Scott", description="pattern formation")
        config = {"model": "gray_scott", "nx": 32, "n_steps": 1000}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_turing(self):
        pattern = ReactionDiffusionPattern()
        h = Hypothesis(title="Turing", description="morphogenesis")
        config = {"model": "turing", "nx": 32, "n_steps": 1000}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = ReactionDiffusionPattern.get_metadata()
        assert meta["id"] == "reaction_diffusion"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
