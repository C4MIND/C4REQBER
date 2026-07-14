"""
Tests for src/patterns/library/game_theory.py (Game Theory pattern)

Covers:
- GameTheoryPattern initialization
- can_simulate() keyword matching
- _prisoners_dilemma() simulation
- _battle_of_sexes() simulation
- _evolutionary_game() simulation
- _calculate_confidence()
- estimate_resources()
- run() async integration
- Edge cases: few rounds, many players
"""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.core import Hypothesis, SimulationStatus
from src.patterns.library.game_theory import GameTheoryPattern


# ═══════════════════════════════════════════════════════════════════
# Initialization Tests
# ═══════════════════════════════════════════════════════════════════


class TestGameTheoryPatternInit:
    def test_init(self):
        pattern = GameTheoryPattern()
        assert pattern is not None

    def test_parameters_defined(self):
        pattern = GameTheoryPattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0
        param_names = [p.name for p in pattern.parameters]
        assert "game_type" in param_names
        assert "num_rounds" in param_names
        assert "num_players" in param_names


# ═══════════════════════════════════════════════════════════════════
# can_simulate Tests
# ═══════════════════════════════════════════════════════════════════


class TestCanSimulate:
    def test_matches_game_theory(self):
        pattern = GameTheoryPattern()
        h = Hypothesis(title="Game theory analysis", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_nash(self):
        pattern = GameTheoryPattern()
        h = Hypothesis(title="Nash equilibrium", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_equilibrium(self):
        pattern = GameTheoryPattern()
        h = Hypothesis(title="Strategic equilibrium", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_prisoners_dilemma(self):
        pattern = GameTheoryPattern()
        h = Hypothesis(title="Prisoner's dilemma", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_battle_of_sexes(self):
        pattern = GameTheoryPattern()
        h = Hypothesis(title="Battle of sexes", description="coordination game")
        assert pattern.can_simulate(h) is True

    def test_matches_coordination(self):
        pattern = GameTheoryPattern()
        h = Hypothesis(title="Coordination game", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_hawk_dove(self):
        pattern = GameTheoryPattern()
        h = Hypothesis(title="Hawk-dove game", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_strategy(self):
        pattern = GameTheoryPattern()
        h = Hypothesis(title="Dominant strategy", description="payoff analysis")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = GameTheoryPattern()
        h = Hypothesis(title="Fluid dynamics", description="navier stokes")
        assert pattern.can_simulate(h) is False


# ═══════════════════════════════════════════════════════════════════
# Core Methods Tests
# ═══════════════════════════════════════════════════════════════════


class TestCalculateConfidence:
    def test_with_nash_equilibrium(self):
        pattern = GameTheoryPattern()
        results = {"metrics": {"nash_equilibrium": ("defect", "defect")}}
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5

    def test_with_equilibrium_type(self):
        pattern = GameTheoryPattern()
        results = {"metrics": {"equilibrium_type": "mixed"}}
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.4

    def test_empty_metrics(self):
        pattern = GameTheoryPattern()
        results = {"metrics": {}}
        confidence = pattern._calculate_confidence(results)
        assert 0.0 <= confidence <= 0.9


# ═══════════════════════════════════════════════════════════════════
# Resource Estimation Tests
# ═══════════════════════════════════════════════════════════════════


class TestEstimateResources:
    def test_default_params(self):
        pattern = GameTheoryPattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert "gpu_required" in resources
        assert "estimated_time_seconds" in resources
        assert resources["gpu_required"] is False

    def test_many_players(self):
        pattern = GameTheoryPattern()
        h = Hypothesis(parameters={"num_players": 1000})
        resources = pattern.estimate_resources(h)
        assert resources["estimated_time_seconds"] > 0


# ═══════════════════════════════════════════════════════════════════
# Run Integration Tests
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRun:
    async def test_run_default(self):
        pattern = GameTheoryPattern()
        h = Hypothesis(title="Game theory", description="nash equilibrium")
        result = await pattern.run(h, {"num_rounds": 50})
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("gt_")

    async def test_run_prisoners_dilemma(self):
        pattern = GameTheoryPattern()
        h = Hypothesis(title="Game theory", description="nash equilibrium")
        result = await pattern.run(h, {"game_type": "prisoners_dilemma", "num_rounds": 50})
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_battle_of_sexes(self):
        pattern = GameTheoryPattern()
        h = Hypothesis(title="Game theory", description="nash equilibrium")
        result = await pattern.run(h, {"game_type": "battle_of_sexes", "num_rounds": 50})
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_coordination(self):
        pattern = GameTheoryPattern()
        h = Hypothesis(title="Game theory", description="nash equilibrium")
        result = await pattern.run(h, {"game_type": "coordination", "num_rounds": 50})
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_hawk_dove(self):
        pattern = GameTheoryPattern()
        h = Hypothesis(title="Game theory", description="nash equilibrium")
        result = await pattern.run(h, {"game_type": "hawk_dove", "num_rounds": 50})
        assert result.status == SimulationStatus.COMPLETED

    async def test_metrics_present_prisoners(self):
        pattern = GameTheoryPattern()
        h = Hypothesis(title="Game theory", description="nash equilibrium")
        result = await pattern.run(h, {"game_type": "prisoners_dilemma", "num_rounds": 50})
        assert result.status == SimulationStatus.COMPLETED
        assert "nash_equilibrium_payoff" in result.metrics

    async def test_logs_present(self):
        pattern = GameTheoryPattern()
        h = Hypothesis(title="Game theory", description="nash equilibrium")
        result = await pattern.run(h, {"num_rounds": 50})
        assert len(result.logs) > 0


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestEdgeCases:
    async def test_very_few_rounds(self):
        pattern = GameTheoryPattern()
        h = Hypothesis(title="Game theory", description="nash equilibrium")
        result = await pattern.run(h, {"num_rounds": 10})
        assert result.status == SimulationStatus.COMPLETED

    async def test_many_rounds(self):
        pattern = GameTheoryPattern()
        h = Hypothesis(title="Game theory", description="nash equilibrium")
        result = await pattern.run(h, {"num_rounds": 1000})
        assert result.status == SimulationStatus.COMPLETED

    async def test_few_players(self):
        pattern = GameTheoryPattern()
        h = Hypothesis(title="Game theory", description="nash equilibrium")
        result = await pattern.run(h, {"game_type": "hawk_dove", "num_players": 2})
        assert result.status == SimulationStatus.COMPLETED

    async def test_many_players(self):
        pattern = GameTheoryPattern()
        h = Hypothesis(title="Game theory", description="nash equilibrium")
        result = await pattern.run(h, {"game_type": "hawk_dove", "num_players": 500})
        assert result.status == SimulationStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
