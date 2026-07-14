"""
Tests for src/patterns/library/migration.py (Migration Pattern)

Covers:
- MigrationModel enum values
- MigrationConfig dataclass
- MigrationPattern initialization
- _calculate_distances()
- _gravity_flows()
- _radiation_flows()
- _calculate_gini()
- run() simulation
- get_metadata()
- Edge cases: single region, zero migration
"""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.migration import (
    MigrationConfig,
    MigrationModel,
    MigrationPattern,
)


# ═══════════════════════════════════════════════════════════════════
# Enum Tests
# ═══════════════════════════════════════════════════════════════════


class TestMigrationModel:
    def test_gravity_value(self):
        assert MigrationModel.GRAVITY.value == "gravity"

    def test_radiation_value(self):
        assert MigrationModel.RADIATION.value == "radiation"

    def test_io_value(self):
        assert MigrationModel.INTERVENING_OPPORTUNITY.value == "io"


# ═══════════════════════════════════════════════════════════════════
# Config Tests
# ═══════════════════════════════════════════════════════════════════


class TestMigrationConfig:
    def test_default_init(self):
        cfg = MigrationConfig()
        assert cfg.model == MigrationModel.GRAVITY
        assert cfg.n_regions == 10
        assert cfg.alpha == 1.0
        assert cfg.beta == 1.0
        assert cfg.gamma == 2.0
        assert cfg.n_steps == 20

    def test_custom_init(self):
        cfg = MigrationConfig(
            model=MigrationModel.RADIATION,
            n_regions=5,
            gamma=1.5,
            n_steps=10,
        )
        assert cfg.model == MigrationModel.RADIATION
        assert cfg.n_regions == 5
        assert cfg.gamma == 1.5
        assert cfg.n_steps == 10


# ═══════════════════════════════════════════════════════════════════
# Initialization Tests
# ═══════════════════════════════════════════════════════════════════


class TestMigrationPatternInit:
    def test_init_default(self):
        pattern = MigrationPattern()
        assert pattern is not None
        assert pattern.config.n_regions == 10
        assert pattern.population is not None

    def test_init_with_config(self):
        cfg = MigrationConfig(n_regions=5)
        pattern = MigrationPattern(cfg)
        assert pattern.config.n_regions == 5

    def test_class_constants(self):
        assert MigrationPattern.PATTERN_ID == "migration"
        assert MigrationPattern.PATTERN_VERSION == "6.0.0"


# ═══════════════════════════════════════════════════════════════════
# Distance Matrix Tests
# ═══════════════════════════════════════════════════════════════════


class TestCalculateDistances:
    def test_distance_matrix_shape(self):
        pattern = MigrationPattern(MigrationConfig(n_regions=5))
        coords = np.array([[0, 0], [3, 4], [0, 5], [5, 0], [5, 5]])
        dist = pattern._calculate_distances(coords)
        assert dist.shape == (5, 5)

    def test_distance_diagonal_one(self):
        pattern = MigrationPattern(MigrationConfig(n_regions=3))
        coords = np.array([[0, 0], [3, 4], [0, 5]])
        dist = pattern._calculate_distances(coords)
        assert np.all(np.diag(dist) == 1)  # Avoids division by zero

    def test_distance_symmetric(self):
        pattern = MigrationPattern(MigrationConfig(n_regions=3))
        coords = np.array([[0, 0], [3, 4], [0, 5]])
        dist = pattern._calculate_distances(coords)
        assert np.allclose(dist, dist.T)


# ═══════════════════════════════════════════════════════════════════
# Gravity Model Tests
# ═══════════════════════════════════════════════════════════════════


class TestGravityFlows:
    def test_gravity_flows_shape(self):
        cfg = MigrationConfig(n_regions=5, n_steps=1)
        pattern = MigrationPattern(cfg)
        flows = pattern._gravity_flows()
        assert flows.shape == (5, 5)

    def test_gravity_diagonal_zero(self):
        cfg = MigrationConfig(n_regions=5, n_steps=1)
        pattern = MigrationPattern(cfg)
        flows = pattern._gravity_flows()
        assert np.all(np.diag(flows) == 0)

    def test_gravity_flows_non_negative(self):
        cfg = MigrationConfig(n_regions=5, n_steps=1)
        pattern = MigrationPattern(cfg)
        flows = pattern._gravity_flows()
        assert np.all(flows >= 0)


# ═══════════════════════════════════════════════════════════════════
# Radiation Model Tests
# ═══════════════════════════════════════════════════════════════════


