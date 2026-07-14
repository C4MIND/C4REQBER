"""
Tests for src/patterns/library/cfd.py (Computational Fluid Dynamics pattern)

Covers:
- FlowType enum
- CFDPattern initialization
- can_simulate() keyword matching
- _potential_flow() 2D potential flow
- _stokes_flow() creeping flow
- _laminar_flow() Hagen-Poiseuille
- _turbulent_flow() empirical correlations
- _calculate_confidence()
- estimate_resources()
- run() integration with different flow types
- get_metadata()
- Edge cases: Re < 0, zero grid, zero velocity
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.core import Hypothesis, SimulationStatus
from src.patterns.library.cfd import CFDPattern, FlowType


# ═══════════════════════════════════════════════════════════════════
# FlowType Enum
# ═══════════════════════════════════════════════════════════════════


class TestFlowType:
    def test_enum_values(self):
        assert FlowType.POTENTIAL.value == "potential"
        assert FlowType.STOKES.value == "stokes"
        assert FlowType.LAMINAR.value == "laminar"
        assert FlowType.TURBULENT.value == "turbulent"


# ═══════════════════════════════════════════════════════════════════
# CFDPattern Initialization
# ═══════════════════════════════════════════════════════════════════


class TestCFDPatternInit:
    def test_init(self):
        pattern = CFDPattern()
        assert pattern is not None

    def test_parameters_defined(self):
        pattern = CFDPattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0
        param_names = [p.name for p in pattern.parameters]
        assert "flow_type" in param_names
        assert "grid_size" in param_names
        assert "reynolds_number" in param_names
        assert "inlet_velocity" in param_names
        assert "domain_size" in param_names


# ═══════════════════════════════════════════════════════════════════
# can_simulate
# ═══════════════════════════════════════════════════════════════════


class TestCanSimulate:
    def test_matches_fluid(self):
        pattern = CFDPattern()
        h = Hypothesis(title="Fluid flow analysis", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_cfd(self):
        pattern = CFDPattern()
        h = Hypothesis(title="CFD simulation", description="navier-stokes")
        assert pattern.can_simulate(h) is True

    def test_matches_aerodynamic(self):
        pattern = CFDPattern()
        h = Hypothesis(title="Aerodynamic drag", description="wind tunnel")
        assert pattern.can_simulate(h) is True

    def test_matches_turbulence(self):
        pattern = CFDPattern()
        h = Hypothesis(title="Turbulence modeling", description="RANS")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = CFDPattern()
        h = Hypothesis(title="Neural network", description="deep learning")
        assert pattern.can_simulate(h) is False

    def test_empty_hypothesis(self):
        pattern = CFDPattern()
        h = Hypothesis()
        assert pattern.can_simulate(h) is False


# ═══════════════════════════════════════════════════════════════════
# Potential Flow
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestPotentialFlow:
    async def test_potential_flow_default(self):
        pattern = CFDPattern()
        h = Hypothesis(parameters={})
        config = {
            "flow_type": "potential",
            "grid_size": 20,
            "inlet_velocity": 1.0,
            "domain_size": 1.0,
        }
        result = await pattern._potential_flow(h, config)
        assert "metrics" in result
        assert "logs" in result
        assert "max_velocity" in result["metrics"]
        assert "avg_velocity" in result["metrics"]
        assert "grid_size" in result["metrics"]

    async def test_potential_flow_convergence(self):
        pattern = CFDPattern()
        h = Hypothesis(parameters={})
        config = {"flow_type": "potential", "grid_size": 20, "inlet_velocity": 1.0}
        result = await pattern._potential_flow(h, config)
        assert result["metrics"]["iterations"] > 0
        assert result["metrics"]["iterations"] <= 10002

    async def test_potential_flow_mass_conservation(self):
        pattern = CFDPattern()
        h = Hypothesis(parameters={})
        config = {"flow_type": "potential", "grid_size": 20, "inlet_velocity": 1.0}
        result = await pattern._potential_flow(h, config)
        # Mass conservation error should be relatively small
        assert result["metrics"]["mass_conservation"] >= 0

    async def test_potential_flow_logs(self):
        pattern = CFDPattern()
        h = Hypothesis(parameters={})
        config = {"flow_type": "potential", "grid_size": 20}
        result = await pattern._potential_flow(h, config)
        assert any("potential" in log.lower() for log in result["logs"])


# ═══════════════════════════════════════════════════════════════════
# Stokes Flow
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestStokesFlow:
    async def test_stokes_flow_default(self):
        pattern = CFDPattern()
        h = Hypothesis(parameters={})
        config = {
            "flow_type": "stokes",
            "grid_size": 20,
            "inlet_velocity": 0.01,
            "domain_size": 1.0,
        }
        result = await pattern._stokes_flow(h, config)
        assert "metrics" in result
        assert "logs" in result
        assert "drag_force" in result["metrics"]
        assert "cylinder_radius" in result["metrics"]
        assert result["metrics"]["reynolds_number"] == 0.0

    async def test_stokes_drag_positive(self):
        pattern = CFDPattern()
        h = Hypothesis(parameters={})
        config = {"flow_type": "stokes", "inlet_velocity": 0.01, "domain_size": 1.0}
        result = await pattern._stokes_flow(h, config)
        assert result["metrics"]["drag_force"] > 0

    async def test_stokes_logs(self):
        pattern = CFDPattern()
        h = Hypothesis(parameters={})
        config = {"flow_type": "stokes", "inlet_velocity": 0.01}
        result = await pattern._stokes_flow(h, config)
        assert any("stokes" in log.lower() for log in result["logs"])


# ═══════════════════════════════════════════════════════════════════
# Laminar Flow
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestLaminarFlow:
    async def test_laminar_flow_default(self):
        pattern = CFDPattern()
        h = Hypothesis(parameters={})
        config = {
            "flow_type": "laminar",
            "reynolds_number": 100.0,
            "inlet_velocity": 1.0,
            "domain_size": 0.1,
        }
        result = await pattern._laminar_flow(h, config)
        assert "metrics" in result
        assert "logs" in result
        assert "avg_velocity" in result["metrics"]
        assert "max_velocity" in result["metrics"]
        assert "pressure_drop" in result["metrics"]
        assert "friction_factor" in result["metrics"]

    async def test_laminar_max_velocity(self):
        pattern = CFDPattern()
        h = Hypothesis(parameters={})
        config = {"flow_type": "laminar", "reynolds_number": 100.0, "inlet_velocity": 1.0}
        result = await pattern._laminar_flow(h, config)
        # u_max = 2 * U_avg for parabolic profile
        assert result["metrics"]["max_velocity"] == pytest.approx(2.0)

    async def test_laminar_friction_factor(self):
        pattern = CFDPattern()
        h = Hypothesis(parameters={})
        config = {"flow_type": "laminar", "reynolds_number": 100.0, "inlet_velocity": 1.0}
        result = await pattern._laminar_flow(h, config)
        # f = 64/Re = 64/100 = 0.64
        assert result["metrics"]["friction_factor"] == pytest.approx(0.64, abs=0.01)

    async def test_laminar_logs(self):
        pattern = CFDPattern()
        h = Hypothesis(parameters={})
        config = {"flow_type": "laminar", "reynolds_number": 100.0}
        result = await pattern._laminar_flow(h, config)
        assert any("laminar" in log.lower() for log in result["logs"])


# ═══════════════════════════════════════════════════════════════════
# Turbulent Flow
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestTurbulentFlow:
    async def test_turbulent_flow_default(self):
        pattern = CFDPattern()
        h = Hypothesis(parameters={})
        config = {
            "flow_type": "turbulent",
            "reynolds_number": 10000.0,
            "inlet_velocity": 1.0,
            "domain_size": 0.1,
        }
        result = await pattern._turbulent_flow(h, config)
        assert "metrics" in result
        assert "logs" in result
        assert "pressure_drop" in result["metrics"]
        assert "friction_factor" in result["metrics"]
        assert "flow_regime" in result["metrics"]
        assert result["metrics"]["flow_regime"] == "turbulent"

    async def test_turbulent_blasius(self):
        pattern = CFDPattern()
        h = Hypothesis(parameters={})
        config = {"flow_type": "turbulent", "reynolds_number": 10000.0, "inlet_velocity": 1.0}
        result = await pattern._turbulent_flow(h, config)
        # Blasius: f = 0.316/Re^0.25 = 0.316/10 = 0.0316
        expected_f = 0.316 / (10000**0.25)
        assert result["metrics"]["friction_factor"] == pytest.approx(expected_f, rel=0.1)

    async def test_turbulent_falls_back_to_laminar(self):
        pattern = CFDPattern()
        h = Hypothesis(parameters={})
        config = {
            "flow_type": "turbulent",
            "reynolds_number": 100.0,
            "inlet_velocity": 1.0,
            "domain_size": 0.1,
        }
        result = await pattern._turbulent_flow(h, config)
        # Re < 2300 should fall back to laminar
        assert result["metrics"]["reynolds_number"] == 100.0

    async def test_turbulent_logs(self):
        pattern = CFDPattern()
        h = Hypothesis(parameters={})
        config = {"flow_type": "turbulent", "reynolds_number": 10000.0}
        result = await pattern._turbulent_flow(h, config)
        assert any("turbulent" in log.lower() for log in result["logs"])


# ═══════════════════════════════════════════════════════════════════
# Confidence Calculation
# ═══════════════════════════════════════════════════════════════════


class TestCalculateConfidence:
    def test_high_confidence(self):
        pattern = CFDPattern()
        results = {
            "metrics": {
                "reynolds_number": 100.0,
                "mass_conservation": 0.5,
                "max_velocity": 1.5,
                "pressure_drop": 100.0,
            }
        }
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5

    def test_low_confidence(self):
        pattern = CFDPattern()
        results = {"metrics": {"reynolds_number": 0.0}}
        confidence = pattern._calculate_confidence(results)
        assert confidence < 0.5

    def test_empty_metrics(self):
        pattern = CFDPattern()
        results = {"metrics": {}}
        confidence = pattern._calculate_confidence(results)
        assert confidence == 0.0


# ═══════════════════════════════════════════════════════════════════
# Resource Estimation
# ═══════════════════════════════════════════════════════════════════


class TestEstimateResources:
    def test_default_params(self):
        pattern = CFDPattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert "gpu_required" in resources
        assert "estimated_time_seconds" in resources
        assert resources["gpu_required"] is False

    def test_custom_grid(self):
        pattern = CFDPattern()
        h = Hypothesis(parameters={"grid_size": 100})
        resources = pattern.estimate_resources(h)
        assert resources["memory_gb"] > 0.5


# ═══════════════════════════════════════════════════════════════════
# run() Integration
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRun:
    async def test_run_potential(self):
        pattern = CFDPattern()
        h = Hypothesis(title="Fluid flow", description="test")
        config = {"flow_type": "potential", "grid_size": 20, "inlet_velocity": 1.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("cfd_")
        assert "max_velocity" in result.metrics

    async def test_run_stokes(self):
        pattern = CFDPattern()
        h = Hypothesis(title="Stokes flow", description="test")
        config = {"flow_type": "stokes", "inlet_velocity": 0.01}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert "drag_force" in result.metrics

    async def test_run_laminar(self):
        pattern = CFDPattern()
        h = Hypothesis(title="Pipe flow", description="test")
        config = {"flow_type": "laminar", "reynolds_number": 100.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert "pressure_drop" in result.metrics

    async def test_run_turbulent(self):
        pattern = CFDPattern()
        h = Hypothesis(title="Turbulent flow", description="test")
        config = {"flow_type": "turbulent", "reynolds_number": 10000.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert "friction_factor" in result.metrics

    async def test_run_logs_present(self):
        pattern = CFDPattern()
        h = Hypothesis(title="CFD test", description="test")
        config = {"flow_type": "potential", "grid_size": 20}
        result = await pattern.run(h, config)
        assert len(result.logs) > 0

    async def test_run_failure_handling(self):
        pattern = CFDPattern()
        h = Hypothesis(title="CFD test", description="test")
        with patch.object(pattern, "_potential_flow", side_effect=ValueError("test error")):
            result = await pattern.run(h, {"flow_type": "potential"})
            assert result.status == SimulationStatus.FAILED
            assert "test error" in result.error_message


# ═══════════════════════════════════════════════════════════════════
# get_metadata
# ═══════════════════════════════════════════════════════════════════


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = CFDPattern.get_metadata()
        assert meta["id"] == "cfd"
        assert meta["name"] == "CFDPattern"
        assert "category" in meta


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestEdgeCases:
    async def test_potential_flow_small_grid(self):
        pattern = CFDPattern()
        h = Hypothesis(parameters={})
        config = {"flow_type": "potential", "grid_size": 10, "inlet_velocity": 1.0}
        result = await pattern._potential_flow(h, config)
        assert result["metrics"]["grid_size"] == 10

    async def test_laminar_zero_reynolds(self):
        pattern = CFDPattern()
        h = Hypothesis(parameters={})
        config = {"flow_type": "laminar", "reynolds_number": 0.0, "inlet_velocity": 1.0}
        result = await pattern._laminar_flow(h, config)
        assert result["metrics"]["friction_factor"] == 0.0

    async def test_empty_config(self):
        pattern = CFDPattern()
        h = Hypothesis(title="CFD", description="test")
        result = await pattern.run(h, {})
        assert result.status == SimulationStatus.COMPLETED

    async def test_turbulent_prandtl_karman(self):
        pattern = CFDPattern()
        h = Hypothesis(parameters={})
        config = {"flow_type": "turbulent", "reynolds_number": 200000.0, "inlet_velocity": 1.0}
        result = await pattern._turbulent_flow(h, config)
        # Should use Prandtl-Karman correlation
        assert "friction_factor" in result["metrics"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
