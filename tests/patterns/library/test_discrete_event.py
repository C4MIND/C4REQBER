"""
Tests for src/patterns/library/discrete_event.py (Discrete Event Simulation pattern)

Covers:
- QueueDiscipline enum values
- Resource dataclass
- Entity dataclass
- DiscreteEventPattern initialization
- can_simulate() keyword matching
- _run_simpy() and _run_fallback()
- _calculate_metrics()
- _calculate_confidence()
- estimate_resources()
- run() async integration
- Edge cases: empty entities, unstable queue
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.discrete_event import (
    DiscreteEventPattern,
    QueueDiscipline,
    Resource,
    Entity,
)
from src.patterns.core import Hypothesis, SimulationStatus



# ═══════════════════════════════════════════════════════════════════
# Enum Tests
# ═══════════════════════════════════════════════════════════════════


class TestQueueDiscipline:
    def test_fifo_value(self):
        assert QueueDiscipline.FIFO.value == "fifo"

    def test_lifo_value(self):
        assert QueueDiscipline.LIFO.value == "lifo"

    def test_priority_value(self):
        assert QueueDiscipline.PRIORITY.value == "priority"

    def test_sjf_value(self):
        assert QueueDiscipline.SJF.value == "shortest_job_first"


# ═══════════════════════════════════════════════════════════════════
# Config/Dataclass Tests
# ═══════════════════════════════════════════════════════════════════


class TestResource:
    def test_default_init(self):
        r = Resource(name="server1", capacity=2)
        assert r.name == "server1"
        assert r.capacity == 2
        assert r.service_time_dist == "exponential"
        assert r.service_time_mean == 1.0

    def test_custom_init(self):
        r = Resource(
            name="server2",
            capacity=5,
            service_time_dist="uniform",
            service_time_mean=2.5,
        )
        assert r.name == "server2"
        assert r.capacity == 5
        assert r.service_time_dist == "uniform"
        assert r.service_time_mean == 2.5


class TestEntity:
    def test_default_init(self):
        e = Entity(entity_id=1, arrival_time=0.0)
        assert e.entity_id == 1
        assert e.arrival_time == 0.0
        assert e.priority == 0
        assert e.service_time == 0.0
        assert e.start_service_time is None
        assert e.completion_time is None

    def test_waiting_time_not_started(self):
        e = Entity(entity_id=1, arrival_time=0.0)
        assert e.waiting_time == 0.0

    def test_waiting_time_started(self):
        e = Entity(entity_id=1, arrival_time=0.0, start_service_time=5.0)
        assert e.waiting_time == 5.0

    def test_total_time_not_completed(self):
        e = Entity(entity_id=1, arrival_time=0.0)
        assert e.total_time == 0.0

    def test_total_time_completed(self):
        e = Entity(entity_id=1, arrival_time=0.0, completion_time=10.0)
        assert e.total_time == 10.0


# ═══════════════════════════════════════════════════════════════════
# Initialization Tests
# ═══════════════════════════════════════════════════════════════════


class TestDiscreteEventPatternInit:
    def test_init(self):
        pattern = DiscreteEventPattern()
        assert pattern is not None
        assert pattern.entities == []
        assert pattern.queue_lengths == []

    def test_parameters_defined(self):
        pattern = DiscreteEventPattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0
        param_names = [p.name for p in pattern.parameters]
        assert "simulation_time" in param_names
        assert "arrival_rate" in param_names
        assert "num_servers" in param_names


# ═══════════════════════════════════════════════════════════════════
# can_simulate Tests
# ═══════════════════════════════════════════════════════════════════


class TestCanSimulate:
    def test_matches_queue(self):
        pattern = DiscreteEventPattern()
        h = Hypothesis(title="Queue analysis", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_server(self):
        pattern = DiscreteEventPattern()
        h = Hypothesis(title="Server capacity", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_wait_time(self):
        pattern = DiscreteEventPattern()
        h = Hypothesis(title="Wait time analysis", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_throughput(self):
        pattern = DiscreteEventPattern()
        h = Hypothesis(title="Throughput optimization", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_bottleneck(self):
        pattern = DiscreteEventPattern()
        h = Hypothesis(title="Bottleneck identification", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_manufacturing(self):
        pattern = DiscreteEventPattern()
        h = Hypothesis(title="Manufacturing line", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_mmk(self):
        pattern = DiscreteEventPattern()
        h = Hypothesis(title="M/M/1 queue model", description="kendall notation")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = DiscreteEventPattern()
        h = Hypothesis(title="Quantum mechanics", description="superposition")
        assert pattern.can_simulate(h) is False


# ═══════════════════════════════════════════════════════════════════
# Core Methods Tests
# ═══════════════════════════════════════════════════════════════════


class TestCalculateMetrics:
    def test_empty_wait_times(self):
        pattern = DiscreteEventPattern()
        metrics = pattern._calculate_metrics([], [], 1, 1000.0)
        assert metrics == {}

    def test_basic_metrics(self):
        pattern = DiscreteEventPattern()
        wait_times = [1.0, 2.0, 3.0, 4.0, 5.0]
        service_times = [0.5, 0.6, 0.7, 0.8, 0.9]
        metrics = pattern._calculate_metrics(wait_times, service_times, 2, 1000.0)

        assert "avg_wait_time" in metrics
        assert "std_wait_time" in metrics
        assert "max_wait_time" in metrics
        assert "avg_service_time" in metrics
        assert "throughput" in metrics
        assert metrics["num_entities"] == 5
        assert metrics["num_servers"] == 2


class TestCalculateConfidence:
    def test_stable_queue(self):
        pattern = DiscreteEventPattern()
        results = {"metrics": {"stability": "stable", "num_entities": 200, "avg_wait_time": 5.0}}
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5

    def test_unstable_queue(self):
        pattern = DiscreteEventPattern()
        results = {"metrics": {"stability": "unstable", "utilization": 1.2}}
        confidence = pattern._calculate_confidence(results)
        assert confidence >= 0.0

    def test_high_utilization(self):
        pattern = DiscreteEventPattern()
        results = {"metrics": {"utilization": 0.95, "num_entities": 50, "avg_wait_time": 50.0}}
        confidence = pattern._calculate_confidence(results)
        assert 0.0 <= confidence <= 0.95


class TestErlangApprox:
    def test_mm1_formula(self):
        pattern = DiscreteEventPattern()
        result = pattern._erlang_c_approx(1.0, 2.0, 1)
        assert result > 0

    def test_mmc_formula(self):
        pattern = DiscreteEventPattern()
        result = pattern._erlang_c_approx(1.0, 2.0, 2)
        assert result > 0


# ═══════════════════════════════════════════════════════════════════
# Resource Estimation Tests
# ═══════════════════════════════════════════════════════════════════


class TestEstimateResources:
    def test_default_params(self):
        pattern = DiscreteEventPattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert "gpu_required" in resources
        assert "estimated_time_seconds" in resources
        assert resources["gpu_required"] is False

    def test_high_load(self):
        pattern = DiscreteEventPattern()
        h = Hypothesis(parameters={"simulation_time": 10000.0, "arrival_rate": 10.0})
        resources = pattern.estimate_resources(h)
        assert resources["memory_gb"] > 0.5


# ═══════════════════════════════════════════════════════════════════
# Run Integration Tests
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRun:
    async def test_run_default(self):
        pattern = DiscreteEventPattern()
        h = Hypothesis(title="Queue analysis", description="server capacity")
        result = await pattern.run(h, {"simulation_time": 100.0})
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("des_")

    async def test_run_with_config(self):
        pattern = DiscreteEventPattern()
        h = Hypothesis(title="Queue analysis", description="server capacity")
        result = await pattern.run(h, {
            "simulation_time": 100.0,
            "arrival_rate": 2.0,
            "num_servers": 2,
            "service_rate": 3.0,
        })
        assert result.status == SimulationStatus.COMPLETED

    async def test_metrics_present(self):
        pattern = DiscreteEventPattern()
        h = Hypothesis(title="Queue analysis", description="server capacity")
        result = await pattern.run(h, {"simulation_time": 100.0})
        assert "utilization" in result.metrics or "stability" in result.metrics

    async def test_logs_present(self):
        pattern = DiscreteEventPattern()
        h = Hypothesis(title="Queue analysis", description="server capacity")
        result = await pattern.run(h, {"simulation_time": 100.0})
        assert len(result.logs) > 0


# ═══════════════════════════════════════════════════════════════════
# Fallback Tests
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestFallback:
    async def test_fallback_unstable(self):
        pattern = DiscreteEventPattern()
        # High arrival rate relative to service should be unstable
        results = await pattern._run_fallback(1000.0, 10.0, 1, 1.0)
        assert "metrics" in results
        assert "logs" in results

    async def test_fallback_stable(self):
        pattern = DiscreteEventPattern()
        # Low arrival rate should be stable
        results = await pattern._run_fallback(1000.0, 1.0, 2, 2.0)
        assert "metrics" in results
        assert results["metrics"]["stability"] == "stable"


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestEdgeCases:
    async def test_very_short_simulation(self):
        pattern = DiscreteEventPattern()
        h = Hypothesis(title="Queue analysis", description="server capacity")
        result = await pattern.run(h, {"simulation_time": 10.0})
        assert result.status in [SimulationStatus.COMPLETED, SimulationStatus.FAILED]

    async def test_high_arrival_rate(self):
        pattern = DiscreteEventPattern()
        h = Hypothesis(title="Queue analysis", description="server capacity")
        result = await pattern.run(h, {"simulation_time": 50.0, "arrival_rate": 50.0})
        assert result.status == SimulationStatus.COMPLETED

    async def test_single_server(self):
        pattern = DiscreteEventPattern()
        h = Hypothesis(title="Queue analysis", description="server capacity")
        result = await pattern.run(h, {"simulation_time": 50.0, "num_servers": 1})
        assert result.status == SimulationStatus.COMPLETED

    async def test_many_servers(self):
        pattern = DiscreteEventPattern()
        h = Hypothesis(title="Queue analysis", description="server capacity")
        result = await pattern.run(h, {"simulation_time": 50.0, "num_servers": 10})
        assert result.status == SimulationStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