class TestRadiationFlows:
    def test_radiation_flows_shape(self):
        cfg = MigrationConfig(model=MigrationModel.RADIATION, n_regions=5, n_steps=1)
        pattern = MigrationPattern(cfg)
        flows = pattern._radiation_flows()
        assert flows.shape == (5, 5)

    def test_radiation_diagonal_zero(self):
        cfg = MigrationConfig(model=MigrationModel.RADIATION, n_regions=5, n_steps=1)
        pattern = MigrationPattern(cfg)
        flows = pattern._radiation_flows()
        assert np.all(np.diag(flows) == 0)

    def test_radiation_flows_non_negative(self):
        cfg = MigrationConfig(model=MigrationModel.RADIATION, n_regions=5, n_steps=1)
        pattern = MigrationPattern(cfg)
        flows = pattern._radiation_flows()
        assert np.all(flows >= 0)


# ═══════════════════════════════════════════════════════════════════
# Gini Coefficient Tests
# ═══════════════════════════════════════════════════════════════════


class TestCalculateGini:
    def test_gini_perfect_equality(self):
        pattern = MigrationPattern()
        x = np.ones(10)
        gini = pattern._calculate_gini(x)
        assert gini == pytest.approx(0.0, abs=1e-10)

    def test_gini_inequality(self):
        pattern = MigrationPattern()
        x = np.array([1, 1, 1, 1, 100])
        gini = pattern._calculate_gini(x)
        assert gini > 0.5  # High inequality

    def test_gini_range(self):
        pattern = MigrationPattern()
        x = np.random.random(10) + 1
        gini = pattern._calculate_gini(x)
        assert 0 <= gini <= 1


# ═══════════════════════════════════════════════════════════════════
# Run Tests
# ═══════════════════════════════════════════════════════════════════


class TestRun:
    def test_run_gravity(self):
        cfg = MigrationConfig(model=MigrationModel.GRAVITY, n_regions=5, n_steps=5)
        pattern = MigrationPattern(cfg)
        result = pattern.run()
        assert result is not None
        assert "final_population" in result
        assert "statistics" in result

    def test_run_radiation(self):
        cfg = MigrationConfig(model=MigrationModel.RADIATION, n_regions=5, n_steps=5)
        pattern = MigrationPattern(cfg)
        result = pattern.run()
        assert result is not None
        assert "final_population" in result

    def test_statistics_structure(self):
        cfg = MigrationConfig(n_regions=5, n_steps=5)
        pattern = MigrationPattern(cfg)
        result = pattern.run()
        stats = result["statistics"]
        assert "total_migration_volume" in stats
        assert "connectivity" in stats
        assert "population_gini" in stats

    def test_region_data(self):
        cfg = MigrationConfig(n_regions=5, n_steps=5)
        pattern = MigrationPattern(cfg)
        result = pattern.run()
        assert "region_data" in result
        assert len(result["region_data"]) == 5

    def test_net_migration_sum(self):
        cfg = MigrationConfig(n_regions=5, n_steps=5)
        pattern = MigrationPattern(cfg)
        result = pattern.run()
        # Sum of net migration should be close to 0 (conservation)
        net_sum = np.sum(result["statistics"]["total_population_change"])
        assert abs(net_sum) < 10  # Small numerical error allowed


# ═══════════════════════════════════════════════════════════════════
# Metadata Tests
# ═══════════════════════════════════════════════════════════════════


class TestMetadata:
    def test_metadata_structure(self):
        meta = MigrationPattern.get_metadata()
        assert meta["id"] == "migration"
        assert meta["version"] == "6.0.0"
        assert meta["name"] == "Migration"
        assert "Demography" in meta["domain"]

    def test_metadata_parameters(self):
        meta = MigrationPattern.get_metadata()
        param_names = [p["name"] for p in meta["parameters"]]
        assert "model" in param_names
        assert "n_regions" in param_names
        assert "gamma" in param_names


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_single_region(self):
        cfg = MigrationConfig(n_regions=1, n_steps=1)
        pattern = MigrationPattern(cfg)
        result = pattern.run()
        assert "final_population" in result

    def test_two_regions(self):
        cfg = MigrationConfig(n_regions=2, n_steps=5)
        pattern = MigrationPattern(cfg)
        result = pattern.run()
        assert len(result["final_population"]) == 2

    def test_zero_migration_rate(self):
        cfg = MigrationConfig(n_regions=5, n_steps=5, migration_rate=0.0)
        pattern = MigrationPattern(cfg)
        result = pattern.run()
        # No migration should happen
        assert result["statistics"]["total_migration_volume"] == 0

    def test_high_gamma(self):
        cfg = MigrationConfig(n_regions=5, n_steps=5, gamma=5.0)
        pattern = MigrationPattern(cfg)
        result = pattern.run()
        assert "final_population" in result

    def test_low_gamma(self):
        cfg = MigrationConfig(n_regions=5, n_steps=5, gamma=0.5)
        pattern = MigrationPattern(cfg)
        result = pattern.run()
        assert "final_population" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
