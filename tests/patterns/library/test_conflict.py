"""
Tests for src/patterns/library/conflict.py (Conflict Pattern - Lanchester Models)

Covers:
- ConflictModel enum
- ConflictConfig dataclass
- ConflictPattern initialization
- _initialize() setup
- _lanchester_linear_derivatives()
- _lanchester_square_derivatives()
- _lanchester_mixed_derivatives()
- _salvo_step()
- _calculate_win_probability()
- _check_termination()
- run() simulation
- _format_output()
- get_metadata()
- Edge cases: equal forces, reinforcement, early termination
"""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.conflict import ConflictConfig, ConflictModel, ConflictPattern


# ═══════════════════════════════════════════════════════════════════
# Enums and Dataclasses
# ═══════════════════════════════════════════════════════════════════


class TestConflictModel:
    def test_enum_values(self):
        assert ConflictModel.LANCHESTER_LINEAR.value == "lanchester_linear"
        assert ConflictModel.LANCHESTER_SQUARE.value == "lanchester_square"
        assert ConflictModel.LANCHESTER_MIXED.value == "lanchester_mixed"
        assert ConflictModel.SALVO.value == "salvo"


class TestConflictConfig:
    def test_default_init(self):
        cfg = ConflictConfig()
        assert cfg.model == ConflictModel.LANCHESTER_SQUARE
        assert cfg.force_a_initial == 1000.0
        assert cfg.force_b_initial == 1000.0
        assert cfg.lethality_a == 0.05
        assert cfg.lethality_b == 0.05
        assert cfg.dt == 0.1
        assert cfg.max_time == 100.0

    def test_custom_init(self):
        cfg = ConflictConfig(
            model=ConflictModel.LANCHESTER_LINEAR,
            force_a_initial=2000.0,
            force_b_initial=1500.0,
            lethality_a=0.1,
        )
        assert cfg.model == ConflictModel.LANCHESTER_LINEAR
        assert cfg.force_a_initial == 2000.0
        assert cfg.force_b_initial == 1500.0
        assert cfg.lethality_a == 0.1


# ═══════════════════════════════════════════════════════════════════
# ConflictPattern Initialization
# ═══════════════════════════════════════════════════════════════════


class TestConflictPatternInit:
    def test_init(self):
        pattern = ConflictPattern()
        assert pattern is not None
        assert pattern.config is not None
        assert pattern.force_a == 1000.0
        assert pattern.force_b == 1000.0

    def test_pattern_id(self):
        assert ConflictPattern.PATTERN_ID == "conflict"
        assert ConflictPattern.PATTERN_VERSION == "6.0.0"


# ═══════════════════════════════════════════════════════════════════
# Initialize
# ═══════════════════════════════════════════════════════════════════


class TestInitialize:
    def test_initial_forces_set(self):
        cfg = ConflictConfig(force_a_initial=2000.0, force_b_initial=1500.0)
        pattern = ConflictPattern(cfg)
        assert pattern.force_a == 2000.0
        assert pattern.force_b == 1500.0

    def test_history_initialized(self):
        pattern = ConflictPattern()
        assert len(pattern.history_a) == 1
        assert len(pattern.history_b) == 1
        assert pattern.history_a[0] == 1000.0
        assert pattern.history_b[0] == 1000.0


# ═══════════════════════════════════════════════════════════════════
# Derivative Calculations
# ═══════════════════════════════════════════════════════════════════


class TestLanchesterLinearDerivatives:
    def test_linear_derivatives_negative(self):
        cfg = ConflictConfig(model=ConflictModel.LANCHESTER_LINEAR)
        pattern = ConflictPattern(cfg)
        d_a, d_b = pattern._lanchester_linear_derivatives()
        # Both derivatives should be negative (attrition)
        assert d_a < 0
        assert d_b < 0

    def test_linear_with_reinforcement(self):
        cfg = ConflictConfig(
            model=ConflictModel.LANCHESTER_LINEAR,
            reinforcement_rate_a=10.0,
            reinforcement_rate_b=5.0,
        )
        pattern = ConflictPattern(cfg)
        d_a, d_b = pattern._lanchester_linear_derivatives()
        # Reinforcement can make derivatives positive
        assert d_a > -pattern.config.aim_effectiveness_b * pattern.force_b


