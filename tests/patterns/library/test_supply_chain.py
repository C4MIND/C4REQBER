"""
Tests for src/patterns/library/supply_chain.py (Supply Chain Pattern)

Covers:
- SupplyChainPattern initialization
- can_simulate() keyword matching
- _simulate_supply_chain()
- _calculate_confidence()
- estimate_resources()
- run() async integration
- Edge cases: single echelon, extreme demand
"""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.core import Hypothesis, SimulationStatus
from src.patterns.library.supply_chain import SupplyChainPattern


# ═══════════════════════════════════════════════════════════════════
# Initialization Tests
# ═══════════════════════════════════════════════════════════════════


class TestSupplyChainPatternInit:
    def test_init(self):
        pattern = SupplyChainPattern()
        assert pattern is not None

    def test_parameters_defined(self):
        pattern = SupplyChainPattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0
        param_names = [p.name for p in pattern.parameters]
        assert "num_echelons" in param_names
        assert "periods" in param_names
        assert "demand_mean" in param_names
        assert "lead_time" in param_names
        assert "holding_cost" in param_names
        assert "shortage_cost" in param_names


# ═══════════════════════════════════════════════════════════════════
# can_simulate Tests
# ═══════════════════════════════════════════════════════════════════


class TestCanSimulate:
    def test_matches_supply_chain(self):
        pattern = SupplyChainPattern()
        h = Hypothesis(title="Supply chain optimization", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_inventory(self):
        pattern = SupplyChainPattern()
        h = Hypothesis(title="Inventory management", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_logistics(self):
        pattern = SupplyChainPattern()
        h = Hypothesis(title="Logistics planning", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_bullwhip(self):
        pattern = SupplyChainPattern()
        h = Hypothesis(title="Bullwhip effect analysis", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_eoq(self):
        pattern = SupplyChainPattern()
        h = Hypothesis(title="EOQ calculation", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_newsvendor(self):
        pattern = SupplyChainPattern()
        h = Hypothesis(title="Newsvendor model", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_reorder_point(self):
        pattern = SupplyChainPattern()
        h = Hypothesis(title="Reorder point analysis", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_safety_stock(self):
        pattern = SupplyChainPattern()
        h = Hypothesis(title="Safety stock optimization", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_multi_echelon(self):
        pattern = SupplyChainPattern()
        h = Hypothesis(title="Multi-echelon inventory", description="test")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = SupplyChainPattern()
        h = Hypothesis(title="Quantum mechanics", description="superposition")
        assert pattern.can_simulate(h) is False


# ═══════════════════════════════════════════════════════════════════
# Core Methods Tests
# ═══════════════════════════════════════════════════════════════════


class TestCalculateConfidence:
    def test_good_simulation(self):
        pattern = SupplyChainPattern()
        results = {
            "metrics": {
                "eoq": 100.0,
                "total_cost": 5000.0,
                "avg_bullwhip": 2.0,
            }
        }
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5

    def test_high_bullwhip(self):
        pattern = SupplyChainPattern()
        results = {"metrics": {"eoq": 100.0, "avg_bullwhip": 20.0}}
        confidence = pattern._calculate_confidence(results)
        assert 0 <= confidence < 0.9

    def test_zero_cost(self):
        pattern = SupplyChainPattern()
        results = {"metrics": {"eoq": 100.0, "total_cost": 0.0}}
        confidence = pattern._calculate_confidence(results)
        assert 0 <= confidence < 0.9


# ═══════════════════════════════════════════════════════════════════
# Resource Estimation Tests
# ═══════════════════════════════════════════════════════════════════


class TestEstimateResources:
    def test_default_params(self):
        pattern = SupplyChainPattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert "gpu_required" in resources
        assert "estimated_time_seconds" in resources
        assert resources["gpu_required"] is False

    def test_more_echelons_more_time(self):
        pattern = SupplyChainPattern()
        h_small = Hypothesis(parameters={"num_echelons": 2, "periods": 50})
        h_large = Hypothesis(parameters={"num_echelons": 10, "periods": 50})

        resources_small = pattern.estimate_resources(h_small)
        resources_large = pattern.estimate_resources(h_large)

        assert resources_large["estimated_time_seconds"] > resources_small["estimated_time_seconds"]


# ═══════════════════════════════════════════════════════════════════
# Run Integration Tests
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRun:
    async def test_run_default(self):
        pattern = SupplyChainPattern()
        h = Hypothesis(title="Supply chain", description="inventory optimization")
        result = await pattern.run(h, {"periods": 50})
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("sc_")

    async def test_run_with_config(self):
        pattern = SupplyChainPattern()
        h = Hypothesis(title="Supply chain", description="inventory optimization")
        result = await pattern.run(
            h,
            {
                "num_echelons": 3,
                "periods": 50,
                "demand_mean": 200.0,
                "demand_std": 30.0,
                "lead_time": 3,
            },
        )
        assert result.status == SimulationStatus.COMPLETED

    async def test_metrics_present(self):
        pattern = SupplyChainPattern()
        h = Hypothesis(title="Supply chain", description="inventory optimization")
        result = await pattern.run(h, {"periods": 50})
        assert result.status == SimulationStatus.COMPLETED
        assert "num_echelons" in result.metrics
        assert "total_cost" in result.metrics
        assert "eoq" in result.metrics

    async def test_logs_present(self):
        pattern = SupplyChainPattern()
        h = Hypothesis(title="Supply chain", description="inventory optimization")
        result = await pattern.run(h, {"periods": 50})
        assert len(result.logs) > 0


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestEdgeCases:
    async def test_single_echelon(self):
        pattern = SupplyChainPattern()
        h = Hypothesis(title="Supply chain", description="inventory optimization")
        result = await pattern.run(h, {"num_echelons": 1, "periods": 50})
        assert result.status == SimulationStatus.COMPLETED

    async def test_many_echelons(self):
        pattern = SupplyChainPattern()
        h = Hypothesis(title="Supply chain", description="inventory optimization")
        result = await pattern.run(h, {"num_echelons": 10, "periods": 50})
        assert result.status == SimulationStatus.COMPLETED

    async def test_high_demand(self):
        pattern = SupplyChainPattern()
        h = Hypothesis(title="Supply chain", description="inventory optimization")
        result = await pattern.run(h, {"periods": 50, "demand_mean": 1000.0})
        assert result.status == SimulationStatus.COMPLETED

    async def test_zero_demand_std(self):
        pattern = SupplyChainPattern()
        h = Hypothesis(title="Supply chain", description="inventory optimization")
        result = await pattern.run(h, {"periods": 50, "demand_std": 0.0})
        assert result.status == SimulationStatus.COMPLETED

    async def test_high_lead_time(self):
        pattern = SupplyChainPattern()
        h = Hypothesis(title="Supply chain", description="inventory optimization")
        result = await pattern.run(h, {"periods": 50, "lead_time": 10})
        assert result.status == SimulationStatus.COMPLETED

    async def test_high_holding_cost(self):
        pattern = SupplyChainPattern()
        h = Hypothesis(title="Supply chain", description="inventory optimization")
        result = await pattern.run(h, {"periods": 50, "holding_cost": 10.0})
        assert result.status == SimulationStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
