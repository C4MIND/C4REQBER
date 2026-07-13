"""
Tests for src/patterns/library/enzyme_kinetics.py

Covers:
- KineticModel enum
- EnzymeKineticsConfig dataclass and defaults
- EnzymeKineticsPattern initialization
- can_simulate() keyword matching
- _parse_config()
- _michaelis_menten_simulation(), _briggs_haldane_simulation()
- _competitive_inhibition_simulation(), _hill_simulation(), _mwc_simulation()
- _calculate_mm_metrics()
- _calculate_confidence()
- estimate_resources()
- run() integration for all models
- get_metadata()
- Edge cases: zero substrate, zero enzyme, very short time
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.core import Hypothesis, SimulationStatus
from src.patterns.library.enzyme_kinetics import (
    EnzymeKineticsConfig,
    EnzymeKineticsPattern,
    KineticModel,
)


# ═══════════════════════════════════════════════════════════════════
# Enums and Dataclasses
# ═══════════════════════════════════════════════════════════════════


class TestKineticModel:
    def test_enum_values(self):
        assert KineticModel.MICHAELIS_MENTEN.value == "michaelis_menten"
        assert KineticModel.BRIGGS_HALDANE.value == "briggs_haldane"
        assert KineticModel.COMPETITIVE_INHIBITION.value == "competitive_inhibition"
        assert KineticModel.HILL.value == "hill"
        assert KineticModel.MWC.value == "mwc"


class TestEnzymeKineticsConfig:
    def test_default_init(self):
        cfg = EnzymeKineticsConfig()
        assert cfg.model == KineticModel.MICHAELIS_MENTEN
        assert cfg.Vmax == 100.0
        assert cfg.Km == 50.0
        assert cfg.E0 == 1.0
        assert cfg.S0 == 100.0
        assert cfg.t_max == 100.0
        assert cfg.dt == 0.01

    def test_custom_init(self):
        cfg = EnzymeKineticsConfig(
            model=KineticModel.HILL,
            Vmax=200.0,
            n=2.5,
        )
        assert cfg.model == KineticModel.HILL
        assert cfg.Vmax == 200.0
        assert cfg.n == 2.5

    def test_to_dict(self):
        cfg = EnzymeKineticsConfig()
        d = cfg.to_dict()
        assert d["model"] == "michaelis_menten"
        assert d["Vmax"] == 100.0
        assert "k1" in d
        assert "substrate_range" in d


# ═══════════════════════════════════════════════════════════════════
# EnzymeKineticsPattern Initialization
# ═══════════════════════════════════════════════════════════════════


class TestEnzymeKineticsPatternInit:
    def test_init(self):
        pattern = EnzymeKineticsPattern()
        assert pattern is not None
        assert pattern.config.model == KineticModel.MICHAELIS_MENTEN

    def test_parameters_defined(self):
        pattern = EnzymeKineticsPattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0
        param_names = [p.name for p in pattern.parameters]
        assert "model" in param_names
        assert "Vmax" in param_names
        assert "Km" in param_names
        assert "E0" in param_names


# ═══════════════════════════════════════════════════════════════════
# can_simulate
# ═══════════════════════════════════════════════════════════════════


class TestCanSimulate:
    def test_matches_enzyme(self):
        pattern = EnzymeKineticsPattern()
        h = Hypothesis(title="Enzyme kinetics", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_michaelis(self):
        pattern = EnzymeKineticsPattern()
        h = Hypothesis(title="Michaelis-Menten model", description="substrate binding")
        assert pattern.can_simulate(h) is True

    def test_matches_inhibition(self):
        pattern = EnzymeKineticsPattern()
        h = Hypothesis(title="Competitive inhibition", description="drug screening")
        assert pattern.can_simulate(h) is True

    def test_matches_allosteric(self):
        pattern = EnzymeKineticsPattern()
        h = Hypothesis(title="Allosteric regulation", description="cooperative binding")
        assert pattern.can_simulate(h) is True

    def test_matches_metabolism(self):
        pattern = EnzymeKineticsPattern()
        h = Hypothesis(title="Drug metabolism", description="CYP450 pathway")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = EnzymeKineticsPattern()
        h = Hypothesis(title="Linear regression", description="statistics")
        assert pattern.can_simulate(h) is False

    def test_empty_hypothesis(self):
        pattern = EnzymeKineticsPattern()
        h = Hypothesis()
        assert pattern.can_simulate(h) is False


# ═══════════════════════════════════════════════════════════════════
# Config Parsing
# ═══════════════════════════════════════════════════════════════════


class TestParseConfig:
    def test_default_parsing(self):
        pattern = EnzymeKineticsPattern()
        cfg = pattern._parse_config({})
        assert cfg.model == KineticModel.MICHAELIS_MENTEN
        assert cfg.Vmax == 100.0
        assert cfg.Km == 50.0

    def test_custom_parsing(self):
        pattern = EnzymeKineticsPattern()
        cfg = pattern._parse_config({"model": "hill", "Vmax": 200.0, "n": 3.0})
        assert cfg.model == KineticModel.HILL
        assert cfg.Vmax == 200.0
        assert cfg.n == 3.0

    def test_all_fields_parsing(self):
        pattern = EnzymeKineticsPattern()
        cfg = pattern._parse_config(
            {
                "model": "briggs_haldane",
                "Vmax": 150.0,
                "Km": 25.0,
                "E0": 2.0,
                "S0": 200.0,
                "P0": 0.0,
                "ES0": 0.0,
                "k1": 200.0,
                "k_1": 100.0,
                "k2": 100.0,
                "I0": 10.0,
                "Ki": 5.0,
                "n": 2.0,
                "Kd": 30.0,
                "L": 500.0,
                "c": 0.005,
                "t_max": 50.0,
                "dt": 0.05,
                "num_points": 15,
            }
        )
        assert cfg.model == KineticModel.BRIGGS_HALDANE
        assert cfg.E0 == 2.0
        assert cfg.k1 == 200.0
        assert cfg.num_points == 15


# ═══════════════════════════════════════════════════════════════════
# Simulation Methods
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestMichaelisMentenSimulation:
    async def test_mm_basic(self):
        pattern = EnzymeKineticsPattern()
        pattern.config = EnzymeKineticsConfig(
            model=KineticModel.MICHAELIS_MENTEN,
            t_max=50.0,
            dt=0.5,
        )
        result = await pattern._michaelis_menten_simulation()
        assert "metrics" in result
        assert "logs" in result
        assert "time" in result
        assert "substrate" in result
        assert "product" in result
        assert result["metrics"]["model"] == "michaelis_menten"
        assert result["metrics"]["final_product"] >= 0

    async def test_mm_substrate_depletion(self):
        pattern = EnzymeKineticsPattern()
        pattern.config = EnzymeKineticsConfig(
            model=KineticModel.MICHAELIS_MENTEN,
            t_max=100.0,
            dt=0.5,
            S0=50.0,
            Vmax=100.0,
            Km=10.0,
        )
        result = await pattern._michaelis_menten_simulation()
        metrics = result["metrics"]
        assert metrics["final_substrate"] < metrics["input_Vmax"] * 2  # Sanity check
        assert metrics["reaction_extent"] > 0

    async def test_mm_saturation_curve(self):
        pattern = EnzymeKineticsPattern()
        pattern.config = EnzymeKineticsConfig(
            model=KineticModel.MICHAELIS_MENTEN,
            num_points=10,
        )
        result = await pattern._michaelis_menten_simulation()
        assert "saturation_S" in result
        assert "saturation_v" in result
        assert len(result["saturation_S"]) == 10


@pytest.mark.asyncio
class TestBriggsHaldaneSimulation:
    async def test_bh_basic(self):
        pattern = EnzymeKineticsPattern()
        pattern.config = EnzymeKineticsConfig(
            model=KineticModel.BRIGGS_HALDANE,
            t_max=50.0,
            dt=0.5,
        )
        result = await pattern._briggs_haldane_simulation()
        assert "metrics" in result
        assert result["metrics"]["model"] == "briggs_haldane"
        assert "apparent_Vmax" in result["metrics"]
        assert "apparent_Km" in result["metrics"]
        assert "enzyme_substrate" in result
        assert "free_enzyme" in result

    async def test_bh_conservation(self):
        pattern = EnzymeKineticsPattern()
        pattern.config = EnzymeKineticsConfig(
            model=KineticModel.BRIGGS_HALDANE,
            t_max=50.0,
            dt=0.5,
            E0=1.0,
        )
        result = await pattern._briggs_haldane_simulation()
        ES = np.array(result["enzyme_substrate"])
        E = np.array(result["free_enzyme"])
        # Enzyme conservation: E + ES = E0
        total_E = E + ES
        np.testing.assert_array_almost_equal(total_E, np.ones_like(total_E) * 1.0, decimal=3)


@pytest.mark.asyncio
class TestCompetitiveInhibitionSimulation:
    async def test_inhibition_basic(self):
        pattern = EnzymeKineticsPattern()
        pattern.config = EnzymeKineticsConfig(
            model=KineticModel.COMPETITIVE_INHIBITION,
            t_max=50.0,
            dt=0.5,
            I0=10.0,
            Ki=5.0,
        )
        result = await pattern._competitive_inhibition_simulation()
        assert "metrics" in result
        assert result["metrics"]["model"] == "competitive_inhibition"
        assert "Km_apparent" in result["metrics"]
        assert result["metrics"]["Km_apparent"] > result["metrics"]["Km"]

    async def test_no_inhibition(self):
        pattern = EnzymeKineticsPattern()
        pattern.config = EnzymeKineticsConfig(
            model=KineticModel.COMPETITIVE_INHIBITION,
            t_max=50.0,
            dt=0.5,
            I0=0.0,
        )
        result = await pattern._competitive_inhibition_simulation()
        metrics = result["metrics"]
        assert metrics["inhibition_factor"] == 1.0
        assert metrics["Km_apparent"] == metrics["Km"]


@pytest.mark.asyncio
class TestHillSimulation:
    async def test_hill_basic(self):
        pattern = EnzymeKineticsPattern()
        pattern.config = EnzymeKineticsConfig(
            model=KineticModel.HILL,
            t_max=50.0,
            dt=0.5,
            n=2.0,
        )
        result = await pattern._hill_simulation()
        assert "metrics" in result
        assert result["metrics"]["model"] == "hill"
        assert result["metrics"]["n"] == 2.0
        assert "cooperativity" in result["metrics"]

    async def test_hill_positive_cooperativity(self):
        pattern = EnzymeKineticsPattern()
        pattern.config = EnzymeKineticsConfig(
            model=KineticModel.HILL,
            n=3.0,
        )
        result = await pattern._hill_simulation()
        assert result["metrics"]["cooperativity"] == "positive"

    async def test_hill_negative_cooperativity(self):
        pattern = EnzymeKineticsPattern()
        pattern.config = EnzymeKineticsConfig(
            model=KineticModel.HILL,
            n=0.5,
        )
        result = await pattern._hill_simulation()
        assert result["metrics"]["cooperativity"] == "negative"

    async def test_hill_no_cooperativity(self):
        pattern = EnzymeKineticsPattern()
        pattern.config = EnzymeKineticsConfig(
            model=KineticModel.HILL,
            n=1.0,
        )
        result = await pattern._hill_simulation()
        assert result["metrics"]["cooperativity"] == "none"


@pytest.mark.asyncio
class TestMwcSimulation:
    async def test_mwc_basic(self):
        pattern = EnzymeKineticsPattern()
        pattern.config = EnzymeKineticsConfig(
            model=KineticModel.MWC,
            t_max=50.0,
            dt=0.5,
            L=1000.0,
            c=0.01,
        )
        result = await pattern._mwc_simulation()
        assert "metrics" in result
        assert result["metrics"]["model"] == "mwc"
        assert "fraction_active" in result
        assert result["metrics"]["L"] == 1000.0

    async def test_mwc_sigmoid_shape(self):
        pattern = EnzymeKineticsPattern()
        pattern.config = EnzymeKineticsConfig(
            model=KineticModel.MWC,
            L=100.0,
            c=0.01,
            n=4.0,
        )
        result = await pattern._mwc_simulation()
        frac = np.array(result["fraction_active"])
        # Should be sigmoid: low at start, high at end
        assert frac[0] < frac[-1]


# ═══════════════════════════════════════════════════════════════════
# MM Metrics Calculation
# ═══════════════════════════════════════════════════════════════════


class TestCalculateMmMetrics:
    def test_normal_case(self):
        pattern = EnzymeKineticsPattern()
        pattern.config = EnzymeKineticsConfig(Vmax=100.0, Km=50.0)
        t = np.array([0, 1, 2])
        S = np.array([100.0, 80.0, 60.0])
        P = np.array([0.0, 20.0, 40.0])
        v = np.array([66.7, 61.5, 54.5])
        S_range = np.array([1.0, 10.0, 100.0])
        v_curve = np.array([1.96, 16.7, 66.7])
        metrics = pattern._calculate_mm_metrics(t, S, P, v, S_range, v_curve)
        assert "fitted_Vmax" in metrics
        assert "fitted_Km" in metrics
        assert "initial_velocity" in metrics
        assert "reaction_extent" in metrics
        assert "catalytic_efficiency" in metrics

    def test_zero_substrate_range(self):
        pattern = EnzymeKineticsPattern()
        pattern.config = EnzymeKineticsConfig(Vmax=100.0, Km=50.0)
        t = np.array([0, 1])
        S = np.array([100.0, 50.0])
        P = np.array([0.0, 50.0])
        v = np.array([66.7, 50.0])
        S_range = np.array([0.0, 50.0, 100.0])
        v_curve = np.array([0.0, 50.0, 66.7])
        metrics = pattern._calculate_mm_metrics(t, S, P, v, S_range, v_curve)
        assert metrics["fitted_Vmax"] > 0


# ═══════════════════════════════════════════════════════════════════
# Confidence Calculation
# ═══════════════════════════════════════════════════════════════════


class TestCalculateConfidence:
    def test_good_reaction(self):
        pattern = EnzymeKineticsPattern()
        pattern.config = EnzymeKineticsConfig(model=KineticModel.MICHAELIS_MENTEN)
        results = {
            "metrics": {
                "reaction_extent": 0.5,
                "fitted_Km": 45.0,
                "final_product": 30.0,
                "input_Km": 50.0,
            }
        }
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5

    def test_no_reaction(self):
        pattern = EnzymeKineticsPattern()
        pattern.config = EnzymeKineticsConfig(model=KineticModel.MICHAELIS_MENTEN)
        results = {"metrics": {"reaction_extent": 0.0}}
        confidence = pattern._calculate_confidence(results)
        assert confidence < 0.5

    def test_hill_confidence(self):
        pattern = EnzymeKineticsPattern()
        pattern.config = EnzymeKineticsConfig(model=KineticModel.HILL)
        results = {"metrics": {"reaction_extent": 0.3, "fitted_Km": 40.0, "final_product": 20.0}}
        confidence = pattern._calculate_confidence(results)
        assert confidence >= 0.25  # At least positive concentrations


# ═══════════════════════════════════════════════════════════════════
# Resource Estimation
# ═══════════════════════════════════════════════════════════════════


class TestEstimateResources:
    def test_default_params(self):
        pattern = EnzymeKineticsPattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert "gpu_required" in resources
        assert "estimated_time_seconds" in resources
        assert resources["gpu_required"] is False

    def test_custom_params(self):
        pattern = EnzymeKineticsPattern()
        h = Hypothesis(parameters={"t_max": 500.0, "num_points": 50})
        resources = pattern.estimate_resources(h)
        assert resources["estimated_time_seconds"] > 0


# ═══════════════════════════════════════════════════════════════════
# run() Integration
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRun:
    async def test_run_michaelis_menten(self):
        pattern = EnzymeKineticsPattern()
        h = Hypothesis(title="Enzyme kinetics", description="test")
        config = {"model": "michaelis_menten", "t_max": 50.0, "dt": 0.5}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("ek_")
        assert len(result.logs) > 0

    async def test_run_briggs_haldane(self):
        pattern = EnzymeKineticsPattern()
        h = Hypothesis(title="Enzyme mechanism", description="test")
        config = {"model": "briggs_haldane", "t_max": 50.0, "dt": 0.5}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_competitive_inhibition(self):
        pattern = EnzymeKineticsPattern()
        h = Hypothesis(title="Drug inhibition", description="test")
        config = {"model": "competitive_inhibition", "t_max": 50.0, "I0": 10.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_hill(self):
        pattern = EnzymeKineticsPattern()
        h = Hypothesis(title="Cooperative binding", description="test")
        config = {"model": "hill", "t_max": 50.0, "n": 2.5}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_mwc(self):
        pattern = EnzymeKineticsPattern()
        h = Hypothesis(title="Allosteric enzyme", description="test")
        config = {"model": "mwc", "t_max": 50.0, "L": 500.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_logs_present(self):
        pattern = EnzymeKineticsPattern()
        h = Hypothesis(title="Enzyme", description="test")
        config = {"model": "michaelis_menten", "t_max": 50.0}
        result = await pattern.run(h, config)
        assert len(result.logs) > 0

    async def test_run_failure_handling(self):
        pattern = EnzymeKineticsPattern()
        h = Hypothesis(title="Enzyme", description="test")
        with patch.object(pattern, "_parse_config", side_effect=ValueError("test error")):
            result = await pattern.run(h, {"model": "michaelis_menten", "t_max": 50.0})
            assert result.status == SimulationStatus.FAILED
            assert "test error" in result.error_message


# ═══════════════════════════════════════════════════════════════════
# get_metadata
# ═══════════════════════════════════════════════════════════════════


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = EnzymeKineticsPattern.get_metadata()
        assert meta["id"] == "enzyme_kinetics"
        assert meta["name"] == "Enzyme Kinetics"
        assert meta["category"] == "biology"
        assert "parameters" in meta
        assert "references" in meta
        assert len(meta["references"]) > 0


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestEdgeCases:
    async def test_zero_substrate(self):
        pattern = EnzymeKineticsPattern()
        h = Hypothesis(title="Enzyme", description="test")
        config = {"model": "michaelis_menten", "S0": 0.0, "t_max": 10.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_zero_enzyme(self):
        pattern = EnzymeKineticsPattern()
        h = Hypothesis(title="Enzyme", description="test")
        config = {"model": "briggs_haldane", "E0": 0.0, "t_max": 10.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_very_short_time(self):
        pattern = EnzymeKineticsPattern()
        h = Hypothesis(title="Enzyme", description="test")
        config = {"model": "michaelis_menten", "t_max": 0.1, "dt": 0.01}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_very_large_km(self):
        pattern = EnzymeKineticsPattern()
        h = Hypothesis(title="Enzyme", description="test")
        config = {"model": "michaelis_menten", "Km": 10000.0, "S0": 1.0, "t_max": 10.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_empty_config(self):
        pattern = EnzymeKineticsPattern()
        h = Hypothesis(title="Enzyme kinetics", description="test")
        result = await pattern.run(h, {})
        assert result.status == SimulationStatus.COMPLETED

    async def test_high_inhibitor_concentration(self):
        pattern = EnzymeKineticsPattern()
        h = Hypothesis(title="Inhibition", description="test")
        config = {"model": "competitive_inhibition", "I0": 1000.0, "Ki": 0.1, "t_max": 10.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
