"""Tests for fisheries pattern module."""

import asyncio

import numpy as np
import pytest

from src.patterns.core import Hypothesis
from src.patterns.library.fisheries import (
    FisheriesConfig,
    FisheriesPattern,
    ProductionModel,
    RecruitmentModel,
)


class TestRecruitmentModel:
    def test_values(self):
        assert RecruitmentModel.BEVERTON_HOLT.value == "beverton_holt"
        assert RecruitmentModel.RICKER.value == "ricker"
        assert RecruitmentModel.LOGISTIC.value == "logistic"


class TestProductionModel:
    def test_values(self):
        assert ProductionModel.SCHAFFER.value == "schaefer"
        assert ProductionModel.FOX.value == "fox"
        assert ProductionModel.THOMPSON_BELL.value == "thompson_bell"


class TestFisheriesConfig:
    def test_default_values(self):
        cfg = FisheriesConfig()
        assert cfg.recruitment_model == RecruitmentModel.BEVERTON_HOLT
        assert cfg.production_model == ProductionModel.SCHAFFER
        assert cfg.K == 10000.0
        assert cfg.B0 == 8000.0
        assert cfg.years == 50

    def test_to_dict(self):
        cfg = FisheriesConfig(r_max=0.5, K=5000.0)
        d = cfg.to_dict()
        assert d["r_max"] == 0.5
        assert d["K"] == 5000.0
        assert d["recruitment_model"] == "beverton_holt"


class TestFisheriesPattern:
    @pytest.fixture
    def pattern(self):
        return FisheriesPattern()

    @pytest.fixture
    def hypothesis(self):
        return Hypothesis(
            title="Fisheries stock assessment",
            description="Surplus production model for fish population",
        )

    def test_init(self, pattern):
        assert pattern.config.production_model == ProductionModel.SCHAFFER
        assert pattern.rng is not None

    def test_can_simulate_matching(self, pattern, hypothesis):
        assert pattern.can_simulate(hypothesis) is True

    def test_can_simulate_non_matching(self, pattern):
        h = Hypothesis(title="Quantum mechanics", description="Particle physics")
        assert pattern.can_simulate(h) is False

    def test_can_simulate_keywords(self, pattern):
        keywords = ["fish", "biomass", "msy", "catch", "overfishing"]
        for kw in keywords:
            h = Hypothesis(title=kw, description="test")
            assert pattern.can_simulate(h) is True

    def test_parse_config(self, pattern):
        pattern.config = pattern._parse_config(
            {
                "production_model": "fox",
                "K": 5000.0,
                "fishing_mortality": 0.3,
                "years": 20,
            }
        )
        assert pattern.config.production_model == ProductionModel.FOX
        assert pattern.config.K == 5000.0
        assert pattern.config.fishing_mortality == 0.3

    def test_assess_status_healthy(self, pattern):
        assert pattern._assess_status(6000, 5000, 0.2, 0.3) == "healthy"

    def test_assess_status_overfishing(self, pattern):
        assert pattern._assess_status(6000, 5000, 0.4, 0.3) == "overfishing"

    def test_assess_status_overfished(self, pattern):
        assert pattern._assess_status(2000, 5000, 0.4, 0.3) == "overfished"

    def test_assess_status_depleted(self, pattern):
        assert pattern._assess_status(2000, 5000, 0.2, 0.3) == "depleted"

    def test_calculate_recruitment_beverton_holt(self, pattern):
        pattern.config = FisheriesConfig(recruitment_model=RecruitmentModel.BEVERTON_HOLT)
        R = pattern._calculate_recruitment(1000.0)
        assert R > 0

    def test_calculate_recruitment_ricker(self, pattern):
        pattern.config = FisheriesConfig(recruitment_model=RecruitmentModel.RICKER)
        R = pattern._calculate_recruitment(1000.0)
        assert R > 0

    def test_calculate_recruitment_logistic(self, pattern):
        pattern.config = FisheriesConfig(recruitment_model=RecruitmentModel.LOGISTIC)
        R = pattern._calculate_recruitment(1000.0)
        assert R > 0

    def test_calculate_confidence(self, pattern):
        results = {"metrics": {"final_biomass": 5000, "final_catch": 100, "status": "healthy"}}
        score = pattern._calculate_confidence(results)
        assert 0 <= score <= 0.95

    def test_estimate_resources(self, pattern):
        h = Hypothesis(title="test", description="test")
        h.parameters = {"years": 50, "max_age": 15}
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources

    @pytest.mark.asyncio
    async def test_run_schaefer(self, pattern, hypothesis):
        result = await pattern.run(hypothesis, {"production_model": "schaefer", "years": 10})
        assert result.status.value == "completed"
        assert result.metrics is not None
        assert result.metrics["model"] == "schaefer"
        assert "B_msy" in result.metrics

    @pytest.mark.asyncio
    async def test_run_fox(self, pattern, hypothesis):
        result = await pattern.run(hypothesis, {"production_model": "fox", "years": 10})
        assert result.status.value == "completed"
        assert result.metrics["model"] == "fox"

    @pytest.mark.asyncio
    async def test_run_age_structured(self, pattern, hypothesis):
        result = await pattern.run(
            hypothesis, {"production_model": "thompson_bell", "years": 10, "max_age": 10}
        )
        assert result.status.value == "completed"
        assert result.metrics["model"] == "age_structured"

    @pytest.mark.asyncio
    async def test_run_with_quota(self, pattern, hypothesis):
        result = await pattern.run(
            hypothesis, {"production_model": "schaefer", "years": 10, "quota": 500.0}
        )
        assert result.status.value == "completed"

    @pytest.mark.asyncio
    async def test_run_high_fishing(self, pattern, hypothesis):
        result = await pattern.run(
            hypothesis, {"production_model": "schaefer", "years": 10, "fishing_mortality": 0.8}
        )
        assert result.status.value == "completed"

    def test_get_metadata(self):
        metadata = FisheriesPattern.get_metadata()
        assert metadata["id"] == "fisheries"
        assert "parameters" in metadata
        assert len(metadata["references"]) > 0
