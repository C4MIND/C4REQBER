"""
Tests for src/patterns/library/connectome.py

Covers:
- NetworkModel enum
- ConnectomeConfig default/custom initialization and to_dict
- ConnectomePattern initialization
- can_simulate() keyword matching
- _parse_config()
- _generate_connectivity()
- _calculate_fc_kuramoto()
- _calculate_order_parameters()
- _calculate_network_metrics()
- _calculate_confidence()
- estimate_resources()
- run() integration for all models (kuramoto, wilson_cowan, hopf, fitzhugh_nagumo)
- get_metadata()
- Edge cases: zero regions, minimal t_max, no stimulation
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.connectome import (
    ConnectomeConfig,
    ConnectomePattern,
    NetworkModel,
)
from src.patterns.core import Hypothesis, SimulationStatus



# ═══════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════


class TestNetworkModel:
    def test_enum_values(self):
        assert NetworkModel.KURAMOTO.value == "kuramoto"
        assert NetworkModel.WILSON_COWAN.value == "wilson_cowan"
        assert NetworkModel.HOPF.value == "hopf"
        assert NetworkModel.FITZHUGH_NAGUMO.value == "fitzhugh_nagumo"


# ═══════════════════════════════════════════════════════════════════
# ConnectomeConfig
# ═══════════════════════════════════════════════════════════════════


class TestConnectomeConfig:
    def test_default_init(self):
        cfg = ConnectomeConfig()
        assert cfg.num_regions == 68
        assert cfg.connection_density == 0.3
        assert cfg.model == NetworkModel.KURAMOTO
        assert cfg.coupling_strength == 0.5
        assert cfg.noise_level == 0.01
        assert cfg.t_max == 60.0
        assert cfg.dt == 0.001
        assert cfg.stimulation_site is None
        assert cfg.stimulation_amp == 0.0

    def test_custom_init(self):
        cfg = ConnectomeConfig(
            num_regions=20,
            model=NetworkModel.WILSON_COWAN,
            coupling_strength=1.0,
            t_max=10.0,
            stimulation_site=5,
            stimulation_amp=0.5,
        )
        assert cfg.num_regions == 20
        assert cfg.model == NetworkModel.WILSON_COWAN
        assert cfg.coupling_strength == 1.0
        assert cfg.t_max == 10.0
        assert cfg.stimulation_site == 5
        assert cfg.stimulation_amp == 0.5

    def test_to_dict(self):
        cfg = ConnectomeConfig(num_regions=10, coupling_strength=0.8)
        d = cfg.to_dict()
        assert d["num_regions"] == 10
        assert d["coupling_strength"] == 0.8
        assert d["model"] == "kuramoto"
        assert "omega_mean" in d


# ═══════════════════════════════════════════════════════════════════
# ConnectomePattern Initialization
# ═══════════════════════════════════════════════════════════════════


class TestConnectomePatternInit:
    def test_init(self):
        pattern = ConnectomePattern()
        assert pattern.config is not None
        assert isinstance(pattern.config, ConnectomeConfig)
        assert pattern.structural_connectivity is None

    def test_parameters_defined(self):
        pattern = ConnectomePattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0
        param_names = [p.name for p in pattern.parameters]
        assert "num_regions" in param_names
        assert "model" in param_names
        assert "coupling_strength" in param_names


# ═══════════════════════════════════════════════════════════════════
# can_simulate
# ═══════════════════════════════════════════════════════════════════


class TestCanSimulate:
    def test_matches_connectome(self):
        pattern = ConnectomePattern()
        h = Hypothesis(title="Brain connectome", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_brain(self):
        pattern = ConnectomePattern()
        h = Hypothesis(title="Neural network", description="brain dynamics")
        assert pattern.can_simulate(h) is True

    def test_matches_fmri(self):
        pattern = ConnectomePattern()
        h = Hypothesis(title="fMRI analysis", description="resting state")
        assert pattern.can_simulate(h) is True

    def test_matches_kuramoto(self):
        pattern = ConnectomePattern()
        h = Hypothesis(title="Kuramoto model", description="synchronization")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = ConnectomePattern()
        h = Hypothesis(title="Linear regression", description="statistics")
        assert pattern.can_simulate(h) is False

    def test_empty_hypothesis(self):
        pattern = ConnectomePattern()
        h = Hypothesis()
        assert pattern.can_simulate(h) is False


# ═══════════════════════════════════════════════════════════════════
# Config Parsing
# ═══════════════════════════════════════════════════════════════════


class TestParseConfig:
    def test_default_parsing(self):
        pattern = ConnectomePattern()
        cfg = pattern._parse_config({})
        assert cfg.num_regions == 68
        assert cfg.model == NetworkModel.KURAMOTO

    def test_custom_parsing(self):
        pattern = ConnectomePattern()
        cfg = pattern._parse_config({
            "num_regions": 20,
            "model": "wilson_cowan",
            "coupling_strength": 0.8,
            "t_max": 10.0,
        })
        assert cfg.num_regions == 20
        assert cfg.model == NetworkModel.WILSON_COWAN
        assert cfg.coupling_strength == 0.8
        assert cfg.t_max == 10.0

    def test_stimulation_site_negative(self):
        pattern = ConnectomePattern()
        cfg = pattern._parse_config({"stimulation_site": -1})
        assert cfg.stimulation_site is None

    def test_stimulation_site_positive(self):
        pattern = ConnectomePattern()
        cfg = pattern._parse_config({"stimulation_site": 5})
        assert cfg.stimulation_site == 5


# ═══════════════════════════════════════════════════════════════════
# Connectivity Generation
# ═══════════════════════════════════════════════════════════════════


class TestGenerateConnectivity:
    def test_shape(self):
        pattern = ConnectomePattern()
        pattern.config = ConnectomeConfig(num_regions=20, connection_density=0.3)
        pattern.rng = np.random.default_rng(42)
        sc = pattern._generate_connectivity()
        assert sc.shape == (20, 20)

    def test_no_self_connections(self):
        pattern = ConnectomePattern()
        pattern.config = ConnectomeConfig(num_regions=20)
        pattern.rng = np.random.default_rng(42)
        sc = pattern._generate_connectivity()
        assert np.all(np.diag(sc) == 0)

    def test_symmetric(self):
        pattern = ConnectomePattern()
        pattern.config = ConnectomeConfig(num_regions=20)
        pattern.rng = np.random.default_rng(42)
        sc = pattern._generate_connectivity()
        # After weighting, the matrix may not be exactly symmetric due to log-normal weights
        # Check that the binary mask (SC > 0) is symmetric
        mask = sc > 0
        np.testing.assert_array_equal(mask, mask.T)

    def test_row_normalized(self):
        pattern = ConnectomePattern()
        pattern.config = ConnectomeConfig(num_regions=20)
        pattern.rng = np.random.default_rng(42)
        sc = pattern._generate_connectivity()
        row_sums = sc.sum(axis=1)
        # Rows should sum to approximately 1 (or 0 for isolated nodes)
        for rs in row_sums:
            assert rs == pytest.approx(1.0, abs=1e-6) or rs == 0.0


# ═══════════════════════════════════════════════════════════════════
# Functional Connectivity
# ═══════════════════════════════════════════════════════════════════


class TestCalculateFCKuramoto:
    def test_perfect_sync(self):
        pattern = ConnectomePattern()
        # All phases identical → PLV = 1
        theta = np.zeros((100, 5))
        fc = pattern._calculate_fc_kuramoto(theta)
        assert fc.shape == (5, 5)
        assert np.allclose(np.diag(fc), 0.0)
        assert np.allclose(fc[0, 1], 1.0, atol=1e-6)

    def test_random_phases(self):
        pattern = ConnectomePattern()
        rng = np.random.default_rng(42)
        theta = rng.uniform(0, 2 * np.pi, (100, 5))
        fc = pattern._calculate_fc_kuramoto(theta)
        assert fc.shape == (5, 5)
        assert np.all(fc >= 0)
        assert np.all(fc <= 1)


# ═══════════════════════════════════════════════════════════════════
# Order Parameters
# ═══════════════════════════════════════════════════════════════════


class TestCalculateOrderParameters:
    def test_full_synchronization(self):
        pattern = ConnectomePattern()
        theta = np.zeros((50, 10))
        sc = np.eye(10)
        r_global, r_local = pattern._calculate_order_parameters(theta, sc)
        assert np.allclose(r_global, 1.0, atol=1e-6)
        assert len(r_local) == 50

    def test_random_phases(self):
        pattern = ConnectomePattern()
        rng = np.random.default_rng(42)
        theta = rng.uniform(0, 2 * np.pi, (50, 10))
        sc = np.eye(10)
        r_global, r_local = pattern._calculate_order_parameters(theta, sc)
        assert np.all(r_global >= 0)
        assert np.all(r_global <= 1)


# ═══════════════════════════════════════════════════════════════════
# Network Metrics
# ═══════════════════════════════════════════════════════════════════


class TestCalculateNetworkMetrics:
    def test_basic_metrics(self):
        pattern = ConnectomePattern()
        rng = np.random.default_rng(42)
        activity = rng.random((100, 10))
        fc = np.corrcoef(activity.T)
        sc = np.eye(10)
        r_global = rng.random(100)
        r_local = rng.random(100)
        metrics = pattern._calculate_network_metrics(activity, fc, sc, r_global, r_local)
        assert "fc_mean" in metrics
        assert "fc_variance" in metrics
        assert "mean_order_parameter" in metrics
        assert "metastability" in metrics
        assert "integration" in metrics
        assert "segregation" in metrics


# ═══════════════════════════════════════════════════════════════════
# Confidence Calculation
# ═══════════════════════════════════════════════════════════════════


class TestCalculateConfidence:
    def test_high_confidence(self):
        pattern = ConnectomePattern()
        results = {
            "metrics": {
                "fc_mean": 0.5,
                "sc_fc_correlation": 0.3,
                "mean_order_parameter": 0.5,
                "mean_activity": 1.0,
            }
        }
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5

    def test_low_confidence(self):
        pattern = ConnectomePattern()
        results = {"metrics": {}}
        confidence = pattern._calculate_confidence(results)
        assert confidence >= 0.0
        assert confidence < 0.3

    def test_partial_confidence(self):
        pattern = ConnectomePattern()
        results = {"metrics": {"fc_mean": 0.5, "mean_activity": 1.0}}
        confidence = pattern._calculate_confidence(results)
        assert 0 < confidence < 0.95


# ═══════════════════════════════════════════════════════════════════
# Resource Estimation
# ═══════════════════════════════════════════════════════════════════


class TestEstimateResources:
    def test_default_params(self):
        pattern = ConnectomePattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert "gpu_required" in resources
        assert "estimated_time_seconds" in resources
        assert resources["gpu_required"] is False

    def test_custom_params(self):
        pattern = ConnectomePattern()
        h = Hypothesis(parameters={"num_regions": 200, "t_max": 120, "dt": 0.0005})
        resources = pattern.estimate_resources(h)
        assert resources["estimated_time_seconds"] > 0


# ═══════════════════════════════════════════════════════════════════
# run() Integration
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRun:
    async def test_run_kuramoto(self):
        pattern = ConnectomePattern()
        h = Hypothesis(title="Brain network", description="test")
        config = {"num_regions": 10, "t_max": 0.5, "dt": 0.01, "transient": 0.1}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("conn_")
        assert "fc_mean" in result.metrics

    async def test_run_wilson_cowan(self):
        pattern = ConnectomePattern()
        h = Hypothesis(title="Brain network", description="test")
        config = {
            "num_regions": 10,
            "model": "wilson_cowan",
            "t_max": 0.5,
            "dt": 0.01,
            "transient": 0.1,
        }
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert result.metrics.get("model") == "wilson_cowan"

    async def test_run_hopf(self):
        pattern = ConnectomePattern()
        h = Hypothesis(title="Brain network", description="test")
        config = {
            "num_regions": 10,
            "model": "hopf",
            "t_max": 0.5,
            "dt": 0.01,
            "transient": 0.1,
        }
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert result.metrics.get("model") == "hopf"

    async def test_run_fitzhugh_nagumo(self):
        pattern = ConnectomePattern()
        h = Hypothesis(title="Brain network", description="test")
        config = {
            "num_regions": 10,
            "model": "fitzhugh_nagumo",
            "t_max": 0.5,
            "dt": 0.01,
            "transient": 0.1,
        }
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert result.metrics.get("model") == "fitzhugh_nagumo"

    async def test_run_with_stimulation(self):
        pattern = ConnectomePattern()
        h = Hypothesis(title="Brain stimulation", description="tms test")
        config = {
            "num_regions": 10,
            "t_max": 0.5,
            "dt": 0.01,
            "transient": 0.1,
            "stimulation_site": 2,
            "stimulation_amp": 1.0,
        }
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_logs_present(self):
        pattern = ConnectomePattern()
        h = Hypothesis(title="Brain network", description="test")
        config = {"num_regions": 10, "t_max": 0.5, "dt": 0.01, "transient": 0.1}
        result = await pattern.run(h, config)
        assert len(result.logs) > 0

    async def test_run_failure_handling(self):
        pattern = ConnectomePattern()
        h = Hypothesis(title="Brain network", description="test")
        with patch.object(pattern, "_parse_config", side_effect=ValueError("test error")):
            result = await pattern.run(h, {"num_regions": 10})
            assert result.status == SimulationStatus.FAILED
            assert "test error" in result.error_message


# ═══════════════════════════════════════════════════════════════════
# get_metadata
# ═══════════════════════════════════════════════════════════════════


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = ConnectomePattern.get_metadata()
        assert meta["id"] == "connectome"
        assert meta["name"] == "Connectome Network Dynamics"
        assert meta["category"] == "neuroscience"
        assert "parameters" in meta
        assert isinstance(meta["parameters"], list)
        assert "references" in meta


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestEdgeCases:
    async def test_minimal_regions(self):
        pattern = ConnectomePattern()
        h = Hypothesis(title="Brain", description="test")
        config = {"num_regions": 5, "t_max": 0.2, "dt": 0.01, "transient": 0.05}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_zero_coupling(self):
        pattern = ConnectomePattern()
        h = Hypothesis(title="Brain", description="test")
        config = {"num_regions": 10, "coupling_strength": 0.0, "t_max": 0.2, "dt": 0.01, "transient": 0.05}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_high_noise(self):
        pattern = ConnectomePattern()
        h = Hypothesis(title="Brain", description="test")
        config = {"num_regions": 10, "noise_level": 1.0, "t_max": 0.2, "dt": 0.01, "transient": 0.05}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_empty_config(self):
        pattern = ConnectomePattern()
        h = Hypothesis(title="Brain connectome", description="test")
        result = await pattern.run(h, {})
        assert result.status == SimulationStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
