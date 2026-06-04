"""
Tests for src/patterns/library/thermal.py (Thermal Analysis Pattern)

Covers:
- HeatTransferMode enum values
- ThermalPattern initialization
- can_simulate() keyword matching
- _steady_state_1d()
- _steady_state_2d()
- _transient_1d()
- _transient_2d()
- _calculate_confidence()
- estimate_resources()
- run() async integration
- Edge cases: extreme temperatures, small grids
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.thermal import ThermalPattern, HeatTransferMode
from src.patterns.core import Hypothesis, SimulationStatus



# ═══════════════════════════════════════════════════════════════════
# Enum Tests
# ═══════════════════════════════════════════════════════════════════


class TestHeatTransferMode:
    def test_conduction_value(self):
        assert HeatTransferMode.CONDUCTION.value == "conduction"

    def test_convection_value(self):
        assert HeatTransferMode.CONVECTION.value == "convection"

    def test_radiation_value(self):
        assert HeatTransferMode.RADIATION.value == "radiation"

    def test_combined_value(self):
        assert HeatTransferMode.COMBINED.value == "combined"


# ═══════════════════════════════════════════════════════════════════
# Initialization Tests
# ═══════════════════════════════════════════════════════════════════


class TestThermalPatternInit:
    def test_init(self):
        pattern = ThermalPattern()
        assert pattern is not None

    def test_parameters_defined(self):
        pattern = ThermalPattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0
        param_names = [p.name for p in pattern.parameters]
        assert "dimension" in param_names
        assert "analysis_type" in param_names
        assert "grid_size" in param_names
        assert "thermal_conductivity" in param_names


# ═══════════════════════════════════════════════════════════════════
# can_simulate Tests
# ═══════════════════════════════════════════════════════════════════


class TestCanSimulate:
    def test_matches_thermal(self):
        pattern = ThermalPattern()
        h = Hypothesis(title="Thermal analysis", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_heat(self):
        pattern = ThermalPattern()
        h = Hypothesis(title="Heat transfer", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_temperature(self):
        pattern = ThermalPattern()
        h = Hypothesis(title="Temperature distribution", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_conduction(self):
        pattern = ThermalPattern()
        h = Hypothesis(title="Heat conduction", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_convection(self):
        pattern = ThermalPattern()
        h = Hypothesis(title="Convective heat transfer", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_radiation(self):
        pattern = ThermalPattern()
        h = Hypothesis(title="Radiative heat transfer", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_cooling(self):
        pattern = ThermalPattern()
        h = Hypothesis(title="Cooling system design", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_heating(self):
        pattern = ThermalPattern()
        h = Hypothesis(title="Heating analysis", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_fourier(self):
        pattern = ThermalPattern()
        h = Hypothesis(title="Fourier heat equation", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_hotspot(self):
        pattern = ThermalPattern()
        h = Hypothesis(title="Hotspot analysis", description="heat sink")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = ThermalPattern()
        h = Hypothesis(title="Neural network", description="deep learning")
        assert pattern.can_simulate(h) is False


# ═══════════════════════════════════════════════════════════════════
# Core Methods Tests
# ═══════════════════════════════════════════════════════════════════


class TestCalculateConfidence:
    def test_good_simulation(self):
        pattern = ThermalPattern()
        results = {
            "metrics": {
                "max_temperature": 100.0,
                "min_temperature": 20.0,
                "iterations": 500,
                "thermal_conductivity": 200.0,
            }
        }
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5

    def test_extreme_temperature(self):
        pattern = ThermalPattern()
        results = {"metrics": {"max_temperature": 5000.0, "min_temperature": 20.0}}
        confidence = pattern._calculate_confidence(results)
        assert 0 <= confidence < 0.9

    def test_no_gradient(self):
        pattern = ThermalPattern()
        results = {"metrics": {"max_temperature": 50.0, "min_temperature": 50.0}}
        confidence = pattern._calculate_confidence(results)
        assert 0 <= confidence < 0.9

    def test_many_iterations(self):
        pattern = ThermalPattern()
        results = {"metrics": {"max_temperature": 100.0, "iterations": 20000}}
        confidence = pattern._calculate_confidence(results)
        assert 0 <= confidence < 0.9


# ═══════════════════════════════════════════════════════════════════
# Resource Estimation Tests
# ═══════════════════════════════════════════════════════════════════


class TestEstimateResources:
    def test_default_params(self):
        pattern = ThermalPattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert "gpu_required" in resources
        assert "estimated_time_seconds" in resources
        assert resources["gpu_required"] is False

    def test_transient_takes_longer(self):
        pattern = ThermalPattern()
        h_ss = Hypothesis(parameters={"analysis_type": "steady_state", "grid_size": 50})
        h_tr = Hypothesis(parameters={"analysis_type": "transient", "grid_size": 50})

        resources_ss = pattern.estimate_resources(h_ss)
        resources_tr = pattern.estimate_resources(h_tr)

        assert resources_tr["estimated_time_seconds"] > resources_ss["estimated_time_seconds"]


# ═══════════════════════════════════════════════════════════════════
# Run Integration Tests
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRun:
    async def test_run_default(self):
        pattern = ThermalPattern()
        h = Hypothesis(title="Thermal analysis", description="heat conduction")
        result = await pattern.run(h, {})
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("thermal_")

    async def test_run_steady_state_1d(self):
        pattern = ThermalPattern()
        h = Hypothesis(title="Thermal analysis", description="heat conduction")
        result = await pattern.run(h, {"analysis_type": "steady_state", "dimension": "1d"})
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_steady_state_2d(self):
        pattern = ThermalPattern()
        h = Hypothesis(title="Thermal analysis", description="heat conduction")
        result = await pattern.run(h, {"analysis_type": "steady_state", "dimension": "2d"})
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_transient_1d(self):
        pattern = ThermalPattern()
        h = Hypothesis(title="Thermal analysis", description="heat conduction")
        result = await pattern.run(h, {"analysis_type": "transient", "dimension": "1d"})
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_transient_2d(self):
        pattern = ThermalPattern()
        h = Hypothesis(title="Thermal analysis", description="heat conduction")
        result = await pattern.run(h, {"analysis_type": "transient", "dimension": "2d"})
        assert result.status == SimulationStatus.COMPLETED

    async def test_metrics_present(self):
        pattern = ThermalPattern()
        h = Hypothesis(title="Thermal analysis", description="heat conduction")
        result = await pattern.run(h, {})
        assert "max_temperature" in result.metrics
        assert "min_temperature" in result.metrics

    async def test_logs_present(self):
        pattern = ThermalPattern()
        h = Hypothesis(title="Thermal analysis", description="heat conduction")
        result = await pattern.run(h, {})
        assert len(result.logs) > 0


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestEdgeCases:
    async def test_small_grid(self):
        pattern = ThermalPattern()
        h = Hypothesis(title="Thermal analysis", description="heat conduction")
        result = await pattern.run(h, {"grid_size": 10})
        assert result.status == SimulationStatus.COMPLETED

    async def test_high_conductivity(self):
        pattern = ThermalPattern()
        h = Hypothesis(title="Thermal analysis", description="heat conduction")
        result = await pattern.run(h, {"thermal_conductivity": 1000.0})
        assert result.status == SimulationStatus.COMPLETED

    async def test_low_conductivity(self):
        pattern = ThermalPattern()
        h = Hypothesis(title="Thermal analysis", description="heat conduction")
        result = await pattern.run(h, {"thermal_conductivity": 0.1})
        assert result.status == SimulationStatus.COMPLETED

    async def test_high_heat_source(self):
        pattern = ThermalPattern()
        h = Hypothesis(title="Thermal analysis", description="heat conduction")
        result = await pattern.run(h, {"heat_source": 100000.0})
        assert result.status == SimulationStatus.COMPLETED

    async def test_extreme_temperatures(self):
        pattern = ThermalPattern()
        h = Hypothesis(title="Thermal analysis", description="heat conduction")
        result = await pattern.run(h, {"initial_temp": -50.0})
        assert result.status == SimulationStatus.COMPLETED

    async def test_short_simulation_time(self):
        pattern = ThermalPattern()
        h = Hypothesis(title="Thermal analysis", description="heat conduction")
        result = await pattern.run(h, {"analysis_type": "transient", "simulation_time": 1.0})
        assert result.status == SimulationStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
