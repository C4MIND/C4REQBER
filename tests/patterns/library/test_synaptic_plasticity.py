"""
Tests for synaptic_plasticity pattern module.
"""
import numpy as np
import pytest
import asyncio

from src.patterns.library.synaptic_plasticity import (
    PlasticityRule,
    SynapticPlasticityConfig,
    SynapticPlasticityPattern,
)


class TestEnums:
    def test_rule_values(self):
        assert PlasticityRule.STDP.value == "stdp"
        assert PlasticityRule.BCM.value == "bcm"
        assert PlasticityRule.OJA.value == "oja"
        assert PlasticityRule.CALCIUM.value == "calcium"


class TestConfig:
    def test_default_config(self):
        cfg = SynapticPlasticityConfig()
        assert cfg.rule == PlasticityRule.STDP
        assert cfg.A_plus == 0.01
        assert cfg.num_pre == 100
        assert cfg.num_post == 10

    def test_to_dict(self):
        cfg = SynapticPlasticityConfig()
        d = cfg.to_dict()
        assert d["rule"] == "stdp"
        assert "A_plus" in d


class TestInit:
    def test_pattern_init(self):
        pattern = SynapticPlasticityPattern()
        assert pattern.config is not None


class TestCanSimulate:
    def test_can_simulate_plasticity(self):
        pattern = SynapticPlasticityPattern()
        from src.patterns.core import Hypothesis
        h = Hypothesis(title="STDP learning", description="synaptic plasticity")
        assert pattern.can_simulate(h) is True

    def test_can_simulate_no_match(self):
        pattern = SynapticPlasticityPattern()
        from src.patterns.core import Hypothesis
        h = Hypothesis(title="weather forecast", description="")
        assert pattern.can_simulate(h) is False


class TestParseConfig:
    def test_parse_config(self):
        pattern = SynapticPlasticityPattern()
        cfg = pattern._parse_config({"A_plus": 0.02, "num_pre": 50})
        assert cfg.A_plus == 0.02
        assert cfg.num_pre == 50


class TestSTDP:
    @pytest.mark.asyncio
    async def test_stdp_simulation(self):
        pattern = SynapticPlasticityPattern()
        pattern.config = SynapticPlasticityConfig(
            rule=PlasticityRule.STDP,
            num_pre=20,
            num_post=5,
            simulation_time=100.0,
        )
        result = await pattern._stdp_simulation()
        assert "metrics" in result
        assert "final_weights" in result

    @pytest.mark.asyncio
    async def test_stdp_weight_change(self):
        pattern = SynapticPlasticityPattern()
        pattern.config = SynapticPlasticityConfig(
            rule=PlasticityRule.STDP,
            num_pre=20,
            num_post=5,
            simulation_time=100.0,
        )
        result = await pattern._stdp_simulation()
        assert "weight_change_percent" in result["metrics"]


class TestBCM:
    @pytest.mark.asyncio
    async def test_bcm_simulation(self):
        pattern = SynapticPlasticityPattern()
        pattern.config = SynapticPlasticityConfig(
            rule=PlasticityRule.BCM,
            num_pre=20,
            simulation_time=100.0,
        )
        result = await pattern._bcm_simulation()
        assert result["metrics"]["rule"] == "bcm"
        assert "final_threshold" in result["metrics"]


class TestOja:
    @pytest.mark.asyncio
    async def test_oja_simulation(self):
        pattern = SynapticPlasticityPattern()
        pattern.config = SynapticPlasticityConfig(
            rule=PlasticityRule.OJA,
            num_pre=20,
            simulation_time=100.0,
        )
        result = await pattern._oja_simulation()
        assert result["metrics"]["rule"] == "oja"
        assert "final_weight_norm" in result["metrics"]


class TestCalcium:
    @pytest.mark.asyncio
    async def test_calcium_simulation(self):
        pattern = SynapticPlasticityPattern()
        pattern.config = SynapticPlasticityConfig(
            rule=PlasticityRule.CALCIUM,
            num_pre=20,
            num_post=5,
            simulation_time=100.0,
        )
        result = await pattern._calcium_simulation()
        assert result["metrics"]["rule"] == "calcium"
        assert "mean_calcium" in result["metrics"]


class TestRun:
    @pytest.mark.asyncio
    async def test_run_stdp(self):
        pattern = SynapticPlasticityPattern()
        result = await pattern.run(
            hypothesis=None,
            config={"rule": "stdp", "num_pre": 20, "num_post": 5, "simulation_time": 100.0},
        )
        assert result.status.name == "COMPLETED"

    @pytest.mark.asyncio
    async def test_run_bcm(self):
        pattern = SynapticPlasticityPattern()
        result = await pattern.run(
            hypothesis=None,
            config={"rule": "bcm", "num_pre": 20, "simulation_time": 100.0},
        )
        assert result.status.name == "COMPLETED"


class TestEdgeCases:
    def test_confidence(self):
        pattern = SynapticPlasticityPattern()
        results = {"metrics": {"weight_change_percent": 10, "saturation_ratio": 0.1, "pre_rate_hz": 5, "stability": 0.05}}
        score = pattern._calculate_confidence(results)
        assert 0 <= score <= 0.95

    def test_estimate_resources(self):
        pattern = SynapticPlasticityPattern()
        from src.patterns.core import Hypothesis

        h = Hypothesis(title="test", description="test", parameters={"num_pre": 100, "num_post": 10, "simulation_time": 10000})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources

    def test_get_metadata(self):
        meta = SynapticPlasticityPattern.get_metadata()
        assert "id" in meta
        assert "parameters" in meta

    def test_weight_bounds(self):
        pattern = SynapticPlasticityPattern()
        pattern.config = SynapticPlasticityConfig(w_min=0.0, w_max=1.0)
        weights = np.array([[-0.1, 1.2]])
        clipped = np.clip(weights, pattern.config.w_min, pattern.config.w_max)
        assert np.all(clipped >= 0.0)
        assert np.all(clipped <= 1.0)