class TestLanchesterSquareDerivatives:
    def test_square_derivatives_negative(self):
        cfg = ConflictConfig(model=ConflictModel.LANCHESTER_SQUARE)
        pattern = ConflictPattern(cfg)
        d_a, d_b = pattern._lanchester_square_derivatives()
        # Both derivatives should be negative
        assert d_a < 0
        assert d_b < 0


class TestLanchesterMixedDerivatives:
    def test_mixed_derivatives_negative(self):
        cfg = ConflictConfig(model=ConflictModel.LANCHESTER_MIXED)
        pattern = ConflictPattern(cfg)
        d_a, d_b = pattern._lanchester_mixed_derivatives()
        # Both derivatives should be negative
        assert d_a < 0
        assert d_b < 0


# ═══════════════════════════════════════════════════════════════════
# Salvo Model
# ═══════════════════════════════════════════════════════════════════


class TestSalvoStep:
    def test_salvo_reduces_forces(self):
        cfg = ConflictConfig(
            model=ConflictModel.SALVO,
            force_a_initial=10.0,
            force_b_initial=10.0,
            offensive_firepower_a=3.0,
            offensive_firepower_b=3.0,
        )
        pattern = ConflictPattern(cfg)
        initial_a = pattern.force_a
        initial_b = pattern.force_b
        pattern._salvo_step()
        assert pattern.force_a <= initial_a
        assert pattern.force_b <= initial_b

    def test_salvo_casualties_recorded(self):
        cfg = ConflictConfig(model=ConflictModel.SALVO)
        pattern = ConflictPattern(cfg)
        initial_casualties = pattern.casualties_a
        pattern._salvo_step()
        assert pattern.casualties_a >= initial_casualties


# ═══════════════════════════════════════════════════════════════════
# Win Probability
# ═══════════════════════════════════════════════════════════════════


class TestCalculateWinProbability:
    def test_equal_forces(self):
        cfg = ConflictConfig(
            model=ConflictModel.LANCHESTER_SQUARE,
            force_a_initial=1000.0,
            force_b_initial=1000.0,
            lethality_a=0.05,
            lethality_b=0.05,
        )
        pattern = ConflictPattern(cfg)
        prob = pattern._calculate_win_probability()
        # Equal forces should give 0.5 (draw) or deterministic based on FAD
        assert prob in [0.0, 0.5, 1.0]

    def test_superior_force_a(self):
        cfg = ConflictConfig(
            model=ConflictModel.LANCHESTER_SQUARE,
            force_a_initial=2000.0,
            force_b_initial=1000.0,
            lethality_a=0.05,
            lethality_b=0.05,
        )
        pattern = ConflictPattern(cfg)
        prob = pattern._calculate_win_probability()
        # With square law, 2:1 advantage gives 4:1 fighting strength
        assert prob == 1.0

    def test_linear_law_winner(self):
        cfg = ConflictConfig(
            model=ConflictModel.LANCHESTER_LINEAR,
            force_a_initial=1000.0,
            force_b_initial=1000.0,
            aim_effectiveness_a=0.02,
            aim_effectiveness_b=0.01,
        )
        pattern = ConflictPattern(cfg)
        prob = pattern._calculate_win_probability()
        # Higher effectiveness for A should make A win
        assert prob == 1.0


# ═══════════════════════════════════════════════════════════════════
# Termination Check
# ═══════════════════════════════════════════════════════════════════


class TestCheckTermination:
    def test_termination_when_eliminated(self):
        cfg = ConflictConfig()
        pattern = ConflictPattern(cfg)
        pattern.force_a = 0
        assert pattern._check_termination() is True

    def test_no_termination_early(self):
        cfg = ConflictConfig()
        pattern = ConflictPattern(cfg)
        assert pattern._check_termination() is False

    def test_termination_casualty_threshold(self):
        cfg = ConflictConfig(max_casualties=0.5)
        pattern = ConflictPattern(cfg)
        pattern.casualties_a = 600.0  # > 50% of 1000
        assert pattern._check_termination() is True


