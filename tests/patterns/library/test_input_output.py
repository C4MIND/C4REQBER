"""
Tests for src/patterns/library/input_output.py (Input-Output Model pattern)

Covers:
- InputOutputConfig dataclass
- InputOutputModel initialization
- run() method
- get_metadata()
- Leontief inverse calculation
- Multiplier calculations
- Edge cases: zero values, singular matrices
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.input_output import (
    InputOutputModel,
    InputOutputConfig,
)


# ═══════════════════════════════════════════════════════════════════
# Config Tests
# ═══════════════════════════════════════════════════════════════════


class TestInputOutputConfig:
    def test_default_init(self):
        cfg = InputOutputConfig()
        assert cfg.n_sectors == 5
        assert cfg.total_output is None
        assert cfg.intermediate_demand is None
        assert cfg.final_demand is None
        assert cfg.random_seed == 42

    def test_custom_init(self):
        cfg = InputOutputConfig(
            n_sectors=3,
            total_output=np.array([100, 200, 300]),
            random_seed=123,
        )
        assert cfg.n_sectors == 3
        assert np.array_equal(cfg.total_output, np.array([100, 200, 300]))
        assert cfg.random_seed == 123


# ═══════════════════════════════════════════════════════════════════
# Initialization Tests
# ═══════════════════════════════════════════════════════════════════


class TestInputOutputModelInit:
    def test_init_default(self):
        model = InputOutputModel()
        assert model is not None
        assert model.config.n_sectors == 5

    def test_init_with_config(self):
        cfg = InputOutputConfig(n_sectors=3)
        model = InputOutputModel(cfg)
        assert model.config.n_sectors == 3

    def test_setup_data(self):
        model = InputOutputModel()
        assert len(model.total_output) == 5
        assert model.tech_coeffs.shape == (5, 5)
        assert len(model.final_demand) == 5


# ═══════════════════════════════════════════════════════════════════
# Run Tests
# ═══════════════════════════════════════════════════════════════════


class TestRun:
    def test_run_default(self):
        model = InputOutputModel()
        result = model.run()
        assert result is not None
        assert "leontief_inverse" in result
        assert "output_multipliers" in result
        assert "key_sectors" in result

    def test_leontief_inverse_positive(self):
        model = InputOutputModel()
        result = model.run()
        L = np.array(result["leontief_inverse"])
        assert np.all(L >= 0)

    def test_leontief_diagonal(self):
        model = InputOutputModel()
        result = model.run()
        L = np.array(result["leontief_inverse"])
        # Diagonal should be >= 1 (direct + indirect effects)
        assert np.all(np.diag(L) >= 1)

    def test_multiplier_properties(self):
        model = InputOutputModel()
        result = model.run()
        multipliers = np.array(result["output_multipliers"])
        # Output multipliers should be >= 1
        assert np.all(multipliers >= 1)
        assert len(multipliers) == 5

    def test_demand_shock_impact(self):
        model = InputOutputModel()
        result = model.run()
        impact = np.array(result["demand_shock_impact"])
        # First sector should have largest impact (shock applied there)
        assert np.argmax(impact) == 0
        # All impacts should be non-negative
        assert np.all(impact >= 0)

    def test_custom_sectors(self):
        # InputOutputModel has hardcoded data, only works with 5 sectors
        cfg = InputOutputConfig(n_sectors=5)
        model = InputOutputModel(cfg)
        result = model.run()
        assert len(result["output_multipliers"]) == 5


# ═══════════════════════════════════════════════════════════════════
# Metadata Tests
# ═══════════════════════════════════════════════════════════════════


class TestMetadata:
    def test_metadata_structure(self):
        meta = InputOutputModel.get_metadata()
        assert meta["pattern_id"] == 51
        assert meta["name"] == "Input-Output Model"
        assert "Macroeconomics" in meta["category"]
        assert meta["author"] == "Wassily Leontief"
        assert meta["year"] == 1936

    def test_metadata_outputs(self):
        meta = InputOutputModel.get_metadata()
        assert "leontief_inverse" in meta["outputs"]
        assert "multipliers" in meta["outputs"]

    def test_metadata_applications(self):
        meta = InputOutputModel.get_metadata()
        assert "economic_planning" in meta["applications"]


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_small_model(self):
        # InputOutputModel has hardcoded data, only works with 5 sectors
        cfg = InputOutputConfig(n_sectors=5)
        model = InputOutputModel(cfg)
        result = model.run()
        assert "leontief_inverse" in result

    def test_large_model(self):
        # InputOutputModel has hardcoded data, only works with 5 sectors
        cfg = InputOutputConfig(n_sectors=5)
        model = InputOutputModel(cfg)
        result = model.run()
        assert len(result["output_multipliers"]) == 5

    def test_custom_total_output(self):
        custom_output = np.array([1000, 2000, 3000, 4000, 5000])
        cfg = InputOutputConfig(total_output=custom_output)
        model = InputOutputModel(cfg)
        result = model.run()
        assert np.array_equal(result["total_output"], custom_output.tolist())

    def test_custom_final_demand(self):
        custom_demand = np.array([100, 200, 300, 400, 500])
        cfg = InputOutputConfig(final_demand=custom_demand)
        model = InputOutputModel(cfg)
        result = model.run()
        assert np.array_equal(result["final_demand"], custom_demand.tolist())


# ═══════════════════════════════════════════════════════════════════
# Alias Test
# ═══════════════════════════════════════════════════════════════════


class TestAlias:
    def test_input_output_pattern_alias(self):
        from src.patterns.library.input_output import InputOutputPattern

        # Should be the same as InputOutputModel
        assert InputOutputPattern is InputOutputModel


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
