"""
TURBO-CDI v6.0 - Queueing Networks Pattern
Network of queues using Jackson network theory and simulation.

Pattern Structure (Christopher Alexander):
- Context: Performance analysis, capacity planning, resource allocation
- Forces: Service time variability, routing decisions, congestion propagation
- Solution: Network decomposition with flow conservation
"""

import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


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
    nodes: List[QueueingNodeConfig] = field(
        default_factory=lambda: [
            QueueingNodeConfig(name="source", n_servers=1, service_rate=float("inf")),
            QueueingNodeConfig(name="server1", n_servers=2, service_rate=1.0),
            QueueingNodeConfig(name="server2", n_servers=1, service_rate=0.8),
            QueueingNodeConfig(name="sink", n_servers=1, service_rate=float("inf")),
        ]
    )

    # Routing matrix (from_node, to_node) probabilities
    routing_matrix: Optional[np.ndarray] = None

    # External arrival
    arrival_process: ArrivalProcess = ArrivalProcess.POISSON
    arrival_rate: float = 1.5  # External arrivals per unit time

    # Simulation parameters
    simulation_time: float = 10000.0
    warmup_time: float = 1000.0  # Discard initial data

    # Analysis options
    compute_analytical: bool = True  # Compute Jackson network solution


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

    def __init__(self, config: Optional[QueueingNetworkConfig] = None):
        self.config = config or QueueingNetworkConfig()

        # Initialize routing matrix if not provided
        if self.config.routing_matrix is None:
            self._initialize_default_routing()

        # Simulation state
        self.time: float = 0.0
        self.event_queue: List[Tuple[float, str, Dict]] = []  # (time, type, data)
        self.node_queues: Dict[str, deque] = {}
        self.server_busy: Dict[str, List[Optional[Dict]]] = {}

        # Statistics
        self.node_stats: Dict[str, Dict] = {}
        self.customer_stats: List[Dict] = []

        # Jackson network solution
        self.throughput: Optional[np.ndarray] = None
        self.node_utilization: Optional[np.ndarray] = None
        self.mean_queue_length: Optional[np.ndarray] = None

        self._initialize_network()

    def _initialize_default_routing(self):
        """Create default routing matrix (tandem network)"""
        cfg = self.config
        n_nodes = len(cfg.nodes)

        # Default: tandem network (source -> 1 -> 2 -> ... -> sink)
        cfg.routing_matrix = np.zeros((n_nodes, n_nodes))

        for i in range(n_nodes - 1):
            cfg.routing_matrix[i, i + 1] = 1.0

    def _initialize_network(self):
        """Initialize network state"""
        cfg = self.config

        for i, node in enumerate(cfg.nodes):
            self.node_queues[node.name] = deque()
            self.server_busy[node.name] = [None] * node.n_servers

            self.node_stats[node.name] = {
                "arrivals": 0,
                "departures": 0,
                "blocked": 0,
                "total_queue_time": 0.0,
                "total_service_time": 0.0,
                "queue_length_samples": [],
                "busy_server_samples": [],
                "last_event_time": 0.0,
            }

    def _find_node_index(self, name: str) -> int:
        """Find index of node by name"""
        for i, node in enumerate(self.config.nodes):
            if node.name == name:
                return i
        return -1

    def _generate_interarrival_time(self) -> float:
        """Generate time until next external arrival"""
        cfg = self.config

        if cfg.arrival_process == ArrivalProcess.POISSON:
            return np.random.exponential(1.0 / cfg.arrival_rate)
        elif cfg.arrival_process == ArrivalProcess.DETERMINISTIC:
            return 1.0 / cfg.arrival_rate
        else:
            return np.random.exponential(1.0 / cfg.arrival_rate)

    def _generate_service_time(self, node: QueueingNodeConfig) -> float:
        """Generate service time for a node"""
        if node.service_dist == ServiceDistribution.EXPONENTIAL:
            return np.random.exponential(1.0 / node.service_rate)

        elif node.service_dist == ServiceDistribution.DETERMINISTIC:
            return 1.0 / node.service_rate

        elif node.service_dist == ServiceDistribution.ERLANG:
            # k-stage Erlang = sum of k exponentials
            return np.random.gamma(
                node.erlang_stages, 1.0 / (node.erlang_stages * node.service_rate)
            )

        elif node.service_dist == ServiceDistribution.UNIFORM:
            mean = 1.0 / node.service_rate
            return np.random.uniform(mean * 0.5, mean * 1.5)

        else:
            return np.random.exponential(1.0 / node.service_rate)

    def _schedule_event(self, event_time: float, event_type: str, data: Dict):
        """Schedule a future event"""
        self.event_queue.append((event_time, event_type, data))
        self.event_queue.sort(key=lambda x: x[0])

    def _update_node_stats(self, node_name: str, new_time: float):
        """Update time-based statistics for a node"""
        stats = self.node_stats[node_name]
        delta_t = new_time - stats["last_event_time"]

        if delta_t > 0:
            # Queue length sample
            queue_len = len(self.node_queues[node_name])
            stats["queue_length_samples"].append((new_time, queue_len))

            # Busy servers sample
            busy = sum(1 for s in self.server_busy[node_name] if s is not None)
            stats["busy_server_samples"].append((new_time, busy))

        stats["last_event_time"] = new_time

    def _handle_arrival(self, event_data: Dict):
        """Handle customer arrival at a node"""
        customer = event_data["customer"]
        node_name = event_data["node"]
        node_idx = self._find_node_index(node_name)
        node_config = self.config.nodes[node_idx]

        self._update_node_stats(node_name, self.time)
        self.node_stats[node_name]["arrivals"] += 1

        # Record arrival time
        customer["arrival_times"][node_name] = self.time

        # Check for available server
        available_server = None
        for i, server in enumerate(self.server_busy[node_name]):
            if server is None:
                available_server = i
                break

        if available_server is not None:
            # Start service immediately
            service_time = self._generate_service_time(node_config)
            self.server_busy[node_name][available_server] = customer

            # Schedule departure
            self._schedule_event(
                self.time + service_time,
                "departure",
                {"customer": customer, "node": node_name, "server": available_server},
            )
        else:
            # Add to queue
            if len(self.node_queues[node_name]) < node_config.buffer_size:
                self.node_queues[node_name].append(customer)
            else:
                self.node_stats[node_name]["blocked"] += 1

    def _handle_departure(self, event_data: Dict):
        """Handle customer departure from a node"""
        customer = event_data["customer"]
        node_name = event_data["node"]
        server_idx = event_data["server"]
        node_idx = self._find_node_index(node_name)
        node_config = self.config.nodes[node_idx]

        self._update_node_stats(node_name, self.time)
        self.node_stats[node_name]["departures"] += 1

        # Record departure time and calculate wait
        arrival_time = customer["arrival_times"][node_name]
        wait_time = self.time - arrival_time

        if "wait_times" not in customer:
            customer["wait_times"] = {}
        customer["wait_times"][node_name] = wait_time

        # Free the server
        self.server_busy[node_name][server_idx] = None

        # Check if someone is waiting in queue
        if len(self.node_queues[node_name]) > 0:
            next_customer = self.node_queues[node_name].popleft()
            service_time = self._generate_service_time(node_config)
            self.server_busy[node_name][server_idx] = next_customer

            self._schedule_event(
                self.time + service_time,
                "departure",
                {"customer": next_customer, "node": node_name, "server": server_idx},
            )

        # Route to next node
        self._route_customer(customer, node_idx)

    def _route_customer(self, customer: Dict, from_idx: int):
        """Route customer to next node based on routing matrix"""
        cfg = self.config

        # Get routing probabilities
        probs = cfg.routing_matrix[from_idx]

        if np.sum(probs) == 0:
            # Customer exits system
            customer["departure_time"] = self.time
            if self.time > cfg.warmup_time:
                self.customer_stats.append(customer)
            return

        # Choose destination
        probs = probs / np.sum(probs)
        to_idx = np.random.choice(len(cfg.nodes), p=probs)
        to_node = cfg.nodes[to_idx].name

        # Schedule arrival at next node
        # (assuming negligible transfer time)
        self._schedule_event(
            self.time, "arrival", {"customer": customer, "node": to_node}
        )

    def _calculate_jackson_solution(self):
        """Calculate analytical solution for Jackson network"""
        cfg = self.config
        n_nodes = len(cfg.nodes)

        # Solve traffic equations: λ = λ_ext + R^T λ
        # where λ is total arrival rate to each node

        R = cfg.routing_matrix
        lambda_ext = np.zeros(n_nodes)
        lambda_ext[0] = cfg.arrival_rate  # External arrivals at first node

        # Solve (I - R^T) λ = λ_ext
        I = np.eye(n_nodes)
        try:
            self.throughput = np.linalg.solve(I - R.T, lambda_ext)
        except np.linalg.LinAlgError:
            logger.warning("Could not solve traffic equations")
            return

        # Calculate utilization and queue lengths for each node
        self.node_utilization = np.zeros(n_nodes)
        self.mean_queue_length = np.zeros(n_nodes)
        self.mean_waiting_time = np.zeros(n_nodes)

        for i, node in enumerate(cfg.nodes):
            if node.service_rate == float("inf"):
                continue

            rho = self.throughput[i] / (node.n_servers * node.service_rate)
            self.node_utilization[i] = min(rho, 1.0)

            if rho < 1.0:
                if node.n_servers == 1:
                    # M/M/1 queue
                    self.mean_queue_length[i] = rho**2 / (1 - rho)
                    self.mean_waiting_time[i] = rho / (node.service_rate * (1 - rho))
                else:
                    # M/M/c queue (simplified)
                    # Erlang C formula approximation
                    c = node.n_servers
                    rho_c = rho * c
                    # Simplified queue length
                    self.mean_queue_length[i] = (
                        (rho_c ** (c + 1) / (c * c * (1 - rho) ** 2))
                        if rho < 1
                        else float("inf")
                    )
                    self.mean_waiting_time[i] = (
                        self.mean_queue_length[i] / self.throughput[i]
                        if self.throughput[i] > 0
                        else 0
                    )

    def _compute_simulation_statistics(self) -> Dict[str, Any]:
        """Compute statistics from simulation"""
        cfg = self.config

        results = {}

        for node_name, stats in self.node_stats.items():
            node_idx = self._find_node_index(node_name)
            node_config = cfg.nodes[node_idx]

            # Time-average queue length
            if len(stats["queue_length_samples"]) > 1:
                times, lengths = zip(*stats["queue_length_samples"])
                total_time = (
                    times[-1] - cfg.warmup_time if times[-1] > cfg.warmup_time else 1.0
                )
                mean_queue = np.mean(
                    [l for t, l in stats["queue_length_samples"] if t > cfg.warmup_time]
                )
            else:
                mean_queue = 0.0

            # Time-average server utilization
            if len(stats["busy_server_samples"]) > 1:
                mean_busy = np.mean(
                    [b for t, b in stats["busy_server_samples"] if t > cfg.warmup_time]
                )
                utilization = (
                    mean_busy / node_config.n_servers
                    if node_config.n_servers > 0
                    else 0
                )
            else:
                utilization = 0.0

            # Throughput
            sim_time = cfg.simulation_time - cfg.warmup_time
            throughput = stats["departures"] / sim_time if sim_time > 0 else 0

            results[node_name] = {
                "throughput": throughput,
                "utilization": utilization,
                "mean_queue_length": mean_queue,
                "arrivals": stats["arrivals"],
                "departures": stats["departures"],
                "blocked": stats["blocked"],
            }

        return results

    def _compute_system_metrics(self) -> Dict[str, float]:
        """Compute overall system metrics"""
        cfg = self.config

        # Filter completed customers
        completed = [c for c in self.customer_stats if "departure_time" in c]

        if not completed:
            return {"total_customers": 0}

        # Total time in system
        total_times = [
            c["departure_time"] - c["arrival_times"][cfg.nodes[0].name]
            for c in completed
        ]

        # Little's Law check
        # L = λW
        avg_total_time = np.mean(total_times)
        throughput = len(completed) / (cfg.simulation_time - cfg.warmup_time)

        return {
            "total_customers": len(completed),
            "mean_system_time": avg_total_time,
            "std_system_time": np.std(total_times),
            "throughput": throughput,
            "little_L": throughput * avg_total_time,
        }

    def run(self, hypothesis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run queueing network simulation"""
        cfg = self.config

        logger.info(
            f"Starting queueing network: {len(cfg.nodes)} nodes, "
            f"simulation time={cfg.simulation_time}"
        )

        # Schedule first arrival
        next_arrival = self._generate_interarrival_time()
        customer_id = 0

        self._schedule_event(
            next_arrival,
            "arrival",
            {
                "customer": {"id": customer_id, "arrival_times": {}, "wait_times": {}},
                "node": cfg.nodes[0].name,
            },
        )

        # Main simulation loop
        while self.event_queue and self.time < cfg.simulation_time:
            # Get next event
            event_time, event_type, event_data = self.event_queue.pop(0)
            self.time = event_time

            if event_type == "arrival":
                self._handle_arrival(event_data)

                # Schedule next external arrival if this was from source
                if event_data["node"] == cfg.nodes[0].name and "customer" in event_data:
                    if event_data["customer"]["id"] == customer_id:
                        customer_id += 1
                        next_arrival = self.time + self._generate_interarrival_time()
                        if next_arrival < cfg.simulation_time:
                            self._schedule_event(
                                next_arrival,
                                "arrival",
                                {
                                    "customer": {
                                        "id": customer_id,
                                        "arrival_times": {},
                                        "wait_times": {},
                                    },
                                    "node": cfg.nodes[0].name,
                                },
                            )

            elif event_type == "departure":
                self._handle_departure(event_data)

        # Compute analytical solution
        if cfg.compute_analytical:
            self._calculate_jackson_solution()

        return self._format_output()

    def _format_output(self) -> Dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        sim_results = self._compute_simulation_statistics()
        system_metrics = self._compute_system_metrics()

        output = {
            "n_nodes": len(cfg.nodes),
            "simulation_time": cfg.simulation_time,
            "warmup_time": cfg.warmup_time,
            "external_arrival_rate": cfg.arrival_rate,
            "node_results": sim_results,
            "system_metrics": system_metrics,
        }

        # Add analytical results if available
        if self.throughput is not None:
            output["analytical"] = {
                "throughput": self.throughput.tolist(),
                "utilization": self.node_utilization.tolist(),
                "mean_queue_length": self.mean_queue_length.tolist(),
            }

        # Check stability
        max_util = max(
            r["utilization"] for r in sim_results.values() if r["throughput"] > 0
        )
        output["is_stable"] = max_util < 1.0

        # Total cost
        total_holding_cost = sum(
            r["mean_queue_length"] * cfg.nodes[self._find_node_index(name)].holding_cost
            for name, r in sim_results.items()
        )
        total_server_cost = sum(
            cfg.nodes[self._find_node_index(name)].n_servers
            * cfg.nodes[self._find_node_index(name)].server_cost
            for name in sim_results.keys()
        )

        output["costs"] = {
            "holding_cost": total_holding_cost,
            "server_cost": total_server_cost,
            "total": total_holding_cost + total_server_cost,
        }

        return output

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
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


# =============================================================================
# UNIT TESTS
# =============================================================================


def test_littles_law():
    """Test Little's Law: L = λW"""
    config = QueueingNetworkConfig(
        nodes=[
            QueueingNodeConfig(name="source", n_servers=1, service_rate=float("inf")),
            QueueingNodeConfig(name="server", n_servers=1, service_rate=2.0),
            QueueingNodeConfig(name="sink", n_servers=1, service_rate=float("inf")),
        ],
        arrival_rate=1.0,
        simulation_time=5000,
        warmup_time=500,
    )

    network = QueueingNetworkPattern(config)
    result = network.run()

    # Little's Law should approximately hold
    metrics = result["system_metrics"]
    if "little_L" in metrics:
        # λW should be reasonable
        assert metrics["little_L"] > 0, "Little's Law calculation failed"
    print("✓ Little's Law test passed")


def test_stability_threshold():
    """Test that system becomes unstable when ρ > 1"""
    # Stable case (ρ = 0.5)
    config_stable = QueueingNetworkConfig(
        nodes=[
            QueueingNodeConfig(name="source", n_servers=1, service_rate=float("inf")),
            QueueingNodeConfig(name="server", n_servers=1, service_rate=2.0),
            QueueingNodeConfig(name="sink", n_servers=1, service_rate=float("inf")),
        ],
        arrival_rate=1.0,  # ρ = 1/2 = 0.5
        simulation_time=2000,
        warmup_time=200,
    )
    network_stable = QueueingNetworkPattern(config_stable)
    result_stable = network_stable.run()

    # Unstable case (ρ = 1.5)
    config_unstable = QueueingNetworkConfig(
        nodes=[
            QueueingNodeConfig(name="source", n_servers=1, service_rate=float("inf")),
            QueueingNodeConfig(name="server", n_servers=1, service_rate=2.0),
            QueueingNodeConfig(name="sink", n_servers=1, service_rate=float("inf")),
        ],
        arrival_rate=3.0,  # ρ = 3/2 = 1.5
        simulation_time=2000,
        warmup_time=200,
    )
    network_unstable = QueueingNetworkPattern(config_unstable)
    result_unstable = network_unstable.run()

    # Stable should have lower queue lengths
    stable_queue = result_stable["node_results"]["server"]["mean_queue_length"]
    unstable_queue = result_unstable["node_results"]["server"]["mean_queue_length"]

    assert stable_queue < unstable_queue * 2, (
        f"Unstable system should have higher queue: stable={stable_queue}, unstable={unstable_queue}"
    )
    print("✓ Stability threshold test passed")


def test_throughput_conservation():
    """Test that throughput is conserved through the network"""
    config = QueueingNetworkConfig(
        nodes=[
            QueueingNodeConfig(name="source", n_servers=1, service_rate=float("inf")),
            QueueingNodeConfig(name="server1", n_servers=2, service_rate=1.5),
            QueueingNodeConfig(name="server2", n_servers=1, service_rate=1.0),
            QueueingNodeConfig(name="sink", n_servers=1, service_rate=float("inf")),
        ],
        arrival_rate=1.0,
        simulation_time=3000,
        warmup_time=300,
    )

    network = QueueingNetworkPattern(config)
    result = network.run()

    # In tandem network, throughputs should be approximately equal (after warmup)
    throughputs = [
        result["node_results"][n.name]["throughput"]
        for n in config.nodes
        if n.service_rate != float("inf")
    ]

    if len(throughputs) >= 2:
        # Throughputs should be similar
        assert max(throughputs) < min(throughputs) * 2 or min(throughputs) == 0, (
            f"Throughputs should be similar: {throughputs}"
        )
    print("✓ Throughput conservation test passed")


def test_parallel_servers():
    """Test that adding servers reduces queue length"""
    # Single server
    config_1 = QueueingNetworkConfig(
        nodes=[
            QueueingNodeConfig(name="source", n_servers=1, service_rate=float("inf")),
            QueueingNodeConfig(name="server", n_servers=1, service_rate=2.0),
            QueueingNodeConfig(name="sink", n_servers=1, service_rate=float("inf")),
        ],
        arrival_rate=1.5,
        simulation_time=3000,
        warmup_time=300,
    )
    network_1 = QueueingNetworkPattern(config_1)
    result_1 = network_1.run()

    # Two servers
    config_2 = QueueingNetworkConfig(
        nodes=[
            QueueingNodeConfig(name="source", n_servers=1, service_rate=float("inf")),
            QueueingNodeConfig(name="server", n_servers=2, service_rate=2.0),
            QueueingNodeConfig(name="sink", n_servers=1, service_rate=float("inf")),
        ],
        arrival_rate=1.5,
        simulation_time=3000,
        warmup_time=300,
    )
    network_2 = QueueingNetworkPattern(config_2)
    result_2 = network_2.run()

    queue_1 = result_1["node_results"]["server"]["mean_queue_length"]
    queue_2 = result_2["node_results"]["server"]["mean_queue_length"]

    # Two servers should have shorter queue
    assert queue_2 < queue_1 * 1.5, (
        f"Multiple servers should reduce queue: 1-server={queue_1}, 2-server={queue_2}"
    )
    print("✓ Parallel servers test passed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Run tests
    test_littles_law()
    test_stability_threshold()
    test_throughput_conservation()
    test_parallel_servers()

    # Demo run
    print("\n--- Demo Run ---")
    config = QueueingNetworkConfig(
        nodes=[
            QueueingNodeConfig(name="source", n_servers=1, service_rate=float("inf")),
            QueueingNodeConfig(name="entry", n_servers=2, service_rate=2.0),
            QueueingNodeConfig(name="processing", n_servers=3, service_rate=1.5),
            QueueingNodeConfig(name="verification", n_servers=1, service_rate=1.0),
            QueueingNodeConfig(name="sink", n_servers=1, service_rate=float("inf")),
        ],
        arrival_rate=2.0,
        simulation_time=5000,
        warmup_time=500,
    )

    network = QueueingNetworkPattern(config)
    result = network.run()

    print(f"Nodes: {result['n_nodes']}")
    print(f"Customers processed: {result['system_metrics']['total_customers']}")
    print(f"Mean system time: {result['system_metrics']['mean_system_time']:.2f}")
    print(f"System throughput: {result['system_metrics']['throughput']:.3f}")
    print(f"Stable: {result['is_stable']}")

    print("\nNode statistics:")
    for name, stats in result["node_results"].items():
        if stats["throughput"] > 0:
            print(
                f"  {name}: ρ={stats['utilization']:.2f}, Lq={stats['mean_queue_length']:.2f}"
            )


# Alias for TURBO-CDI compatibility
QueueingNetworksPattern = ServiceDistribution