# ═══════════════════════════════════════════════════════════════════
# Run Simulation
# ═══════════════════════════════════════════════════════════════════


class TestRun:
    def test_run_lanchester_square(self):
        cfg = ConflictConfig(model=ConflictModel.LANCHESTER_SQUARE, max_time=50.0)
        pattern = ConflictPattern(cfg)
        result = pattern.run()
        assert "model" in result
        assert "winner" in result
        assert "final_forces" in result
        assert "casualties" in result
        assert result["model"] == "lanchester_square"

    def test_run_lanchester_linear(self):
        cfg = ConflictConfig(model=ConflictModel.LANCHESTER_LINEAR, max_time=50.0)
        pattern = ConflictPattern(cfg)
        result = pattern.run()
        assert result["model"] == "lanchester_linear"
        assert "winner" in result

    def test_run_lanchester_mixed(self):
        cfg = ConflictConfig(model=ConflictModel.LANCHESTER_MIXED, max_time=50.0)
        pattern = ConflictPattern(cfg)
        result = pattern.run()
        assert result["model"] == "lanchester_mixed"

    def test_run_salvo(self):
        cfg = ConflictConfig(model=ConflictModel.SALVO, max_time=20.0)
        pattern = ConflictPattern(cfg)
        result = pattern.run()
        assert result["model"] == "salvo"

    def test_force_history_recorded(self):
        cfg = ConflictConfig(max_time=50.0)
        pattern = ConflictPattern(cfg)
        result = pattern.run()
        assert "force_history" in result
        assert "A" in result["force_history"]
        assert "B" in result["force_history"]
        assert len(result["force_history"]["A"]) > 0


# ═══════════════════════════════════════════════════════════════════
# Output Formatting
# ═══════════════════════════════════════════════════════════════════


class TestFormatOutput:
    def test_output_structure(self):
        cfg = ConflictConfig()
        pattern = ConflictPattern(cfg)
        pattern.run()
        result = pattern._format_output(0.5)
        assert "model" in result
        assert "winner" in result
        assert "final_forces" in result
        assert "casualties" in result
        assert "casualty_rates" in result
        assert "duration" in result
        assert "lanchester_metrics" in result
        assert "outcome_prediction" in result

    def test_casualty_rates_calculated(self):
        cfg = ConflictConfig(force_a_initial=1000.0, force_b_initial=1000.0)
        pattern = ConflictPattern(cfg)
        pattern.force_a = 500.0
        pattern.force_b = 600.0
        pattern.casualties_a = 500.0
        pattern.casualties_b = 400.0
        result = pattern._format_output(0.5)
        assert result["casualty_rates"]["A"] == 0.5
        assert result["casualty_rates"]["B"] == 0.4


# ═══════════════════════════════════════════════════════════════════
# get_metadata
# ═══════════════════════════════════════════════════════════════════


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = ConflictPattern.get_metadata()
        assert meta["id"] == "conflict"
        assert meta["name"] == "Conflict"
        assert "category" in meta
        assert "parameters" in meta


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_reinforcement_changes_outcome(self):
        cfg = ConflictConfig(
            force_a_initial=800.0,
            force_b_initial=1000.0,
            reinforcement_rate_a=20.0,
            reinforcement_rate_b=0.0,
            max_time=50.0,
        )
        pattern = ConflictPattern(cfg)
        result = pattern.run()
        # Reinforcement can help smaller force win
        assert "winner" in result

    def test_very_small_forces(self):
        cfg = ConflictConfig(
            force_a_initial=10.0,
            force_b_initial=10.0,
            max_time=50.0,
        )
        pattern = ConflictPattern(cfg)
        result = pattern.run()
        assert "winner" in result

    def test_very_high_lethality(self):
        cfg = ConflictConfig(
            lethality_a=1.0,
            lethality_b=1.0,
            max_time=10.0,
        )
        pattern = ConflictPattern(cfg)
        result = pattern.run()
        # High lethality should lead to quick battle
        assert result["duration"] < 10.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
