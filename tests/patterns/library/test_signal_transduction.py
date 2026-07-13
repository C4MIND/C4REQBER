"""
Tests for src/patterns/library/signal_transduction.py

Covers:
- SignalingModel enum
- SignalTransductionConfig dataclass and defaults
- SignalTransductionPattern initialization
- can_simulate() keyword matching
- _parse_config()
- _mapk_simulation(), _gpcr_simulation(), _adaptation_simulation()
- _repressilator_simulation(), _toggle_switch_simulation()
- _estimate_hill_coefficient(), _find_peaks()
- _calculate_confidence()
- estimate_resources()
- run() integration for all models
- get_metadata()
- Edge cases: zero time, minimal params, empty hypothesis
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.core import Hypothesis, SimulationStatus
from src.patterns.library.signal_transduction import (
    SignalingModel,
    SignalTransductionConfig,
    SignalTransductionPattern,
)


# ═══════════════════════════════════════════════════════════════════
# Enums and Dataclasses
# ═══════════════════════════════════════════════════════════════════


class TestSignalingModel:
    def test_enum_values(self):
        assert SignalingModel.MAPK_CASCADE.value == "mapk_cascade"
        assert SignalingModel.GPCR.value == "gpcr"
        assert SignalingModel.ADAPTATION.value == "adaptation"
        assert SignalingModel.REPRESSILATOR.value == "repressilator"
        assert SignalingModel.TOGGLE_SWITCH.value == "toggle_switch"


class TestSignalTransductionConfig:
    def test_default_init(self):
        cfg = SignalTransductionConfig()
        assert cfg.model == SignalingModel.MAPK_CASCADE
        assert cfg.t_max == 1000.0
        assert cfg.dt == 0.1
        assert cfg.E1_total == 0.1
        assert cfg.MAPKK_total == 10.0
        assert cfg.MAPK_total == 10.0

    def test_custom_init(self):
        cfg = SignalTransductionConfig(
            model=SignalingModel.GPCR,
            t_max=500.0,
            ligand_conc=0.5,
        )
        assert cfg.model == SignalingModel.GPCR
        assert cfg.t_max == 500.0
        assert cfg.ligand_conc == 0.5

    def test_to_dict(self):
        cfg = SignalTransductionConfig()
        d = cfg.to_dict()
        assert d["model"] == "mapk_cascade"
        assert d["t_max"] == 1000.0
        assert "E1_total" in d
        assert "alpha" in d


# ═══════════════════════════════════════════════════════════════════
# SignalTransductionPattern Initialization
# ═══════════════════════════════════════════════════════════════════


class TestSignalTransductionPatternInit:
    def test_init(self):
        pattern = SignalTransductionPattern()
        assert pattern is not None
        assert pattern.config.model == SignalingModel.MAPK_CASCADE

    def test_parameters_defined(self):
        pattern = SignalTransductionPattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0
        param_names = [p.name for p in pattern.parameters]
        assert "model" in param_names
        assert "t_max" in param_names
        assert "E1_total" in param_names


# ═══════════════════════════════════════════════════════════════════
# can_simulate
# ═══════════════════════════════════════════════════════════════════


class TestCanSimulate:
    def test_matches_signaling(self):
        pattern = SignalTransductionPattern()
        h = Hypothesis(title="MAPK signaling", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_kinase(self):
        pattern = SignalTransductionPattern()
        h = Hypothesis(title="Protein kinase cascade", description="phosphorylation")
        assert pattern.can_simulate(h) is True

    def test_matches_gpcr(self):
        pattern = SignalTransductionPattern()
        h = Hypothesis(title="GPCR receptor dynamics", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_oscillation(self):
        pattern = SignalTransductionPattern()
        h = Hypothesis(title="Genetic oscillator", description="repressilator")
        assert pattern.can_simulate(h) is True

    def test_matches_bistability(self):
        pattern = SignalTransductionPattern()
        h = Hypothesis(title="Bistable switch", description="toggle")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = SignalTransductionPattern()
        h = Hypothesis(title="Linear regression", description="statistics")
        assert pattern.can_simulate(h) is False

    def test_empty_hypothesis(self):
        pattern = SignalTransductionPattern()
        h = Hypothesis()
        assert pattern.can_simulate(h) is False


# ═══════════════════════════════════════════════════════════════════
# Config Parsing
# ═══════════════════════════════════════════════════════════════════


class TestParseConfig:
    def test_default_parsing(self):
        pattern = SignalTransductionPattern()
        cfg = pattern._parse_config({})
        assert cfg.model == SignalingModel.MAPK_CASCADE
        assert cfg.t_max == 1000.0

    def test_custom_parsing(self):
        pattern = SignalTransductionPattern()
        cfg = pattern._parse_config({"model": "gpcr", "t_max": 500.0, "ligand_conc": 0.5})
        assert cfg.model == SignalingModel.GPCR
        assert cfg.t_max == 500.0
        assert cfg.ligand_conc == 0.5

    def test_all_fields_parsing(self):
        pattern = SignalTransductionPattern()
        cfg = pattern._parse_config(
            {
                "model": "repressilator",
                "t_max": 100.0,
                "dt": 0.05,
                "E1_total": 0.2,
                "E2_total": 0.2,
                "MAPKK_total": 20.0,
                "MAPK_total": 20.0,
                "k1": 0.02,
                "k2": 0.2,
                "k3": 0.02,
                "k4": 0.2,
                "R_total": 2.0,
                "G_total": 2.0,
                "ligand_conc": 0.5,
                "stimulus_amp": 2.0,
                "stimulus_duration": 50.0,
                "adaptation_rate": 0.2,
                "n_genes": 4,
                "alpha": 500.0,
                "beta": 10.0,
                "n_hill": 3.0,
                "gamma": 2.0,
                "K": 2.0,
                "num_stimulus_levels": 15,
            }
        )
        assert cfg.model == SignalingModel.REPRESSILATOR
        assert cfg.t_max == 100.0
        assert cfg.alpha == 500.0
        assert cfg.n_genes == 4


# ═══════════════════════════════════════════════════════════════════
# Simulation Methods
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestMapkSimulation:
    async def test_mapk_basic(self):
        pattern = SignalTransductionPattern()
        pattern.config = SignalTransductionConfig(
            model=SignalingModel.MAPK_CASCADE,
            t_max=50.0,
            dt=0.5,
        )
        result = await pattern._mapk_simulation()
        assert "metrics" in result
        assert "logs" in result
        assert "time" in result
        assert "MAPK_PP" in result
        assert result["metrics"]["model"] == "mapk_cascade"
        assert result["metrics"]["final_MAPK_PP"] >= 0

    async def test_mapk_amplification(self):
        pattern = SignalTransductionPattern()
        pattern.config = SignalTransductionConfig(
            model=SignalingModel.MAPK_CASCADE,
            t_max=50.0,
            dt=0.5,
            E1_total=0.1,
            MAPKK_total=10.0,
            MAPK_total=10.0,
        )
        result = await pattern._mapk_simulation()
        metrics = result["metrics"]
        assert "amplification_factor" in metrics
        assert "hill_coefficient" in metrics

    async def test_mapk_dose_response(self):
        pattern = SignalTransductionPattern()
        pattern.config = SignalTransductionConfig(
            model=SignalingModel.MAPK_CASCADE,
            num_stimulus_levels=5,
        )
        dose = pattern._mapk_dose_response()
        assert "stimulus_levels" in dose
        assert "responses" in dose
        assert len(dose["stimulus_levels"]) == 5
        assert len(dose["responses"]) == 5


@pytest.mark.asyncio
class TestGpcrSimulation:
    async def test_gpcr_basic(self):
        pattern = SignalTransductionPattern()
        pattern.config = SignalTransductionConfig(
            model=SignalingModel.GPCR,
            t_max=50.0,
            dt=0.5,
        )
        result = await pattern._gpcr_simulation()
        assert "metrics" in result
        assert result["metrics"]["model"] == "gpcr"
        assert 0 <= result["metrics"]["final_receptor_occupancy"] <= 1


@pytest.mark.asyncio
class TestAdaptationSimulation:
    async def test_adaptation_basic(self):
        pattern = SignalTransductionPattern()
        pattern.config = SignalTransductionConfig(
            model=SignalingModel.ADAPTATION,
            t_max=200.0,
            dt=1.0,
            stimulus_amp=1.0,
            stimulus_duration=50.0,
        )
        result = await pattern._adaptation_simulation()
        assert "metrics" in result
        assert "adaptation_quality" in result["metrics"]
        assert result["metrics"]["model"] == "adaptation"
        assert result["metrics"]["peak_response"] >= 0


@pytest.mark.asyncio
class TestRepressilatorSimulation:
    async def test_repressilator_basic(self):
        pattern = SignalTransductionPattern()
        pattern.config = SignalTransductionConfig(
            model=SignalingModel.REPRESSILATOR,
            t_max=100.0,
            dt=0.5,
            n_genes=3,
            alpha=250.0,
            beta=5.0,
        )
        result = await pattern._repressilator_simulation()
        assert "metrics" in result
        assert result["metrics"]["model"] == "repressilator"
        assert result["metrics"]["num_genes"] == 3

    async def test_repressilator_no_oscillation_short(self):
        pattern = SignalTransductionPattern()
        pattern.config = SignalTransductionConfig(
            model=SignalingModel.REPRESSILATOR,
            t_max=10.0,
            dt=0.5,
        )
        result = await pattern._repressilator_simulation()
        # Short simulation may not show oscillation
        assert "metrics" in result


@pytest.mark.asyncio
class TestToggleSwitchSimulation:
    async def test_toggle_switch_basic(self):
        pattern = SignalTransductionPattern()
        pattern.config = SignalTransductionConfig(
            model=SignalingModel.TOGGLE_SWITCH,
            t_max=100.0,
            dt=0.5,
            alpha=250.0,
            n_hill=2.0,
        )
        result = await pattern._toggle_switch_simulation()
        assert "metrics" in result
        assert result["metrics"]["model"] == "toggle_switch"
        assert "bistable" in result["metrics"]
        assert "steady_state" in result["metrics"]


# ═══════════════════════════════════════════════════════════════════
# Helper Methods
# ═══════════════════════════════════════════════════════════════════


class TestEstimateHillCoefficient:
    def test_normal_curve(self):
        pattern = SignalTransductionPattern()
        dose = {
            "stimulus_levels": [0.001, 0.01, 0.1, 1.0],
            "responses": [0.01, 0.1, 0.5, 0.99],
        }
        n = pattern._estimate_hill_coefficient(dose)
        assert n > 0

    def test_flat_response(self):
        pattern = SignalTransductionPattern()
        dose = {
            "stimulus_levels": [0.001, 0.01, 0.1, 1.0],
            "responses": [0.0, 0.0, 0.0, 0.0],
        }
        n = pattern._estimate_hill_coefficient(dose)
        assert n == 1.0

    def test_insufficient_points(self):
        pattern = SignalTransductionPattern()
        dose = {
            "stimulus_levels": [0.1, 1.0],
            "responses": [0.1, 0.9],
        }
        n = pattern._estimate_hill_coefficient(dose)
        assert n == 1.0


class TestFindPeaks:
    def test_find_peaks_sine(self):
        pattern = SignalTransductionPattern()
        t = np.linspace(0, 10, 1000)
        signal = np.sin(2 * np.pi * t)
        peaks = pattern._find_peaks(t, signal)
        assert len(peaks) > 0

    def test_find_peaks_flat(self):
        pattern = SignalTransductionPattern()
        t = np.linspace(0, 10, 100)
        signal = np.ones_like(t)
        peaks = pattern._find_peaks(t, signal)
        assert len(peaks) == 0


# ═══════════════════════════════════════════════════════════════════
# Confidence Calculation
# ═══════════════════════════════════════════════════════════════════


class TestCalculateConfidence:
    def test_mapk_confidence(self):
        pattern = SignalTransductionPattern()
        pattern.config = SignalTransductionConfig(model=SignalingModel.MAPK_CASCADE)
        results = {"metrics": {"amplification_factor": 2.0, "hill_coefficient": 3.0}}
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5

    def test_repressilator_confidence(self):
        pattern = SignalTransductionPattern()
        pattern.config = SignalTransductionConfig(model=SignalingModel.REPRESSILATOR)
        results = {"metrics": {"oscillation_detected": True}}
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5

    def test_toggle_confidence(self):
        pattern = SignalTransductionPattern()
        pattern.config = SignalTransductionConfig(model=SignalingModel.TOGGLE_SWITCH)
        results = {"metrics": {"bistable": True}}
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5

    def test_adaptation_confidence(self):
        pattern = SignalTransductionPattern()
        pattern.config = SignalTransductionConfig(model=SignalingModel.ADAPTATION)
        results = {"metrics": {"adaptation_quality": "perfect"}}
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5

    def test_low_confidence(self):
        pattern = SignalTransductionPattern()
        pattern.config = SignalTransductionConfig(model=SignalingModel.MAPK_CASCADE)
        results = {"metrics": {}}
        confidence = pattern._calculate_confidence(results)
        assert confidence < 0.5


# ═══════════════════════════════════════════════════════════════════
# Resource Estimation
# ═══════════════════════════════════════════════════════════════════


class TestEstimateResources:
    def test_default_params(self):
        pattern = SignalTransductionPattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert "gpu_required" in resources
        assert "estimated_time_seconds" in resources
        assert resources["gpu_required"] is False

    def test_custom_params(self):
        pattern = SignalTransductionPattern()
        h = Hypothesis(parameters={"t_max": 5000.0})
        resources = pattern.estimate_resources(h)
        assert resources["estimated_time_seconds"] > 0


# ═══════════════════════════════════════════════════════════════════
# run() Integration
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRun:
    async def test_run_mapk(self):
        pattern = SignalTransductionPattern()
        h = Hypothesis(title="MAPK signaling", description="test")
        config = {"model": "mapk_cascade", "t_max": 50.0, "dt": 0.5}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("st_")
        assert "final_MAPK_PP" in result.metrics or len(result.logs) > 0

    async def test_run_gpcr(self):
        pattern = SignalTransductionPattern()
        h = Hypothesis(title="GPCR dynamics", description="test")
        config = {"model": "gpcr", "t_max": 50.0, "dt": 0.5}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_adaptation(self):
        pattern = SignalTransductionPattern()
        h = Hypothesis(title="Cellular adaptation", description="test")
        config = {"model": "adaptation", "t_max": 100.0, "dt": 1.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_repressilator(self):
        pattern = SignalTransductionPattern()
        h = Hypothesis(title="Genetic oscillator", description="test")
        config = {"model": "repressilator", "t_max": 50.0, "dt": 0.5}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_toggle_switch(self):
        pattern = SignalTransductionPattern()
        h = Hypothesis(title="Toggle switch", description="test")
        config = {"model": "toggle_switch", "t_max": 50.0, "dt": 0.5}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_logs_present(self):
        pattern = SignalTransductionPattern()
        h = Hypothesis(title="Signaling", description="test")
        config = {"model": "mapk_cascade", "t_max": 50.0, "dt": 0.5}
        result = await pattern.run(h, config)
        assert len(result.logs) > 0

    async def test_run_failure_handling(self):
        pattern = SignalTransductionPattern()
        h = Hypothesis(title="Signaling", description="test")
        with patch.object(pattern, "_parse_config", side_effect=ValueError("test error")):
            result = await pattern.run(h, {"model": "mapk_cascade", "t_max": 50.0})
            assert result.status == SimulationStatus.FAILED
            assert "test error" in result.error_message


# ═══════════════════════════════════════════════════════════════════
# get_metadata
# ═══════════════════════════════════════════════════════════════════


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = SignalTransductionPattern.get_metadata()
        assert meta["id"] == "signal_transduction"
        assert meta["name"] == "Signal Transduction"
        assert meta["category"] == "biology"
        assert "parameters" in meta
        assert "references" in meta
        assert len(meta["references"]) > 0


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestEdgeCases:
    async def test_zero_t_max(self):
        pattern = SignalTransductionPattern()
        h = Hypothesis(title="Signaling", description="test")
        config = {"model": "mapk_cascade", "t_max": 0.0}
        result = await pattern.run(h, config)
        # Zero t_max causes solve_ivp to return empty solution -> fails
        assert result.status == SimulationStatus.FAILED

    async def test_very_small_dt(self):
        pattern = SignalTransductionPattern()
        h = Hypothesis(title="Signaling", description="test")
        config = {"model": "mapk_cascade", "t_max": 10.0, "dt": 0.01}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_empty_config(self):
        pattern = SignalTransductionPattern()
        h = Hypothesis(title="MAPK cascade", description="test")
        result = await pattern.run(h, {})
        assert result.status == SimulationStatus.COMPLETED

    async def test_single_gene_repressilator(self):
        pattern = SignalTransductionPattern()
        h = Hypothesis(title="Oscillator", description="test")
        config = {"model": "repressilator", "n_genes": 1, "t_max": 20.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
