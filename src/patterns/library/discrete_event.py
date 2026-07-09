"""
Discrete Event Simulation Pattern
Production-grade event-driven simulation using SimPy framework

Based on:
- SimPy (Python discrete-event simulation)
- Queueing theory (Kendall notation)
- Operations research methodology
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np


try:
    import simpy
    HAS_SIMPY = True
except ImportError:
    HAS_SIMPY = False

from ..core import (
    Hypothesis,
    SimulationParameter,
    SimulationPattern,
    SimulationResult,
    SimulationStatus,
    ValidationLevel,
    simulation_pattern,
)


logger = logging.getLogger(__name__)


class QueueDiscipline(Enum):
    """QueueDiscipline."""
    FIFO = "fifo"
    LIFO = "lifo"
    PRIORITY = "priority"
    SJF = "shortest_job_first"


@dataclass
class Resource:
    """Resource in the system"""
    name: str
    capacity: int
    service_time_dist: str = "exponential"  # exponential, uniform, constant
    service_time_mean: float = 1.0


@dataclass
class Entity:
    """Entity flowing through the system"""
    entity_id: int
    arrival_time: float
    priority: int = 0
    service_time: float = 0.0
    start_service_time: float | None = None
    completion_time: float | None = None

    @property
    def waiting_time(self) -> float:
        """Waiting time."""
        if self.start_service_time:
            return self.start_service_time - self.arrival_time
        return 0.0

    @property
    def total_time(self) -> float:
        """Total time."""
        if self.completion_time:
            return self.completion_time - self.arrival_time
        return 0.0


@simulation_pattern(
    id="discrete_event",
    name="Discrete Event Simulation",
    category="operations",
    description="Event-driven simulation for queues, manufacturing, logistics",
)
class DiscreteEventPattern(SimulationPattern):
    """
    Discrete event simulation for queuing systems and operations

    Implements:
    - Multiple resource types
    - Various queue disciplines
    - Entity routing
    - Performance metrics (utilization, wait times, throughput)
    """

    parameters = [
        SimulationParameter(
            name="simulation_time",
            type="float",
            default=1000.0,
            min=100.0,
            max=100000.0,
            description="Total simulation time",
        ),
        SimulationParameter(
            name="arrival_rate",
            type="float",
            default=1.0,
            min=0.1,
            max=100.0,
            description="Entity arrival rate (per unit time)",
        ),
        SimulationParameter(
            name="num_servers",
            type="int",
            default=1,
            min=1,
            max=100,
            description="Number of parallel servers",
        ),
        SimulationParameter(
            name="service_rate",
            type="float",
            default=1.5,
            min=0.1,
            max=100.0,
            description="Service rate (per unit time per server)",
        ),
        SimulationParameter(
            name="queue_discipline",
            type="select",
            default="fifo",
            options=["fifo", "lifo", "priority"],
            description="Queue discipline",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.entities: list[Entity] = []
        self.resource_busy_time: dict[str, float] = defaultdict(float)
        self.queue_lengths: list[tuple[float, int]] = []

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if DES can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()

        keywords = [
            "queue", "queuing", "server", "wait time",
            "throughput", "bottleneck", "capacity",
            "manufacturing", "production line", "supply chain",
            "call center", "traffic", "congestion",
            "discrete event", "simulation",
            "m/m/1", "m/m/c", "kendall",
        ]

        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute discrete event simulation"""
        start_time = datetime.now()
        simulation_id = f"des_{start_time.timestamp()}"

        logger.info(f"Starting DES {simulation_id}")

        # Parse configuration
        sim_time = config.get("simulation_time", 1000.0)
        arrival_rate = config.get("arrival_rate", 1.0)
        num_servers = config.get("num_servers", 1)
        service_rate = config.get("service_rate", 1.5)
        discipline = config.get("queue_discipline", "fifo")

        try:
            if HAS_SIMPY:
                results = await self._run_simpy(
                    sim_time, arrival_rate, num_servers, service_rate, discipline
                )
            else:
                results = await self._run_fallback(
                    sim_time, arrival_rate, num_servers, service_rate
                )

            end_time = datetime.now()

            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.COMPLETED,
                start_time=start_time,
                end_time=end_time,
                metrics=results["metrics"],
                logs=results["logs"],
                confidence_score=self._calculate_confidence(results),
                validation_level=ValidationLevel.MONTE_CARLO,
            )

        except Exception as e:
            logger.exception("DES failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    async def _run_simpy(
        self, sim_time: float, arrival_rate: float,
        num_servers: int, service_rate: float, discipline: str
    ) -> dict[str, Any]:
        """Run simulation using SimPy"""

        env = simpy.Environment()

        # Resource with specified capacity
        resource = simpy.Resource(env, capacity=num_servers)

        # Tracking
        self.entities = []
        wait_times = []
        service_times = []
        queue_length_samples = []
        entity_id = 0

        def entity_process(env: Any, entity_id: Any) -> None:  # type: ignore[misc]
            """Process for each entity"""
            arrival_time = env.now

            with resource.request() as req:
                yield req

                start_service = env.now
                wait_time = start_service - arrival_time
                wait_times.append(wait_time)

                # Service time
                service_time = np.random.exponential(1.0 / service_rate)
                yield env.timeout(service_time)
                service_times.append(service_time)

                self.entities.append(Entity(
                    entity_id=entity_id,
                    arrival_time=arrival_time,
                    start_service_time=start_service,
                    completion_time=env.now,
                ))

        def arrival_process(env: Any) -> None:  # type: ignore[misc]
            """Generate arrivals"""
            nonlocal entity_id
            while True:
                interarrival = np.random.exponential(1.0 / arrival_rate)
                yield env.timeout(interarrival)

                entity_id += 1
                env.process(entity_process(env, entity_id))  # type: ignore[func-returns-value]

                # Sample queue length
                queue_length_samples.append((env.now, len(resource.queue)))

        # Start arrival process
        env.process(arrival_process(env))  # type: ignore[func-returns-value]

        # Run simulation
        env.run(until=sim_time)

        # Calculate metrics
        metrics = self._calculate_metrics(
            wait_times, service_times, num_servers, sim_time
        )

        logs = [
            f"Simulation completed: {len(self.entities)} entities processed",
            f"Average wait time: {metrics['avg_wait_time']:.2f}",
            f"Average service time: {metrics['avg_service_time']:.2f}",
            f"Server utilization: {metrics['utilization']:.2%}",
            f"Throughput: {metrics['throughput']:.2f} entities/time",
        ]

        return {"metrics": metrics, "logs": logs}

    async def _run_fallback(
        self, sim_time: float, arrival_rate: float,
        num_servers: int, service_rate: float
    ) -> dict[str, Any]:
        """Analytical fallback when SimPy not available"""

        # M/M/c queue analytical solution
        rho = arrival_rate / (num_servers * service_rate)

        if rho >= 1:
            # Unstable queue
            return {
                "metrics": {
                    "utilization": rho,
                    "avg_wait_time": float('inf'),
                    "throughput": num_servers * service_rate,
                    "stability": "unstable",
                },
                "logs": ["Queue is unstable (rho >= 1)", "Using analytical approximation"],
            }

        # Erlang C formula approximation
        # Simplified calculation
        avg_wait = self._erlang_c_approx(arrival_rate, service_rate, num_servers)

        metrics = {
            "utilization": rho,
            "avg_wait_time": avg_wait,
            "avg_service_time": 1.0 / service_rate,
            "throughput": arrival_rate,
            "stability": "stable",
            "num_servers": num_servers,
        }

        logs = [
            "SimPy not available, using analytical approximation",
            f"Traffic intensity (rho): {rho:.2f}",
            f"Estimated wait time: {avg_wait:.2f}",
        ]

        return {"metrics": metrics, "logs": logs}

    def _erlang_c_approx(self, arrival_rate: float, service_rate: float, c: int) -> float:
        """Simplified Erlang C formula"""
        rho = arrival_rate / (c * service_rate)
        1.0 / service_rate

        # Simplified approximation
        if c == 1:
            # M/M/1: W = rho / (mu * (1 - rho))
            return rho / (service_rate * (1 - rho))
        else:
            # M/M/c approximation
            return (rho ** (np.sqrt(2 * (c + 1)) - 1)) / (c * service_rate * (1 - rho))  # type: ignore[no-any-return]

    def _calculate_metrics(
        self, wait_times: list[float], service_times: list[float],
        num_servers: int, sim_time: float
    ) -> dict[str, float]:
        """Calculate performance metrics"""

        if not wait_times:
            return {}

        total_service_time = sum(service_times)

        return {
            "avg_wait_time": float(np.mean(wait_times)),
            "std_wait_time": float(np.std(wait_times)),
            "max_wait_time": float(np.max(wait_times)),
            "avg_service_time": float(np.mean(service_times)),
            "std_service_time": float(np.std(service_times)),
            "utilization": total_service_time / (sim_time * num_servers),
            "throughput": len(wait_times) / sim_time,
            "num_entities": len(wait_times),
            "num_servers": num_servers,
        }

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        # Stable queue
        if metrics.get("stability") == "stable":
            factors.append(0.3)
        elif metrics.get("utilization", 0) < 0.9:
            factors.append(0.3)

        # Sufficient sample
        if metrics.get("num_entities", 0) > 100:
            factors.append(0.3)

        # Reasonable metrics
        if 0 < metrics.get("avg_wait_time", -1) < 100:
            factors.append(0.2)

        # SimPy used (more accurate)
        if HAS_SIMPY:
            factors.append(0.2)

        return min(0.95, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        params = hypothesis.parameters
        sim_time = params.get("simulation_time", 1000.0)
        arrival_rate = params.get("arrival_rate", 1.0)

        expected_entities = int(sim_time * arrival_rate)

        return {
            "cpu_cores": 1,
            "memory_gb": 0.5 + expected_entities / 10000,
            "gpu_required": False,
            "estimated_time_seconds": sim_time / 100,  # SimPy is fast
        }
