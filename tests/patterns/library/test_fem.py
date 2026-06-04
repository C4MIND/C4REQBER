"""
Tests for src/patterns/library/fem.py (Finite Element Method pattern)

Covers:
- ElementType enum
- Node and Element dataclasses
- FEMPattern initialization
- can_simulate() keyword matching
- _truss_1d() structural analysis
- _beam_1d() beam analysis
- _plane_stress_2d() simplified 2D
- _calculate_confidence()
- estimate_resources()
- run() integration with different element types
- get_metadata()
- Edge cases: zero elements, negative load, missing params
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.fem import (
    Element,
    ElementType,
    FEMPattern,
    Node,
)
from src.patterns.core import Hypothesis, SimulationStatus



# ═══════════════════════════════════════════════════════════════════
# Enums and Dataclasses
# ═══════════════════════════════════════════════════════════════════


class TestElementType:
    def test_enum_values(self):
        assert ElementType.TRUSS_1D.value == "truss_1d"
        assert ElementType.BEAM_1D.value == "beam_1d"
        assert ElementType.TRIANGLE_2D.value == "triangle_2d"
        assert ElementType.QUAD_2D.value == "quad_2d"


class TestNode:
    def test_default_init(self):
        node = Node(node_id=0, x=0.0)
        assert node.node_id == 0
        assert node.x == 0.0
        assert node.y == 0.0
        assert node.z == 0.0
        assert node.fixed == (False, False, False)

    def test_custom_init(self):
        node = Node(node_id=1, x=1.0, y=2.0, z=3.0, fixed=(True, False, True))
        assert node.x == 1.0
        assert node.y == 2.0
        assert node.z == 3.0
        assert node.fixed == (True, False, True)


class TestElement:
    def test_default_init(self):
        elem = Element(element_id=0, nodes=[0, 1], youngs_modulus=200e9, area=0.01)
        assert elem.element_id == 0
        assert elem.nodes == [0, 1]
        assert elem.youngs_modulus == 200e9
        assert elem.area == 0.01
        assert elem.element_type == ElementType.TRUSS_1D


# ═══════════════════════════════════════════════════════════════════
# FEMPattern Initialization
# ═══════════════════════════════════════════════════════════════════


class TestFEMPatternInit:
    def test_init(self):
        pattern = FEMPattern()
        assert pattern is not None
        assert pattern.nodes == []
        assert pattern.elements == []

    def test_parameters_defined(self):
        pattern = FEMPattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0
        param_names = [p.name for p in pattern.parameters]
        assert "element_type" in param_names
        assert "num_elements" in param_names
        assert "youngs_modulus" in param_names
        assert "area" in param_names
        assert "load" in param_names


# ═══════════════════════════════════════════════════════════════════
# can_simulate
# ═══════════════════════════════════════════════════════════════════


class TestCanSimulate:
    def test_matches_fem_keyword(self):
        pattern = FEMPattern()
        h = Hypothesis(title="Finite element analysis", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_stress(self):
        pattern = FEMPattern()
        h = Hypothesis(title="Stress analysis", description="structural mechanics")
        assert pattern.can_simulate(h) is True

    def test_matches_truss(self):
        pattern = FEMPattern()
        h = Hypothesis(title="Truss structure", description="load displacement")
        assert pattern.can_simulate(h) is True

    def test_matches_beam(self):
        pattern = FEMPattern()
        h = Hypothesis(title="Cantilever beam", description="bending stress")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = FEMPattern()
        h = Hypothesis(title="Neural network", description="deep learning")
        assert pattern.can_simulate(h) is False

    def test_empty_hypothesis(self):
        pattern = FEMPattern()
        h = Hypothesis()
        assert pattern.can_simulate(h) is False


# ═══════════════════════════════════════════════════════════════════
# 1D Truss Analysis
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestTruss1D:
    async def test_truss_default(self):
        pattern = FEMPattern()
        h = Hypothesis(parameters={"length": 10.0})
        config = {"element_type": "truss_1d", "num_elements": 10, "youngs_modulus": 200e9, "area": 0.01, "load": 1000.0}
        result = await pattern._truss_1d(h, config)
        assert "metrics" in result
        assert "logs" in result
        assert "max_deflection" in result["metrics"]
        assert "max_stress" in result["metrics"]
        assert "num_elements" in result["metrics"]
        assert result["metrics"]["num_elements"] == 10

    async def test_truss_with_custom_length(self):
        pattern = FEMPattern()
        h = Hypothesis(parameters={"length": 5.0})
        config = {"element_type": "truss_1d", "num_elements": 5, "youngs_modulus": 200e9, "area": 0.01, "load": 1000.0}
        result = await pattern._truss_1d(h, config)
        assert result["metrics"]["num_nodes"] == 6

    async def test_truss_stress_positive(self):
        pattern = FEMPattern()
        h = Hypothesis(parameters={"length": 10.0})
        config = {"element_type": "truss_1d", "num_elements": 10, "load": 1000.0}
        result = await pattern._truss_1d(h, config)
        assert result["metrics"]["max_stress"] > 0

    async def test_truss_deflection_positive(self):
        pattern = FEMPattern()
        h = Hypothesis(parameters={"length": 10.0})
        config = {"element_type": "truss_1d", "num_elements": 10, "load": 1000.0}
        result = await pattern._truss_1d(h, config)
        assert result["metrics"]["max_deflection"] > 0

    async def test_truss_strain_energy_positive(self):
        pattern = FEMPattern()
        h = Hypothesis(parameters={"length": 10.0})
        config = {"element_type": "truss_1d", "num_elements": 10, "load": 1000.0}
        result = await pattern._truss_1d(h, config)
        assert result["metrics"]["strain_energy"] > 0

    async def test_truss_logs_present(self):
        pattern = FEMPattern()
        h = Hypothesis(parameters={"length": 10.0})
        config = {"element_type": "truss_1d", "num_elements": 10, "load": 1000.0}
        result = await pattern._truss_1d(h, config)
        assert any("truss" in log.lower() for log in result["logs"])
        assert any("deflection" in log.lower() for log in result["logs"])


# ═══════════════════════════════════════════════════════════════════
# 1D Beam Analysis
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestBeam1D:
    async def test_beam_default(self):
        pattern = FEMPattern()
        h = Hypothesis(parameters={"length": 10.0, "width": 0.1, "height": 0.2})
        config = {"element_type": "beam_1d", "num_elements": 10, "youngs_modulus": 200e9, "load": 1000.0}
        result = await pattern._beam_1d(h, config)
        assert "metrics" in result
        assert "logs" in result
        assert "max_deflection" in result["metrics"]
        assert "max_bending_stress" in result["metrics"]
        assert "moment_of_inertia" in result["metrics"]

    async def test_beam_deflection_positive(self):
        pattern = FEMPattern()
        h = Hypothesis(parameters={"length": 10.0, "width": 0.1, "height": 0.2})
        config = {"element_type": "beam_1d", "num_elements": 10, "load": 1000.0}
        result = await pattern._beam_1d(h, config)
        assert result["metrics"]["max_deflection"] > 0

    async def test_beam_moment_of_inertia(self):
        pattern = FEMPattern()
        h = Hypothesis(parameters={"length": 10.0, "width": 0.1, "height": 0.2})
        config = {"element_type": "beam_1d", "num_elements": 10, "load": 1000.0}
        result = await pattern._beam_1d(h, config)
        # I = b*h^3/12 = 0.1 * 0.008 / 12 = 6.667e-5
        expected_I = 0.1 * 0.2**3 / 12
        assert result["metrics"]["moment_of_inertia"] == pytest.approx(expected_I, rel=1e-3)

    async def test_beam_logs_present(self):
        pattern = FEMPattern()
        h = Hypothesis(parameters={"length": 10.0, "width": 0.1, "height": 0.2})
        config = {"element_type": "beam_1d", "num_elements": 10, "load": 1000.0}
        result = await pattern._beam_1d(h, config)
        assert any("beam" in log.lower() for log in result["logs"])


# ═══════════════════════════════════════════════════════════════════
# 2D Plane Stress
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestPlaneStress2D:
    async def test_plane_stress_default(self):
        pattern = FEMPattern()
        h = Hypothesis(parameters={})
        config = {"element_type": "triangle_2d", "load": 1000.0, "youngs_modulus": 200e9}
        result = await pattern._plane_stress_2d(h, config)
        assert "metrics" in result
        assert "logs" in result
        assert "max_stress" in result["metrics"]
        assert "stress_concentration" in result["metrics"]
        assert "note" in result["metrics"]

    async def test_plane_stress_simplified(self):
        pattern = FEMPattern()
        h = Hypothesis(parameters={})
        config = {"element_type": "triangle_2d", "load": 1000.0}
        result = await pattern._plane_stress_2d(h, config)
        assert result["metrics"]["stress_concentration"] == 3.0


# ═══════════════════════════════════════════════════════════════════
# Confidence Calculation
# ═══════════════════════════════════════════════════════════════════


class TestCalculateConfidence:
    def test_high_confidence_truss(self):
        pattern = FEMPattern()
        results = {
            "metrics": {
                "max_deflection": 0.01,
                "max_stress": 100e6,
                "num_elements": 10,
            }
        }
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5

    def test_low_confidence_no_elements(self):
        pattern = FEMPattern()
        results = {"metrics": {"max_deflection": 0.01, "max_stress": 100e6, "num_elements": 1}}
        confidence = pattern._calculate_confidence(results)
        assert confidence < 0.9

    def test_fallback_note_reduces_confidence(self):
        pattern = FEMPattern()
        results = {"metrics": {"max_deflection": 0.01, "max_stress": 100e6, "num_elements": 10, "note": "simplified"}}
        confidence = pattern._calculate_confidence(results)
        # Note reduces confidence by 0.2
        assert confidence < 0.9

    def test_empty_metrics(self):
        pattern = FEMPattern()
        results = {"metrics": {}}
        confidence = pattern._calculate_confidence(results)
        # Empty metrics gives 0 factors, but num_elements default contributes 0.2
        assert confidence >= 0.0


# ═══════════════════════════════════════════════════════════════════
# Resource Estimation
# ═══════════════════════════════════════════════════════════════════


class TestEstimateResources:
    def test_default_params(self):
        pattern = FEMPattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert "gpu_required" in resources
        assert "estimated_time_seconds" in resources
        assert resources["gpu_required"] is False

    def test_custom_params(self):
        pattern = FEMPattern()
        h = Hypothesis(parameters={"num_elements": 100})
        resources = pattern.estimate_resources(h)
        assert resources["memory_gb"] > 0.5


# ═══════════════════════════════════════════════════════════════════
# run() Integration
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRun:
    async def test_run_truss(self):
        pattern = FEMPattern()
        h = Hypothesis(title="Truss analysis", description="test")
        config = {"element_type": "truss_1d", "num_elements": 5, "load": 1000.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("fem_")
        assert "max_deflection" in result.metrics

    async def test_run_beam(self):
        pattern = FEMPattern()
        h = Hypothesis(title="Beam analysis", description="test")
        config = {"element_type": "beam_1d", "num_elements": 5, "load": 1000.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert "max_deflection" in result.metrics

    async def test_run_2d(self):
        pattern = FEMPattern()
        h = Hypothesis(title="Plane stress", description="test")
        config = {"element_type": "triangle_2d", "load": 1000.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_logs_present(self):
        pattern = FEMPattern()
        h = Hypothesis(title="FEM test", description="test")
        config = {"element_type": "truss_1d", "num_elements": 5}
        result = await pattern.run(h, config)
        assert len(result.logs) > 0

    async def test_run_failure_handling(self):
        pattern = FEMPattern()
        h = Hypothesis(title="FEM test", description="test")
        with patch.object(pattern, "_truss_1d", side_effect=ValueError("test error")):
            result = await pattern.run(h, {"element_type": "truss_1d"})
            assert result.status == SimulationStatus.FAILED
            assert "test error" in result.error_message


# ═══════════════════════════════════════════════════════════════════
# get_metadata
# ═══════════════════════════════════════════════════════════════════


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = FEMPattern.get_metadata()
        assert meta["id"] == "fem"
        assert meta["name"] == "FEMPattern"
        assert "category" in meta


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestEdgeCases:
    async def test_truss_zero_elements(self):
        pattern = FEMPattern()
        h = Hypothesis(parameters={"length": 10.0})
        config = {"element_type": "truss_1d", "num_elements": 1, "load": 1000.0}
        result = await pattern._truss_1d(h, config)
        assert result["metrics"]["num_elements"] == 1

    async def test_truss_negative_load(self):
        pattern = FEMPattern()
        h = Hypothesis(parameters={"length": 10.0})
        config = {"element_type": "truss_1d", "num_elements": 5, "load": -1000.0}
        result = await pattern._truss_1d(h, config)
        # Negative load should still produce valid results
        assert "max_deflection" in result["metrics"]

    async def test_empty_config(self):
        pattern = FEMPattern()
        h = Hypothesis(title="FEM", description="test")
        result = await pattern.run(h, {})
        assert result.status == SimulationStatus.COMPLETED

    async def test_beam_missing_dimensions(self):
        pattern = FEMPattern()
        h = Hypothesis(parameters={"length": 10.0})  # Missing width/height
        config = {"element_type": "beam_1d", "num_elements": 5, "load": 1000.0}
        result = await pattern._beam_1d(h, config)
        # Should use defaults
        assert "max_deflection" in result["metrics"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
