"""
Tests for src/patterns/library/percolation.py

Covers:
- PercolationConfig default and custom initialization, __post_init__ validation
- UnionFind init, find, union, get_size
- PercolationPattern initialization
- can_simulate() keyword matching
- _parse_config()
- _find_clusters_union_find() 2D and 3D
- _find_clusters_dfs() 2D and 3D
- _check_percolation() 2D and 3D
- _analyze_results()
- _calculate_confidence()
- estimate_resources()
- run() integration (success and failure)
- Edge cases: empty grids, invalid inputs, boundary conditions, all occupied, no occupied
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.core import Hypothesis, SimulationStatus
from src.patterns.library.percolation import (
    PercolationConfig,
    PercolationPattern,
    UnionFind,
)


# ═══════════════════════════════════════════════════════════════════
# PercolationConfig
# ═══════════════════════════════════════════════════════════════════


class TestPercolationConfig:
    def test_default_init(self):
        cfg = PercolationConfig()
        assert cfg.lattice_size == 100
        assert cfg.dimension == 2
        assert cfg.n_realizations == 100
        assert cfg.p_min == 0.0
        assert cfg.p_max == 1.0
        assert cfg.n_p_values == 50
        assert cfg.algorithm == "union_find"
        assert cfg.random_seed is None

    def test_custom_init(self):
        cfg = PercolationConfig(
            lattice_size=50,
            dimension=3,
            n_realizations=200,
            p_min=0.2,
            p_max=0.8,
            n_p_values=20,
            algorithm="dfs",
            random_seed=42,
        )
        assert cfg.lattice_size == 50
        assert cfg.dimension == 3
        assert cfg.n_realizations == 200
        assert cfg.p_min == 0.2
        assert cfg.p_max == 0.8
        assert cfg.n_p_values == 20
        assert cfg.algorithm == "dfs"
        assert cfg.random_seed == 42

    def test_post_init_invalid_dimension(self):
        cfg = PercolationConfig(dimension=5)
        assert cfg.dimension == 2

    def test_post_init_invalid_algorithm(self):
        cfg = PercolationConfig(algorithm="invalid")
        assert cfg.algorithm == "union_find"

    def test_post_init_dimension_one(self):
        cfg = PercolationConfig(dimension=1)
        assert cfg.dimension == 2


# ═══════════════════════════════════════════════════════════════════
# UnionFind
# ═══════════════════════════════════════════════════════════════════


class TestUnionFind:
    def test_init(self):
        uf = UnionFind(5)
        assert uf.parent == [0, 1, 2, 3, 4]
        assert uf.rank == [0, 0, 0, 0, 0]
        assert uf.size == [1, 1, 1, 1, 1]

    def test_find_root(self):
        uf = UnionFind(5)
        assert uf.find(2) == 2

    def test_union_merges(self):
        uf = UnionFind(5)
        assert uf.union(0, 1) is True
        assert uf.find(0) == uf.find(1)

    def test_union_same_set(self):
        uf = UnionFind(5)
        uf.union(0, 1)
        assert uf.union(0, 1) is False

    def test_union_by_rank(self):
        uf = UnionFind(4)
        uf.union(0, 1)
        uf.union(2, 3)
        uf.union(0, 2)
        root = uf.find(0)
        assert uf.find(1) == root
        assert uf.find(2) == root
        assert uf.find(3) == root

    def test_get_size(self):
        uf = UnionFind(5)
        uf.union(0, 1)
        uf.union(1, 2)
        assert uf.get_size(0) == 3
        assert uf.get_size(1) == 3
        assert uf.get_size(2) == 3
        assert uf.get_size(3) == 1

    def test_path_compression(self):
        uf = UnionFind(5)
        uf.union(0, 1)
        uf.union(1, 2)
        uf.union(2, 3)
        uf.find(3)
        # After path compression, parent of 3 should point closer to root
        assert uf.find(3) == uf.find(0)

    def test_single_element(self):
        uf = UnionFind(1)
        assert uf.find(0) == 0
        assert uf.get_size(0) == 1


# ═══════════════════════════════════════════════════════════════════
# PercolationPattern Initialization
# ═══════════════════════════════════════════════════════════════════


class TestPercolationPatternInit:
    def test_init(self):
        pattern = PercolationPattern()
        assert pattern.config is None
        assert pattern.results_by_p == {}

    def test_parameters_defined(self):
        pattern = PercolationPattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0
        param_names = [p.name for p in pattern.parameters]
        assert "lattice_size" in param_names
        assert "dimension" in param_names
        assert "n_realizations" in param_names
        assert "p_min" in param_names
        assert "p_max" in param_names
        assert "n_p_values" in param_names


# ═══════════════════════════════════════════════════════════════════
# can_simulate
# ═══════════════════════════════════════════════════════════════════


class TestCanSimulate:
    def test_matches_percolation(self):
        pattern = PercolationPattern()
        h = Hypothesis(title="Percolation analysis", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_cluster(self):
        pattern = PercolationPattern()
        h = Hypothesis(title="Cluster connectivity", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_phase_transition(self):
        pattern = PercolationPattern()
        h = Hypothesis(title="Phase transition study", description="critical threshold")
        assert pattern.can_simulate(h) is True

    def test_matches_porous_media(self):
        pattern = PercolationPattern()
        h = Hypothesis(title="Porous media flow", description="test")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = PercolationPattern()
        h = Hypothesis(title="Neural network", description="deep learning")
        assert pattern.can_simulate(h) is False

    def test_empty_hypothesis(self):
        pattern = PercolationPattern()
        h = Hypothesis()
        assert pattern.can_simulate(h) is False


# ═══════════════════════════════════════════════════════════════════
# Config Parsing
# ═══════════════════════════════════════════════════════════════════


class TestParseConfig:
    def test_default_parsing(self):
        pattern = PercolationPattern()
        cfg = pattern._parse_config({})
        assert cfg.lattice_size == 100
        assert cfg.dimension == 2
        assert cfg.n_realizations == 100
        assert cfg.p_min == 0.0
        assert cfg.p_max == 1.0
        assert cfg.n_p_values == 50
        assert cfg.algorithm == "union_find"
        assert cfg.random_seed is None

    def test_custom_parsing(self):
        pattern = PercolationPattern()
        cfg = pattern._parse_config(
            {
                "lattice_size": 50,
                "dimension": 3,
                "n_realizations": 200,
                "p_min": 0.2,
                "p_max": 0.8,
                "n_p_values": 20,
                "algorithm": "dfs",
                "random_seed": 42,
            }
        )
        assert cfg.lattice_size == 50
        assert cfg.dimension == 3
        assert cfg.n_realizations == 200
        assert cfg.p_min == 0.2
        assert cfg.p_max == 0.8
        assert cfg.n_p_values == 20
        assert cfg.algorithm == "dfs"
        assert cfg.random_seed == 42


# ═══════════════════════════════════════════════════════════════════
# Cluster Finding — Union-Find
# ═══════════════════════════════════════════════════════════════════


class TestFindClustersUnionFind:
    def test_empty_grid_2d(self):
        pattern = PercolationPattern()
        occupied = np.zeros((3, 3), dtype=bool)
        clusters = pattern._find_clusters_union_find(occupied, 3, 2)
        assert clusters == {}

    def test_single_site_2d(self):
        pattern = PercolationPattern()
        occupied = np.zeros((3, 3), dtype=bool)
        occupied[1, 1] = True
        clusters = pattern._find_clusters_union_find(occupied, 3, 2)
        assert len(clusters) == 1
        assert {(1, 1)} in [set(c) for c in clusters.values()]

    def test_two_connected_sites_2d(self):
        pattern = PercolationPattern()
        occupied = np.zeros((3, 3), dtype=bool)
        occupied[0, 0] = True
        occupied[0, 1] = True
        clusters = pattern._find_clusters_union_find(occupied, 3, 2)
        assert len(clusters) == 1
        members = list(clusters.values())[0]
        assert len(members) == 2
        assert (0, 0) in members
        assert (0, 1) in members

    def test_two_separate_clusters_2d(self):
        pattern = PercolationPattern()
        occupied = np.zeros((3, 3), dtype=bool)
        occupied[0, 0] = True
        occupied[2, 2] = True
        clusters = pattern._find_clusters_union_find(occupied, 3, 2)
        assert len(clusters) == 2

    def test_all_occupied_2d(self):
        pattern = PercolationPattern()
        occupied = np.ones((3, 3), dtype=bool)
        clusters = pattern._find_clusters_union_find(occupied, 3, 2)
        assert len(clusters) == 1
        assert len(list(clusters.values())[0]) == 9

    def test_empty_grid_3d(self):
        pattern = PercolationPattern()
        occupied = np.zeros((2, 2, 2), dtype=bool)
        clusters = pattern._find_clusters_union_find(occupied, 2, 3)
        assert clusters == {}

    def test_single_site_3d(self):
        pattern = PercolationPattern()
        occupied = np.zeros((2, 2, 2), dtype=bool)
        occupied[1, 1, 1] = True
        clusters = pattern._find_clusters_union_find(occupied, 2, 3)
        assert len(clusters) == 1
        assert {(1, 1, 1)} in [set(c) for c in clusters.values()]

    def test_two_connected_sites_3d(self):
        pattern = PercolationPattern()
        occupied = np.zeros((2, 2, 2), dtype=bool)
        occupied[0, 0, 0] = True
        occupied[0, 0, 1] = True
        clusters = pattern._find_clusters_union_find(occupied, 2, 3)
        assert len(clusters) == 1
        members = list(clusters.values())[0]
        assert len(members) == 2

    def test_all_occupied_3d(self):
        pattern = PercolationPattern()
        occupied = np.ones((2, 2, 2), dtype=bool)
        clusters = pattern._find_clusters_union_find(occupied, 2, 3)
        assert len(clusters) == 1
        assert len(list(clusters.values())[0]) == 8


# ═══════════════════════════════════════════════════════════════════
# Cluster Finding — DFS
# ═══════════════════════════════════════════════════════════════════


class TestFindClustersDFS:
    def test_empty_grid_2d(self):
        pattern = PercolationPattern()
        occupied = np.zeros((3, 3), dtype=bool)
        clusters = pattern._find_clusters_dfs(occupied, 3, 2)
        assert clusters == {}

    def test_single_site_2d(self):
        pattern = PercolationPattern()
        occupied = np.zeros((3, 3), dtype=bool)
        occupied[1, 1] = True
        clusters = pattern._find_clusters_dfs(occupied, 3, 2)
        assert len(clusters) == 1
        assert {(1, 1)} in [set(c) for c in clusters.values()]

    def test_two_connected_sites_2d(self):
        pattern = PercolationPattern()
        occupied = np.zeros((3, 3), dtype=bool)
        occupied[0, 0] = True
        occupied[1, 0] = True
        clusters = pattern._find_clusters_dfs(occupied, 3, 2)
        assert len(clusters) == 1
        members = list(clusters.values())[0]
        assert len(members) == 2
        assert (0, 0) in members
        assert (1, 0) in members

    def test_two_separate_clusters_2d(self):
        pattern = PercolationPattern()
        occupied = np.zeros((3, 3), dtype=bool)
        occupied[0, 0] = True
        occupied[2, 2] = True
        clusters = pattern._find_clusters_dfs(occupied, 3, 2)
        assert len(clusters) == 2

    def test_all_occupied_2d(self):
        pattern = PercolationPattern()
        occupied = np.ones((3, 3), dtype=bool)
        clusters = pattern._find_clusters_dfs(occupied, 3, 2)
        assert len(clusters) == 1
        assert len(list(clusters.values())[0]) == 9

    def test_empty_grid_3d(self):
        pattern = PercolationPattern()
        occupied = np.zeros((2, 2, 2), dtype=bool)
        clusters = pattern._find_clusters_dfs(occupied, 2, 3)
        assert clusters == {}

    def test_single_site_3d(self):
        pattern = PercolationPattern()
        occupied = np.zeros((2, 2, 2), dtype=bool)
        occupied[1, 1, 1] = True
        clusters = pattern._find_clusters_dfs(occupied, 2, 3)
        assert len(clusters) == 1
        assert {(1, 1, 1)} in [set(c) for c in clusters.values()]

    def test_two_connected_sites_3d(self):
        pattern = PercolationPattern()
        occupied = np.zeros((2, 2, 2), dtype=bool)
        occupied[0, 0, 0] = True
        occupied[1, 0, 0] = True
        clusters = pattern._find_clusters_dfs(occupied, 2, 3)
        assert len(clusters) == 1
        members = list(clusters.values())[0]
        assert len(members) == 2

    def test_all_occupied_3d(self):
        pattern = PercolationPattern()
        occupied = np.ones((2, 2, 2), dtype=bool)
        clusters = pattern._find_clusters_dfs(occupied, 2, 3)
        assert len(clusters) == 1
        assert len(list(clusters.values())[0]) == 8


# ═══════════════════════════════════════════════════════════════════
# Percolation Check
# ═══════════════════════════════════════════════════════════════════


class TestCheckPercolation:
    def test_no_clusters_2d(self):
        pattern = PercolationPattern()
        assert pattern._check_percolation({}, 3, 2) is False

    def test_no_percolation_2d(self):
        pattern = PercolationPattern()
        clusters = {0: {(0, 0), (0, 1)}}
        assert pattern._check_percolation(clusters, 3, 2) is False

    def test_horizontal_span_2d(self):
        pattern = PercolationPattern()
        clusters = {0: {(1, 0), (1, 1), (1, 2)}}
        assert pattern._check_percolation(clusters, 3, 2) is True

    def test_vertical_span_2d(self):
        pattern = PercolationPattern()
        clusters = {0: {(0, 1), (1, 1), (2, 1)}}
        assert pattern._check_percolation(clusters, 3, 2) is True

    def test_no_percolation_3d(self):
        pattern = PercolationPattern()
        clusters = {0: {(0, 0, 0), (0, 0, 1)}}
        assert pattern._check_percolation(clusters, 3, 3) is False

    def test_x_span_3d(self):
        pattern = PercolationPattern()
        clusters = {0: {(0, 1, 1), (1, 1, 1), (2, 1, 1)}}
        assert pattern._check_percolation(clusters, 3, 3) is True

    def test_y_span_3d(self):
        pattern = PercolationPattern()
        clusters = {0: {(1, 0, 1), (1, 1, 1), (1, 2, 1)}}
        assert pattern._check_percolation(clusters, 3, 3) is True

    def test_z_span_3d(self):
        pattern = PercolationPattern()
        clusters = {0: {(1, 1, 0), (1, 1, 1), (1, 1, 2)}}
        assert pattern._check_percolation(clusters, 3, 3) is True

    def test_multiple_clusters_one_spans(self):
        pattern = PercolationPattern()
        clusters = {
            0: {(0, 0), (0, 1)},
            1: {(2, 0), (2, 1), (2, 2)},
        }
        assert pattern._check_percolation(clusters, 3, 2) is True


# ═══════════════════════════════════════════════════════════════════
# Results Analysis
# ═══════════════════════════════════════════════════════════════════


class TestAnalyzeResults:
    def test_empty_results(self):
        pattern = PercolationPattern()
        pattern.results_by_p = {}
        pattern.config = PercolationConfig()
        result = pattern._analyze_results()
        assert result["metrics"] == {}
        assert result["logs"] == ["No results"]

    def test_basic_analysis(self):
        pattern = PercolationPattern()
        pattern.config = PercolationConfig(lattice_size=10, dimension=2, n_realizations=10)
        pattern.results_by_p = {
            0.4: {
                "percolation_prob": 0.0,
                "percolation_std": 0.0,
                "max_cluster_size": 0.1,
                "avg_cluster_size": 5.0,
            },
            0.6: {
                "percolation_prob": 1.0,
                "percolation_std": 0.0,
                "max_cluster_size": 0.8,
                "avg_cluster_size": 50.0,
            },
        }
        result = pattern._analyze_results()
        assert "percolation_threshold" in result["metrics"]
        assert "threshold_error" in result["metrics"]
        assert "max_cluster_at_pc" in result["metrics"]
        assert result["metrics"]["lattice_size"] == 10
        assert result["metrics"]["dimension"] == 2
        assert result["metrics"]["n_realizations"] == 10
        assert len(result["logs"]) > 0

    def test_threshold_interpolation(self):
        pattern = PercolationPattern()
        pattern.config = PercolationConfig(lattice_size=10, dimension=2)
        pattern.results_by_p = {
            0.5: {
                "percolation_prob": 0.3,
                "percolation_std": 0.0,
                "max_cluster_size": 0.2,
                "avg_cluster_size": 5.0,
            },
            0.6: {
                "percolation_prob": 0.7,
                "percolation_std": 0.0,
                "max_cluster_size": 0.5,
                "avg_cluster_size": 20.0,
            },
        }
        result = pattern._analyze_results()
        threshold = result["metrics"]["percolation_threshold"]
        assert 0.5 <= threshold <= 0.6

    def test_no_crossing_fallback(self):
        pattern = PercolationPattern()
        pattern.config = PercolationConfig(lattice_size=10, dimension=2)
        pattern.results_by_p = {
            0.3: {
                "percolation_prob": 0.0,
                "percolation_std": 0.0,
                "max_cluster_size": 0.1,
                "avg_cluster_size": 5.0,
            },
            0.7: {
                "percolation_prob": 0.0,
                "percolation_std": 0.0,
                "max_cluster_size": 0.1,
                "avg_cluster_size": 5.0,
            },
        }
        result = pattern._analyze_results()
        threshold = result["metrics"]["percolation_threshold"]
        assert threshold in [0.3, 0.7]

    def test_3d_analysis(self):
        pattern = PercolationPattern()
        pattern.config = PercolationConfig(lattice_size=5, dimension=3)
        pattern.results_by_p = {
            0.2: {
                "percolation_prob": 0.0,
                "percolation_std": 0.0,
                "max_cluster_size": 0.05,
                "avg_cluster_size": 3.0,
            },
            0.4: {
                "percolation_prob": 1.0,
                "percolation_std": 0.0,
                "max_cluster_size": 0.6,
                "avg_cluster_size": 30.0,
            },
        }
        result = pattern._analyze_results()
        assert result["metrics"]["dimension"] == 3
        assert "percolation_threshold" in result["metrics"]


# ═══════════════════════════════════════════════════════════════════
# Confidence Calculation
# ═══════════════════════════════════════════════════════════════════


class TestCalculateConfidence:
    def test_high_confidence(self):
        pattern = PercolationPattern()
        results = {
            "metrics": {
                "n_realizations": 500,
                "threshold_error": 0.01,
                "lattice_size": 200,
            }
        }
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5

    def test_medium_confidence(self):
        pattern = PercolationPattern()
        results = {
            "metrics": {
                "n_realizations": 100,
                "threshold_error": 0.03,
                "lattice_size": 100,
            }
        }
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.0

    def test_low_confidence(self):
        pattern = PercolationPattern()
        results = {
            "metrics": {
                "n_realizations": 50,
                "threshold_error": 0.1,
                "lattice_size": 50,
            }
        }
        confidence = pattern._calculate_confidence(results)
        assert confidence >= 0.0
        assert confidence <= 0.85

    def test_empty_metrics(self):
        pattern = PercolationPattern()
        results = {"metrics": {}}
        confidence = pattern._calculate_confidence(results)
        assert confidence == 0.0


# ═══════════════════════════════════════════════════════════════════
# Resource Estimation
# ═══════════════════════════════════════════════════════════════════


class TestEstimateResources:
    def test_default_params(self):
        pattern = PercolationPattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert "gpu_required" in resources
        assert "estimated_time_seconds" in resources
        assert resources["gpu_required"] is False

    def test_custom_params(self):
        pattern = PercolationPattern()
        h = Hypothesis(parameters={"lattice_size": 200, "dimension": 3, "n_realizations": 500})
        resources = pattern.estimate_resources(h)
        assert resources["estimated_time_seconds"] > 0
        assert resources["memory_gb"] > 0

    def test_2d_vs_3d(self):
        pattern = PercolationPattern()
        h2d = Hypothesis(parameters={"lattice_size": 10, "dimension": 2, "n_realizations": 10})
        h3d = Hypothesis(parameters={"lattice_size": 10, "dimension": 3, "n_realizations": 10})
        r2d = pattern.estimate_resources(h2d)
        r3d = pattern.estimate_resources(h3d)
        assert r3d["estimated_time_seconds"] > r2d["estimated_time_seconds"]
        assert r3d["memory_gb"] > r2d["memory_gb"]


# ═══════════════════════════════════════════════════════════════════
# run() Integration
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRun:
    async def test_run_2d(self):
        pattern = PercolationPattern()
        h = Hypothesis(title="Percolation study", description="site percolation")
        config = {"lattice_size": 10, "n_realizations": 5, "n_p_values": 3, "dimension": 2}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("percolation_")
        assert "percolation_threshold" in result.metrics

    async def test_run_3d(self):
        pattern = PercolationPattern()
        h = Hypothesis(title="3D percolation", description="cubic lattice")
        config = {"lattice_size": 5, "n_realizations": 3, "n_p_values": 3, "dimension": 3}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert result.metrics["dimension"] == 3

    async def test_run_with_seed(self):
        pattern = PercolationPattern()
        h = Hypothesis(title="Percolation", description="test")
        config = {"lattice_size": 10, "n_realizations": 5, "n_p_values": 3, "random_seed": 42}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_dfs_algorithm(self):
        pattern = PercolationPattern()
        h = Hypothesis(title="Percolation", description="test")
        config = {"lattice_size": 10, "n_realizations": 5, "n_p_values": 3, "algorithm": "dfs"}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_logs_present(self):
        pattern = PercolationPattern()
        h = Hypothesis(title="Percolation", description="test")
        config = {"lattice_size": 10, "n_realizations": 5, "n_p_values": 3}
        result = await pattern.run(h, config)
        assert len(result.logs) > 0

    async def test_run_failure_handling(self):
        pattern = PercolationPattern()
        h = Hypothesis(title="Percolation", description="test")
        with patch.object(pattern, "_simulate", side_effect=ValueError("test error")):
            result = await pattern.run(
                h, {"lattice_size": 10, "n_realizations": 5, "n_p_values": 3}
            )
            assert result.status == SimulationStatus.FAILED
            assert "test error" in result.error_message

    async def test_run_with_validation_level(self):
        pattern = PercolationPattern()
        h = Hypothesis(title="Percolation", description="test")
        config = {"lattice_size": 10, "n_realizations": 5, "n_p_values": 3}
        result = await pattern.run(h, config)
        from src.patterns.core import ValidationLevel

        assert result.validation_level == ValidationLevel.MONTE_CARLO


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_union_find_zero_elements(self):
        uf = UnionFind(0)
        assert uf.parent == []
        assert uf.rank == []
        assert uf.size == []

    def test_percolation_config_negative_values(self):
        cfg = PercolationConfig(lattice_size=-5, p_min=-0.5, p_max=1.5)
        assert cfg.lattice_size == -5
        assert cfg.p_min == -0.5
        assert cfg.p_max == 1.5

    def test_check_percolation_boundary_single_row(self):
        pattern = PercolationPattern()
        clusters = {0: {(0, 0), (0, 1), (0, 2)}}
        assert pattern._check_percolation(clusters, 3, 2) is True

    def test_check_percolation_boundary_single_col(self):
        pattern = PercolationPattern()
        clusters = {0: {(0, 0), (1, 0), (2, 0)}}
        assert pattern._check_percolation(clusters, 3, 2) is True

    def test_cluster_with_diagonal_not_connected(self):
        pattern = PercolationPattern()
        occupied = np.zeros((3, 3), dtype=bool)
        occupied[0, 0] = True
        occupied[1, 1] = True
        clusters = pattern._find_clusters_union_find(occupied, 3, 2)
        assert len(clusters) == 2

    def test_lattice_size_one_2d(self):
        pattern = PercolationPattern()
        occupied = np.ones((1, 1), dtype=bool)
        clusters = pattern._find_clusters_union_find(occupied, 1, 2)
        assert len(clusters) == 1
        assert pattern._check_percolation(clusters, 1, 2) is True

    def test_lattice_size_one_3d(self):
        pattern = PercolationPattern()
        occupied = np.ones((1, 1, 1), dtype=bool)
        clusters = pattern._find_clusters_union_find(occupied, 1, 3)
        assert len(clusters) == 1
        assert pattern._check_percolation(clusters, 1, 3) is True

    def test_very_small_p_values(self):
        pattern = PercolationPattern()
        pattern.config = PercolationConfig(lattice_size=10, n_realizations=2, n_p_values=2)
        pattern.results_by_p = {
            0.0: {
                "percolation_prob": 0.0,
                "percolation_std": 0.0,
                "max_cluster_size": 0.0,
                "avg_cluster_size": 0.0,
            },
            1.0: {
                "percolation_prob": 1.0,
                "percolation_std": 0.0,
                "max_cluster_size": 1.0,
                "avg_cluster_size": 100.0,
            },
        }
        result = pattern._analyze_results()
        assert result["metrics"]["percolation_threshold"] is not None

    def test_run_minimal_lattice(self):
        import asyncio

        pattern = PercolationPattern()
        h = Hypothesis(title="Percolation", description="test")
        config = {"lattice_size": 2, "n_realizations": 2, "n_p_values": 2}
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(pattern.run(h, config))
        finally:
            loop.close()
        assert result.status == SimulationStatus.COMPLETED

    def test_run_single_p_value(self):
        import asyncio

        pattern = PercolationPattern()
        h = Hypothesis(title="Percolation", description="test")
        config = {"lattice_size": 5, "n_realizations": 2, "n_p_values": 1}
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(pattern.run(h, config))
        finally:
            loop.close()
        assert result.status == SimulationStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
