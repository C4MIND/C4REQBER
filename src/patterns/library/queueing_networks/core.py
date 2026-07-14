"""
C4REQBER v6.0 - Queueing Networks Pattern[str] Core
Core simulation logic for queueing network simulation.
"""

from __future__ import annotations

import logging
from collections import deque
from typing import Any

import numpy as np

from .config import ArrivalProcess, QueueingNetworkConfig, QueueingNodeConfig


logger = logging.getLogger(__name__)

class QueueingNetworkSimulator:
    """Discrete-event simulator for queueing networks"""

    def __init__(self, config: QueueingNetworkConfig) -> None:
        self.config = config

        # Initialize routing matrix if not provided
        if self.config.routing_matrix is None:
            self._initialize_default_routing()

        # Simulation state
        self.time: float = 0.0
        self.event_queue: list[tuple[float, str, dict[str, Any]]] = []  # (time, type, data)
        self.node_queues: dict[str, deque] = {}
        self.server_busy: dict[str, list[dict[str, Any] | None]] = {}

        # Statistics
        self.node_stats: dict[str, dict[str, Any]] = {}
        self.customer_stats: list[dict[str, Any]] = []

        # Jackson network solution
        self.throughput: np.ndarray | None = None
        self.node_utilization: np.ndarray | None = None
        self.mean_queue_length: np.ndarray | None = None
        self.mean_waiting_time: np.ndarray | None = None

        self._initialize_network()

    def _initialize_default_routing(self) -> None:
        """Create default routing matrix (tandem network)"""
        cfg = self.config
        n_nodes = len(cfg.nodes)

        # Default: tandem network (source -> 1 -> 2 -> ... -> sink)
        cfg.routing_matrix = np.zeros((n_nodes, n_nodes))

        for i in range(n_nodes - 1):
            cfg.routing_matrix[i, i + 1] = 1.0

    def _initialize_network(self) -> None:
        """Initialize network state"""
        cfg = self.config

        for _i, node in enumerate(cfg.nodes):
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
        if node.service_dist.value == "exponential":
            return np.random.exponential(1.0 / node.service_rate)

        elif node.service_dist.value == "deterministic":
            return 1.0 / node.service_rate

        elif node.service_dist.value == "erlang":
            # k-stage Erlang = sum of k exponentials
            return np.random.gamma(
                node.erlang_stages, 1.0 / (node.erlang_stages * node.service_rate)
            )

        elif node.service_dist.value == "uniform":
            mean = 1.0 / node.service_rate
            return np.random.uniform(mean * 0.5, mean * 1.5)

        else:
            return np.random.exponential(1.0 / node.service_rate)

    def _schedule_event(self, event_time: float, event_type: str, data: dict[str, Any]) -> None:
        """Schedule a future event"""
        self.event_queue.append((event_time, event_type, data))
        self.event_queue.sort(key=lambda x: x[0])

    def _update_node_stats(self, node_name: str, new_time: float) -> None:
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

    def _handle_arrival(self, event_data: dict[str, Any]) -> None:
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

    def _handle_departure(self, event_data: dict[str, Any]) -> None:
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

    def _route_customer(self, customer: dict[str, Any], from_idx: int) -> None:
        """Route customer to next node based on routing matrix"""
        cfg = self.config

        # Get routing probabilities
        probs = cfg.routing_matrix[from_idx]  # type: ignore[index]

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

    def _calculate_jackson_solution(self) -> None:
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
            self.throughput = np.linalg.solve(I - R.T, lambda_ext)  # type: ignore[union-attr]
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

    def run_simulation(self) -> dict[str, Any]:
        """Run the discrete-event simulation"""
        cfg = self.config

        # Schedule first arrival
        next_arrival = self._generate_interarrival_time()
        customer_id = 0

        self._schedule_event(
            next_arrival,
            "arrival",
            {
                "customer": {"id": customer_id, "arrival_times": {}, "wait_times": {}}
                , "node": cfg.nodes[0].name,
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

        return self._compute_results()

    def _compute_results(self) -> dict[str, Any]:
        """Compute and return simulation results"""
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
                "utilization": self.node_utilization.tolist(),  # type: ignore[union-attr]
                "mean_queue_length": self.mean_queue_length.tolist(),  # type: ignore[union-attr]
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

    def _compute_simulation_statistics(self) -> dict[str, Any]:
        """Compute statistics from simulation"""
        cfg = self.config

        results = {}

        for node_name, stats in self.node_stats.items():
            node_idx = self._find_node_index(node_name)
            node_config = cfg.nodes[node_idx]

            # Time-average queue length
            if len(stats["queue_length_samples"]) > 1:
                times, lengths = zip(*stats["queue_length_samples"], strict=False)
                (
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

    def _compute_system_metrics(self) -> dict[str, float]:
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
