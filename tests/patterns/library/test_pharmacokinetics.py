"""
Tests for src/patterns/library/pharmacokinetics.py (Pharmacokinetics pattern)

Covers:
- PKModel enum
- DosingRegimen dataclass
- PKPattern initialization
- can_simulate() keyword matching
- _one_compartment() model
- _two_compartment() model
- _michaelis_menten() model
- _calculate_pk_metrics()
- _estimate_half_life()
- _calculate_confidence()
- estimate_resources()
- run() async integration
- Edge cases: different dosing regimens, model types
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.pharmacokinetics import PKPattern, PKModel, DosingRegimen
from src.patterns.core import Hypothesis, SimulationStatus



# ═══════════════════════════════════════════════════════════════════
# Enum and Dataclass Tests
# ═══════════════════════════════════════════════════════════════════


class TestPKModel:
    def test_enum_values(self):
        assert PKModel.ONE_COMPARTMENT.value == "one_compartment"
        assert PKModel.TWO_COMPARTMENT.value == "two_compartment"
        assert PKModel.MICHAELIS_MENTEN.value == "michaelis_menten"


class TestDosingRegimen:
    def test_default_init(self):
        dr = DosingRegimen(dose=100.0, interval=12.0, num_doses=5)
        assert dr.dose == 100.0
        assert dr.interval == 12.0
        assert dr.num_doses == 5
        assert dr.route == "oral"

    def test_custom_init(self):
        dr = DosingRegimen(
            dose=200.0,
            interval=8.0,
            num_doses=3,
            route="iv",
            absorption_rate=0.0
        )
        assert dr.dose == 200.0
        assert dr.route == "iv"


# ═══════════════════════════════════════════════════════════════════
# Initialization Tests
# ═══════════════════════════════════════════════════════════════════


class TestPKPatternInit:
    def test_init(self):
        pattern = PKPattern()
        assert pattern is not None
        assert hasattr(pattern, "parameters")

    def test_parameters_defined(self):
        pattern = PKPattern()
        assert len(pattern.parameters) > 0
        param_names = [p.name for p in pattern.parameters]
        assert "model_type" in param_names
        assert "dose" in param_names
        assert "halflife" in param_names


# ═══════════════════════════════════════════════════════════════════
# can_simulate Tests
# ═══════════════════════════════════════════════════════════════════


class TestCanSimulate:
    def test_matches_drug(self):
        pattern = PKPattern()
        h = Hypothesis(title="Drug concentration", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_pk(self):
        pattern = PKPattern()
        h = Hypothesis(title="Pharmacokinetics", description="absorption")
        assert pattern.can_simulate(h) is True

    def test_matches_dosing(self):
        pattern = PKPattern()
        h = Hypothesis(title="Dosing regimen", description="administration")
        assert pattern.can_simulate(h) is True

    def test_matches_auc(self):
        pattern = PKPattern()
        h = Hypothesis(title="AUC calculation", description="exposure")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = PKPattern()
        h = Hypothesis(title="Mechanical system", description="vibration")
        assert pattern.can_simulate(h) is False


# ═══════════════════════════════════════════════════════════════════
# One Compartment Tests
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestOneCompartment:
    async def test_one_compartment_runs(self):
        pattern = PKPattern()
        h = Hypothesis(title="PK simulation", description="test")
        result = await pattern._one_compartment(h, {
            "dose": 100.0,
            "halflife": 4.0,
            "volume": 50.0,
            "num_doses": 1
        })
        assert "metrics" in result
        assert "logs" in result

    async def test_cmax_positive(self):
        pattern = PKPattern()
        h = Hypothesis(title="PK simulation", description="test")
        result = await pattern._one_compartment(h, {
            "dose": 100.0,
            "halflife": 4.0,
            "volume": 50.0,
            "num_doses": 1
        })
        assert result["metrics"]["cmax"] > 0

    async def test_tmax_positive(self):
        pattern = PKPattern()
        h = Hypothesis(title="PK simulation", description="test")
        result = await pattern._one_compartment(h, {
            "dose": 100.0,
            "halflife": 4.0,
            "volume": 50.0,
            "num_doses": 1
        })
        assert result["metrics"]["tmax"] >= 0

    async def test_auc_positive(self):
        pattern = PKPattern()
        h = Hypothesis(title="PK simulation", description="test")
        result = await pattern._one_compartment(h, {
            "dose": 100.0,
            "halflife": 4.0,
            "volume": 50.0,
            "num_doses": 1
        })
        assert result["metrics"]["auc"] > 0

    async def test_multiple_doses(self):
        pattern = PKPattern()
        h = Hypothesis(title="PK simulation", description="test")
        result = await pattern._one_compartment(h, {
            "dose": 100.0,
            "interval": 12.0,
            "num_doses": 5,
            "halflife": 4.0,
            "volume": 50.0
        })
        assert result["metrics"]["cmax"] > 0


# ═══════════════════════════════════════════════════════════════════
# Two Compartment Tests
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestTwoCompartment:
    async def test_two_compartment_runs(self):
        pattern = PKPattern()
        h = Hypothesis(title="PK simulation", description="test")
        result = await pattern._two_compartment(h, {
            "dose": 100.0,
            "halflife": 4.0,
            "volume": 50.0
        })
        assert "metrics" in result
        assert "peripheral_cmax" in result["metrics"]

    async def test_peripheral_cmax_positive(self):
        pattern = PKPattern()
        h = Hypothesis(title="PK simulation", description="test")
        result = await pattern._two_compartment(h, {
            "dose": 100.0,
            "halflife": 4.0,
            "volume": 50.0
        })
        assert result["metrics"]["peripheral_cmax"] > 0


# ═══════════════════════════════════════════════════════════════════
# Michaelis-Menten Tests
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestMichaelisMenten:
    async def test_mm_runs(self):
        pattern = PKPattern()
        h = Hypothesis(title="PK simulation", description="test")
        result = await pattern._michaelis_menten(h, {
            "dose": 100.0,
            "volume": 50.0
        })
        assert "metrics" in result
        assert result["metrics"]["nonlinear"] is True

    async def test_mm_cmax_positive(self):
        pattern = PKPattern()
        h = Hypothesis(title="PK simulation", description="test")
        result = await pattern._michaelis_menten(h, {
            "dose": 100.0,
            "volume": 50.0
        })
        assert result["metrics"]["cmax"] > 0


# ═══════════════════════════════════════════════════════════════════
# PK Metrics Tests
# ═══════════════════════════════════════════════════════════════════


class TestCalculatePKMetrics:
    def test_cmax_calculation(self):
        pattern = PKPattern()
        times = np.linspace(0, 24, 100)
        concentrations = 100 * np.exp(-times / 4)  # Exponential decay
        metrics = pattern._calculate_pk_metrics(times, concentrations, 100.0, 0)
        assert metrics["cmax"] == 100.0  # At t=0

    def test_tmax_calculation(self):
        pattern = PKPattern()
        times = np.linspace(0, 24, 100)
        # Peak at t=4
        concentrations = 100 * (times / 4) * np.exp(1 - times / 4)
        concentrations[0] = 0
        metrics = pattern._calculate_pk_metrics(times, concentrations, 100.0, 0)
        assert metrics["tmax"] == pytest.approx(4.0, abs=0.5)

    def test_auc_calculation(self):
        pattern = PKPattern()
        times = np.linspace(0, 24, 100)
        concentrations = np.ones_like(times) * 10  # Constant
        metrics = pattern._calculate_pk_metrics(times, concentrations, 100.0, 0)
        # AUC = 10 * 24 = 240
        assert metrics["auc"] == pytest.approx(240.0, rel=0.1)


# ═══════════════════════════════════════════════════════════════════
# Half-life Estimation Tests
# ═══════════════════════════════════════════════════════════════════


class TestEstimateHalfLife:
    def test_exponential_decay(self):
        pattern = PKPattern()
        times = np.linspace(0, 24, 100)
        concentrations = 100 * np.exp(-0.173 * times)  # Half-life = 4
        hl = pattern._estimate_half_life(times, concentrations)
        assert hl == pytest.approx(4.0, rel=0.2)

    def test_short_data(self):
        pattern = PKPattern()
        times = np.array([0, 1])
        concentrations = np.array([100, 50])
        hl = pattern._estimate_half_life(times, concentrations)
        assert hl >= 0

    def test_zero_concentration(self):
        pattern = PKPattern()
        times = np.linspace(0, 24, 100)
        concentrations = np.zeros_like(times)
        hl = pattern._estimate_half_life(times, concentrations)
        assert hl == 0.0


# ═══════════════════════════════════════════════════════════════════
# Confidence Calculation Tests
# ═══════════════════════════════════════════════════════════════════


class TestCalculateConfidence:
    def test_high_confidence(self):
        pattern = PKPattern()
        results = {
            "metrics": {
                "cmax": 50.0,
                "auc": 500.0,
                "half_life_estimate": 4.0,
                "steady_state_reached": True
            }
        }
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.7

    def test_low_confidence(self):
        pattern = PKPattern()
        results = {"metrics": {}}
        confidence = pattern._calculate_confidence(results)
        assert confidence < 0.5


# ═══════════════════════════════════════════════════════════════════
# Resource Estimation Tests
# ═══════════════════════════════════════════════════════════════════


class TestEstimateResources:
    def test_default_params(self):
        pattern = PKPattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert "gpu_required" in resources
        assert resources["gpu_required"] is False

    def test_multiple_doses(self):
        pattern = PKPattern()
        h = Hypothesis(parameters={"num_doses": 10})
        resources = pattern.estimate_resources(h)
        assert resources["estimated_time_seconds"] > 0


# ═══════════════════════════════════════════════════════════════════
# Run Integration Tests
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRun:
    async def test_run_one_compartment(self):
        pattern = PKPattern()
        h = Hypothesis(title="PK simulation", description="drug concentration")
        result = await pattern.run(h, {
            "model_type": "one_compartment",
            "dose": 100.0,
            "num_doses": 1
        })
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_two_compartment(self):
        pattern = PKPattern()
        h = Hypothesis(title="PK simulation", description="drug concentration")
        result = await pattern.run(h, {
            "model_type": "two_compartment",
            "dose": 100.0
        })
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_michaelis_menten(self):
        pattern = PKPattern()
        h = Hypothesis(title="PK simulation", description="drug concentration")
        result = await pattern.run(h, {
            "model_type": "michaelis_menten",
            "dose": 100.0
        })
        assert result.status == SimulationStatus.COMPLETED

    async def test_logs_present(self):
        pattern = PKPattern()
        h = Hypothesis(title="PK simulation", description="drug concentration")
        result = await pattern.run(h, {"model_type": "one_compartment"})
        assert len(result.logs) > 0


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestEdgeCases:
    async def test_very_small_dose(self):
        pattern = PKPattern()
        h = Hypothesis(title="PK simulation", description="drug concentration")
        result = await pattern.run(h, {"dose": 0.1, "model_type": "one_compartment"})
        assert result.status == SimulationStatus.COMPLETED

    async def test_very_large_dose(self):
        pattern = PKPattern()
        h = Hypothesis(title="PK simulation", description="drug concentration")
        result = await pattern.run(h, {"dose": 10000.0, "model_type": "one_compartment"})
        assert result.status == SimulationStatus.COMPLETED

    async def test_short_half_life(self):
        pattern = PKPattern()
        h = Hypothesis(title="PK simulation", description="drug concentration")
        result = await pattern.run(h, {"halflife": 0.5, "model_type": "one_compartment"})
        assert result.status == SimulationStatus.COMPLETED

    async def test_long_half_life(self):
        pattern = PKPattern()
        h = Hypothesis(title="PK simulation", description="drug concentration")
        result = await pattern.run(h, {"halflife": 100.0, "model_type": "one_compartment"})
        assert result.status == SimulationStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
