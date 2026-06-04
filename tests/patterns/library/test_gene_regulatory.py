"""
Tests for gene_regulatory pattern module.
"""
import numpy as np
import pytest
import asyncio

from src.patterns.library.gene_regulatory import (
    GRNModel,
    GeneRegulatoryConfig,
    GeneRegulatoryPattern,
)


class TestEnums:
    def test_model_values(self):
        assert GRNModel.BOOLEAN.value == "boolean"
        assert GRNModel.ODE.value == "ode"
        assert GRNModel.HYBRID.value == "hybrid"
        assert GRNModel.THRESHOLD.value == "threshold"


class TestConfig:
    def test_default_config(self):
        cfg = GeneRegulatoryConfig()
        assert cfg.model == GRNModel.HYBRID
        assert cfg.num_genes == 5
        assert cfg.connectivity == 0.3

    def test_to_dict(self):
        cfg = GeneRegulatoryConfig()
        d = cfg.to_dict()
        assert d["model"] == "hybrid"
        assert "num_genes" in d


class TestInit:
    def test_pattern_init(self):
        pattern = GeneRegulatoryPattern()
        assert pattern.config is not None
        assert pattern.adjacency is None


class TestCanSimulate:
    def test_can_simulate_gene(self):
        pattern = GeneRegulatoryPattern()
        from src.patterns.core import Hypothesis
        h = Hypothesis(title="gene regulatory network", description="transcription")
        assert pattern.can_simulate(h) is True

    def test_can_simulate_no_match(self):
        pattern = GeneRegulatoryPattern()
        from src.patterns.core import Hypothesis
        h = Hypothesis(title="weather forecast", description="")
        assert pattern.can_simulate(h) is False


class TestParseConfig:
    def test_parse_config(self):
        pattern = GeneRegulatoryPattern()
        cfg = pattern._parse_config({"num_genes": 10, "connectivity": 0.5})
        assert cfg.num_genes == 10
        assert cfg.connectivity == 0.5


class TestNetwork:
    def test_generate_network(self):
        pattern = GeneRegulatoryPattern()
        pattern.config = GeneRegulatoryConfig(num_genes=5, connectivity=0.5)
        pattern._generate_network()
        assert pattern.adjacency is not None
        assert pattern.adjacency.shape == (5, 5)
        assert np.all(np.diag(pattern.adjacency) == 0)


class TestBoolean:
    @pytest.mark.asyncio
    async def test_boolean_simulation(self):
        pattern = GeneRegulatoryPattern()
        pattern.config = GeneRegulatoryConfig(
            model=GRNModel.BOOLEAN,
            num_genes=5,
            num_steps=50,
        )
        pattern._generate_network()
        result = await pattern._boolean_simulation()
        assert "metrics" in result
        assert "attractor" in result
        assert result["metrics"]["model"] == "boolean"

    def test_find_all_attractors(self):
        pattern = GeneRegulatoryPattern()
        pattern.config = GeneRegulatoryConfig(num_genes=3, connectivity=0.5)
        pattern._generate_network()
        attractors = pattern._find_all_attractors()
        assert isinstance(attractors, list)


class TestODE:
    @pytest.mark.asyncio
    async def test_ode_simulation(self):
        pattern = GeneRegulatoryPattern()
        pattern.config = GeneRegulatoryConfig(
            model=GRNModel.ODE,
            num_genes=5,
            t_max=10.0,
        )
        pattern._generate_network()
        result = await pattern._ode_simulation()
        assert result["metrics"]["model"] == "ode"
        assert "final_expression" in result["metrics"]


class TestHybrid:
    @pytest.mark.asyncio
    async def test_hybrid_simulation(self):
        pattern = GeneRegulatoryPattern()
        pattern.config = GeneRegulatoryConfig(
            model=GRNModel.HYBRID,
            num_genes=5,
            t_max=10.0,
        )
        pattern._generate_network()
        result = await pattern._hybrid_simulation()
        assert result["metrics"]["model"] == "hybrid"
        assert "total_switches" in result["metrics"]


class TestThreshold:
    @pytest.mark.asyncio
    async def test_threshold_simulation(self):
        pattern = GeneRegulatoryPattern()
        pattern.config = GeneRegulatoryConfig(
            model=GRNModel.THRESHOLD,
            num_genes=5,
            t_max=10.0,
        )
        pattern._generate_network()
        result = await pattern._threshold_simulation()
        assert result["metrics"]["model"] == "threshold"


class TestHill:
    def test_hill_activation(self):
        pattern = GeneRegulatoryPattern()
        pattern.config = GeneRegulatoryConfig(hill_n=2.0, theta=0.5)
        val = pattern._hill_activation(1.0)
        assert 0 < val <= 1.0

    def test_hill_repression(self):
        pattern = GeneRegulatoryPattern()
        pattern.config = GeneRegulatoryConfig(hill_n=2.0, theta=0.5)
        val = pattern._hill_repression(1.0)
        assert 0 <= val < 1.0


class TestRun:
    @pytest.mark.asyncio
    async def test_run_boolean(self):
        pattern = GeneRegulatoryPattern()
        result = await pattern.run(
            hypothesis=None,
            config={"model": "boolean", "num_genes": 5, "num_steps": 50},
        )
        assert result.status.name == "COMPLETED"

    @pytest.mark.asyncio
    async def test_run_ode(self):
        pattern = GeneRegulatoryPattern()
        result = await pattern.run(
            hypothesis=None,
            config={"model": "ode", "num_genes": 5, "t_max": 10.0},
        )
        assert result.status.name == "COMPLETED"


class TestEdgeCases:
    def test_confidence(self):
        pattern = GeneRegulatoryPattern()
        results = {"metrics": {"num_edges": 5, "attractor_type": "fixed_point"}}
        score = pattern._calculate_confidence(results)
        assert 0 <= score <= 0.95

    def test_estimate_resources(self):
        pattern = GeneRegulatoryPattern()
        from src.patterns.core import Hypothesis

        h = Hypothesis(title="test", description="test", parameters={"num_genes": 10})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources

    def test_get_metadata(self):
        meta = GeneRegulatoryPattern.get_metadata()
        assert "id" in meta
        assert "parameters" in meta

    def test_no_self_loops(self):
        pattern = GeneRegulatoryPattern()
        pattern.config = GeneRegulatoryConfig(num_genes=5)
        pattern._generate_network()
        assert np.all(np.diag(pattern.adjacency) == 0)
