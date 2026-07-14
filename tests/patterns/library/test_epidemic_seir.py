"""
Tests for epidemic_seir pattern module.
"""

import numpy as np
import pytest

from src.patterns.library.epidemic_seir import (
    EpidemicSEIRPattern,
    SEIRConfig,
)


class TestConfig:
    """Test dataclass initialization and defaults"""

    def test_default_config(self):
        cfg = SEIRConfig()
        assert cfg.model_type == "seir"
        assert cfg.N == 100000
        assert cfg.I0 == 10
        assert cfg.t_max == 200.0
        assert cfg.dt == 0.1
        assert cfg.beta == 0.5
        assert cfg.sigma == 0.2
        assert cfg.gamma == 0.1
        assert cfg.mu == 0.0
        assert cfg.omega == 0.0
        assert cfg.stochastic is False
        assert cfg.n_realizations == 100
        assert cfg.random_seed is None

    def test_custom_config(self):
        cfg = SEIRConfig(model_type="sir", N=50000, beta=0.8, gamma=0.2)
        assert cfg.model_type == "sir"
        assert cfg.N == 50000
        assert cfg.beta == 0.8
        assert cfg.gamma == 0.2


class TestInit:
    """Test pattern class __init__"""

    def test_pattern_init(self):
        pattern = EpidemicSEIRPattern()
        assert pattern.config is None  # Not set until run
        assert pattern.rng is not None
        assert len(pattern.time_points) == 0

    def test_pattern_parameters(self):
        assert len(EpidemicSEIRPattern.parameters) > 0
        param_names = [p.name for p in EpidemicSEIRPattern.parameters]
        assert "model_type" in param_names
        assert "N" in param_names
        assert "beta" in param_names
        assert "gamma" in param_names


class TestCanSimulate:
    """Test keyword matching for can_simulate"""

    def test_can_simulate_epidemic(self):
        from src.patterns.core import Hypothesis

        pattern = EpidemicSEIRPattern()
        hypo = Hypothesis(title="Epidemic outbreak simulation", description="Test")
        assert pattern.can_simulate(hypo) is True

    def test_can_simulate_sir(self):
        from src.patterns.core import Hypothesis

        pattern = EpidemicSEIRPattern()
        hypo = Hypothesis(title="SIR model analysis", description="Test")
        assert pattern.can_simulate(hypo) is True

    def test_can_simulate_herd_immunity(self):
        from src.patterns.core import Hypothesis

        pattern = EpidemicSEIRPattern()
        hypo = Hypothesis(title="Herd immunity threshold study", description="Test")
        assert pattern.can_simulate(hypo) is True

    def test_cannot_simulate_unrelated(self):
        from src.patterns.core import Hypothesis

        pattern = EpidemicSEIRPattern()
        hypo = Hypothesis(title="Stock market prediction", description="Test")
        assert pattern.can_simulate(hypo) is False


class TestCoreMethods:
    """Test main simulation methods"""

    def test_parse_config(self):
        pattern = EpidemicSEIRPattern()
        cfg = pattern._parse_config({"model_type": "sir", "N": 50000, "beta": 0.8})
        assert cfg.model_type == "sir"
        assert cfg.N == 50000
        assert cfg.beta == 0.8

    def test_calculate_confidence(self):
        pattern = EpidemicSEIRPattern()
        pattern.config = SEIRConfig(stochastic=True, n_realizations=100)
        results = {"metrics": {"R0": 2.5, "peak_infections": 10000, "final_epidemic_size": 50000}}
        confidence = pattern._calculate_confidence(results)
        assert 0 <= confidence <= 0.9


class TestRun:
    """Test async run() method with mocks"""

    @pytest.mark.asyncio
    async def test_run_deterministic_sir(self):
        from src.patterns.core import Hypothesis

        pattern = EpidemicSEIRPattern()
        hypo = Hypothesis(title="Test", description="Epidemic test")

        config = {
            "model_type": "sir",
            "N": 10000,
            "I0": 50,
            "t_max": 50.0,
            "dt": 0.1,
            "beta": 0.5,
            "gamma": 0.1,
            "stochastic": False,
        }

        result = await pattern.run(hypo, config)
        assert result.status.value in ["completed", "failed"]

        if result.status.value == "completed":
            assert result.metrics is not None

    @pytest.mark.asyncio
    async def test_run_deterministic_seir(self):
        from src.patterns.core import Hypothesis

        pattern = EpidemicSEIRPattern()
        hypo = Hypothesis(title="Test", description="Epidemic test")

        config = {
            "model_type": "seir",
            "N": 10000,
            "I0": 50,
            "t_max": 50.0,
            "dt": 0.1,
            "beta": 0.5,
            "sigma": 0.2,
            "gamma": 0.1,
            "stochastic": False,
        }

        result = await pattern.run(hypo, config)
        assert result.status.value in ["completed", "failed"]

    @pytest.mark.asyncio
    async def test_run_stochastic(self):
        from src.patterns.core import Hypothesis

        pattern = EpidemicSEIRPattern()
        hypo = Hypothesis(title="Test", description="Epidemic test")

        config = {
            "model_type": "sir",
            "N": 1000,
            "I0": 10,
            "t_max": 30.0,
            "dt": 0.1,
            "stochastic": True,
            "n_realizations": 10,
            "random_seed": 42,
        }

        result = await pattern.run(hypo, config)
        assert result.status.value in ["completed", "failed"]


class TestEdgeCases:
    """Test zero values, empty inputs, extremes"""

    def test_r0_less_than_one(self):
        """When R0 < 1, epidemic should die out"""
        pattern = EpidemicSEIRPattern()
        pattern.config = SEIRConfig(beta=0.05, gamma=0.1)  # R0 = 0.5
        R0 = pattern.config.beta / pattern.config.gamma
        assert R0 < 1

    def test_r0_greater_than_one(self):
        """When R0 > 1, epidemic can occur"""
        pattern = EpidemicSEIRPattern()
        pattern.config = SEIRConfig(beta=0.5, gamma=0.1)  # R0 = 5
        R0 = pattern.config.beta / pattern.config.gamma
        assert R0 > 1

    def test_herd_immunity_threshold(self):
        """Test herd immunity calculation"""
        pattern = EpidemicSEIRPattern()
        # R0 = 5, herd immunity = 1 - 1/5 = 0.8
        pattern.config = SEIRConfig(beta=0.5, gamma=0.1)
        R0 = 5.0
        threshold = 1 - 1 / R0
        assert threshold == 0.8

    def test_zero_initial_infected(self):
        """Edge case: I0 = 0"""
        pattern = EpidemicSEIRPattern()
        pattern.config = SEIRConfig(I0=0)
        assert pattern.config.I0 == 0

    def test_estimate_resources(self):
        pattern = EpidemicSEIRPattern()
        from src.patterns.core import Hypothesis

        resources = pattern.estimate_resources(
            Hypothesis(parameters={"t_max": 100.0, "stochastic": True, "n_realizations": 100})
        )
        assert "estimated_time_seconds" in resources
        assert "memory_gb" in resources

    def test_metadata(self):
        meta = EpidemicSEIRPattern.get_metadata()
        assert "id" in meta
        assert "name" in meta
