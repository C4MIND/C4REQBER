from __future__ import annotations


"""
C4REQBER v6.0 - Queueing Networks Pattern[str]
Main pattern class for queueing network simulation.
"""

import logging
from typing import Any

import numpy as np

from .config import QueueingNetworkConfig
from .core import QueueingNetworkSimulator


logger = logging.getLogger(__name__)

class QueueingNetworkPattern:
    """
    Queueing network simulation using discrete-event simulation.

    Supports:
    - Jackson networks (product-form solution)
    - General service distributions
    - State-dependent routing
    - Performance analysis (Littles Law, throughput)

    Jackson Network Properties:
    - Poisson external arrivals
    - Exponential service times
    - Probabilistic routing
    - Product-form stationary distribution
    """

    PATTERN_ID = "queueing_networks"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: QueueingNetworkConfig | None = None) -> None:
        self.config = config or QueueingNetworkConfig()
        self.simulator = QueueingNetworkSimulator(self.config)

        self.time: float = self.simulator.time
        self.event_queue: list[tuple[float, str, dict[str, Any]]] = self.simulator.event_queue
        self.node_queues: dict[str, Any] = self.simulator.node_queues
        self.server_busy: dict[str, list[dict[str, Any] | None]] = self.simulator.server_busy
        self.node_stats: dict[str, dict[str, Any]] = self.simulator.node_stats
        self.customer_stats: list[dict[str, Any]] = self.simulator.customer_stats
        self.throughput: np.ndarray | None = self.simulator.throughput
        self.node_utilization: np.ndarray | None = self.simulator.node_utilization
        self.mean_queue_length: np.ndarray | None = self.simulator.mean_queue_length
        self.mean_waiting_time: np.ndarray | None = self.simulator.mean_waiting_time

    def _find_node_index(self, name: str) -> int:
        return self.simulator._find_node_index(name)

    def _generate_interarrival_time(self) -> float:
        return self.simulator._generate_interarrival_time()

    def _generate_service_time(self, node: Any) -> float:
        return self.simulator._generate_service_time(node)

    def _schedule_event(self, event_time: float, event_type: str, data: dict[str, Any]) -> None:
        self.simulator._schedule_event(event_time, event_type, data)
        self.event_queue = self.simulator.event_queue

    def _update_node_stats(self, node_name: str, new_time: float) -> None:
        self.simulator._update_node_stats(node_name, new_time)
        self.node_stats = self.simulator.node_stats

    def _handle_arrival(self, event_data: dict[str, Any]) -> None:
        self.simulator._handle_arrival(event_data)
        self._sync_state()

    def _handle_departure(self, event_data: dict[str, Any]) -> None:
        self.simulator._handle_departure(event_data)
        self._sync_state()

    def _route_customer(self, customer: dict[str, Any], from_idx: int) -> None:
        self.simulator._route_customer(customer, from_idx)
        self._sync_state()

    def _calculate_jackson_solution(self) -> None:
        self.simulator._calculate_jackson_solution()
        self.throughput = self.simulator.throughput
        self.node_utilization = self.simulator.node_utilization
        self.mean_queue_length = self.simulator.mean_queue_length
        self.mean_waiting_time = self.simulator.mean_waiting_time

    def _compute_simulation_statistics(self) -> dict[str, Any]:
        return self.simulator._compute_simulation_statistics()

    def _compute_system_metrics(self) -> dict[str, Any]:
        self.simulator.customer_stats = self.customer_stats
        result = self.simulator._compute_system_metrics()
        self.customer_stats = self.simulator.customer_stats
        return result

    def _sync_state(self) -> None:
        self.time = self.simulator.time
        self.event_queue = self.simulator.event_queue
        self.node_queues = self.simulator.node_queues
        self.server_busy = self.simulator.server_busy
        self.node_stats = self.simulator.node_stats
        self.customer_stats = self.simulator.customer_stats

    def run(self, hypothesis: dict[str, Any] = None) -> dict[str, Any]:  # type: ignore[assignment]
        """Run queueing network simulation"""
        cfg = self.config

        logger.info(
            f"Starting queueing network: {len(cfg.nodes)} nodes, "
            f"simulation time={cfg.simulation_time}"
        )

        result = self.simulator.run_simulation()
        self._sync_state()
        return result

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Queueing Networks",
            "category": "EXTENDED",
            "domain": ["Operations Research", "Computer Networks", "Manufacturing"],
            "description": "Queueing network simulation with Jackson network analysis",
            "computational_complexity": "O(N log N) for N events",
            "typical_runtime": "seconds to minutes",
            "accuracy": "High (simulation), Exact (Jackson product-form)",
            "assumptions": [
                "Poisson arrivals (Jackson network)",
                "Exponential service times (Jackson network)",
                "First-Come-First-Served discipline",
                "Infinite buffers (or blocking counted)",
            ],
            "parameters": [
                {
                    "name": "arrival_rate",
                    "type": "float",
                    "default": 1.5,
                    "description": "External arrival rate",
                },
                {
                    "name": "simulation_time",
                    "type": "float",
                    "default": 10000.0,
                    "description": "Simulation time units",
                },
                {
                    "name": "service_dist",
                    "type": "enum",
                    "options": ["exponential", "deterministic", "erlang", "uniform"],
                    "default": "exponential",
                },
            ],
        }
