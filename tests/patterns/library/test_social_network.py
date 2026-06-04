"""
Tests for src/patterns/library/social_network.py (Social Network Pattern)

Covers:
- SocialNetworkPattern initialization
- can_simulate() keyword matching
- _create_small_world()
- _create_scale_free()
- _create_random()
- _calculate_clustering()
- _calculate_confidence()
- estimate_resources()
- run() async integration
- Edge cases: few nodes, different network types
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.social_network import SocialNetworkPattern
from src.patterns.core import Hypothesis, SimulationStatus



# ═══════════════════════════════════════════════════════════════════
# Initialization Tests
# ═══════════════════════════════════════════════════════════════════


class TestSocialNetworkPatternInit:
    def test_init(self):
        pattern = SocialNetworkPattern()
        assert pattern is not None

    def test_parameters_defined(self):
        pattern = SocialNetworkPattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0
        param_names = [p.name for p in pattern.parameters]
        assert "num_nodes" in param_names
        assert "network_type" in param_names
        assert "diffusion_model" in param_names
        assert "adoption_rate" in param_names


# ═══════════════════════════════════════════════════════════════════
# can_simulate Tests
# ═══════════════════════════════════════════════════════════════════


class TestCanSimulate:
    def test_matches_social_network(self):
        pattern = SocialNetworkPattern()
        h = Hypothesis(title="Social network analysis", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_diffusion(self):
        pattern = SocialNetworkPattern()
        h = Hypothesis(title="Information diffusion", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_viral(self):
        pattern = SocialNetworkPattern()
        h = Hypothesis(title="Viral marketing", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_cascade(self):
        pattern = SocialNetworkPattern()
        h = Hypothesis(title="Cascade effects", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_influence(self):
        pattern = SocialNetworkPattern()
        h = Hypothesis(title="Influence propagation", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_adoption(self):
        pattern = SocialNetworkPattern()
        h = Hypothesis(title="Technology adoption", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_network_effect(self):
        pattern = SocialNetworkPattern()
        h = Hypothesis(title="Network effects analysis", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_centrality(self):
        pattern = SocialNetworkPattern()
        h = Hypothesis(title="Centrality measures", description="test")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = SocialNetworkPattern()
        h = Hypothesis(title="Quantum mechanics", description="superposition")
        assert pattern.can_simulate(h) is False


# ═══════════════════════════════════════════════════════════════════
# Network Creation Tests
# ═══════════════════════════════════════════════════════════════════


class TestCreateNetworks:
    def test_small_world_shape(self):
        pattern = SocialNetworkPattern()
        adj = pattern._create_small_world(N=20, k=4, p=0.3)
        assert adj.shape == (20, 20)

    def test_small_world_symmetric(self):
        pattern = SocialNetworkPattern()
        adj = pattern._create_small_world(N=20, k=4, p=0.3)
        assert np.allclose(adj, adj.T)

    def test_small_world_diagonal_zero(self):
        pattern = SocialNetworkPattern()
        adj = pattern._create_small_world(N=20, k=4, p=0.3)
        assert np.all(np.diag(adj) == 0)

    def test_scale_free_shape(self):
        pattern = SocialNetworkPattern()
        adj = pattern._create_scale_free(N=20, m=2)
        assert adj.shape == (20, 20)

    def test_scale_free_symmetric(self):
        pattern = SocialNetworkPattern()
        adj = pattern._create_scale_free(N=20, m=2)
        assert np.allclose(adj, adj.T)

    def test_random_shape(self):
        pattern = SocialNetworkPattern()
        adj = pattern._create_random(N=20, p=0.1)
        assert adj.shape == (20, 20)

    def test_random_symmetric(self):
        pattern = SocialNetworkPattern()
        adj = pattern._create_random(N=20, p=0.1)
        assert np.allclose(adj, adj.T)


# ═══════════════════════════════════════════════════════════════════
# Clustering Tests
# ═══════════════════════════════════════════════════════════════════


class TestCalculateClustering:
    def test_clustering_range(self):
        pattern = SocialNetworkPattern()
        adj = pattern._create_small_world(N=20, k=4, p=0.0)  # High clustering
        cc = pattern._calculate_clustering(adj)
        assert 0 <= cc <= 1

    def test_clustering_complete_graph(self):
        pattern = SocialNetworkPattern()
        # Complete graph has clustering = 1
        adj = np.ones((10, 10)) - np.eye(10)
        cc = pattern._calculate_clustering(adj)
        assert cc == pytest.approx(1.0, abs=0.01)

    def test_clustering_no_triangles(self):
        pattern = SocialNetworkPattern()
        # Star graph has no triangles
        adj = np.zeros((10, 10))
        adj[0, 1:] = 1
        adj[1:, 0] = 1
        cc = pattern._calculate_clustering(adj)
        assert cc == pytest.approx(0.0, abs=0.01)


# ═══════════════════════════════════════════════════════════════════
# Core Methods Tests
# ═══════════════════════════════════════════════════════════════════


class TestCalculateConfidence:
    def test_good_network(self):
        pattern = SocialNetworkPattern()
        results = {"metrics": {"avg_degree": 5.0, "final_adoption_rate": 0.5}}
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5

    def test_high_degree(self):
        pattern = SocialNetworkPattern()
        results = {"metrics": {"avg_degree": 50.0, "final_adoption_rate": 0.5}}
        confidence = pattern._calculate_confidence(results)
        assert 0 <= confidence < 0.9


# ═══════════════════════════════════════════════════════════════════
# Resource Estimation Tests
# ═══════════════════════════════════════════════════════════════════


class TestEstimateResources:
    def test_default_params(self):
        pattern = SocialNetworkPattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert "gpu_required" in resources
        assert "estimated_time_seconds" in resources
        assert resources["gpu_required"] is False

    def test_more_nodes_more_memory(self):
        pattern = SocialNetworkPattern()
        h_small = Hypothesis(parameters={"num_nodes": 50})
        h_large = Hypothesis(parameters={"num_nodes": 500})

        resources_small = pattern.estimate_resources(h_small)
        resources_large = pattern.estimate_resources(h_large)

        assert resources_large["memory_gb"] > resources_small["memory_gb"]


# ═══════════════════════════════════════════════════════════════════
# Run Integration Tests
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRun:
    async def test_run_default(self):
        pattern = SocialNetworkPattern()
        h = Hypothesis(title="Social network", description="viral diffusion")
        result = await pattern.run(h, {"num_nodes": 50})
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("sn_")

    async def test_run_small_world(self):
        pattern = SocialNetworkPattern()
        h = Hypothesis(title="Social network", description="viral diffusion")
        result = await pattern.run(h, {"num_nodes": 50, "network_type": "small_world"})
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_scale_free(self):
        pattern = SocialNetworkPattern()
        h = Hypothesis(title="Social network", description="viral diffusion")
        result = await pattern.run(h, {"num_nodes": 50, "network_type": "scale_free"})
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_random(self):
        pattern = SocialNetworkPattern()
        h = Hypothesis(title="Social network", description="viral diffusion")
        result = await pattern.run(h, {"num_nodes": 50, "network_type": "random"})
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_independent_cascade(self):
        pattern = SocialNetworkPattern()
        h = Hypothesis(title="Social network", description="viral diffusion")
        result = await pattern.run(h, {
            "num_nodes": 50,
            "diffusion_model": "independent_cascade",
        })
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_linear_threshold(self):
        pattern = SocialNetworkPattern()
        h = Hypothesis(title="Social network", description="viral diffusion")
        result = await pattern.run(h, {
            "num_nodes": 50,
            "diffusion_model": "linear_threshold",
        })
        assert result.status == SimulationStatus.COMPLETED

    async def test_metrics_present(self):
        pattern = SocialNetworkPattern()
        h = Hypothesis(title="Social network", description="viral diffusion")
        result = await pattern.run(h, {"num_nodes": 50})
        assert "num_nodes" in result.metrics
        assert "num_edges" in result.metrics
        assert "avg_degree" in result.metrics

    async def test_logs_present(self):
        pattern = SocialNetworkPattern()
        h = Hypothesis(title="Social network", description="viral diffusion")
        result = await pattern.run(h, {"num_nodes": 50})
        assert len(result.logs) > 0


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestEdgeCases:
    async def test_very_few_nodes(self):
        pattern = SocialNetworkPattern()
        h = Hypothesis(title="Social network", description="viral diffusion")
        result = await pattern.run(h, {"num_nodes": 10})
        assert result.status == SimulationStatus.COMPLETED

    async def test_high_adoption_rate(self):
        pattern = SocialNetworkPattern()
        h = Hypothesis(title="Social network", description="viral diffusion")
        result = await pattern.run(h, {"num_nodes": 50, "adoption_rate": 1.0})
        assert result.status == SimulationStatus.COMPLETED

    async def test_low_adoption_rate(self):
        pattern = SocialNetworkPattern()
        h = Hypothesis(title="Social network", description="viral diffusion")
        result = await pattern.run(h, {"num_nodes": 50, "adoption_rate": 0.01})
        assert result.status == SimulationStatus.COMPLETED

    async def test_many_nodes(self):
        pattern = SocialNetworkPattern()
        h = Hypothesis(title="Social network", description="viral diffusion")
        result = await pattern.run(h, {"num_nodes": 200})
        assert result.status == SimulationStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
