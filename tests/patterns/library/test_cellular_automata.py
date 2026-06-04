"""
Tests for src/patterns/library/cellular_automata.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.cellular_automata import (
    CellularAutomataPattern,
    CellularAutomataConfig,
)
from src.patterns.core import Hypothesis, SimulationStatus



class TestCellularAutomataConfig:
    def test_default_init(self):
        cfg = CellularAutomataConfig()
        assert cfg.model == "game_of_life"
        assert cfg.width == 100
        assert cfg.height == 100

    def test_custom_init(self):
        cfg = CellularAutomataConfig(model="rule_110", width=50, n_steps=50)
        assert cfg.model == "rule_110"
        assert cfg.width == 50


class TestCellularAutomataPatternInit:
    def test_init(self):
        pattern = CellularAutomataPattern()
        assert pattern is not None

    def test_parameters_defined(self):
        pattern = CellularAutomataPattern()
        param_names = [p.name for p in pattern.parameters]
        assert "model" in param_names
        assert "width" in param_names


class TestCanSimulate:
    def test_matches_gol(self):
        pattern = CellularAutomataPattern()
        h = Hypothesis(title="Game of Life", description="cellular automata")
        assert pattern.can_simulate(h) is True

    def test_matches_rule110(self):
        pattern = CellularAutomataPattern()
        h = Hypothesis(title="Rule 110", description="elementary automata")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = CellularAutomataPattern()
        h = Hypothesis(title="Stock market", description="trading")
        assert pattern.can_simulate(h) is False


class TestParseConfig:
    def test_default_parsing(self):
        pattern = CellularAutomataPattern()
        cfg = pattern._parse_config({})
        assert cfg.model == "game_of_life"

    def test_custom_parsing(self):
        pattern = CellularAutomataPattern()
        cfg = pattern._parse_config({"model": "rule_110", "width": 50})
        assert cfg.model == "rule_110"
        assert cfg.width == 50


@pytest.mark.asyncio
class TestSimulateGOL:
    async def test_simulation_completes(self):
        pattern = CellularAutomataPattern()
        pattern.config = CellularAutomataConfig(model="game_of_life", width=20, height=20, n_steps=10)
        result = await pattern._simulate_gol()
        assert "metrics" in result
        assert "logs" in result
        assert "final_grid" in result

    async def test_density_in_range(self):
        pattern = CellularAutomataPattern()
        pattern.config = CellularAutomataConfig(model="game_of_life", width=20, height=20, n_steps=10)
        result = await pattern._simulate_gol()
        assert 0 <= result["metrics"]["final_density"] <= 1

    async def test_alive_cells_count(self):
        pattern = CellularAutomataPattern()
        pattern.config = CellularAutomataConfig(model="game_of_life", width=20, height=20, n_steps=10)
        result = await pattern._simulate_gol()
        assert 0 <= result["metrics"]["alive_cells"] <= 400

    async def test_entropy_history(self):
        pattern = CellularAutomataPattern()
        pattern.config = CellularAutomataConfig(model="game_of_life", width=20, height=20, n_steps=10)
        result = await pattern._simulate_gol()
        assert len(result["entropy_history"]) == 10

    async def test_density_history(self):
        pattern = CellularAutomataPattern()
        pattern.config = CellularAutomataConfig(model="game_of_life", width=20, height=20, n_steps=10)
        result = await pattern._simulate_gol()
        assert len(result["density_history"]) == 10

    async def test_zero_density(self):
        pattern = CellularAutomataPattern()
        pattern.config = CellularAutomataConfig(model="game_of_life", width=20, height=20, n_steps=10, initial_density=0.0)
        result = await pattern._simulate_gol()
        assert result["metrics"]["final_density"] == 0.0


@pytest.mark.asyncio
class TestSimulateRule110:
    async def test_simulation_completes(self):
        pattern = CellularAutomataPattern()
        pattern.config = CellularAutomataConfig(model="rule_110", width=50, n_steps=50)
        result = await pattern._simulate_rule110()
        assert "metrics" in result
        assert "logs" in result
        assert "grid" in result

    async def test_grid_shape(self):
        pattern = CellularAutomataPattern()
        pattern.config = CellularAutomataConfig(model="rule_110", width=50, n_steps=50)
        result = await pattern._simulate_rule110()
        grid = np.array(result["grid"])
        assert grid.shape == (50, 50)

    async def test_ones_present(self):
        pattern = CellularAutomataPattern()
        pattern.config = CellularAutomataConfig(model="rule_110", width=50, n_steps=50)
        result = await pattern._simulate_rule110()
        assert result["metrics"]["ones_count"] > 0

    async def test_density_in_range(self):
        pattern = CellularAutomataPattern()
        pattern.config = CellularAutomataConfig(model="rule_110", width=50, n_steps=50)
        result = await pattern._simulate_rule110()
        assert 0 <= result["metrics"]["density"] <= 1


class TestCalculateConfidence:
    def test_high_confidence(self):
        pattern = CellularAutomataPattern()
        results = {"metrics": {"final_density": 0.2, "n_steps": 100, "alive_cells": 100}}
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5


@pytest.mark.asyncio
class TestRun:
    async def test_run_gol(self):
        pattern = CellularAutomataPattern()
        h = Hypothesis(title="Game of Life", description="cellular automata")
        config = {"model": "game_of_life", "width": 20, "height": 20, "n_steps": 10}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_rule110(self):
        pattern = CellularAutomataPattern()
        h = Hypothesis(title="Rule 110", description="elementary automata")
        config = {"model": "rule_110", "width": 50, "n_steps": 50}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = CellularAutomataPattern.get_metadata()
        assert meta["id"] == "cellular_automata"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
