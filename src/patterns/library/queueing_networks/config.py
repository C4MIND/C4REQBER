"""
C4REQBER v6.0 - Queueing Networks Pattern[str] Configuration
Configuration classes for queueing network simulation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np


class ServiceDistribution(Enum):
    """Service time distributions"""

    EXPONENTIAL = "exponential"
    DETERMINISTIC = "deterministic"
    ERLANG = "erlang"
    UNIFORM = "uniform"

class RoutingPolicy(Enum):
    """Routing policies between nodes"""

    PROBABILISTIC = "probabilistic"
    ROUND_ROBIN = "round_robin"
    SHORTEST_QUEUE = "shortest_queue"
    LEAST_WORK = "least_work"

class ArrivalProcess(Enum):
    """Arrival process types"""

    POISSON = "poisson"
    BURSTY = "bursty"  # ON/OFF process
    DETERMINISTIC = "deterministic"

@dataclass
class QueueingNodeConfig:
    """Configuration for a single node in the network"""

    name: str
    n_servers: int = 1
    service_rate: float = 1.0  # Customers per unit time
    service_dist: ServiceDistribution = ServiceDistribution.EXPONENTIAL
    buffer_size: int = 1000  # Infinite if large

    # Erlang parameters
    erlang_stages: int = 2

    # Cost parameters
    holding_cost: float = 1.0  # Cost per unit time in queue
    server_cost: float = 10.0  # Cost per server

@dataclass
class QueueingNetworkConfig:
    """Configuration for queueing network"""

    # Network topology
    nodes: list[QueueingNodeConfig] = field(
        default_factory=lambda: [
            QueueingNodeConfig(name="source", n_servers=1, service_rate=float("inf")),
            QueueingNodeConfig(name="server1", n_servers=2, service_rate=1.0),
            QueueingNodeConfig(name="server2", n_servers=1, service_rate=0.8),
            QueueingNodeConfig(name="sink", n_servers=1, service_rate=float("inf")),
        ]
    )

    # Routing matrix (from_node, to_node) probabilities
    routing_matrix: np.ndarray | None = None

    # External arrival
    arrival_process: ArrivalProcess = ArrivalProcess.POISSON
    arrival_rate: float = 1.5  # External arrivals per unit time

    # Simulation parameters
    simulation_time: float = 10000.0
    warmup_time: float = 1000.0  # Discard initial data

    # Analysis options
    compute_analytical: bool = True  # Compute Jackson network solution
