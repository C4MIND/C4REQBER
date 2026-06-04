"""
Agent-Based Simulation Pattern
Production-grade multi-agent simulation using Mesa framework

Based on:
- Joshua Epstein & Robert Axtell's Sugarscape
- Uri Wilensky's NetLogo principles
- Modern Mesa framework best practices
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable

import numpy as np

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


class AgentType(Enum):
    """Types of agents in the simulation"""
    CONSUMER = "consumer"
    PRODUCER = "producer"
    REGULATOR = "regulator"
    INNOVATOR = "innovator"
    COMPETITOR = "competitor"


class AgentBehavior(Enum):
    """Behavior patterns for agents"""
    RATIONAL = "rational"  # Utility maximization
    BOUNDED = "bounded"    # Bounded rationality
    IMITATIVE = "imitative"  # Copy neighbors
    EXPLORATORY = "exploratory"  # Random exploration
    ADAPTIVE = "adaptive"  # Learning/adapting


@dataclass
class AgentBasedConfig:
    """Configuration for Agent-Based simulation"""
    n_agents: int = 100
    n_steps: int = 1000
    grid_size: tuple[int, int] = (50, 50)
    agent_behavior: str = "adaptive"  # See AgentBehavior
    agent_types: list[str] = None  # type: ignore  # See AgentType
    interaction_radius: int = 1

    # Network parameters
    network_type: str = "grid"  # 'grid', 'small_world', 'scale_free', 'random'
    network_rewire_prob: float = 0.1

    # Learning parameters
    learning_rate: float = 0.1
    exploration_rate: float = 0.1

    # Emergence detection
    detect_phase_transitions: bool = True
    emergence_window: int = 50

    # Parallelization
    batch_size: int = 10
    random_seed: int | None = None

    def __post_init__(self) -> None:
        if self.agent_types is None:
            self.agent_types = ["consumer", "producer"]  # type: ignore[unreachable]


@dataclass
class Agent:
    """Individual agent in the simulation"""
    agent_id: int
    agent_type: AgentType
    position: tuple[int, int]
    state: dict[str, float] = None  # type: ignore[assignment]
    neighbors: list[int] = None  # type: ignore[assignment]
    history: list[dict[str, Any]] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.state is None:
            self.state = {"wealth": 100.0, "satisfaction": 0.5, "innovation": 0.0}  # type: ignore[unreachable]
        if self.neighbors is None:
            self.neighbors = []  # type: ignore[unreachable]
        if self.history is None:
            self.history = []  # type: ignore[unreachable]


@simulation_pattern(
    id="agent_based",
    name="Agent-Based Simulation",
    category="agent",
    description="Multi-agent simulation with emergent behavior detection",
)
class AgentBasedPattern(SimulationPattern):
    """
    Agent-based simulation pattern for complex adaptive systems

    Implements:
    - Heterogeneous agents with different behaviors
    - Network-based interactions
    - Emergence detection (phase transitions)
    - Macro-level pattern extraction
    - Multiple behavior models (rational, bounded, adaptive)
    """

    parameters = [
        SimulationParameter(
            name="n_agents",
            type="int",
            default=100,
            min=10,
            max=10000,
            description="Number of agents in simulation",
        ),
        SimulationParameter(
            name="n_steps",
            type="int",
            default=1000,
            min=100,
            max=100000,
            description="Number of simulation steps",
        ),
        SimulationParameter(
            name="grid_size",
            type="int",
            default=50,
            min=10,
            max=500,
            description="Size of simulation grid (N x N)",
        ),
        SimulationParameter(
            name="agent_behavior",
            type="select",
            default="adaptive",
            options=["rational", "bounded", "imitative", "exploratory", "adaptive"],
            description="Agent behavior model",
        ),
        SimulationParameter(
            name="network_type",
            type="select",
            default="grid",
            options=["grid", "small_world", "scale_free", "random"],
            description="Network topology for agent interactions",
        ),
        SimulationParameter(
            name="learning_rate",
            type="float",
            default=0.1,
            min=0.0,
            max=1.0,
            description="Rate at which agents learn/adapt",
        ),
        SimulationParameter(
            name="detect_emergence",
            type="bool",
            default=True,
            description="Detect emergent patterns and phase transitions",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.rng = np.random.default_rng()
        self.agents: dict[int, Agent] = {}
        self.step_count = 0
        self.metrics_history: list[dict[str, float]] = []
        self.phase_transitions: list[dict[str, Any]] = []

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """
        Agent-based can simulate hypotheses with:
        - Multiple interacting entities
        - Emergent behavior
        - Network effects
        - Adaptation/learning
        """
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()

        agent_keywords = [
            "agent",
            "multi-agent",
            "emergence",
            "network",
            "collective",
            " swarm",
            "flock",
            "herd",
            "market",
            "diffusion",
            "adoption",
            "contagion",
            "cascade",
            "viral",
            "social",
            "interaction",
            "behavior",
        ]

        return any(kw in title or kw in desc for kw in agent_keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute Agent-Based simulation"""
        start_time = datetime.now()
        simulation_id = f"abm_{start_time.timestamp()}"

        logger.info(f"Starting Agent-Based simulation {simulation_id}")

        # Parse configuration
        abm_config = self._parse_config(config)

        if abm_config.random_seed:
            self.rng = np.random.default_rng(abm_config.random_seed)

        try:
            # Initialize simulation
            self._initialize_simulation(hypothesis, abm_config)

            # Run simulation steps
            await self._run_simulation(abm_config)

            # Analyze results
            results = self._analyze_results(abm_config)

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
            logger.exception("Agent-Based simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> AgentBasedConfig:
        """Parse configuration dict into AgentBasedConfig"""
        return AgentBasedConfig(
            n_agents=config.get("n_agents", 100),
            n_steps=config.get("n_steps", 1000),
            grid_size=(config.get("grid_size", 50), config.get("grid_size", 50)),
            agent_behavior=config.get("agent_behavior", "adaptive"),
            network_type=config.get("network_type", "grid"),
            learning_rate=config.get("learning_rate", 0.1),
            detect_phase_transitions=config.get("detect_emergence", True),
            random_seed=config.get("random_seed"),
        )

    def _initialize_simulation(
        self, hypothesis: Hypothesis, config: AgentBasedConfig
    ) -> None:
        """Initialize agents and network"""
        self.agents = {}
        self.step_count = 0
        self.metrics_history = []
        self.phase_transitions = []

        # Create network topology
        network = self._create_network(config)

        # Create agents
        for i in range(config.n_agents):
            agent_type = self._select_agent_type(i, config)
            position = self._select_position(config)

            # Initialize state from hypothesis parameters
            state = self._initialize_agent_state(hypothesis, agent_type)

            agent = Agent(
                agent_id=i,
                agent_type=agent_type,
                position=position,
                state=state,
                neighbors=network.get(i, []),
            )
            self.agents[i] = agent

    def _create_network(self, config: AgentBasedConfig) -> dict[int, list[int]]:
        """Create network topology"""
        n = config.n_agents
        network = defaultdict(list)

        if config.network_type == "grid":
            # Grid-based network (von Neumann neighborhood)
            grid_w = int(np.sqrt(n))
            for i in range(n):
                x, y = i % grid_w, i // grid_w
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < grid_w and 0 <= ny < grid_w:
                        neighbor = ny * grid_w + nx
                        if neighbor < n:
                            network[i].append(neighbor)

        elif config.network_type == "small_world":
            # Watts-Strogatz small-world
            k = 4  # Each node connected to k nearest neighbors
            for i in range(n):
                for j in range(1, k // 2 + 1):
                    neighbor = (i + j) % n
                    network[i].append(neighbor)
                    network[neighbor].append(i)

            # Rewire with probability p
            for i in range(n):
                for j in list(network[i]):
                    if i < j and self.rng.random() < config.network_rewire_prob:
                        # Rewire
                        network[i].remove(j)
                        network[j].remove(i)
                        new_neighbor = self.rng.integers(0, n)
                        if new_neighbor != i:
                            network[i].append(int(new_neighbor))

        elif config.network_type == "random":
            # Erdos-Renyi random graph
            p = 0.1  # Connection probability
            for i in range(n):
                for j in range(i + 1, n):
                    if self.rng.random() < p:
                        network[i].append(j)
                        network[j].append(i)

        elif config.network_type == "scale_free":
            # Barabasi-Albert preferential attachment
            m = 2  # New edges per node
            for i in range(m):
                for j in range(i + 1, m):
                    network[i].append(j)
                    network[j].append(i)

            for i in range(m, n):
                degrees = [len(network[j]) for j in range(i)]
                total = sum(degrees)
                if total == 0:
                    probs = [1.0 / i] * i
                else:
                    probs = [d / total for d in degrees]

                targets = self.rng.choice(i, size=min(m, i), replace=False, p=probs)
                for target in targets:
                    network[i].append(int(target))
                    network[int(target)].append(i)

        return dict(network)

    def _select_agent_type(self, agent_id: int, config: AgentBasedConfig) -> AgentType:
        """Select agent type based on distribution"""
        types = [AgentType(t) for t in config.agent_types]
        return types[agent_id % len(types)]

    def _select_position(self, config: AgentBasedConfig) -> tuple[int, int]:
        """Select random position on grid"""
        x = self.rng.integers(0, config.grid_size[0])
        y = self.rng.integers(0, config.grid_size[1])
        return (int(x), int(y))

    def _initialize_agent_state(
        self, hypothesis: Hypothesis, agent_type: AgentType
    ) -> dict[str, float]:
        """Initialize agent state from hypothesis"""
        params = hypothesis.parameters

        state = {
            "wealth": params.get(f"{agent_type.value}_initial_wealth", 100.0),
            "satisfaction": self.rng.random(),
            "innovation": params.get("innovation_rate", 0.1) * self.rng.random(),
            "risk_tolerance": params.get("risk_tolerance", 0.5),
            "social_influence": params.get("social_influence", 0.3),
        }
        return state

    async def _run_simulation(self, config: AgentBasedConfig) -> None:
        """Run simulation for n_steps"""
        behavior_fn = self._get_behavior_function(config.agent_behavior)

        for step in range(config.n_steps):
            self.step_count = step

            # Update all agents
            await self._update_agents(behavior_fn, config)

            # Record metrics
            metrics = self._compute_metrics()
            self.metrics_history.append(metrics)

            # Detect phase transitions
            if config.detect_phase_transitions and step > config.emergence_window:
                self._detect_phase_transition(step, config)

            # Yield control periodically
            if step % 100 == 0:
                await asyncio.sleep(0)

    def _get_behavior_function(self, behavior: str) -> Callable:
        """Get behavior update function"""
        behaviors = {
            "rational": self._rational_behavior,
            "bounded": self._bounded_rationality,
            "imitative": self._imitative_behavior,
            "exploratory": self._exploratory_behavior,
            "adaptive": self._adaptive_behavior,
        }
        return behaviors.get(behavior, self._adaptive_behavior)

    async def _update_agents(
        self, behavior_fn: Callable, config: AgentBasedConfig
    ) -> None:
        """Update all agents in parallel batches"""
        agent_ids = list(self.agents.keys())

        for i in range(0, len(agent_ids), config.batch_size):
            batch = agent_ids[i:i + config.batch_size]

            for agent_id in batch:
                agent = self.agents[agent_id]
                new_state = behavior_fn(agent, config)

                # Record history
                agent.history.append({
                    "step": self.step_count,
                    "state": agent.state.copy(),
                })

                # Update state
                agent.state = new_state

    def _rational_behavior(self, agent: Agent, config: AgentBasedConfig) -> dict[str, float]:
        """Rational utility maximization"""
        new_state = agent.state.copy()

        # Trade with neighbors to maximize wealth
        if agent.neighbors:
            neighbor_id = self.rng.choice(agent.neighbors)
            neighbor = self.agents[neighbor_id]

            # Simple trade: if both benefit
            trade_amount = min(agent.state["wealth"], neighbor.state["wealth"]) * 0.1
            if trade_amount > 0:
                new_state["wealth"] += trade_amount * 0.05  # Small gain from trade
                new_state["satisfaction"] = min(1.0, new_state["satisfaction"] + 0.01)

        return new_state

    def _bounded_rationality(self, agent: Agent, config: AgentBasedConfig) -> dict[str, float]:
        """Bounded rationality (limited information)"""
        new_state = agent.state.copy()

        # Only consider subset of neighbors
        visible_neighbors = agent.neighbors[:3] if len(agent.neighbors) > 3 else agent.neighbors

        if visible_neighbors and self.rng.random() < 0.3:  # 30% chance to interact
            neighbor_id = self.rng.choice(visible_neighbors)
            neighbor = self.agents[neighbor_id]

            # Imitate if neighbor is better off
            if neighbor.state["wealth"] > agent.state["wealth"]:
                new_state["innovation"] = 0.8 * new_state["innovation"] + 0.2 * neighbor.state["innovation"]

        return new_state

    def _imitative_behavior(self, agent: Agent, config: AgentBasedConfig) -> dict[str, float]:
        """Imitate most successful neighbor"""
        new_state = agent.state.copy()

        if agent.neighbors:
            # Find most successful neighbor
            best_neighbor = max(
                (self.agents[nid] for nid in agent.neighbors),
                key=lambda a: a.state["wealth"]
            )

            # Imitate with probability based on difference
            wealth_diff = best_neighbor.state["wealth"] - agent.state["wealth"]
            imitate_prob = min(0.8, wealth_diff / (agent.state["wealth"] + 1))

            if self.rng.random() < imitate_prob:
                new_state["innovation"] = best_neighbor.state["innovation"]
                new_state["risk_tolerance"] = 0.7 * new_state["risk_tolerance"] + 0.3 * best_neighbor.state["risk_tolerance"]

        return new_state

    def _exploratory_behavior(self, agent: Agent, config: AgentBasedConfig) -> dict[str, float]:
        """Random exploration"""
        new_state = agent.state.copy()

        # Random walk in state space
        if self.rng.random() < config.exploration_rate:
            new_state["innovation"] += self.rng.normal(0, 0.1)
            new_state["risk_tolerance"] += self.rng.normal(0, 0.05)

            # Boundary conditions
            new_state["innovation"] = np.clip(new_state["innovation"], 0, 1)
            new_state["risk_tolerance"] = np.clip(new_state["risk_tolerance"], 0, 1)

        return new_state

    def _adaptive_behavior(self, agent: Agent, config: AgentBasedConfig) -> dict[str, float]:
        """Adaptive learning (Q-learning inspired)"""
        new_state = agent.state.copy()

        # Remember previous state
        if len(agent.history) > 0:
            prev_state = agent.history[-1]["state"]
            reward = new_state["wealth"] - prev_state["wealth"]

            # Update based on reward
            if reward > 0:
                # Reinforce successful behavior
                new_state["innovation"] += config.learning_rate * reward * 0.01
            else:
                # Explore when failing
                new_state["innovation"] += self.rng.normal(0, 0.05)

        # Social learning from neighbors
        if agent.neighbors and self.rng.random() < agent.state["social_influence"]:
            neighbor_id = self.rng.choice(agent.neighbors)
            neighbor = self.agents[neighbor_id]
            new_state["innovation"] = (1 - config.learning_rate) * new_state["innovation"] + config.learning_rate * neighbor.state["innovation"]

        # Innovation generates wealth
        innovation_return = new_state["innovation"] * new_state["risk_tolerance"] * self.rng.exponential(1.0)
        new_state["wealth"] += innovation_return - 0.5  # Cost of innovation
        new_state["wealth"] = max(0, new_state["wealth"])  # Non-negative wealth

        # Satisfaction based on wealth change and absolute level
        new_state["satisfaction"] = 0.5 * (new_state["wealth"] / (new_state["wealth"] + 100)) + 0.5 * new_state["satisfaction"]

        return new_state

    def _compute_metrics(self) -> dict[str, float]:
        """Compute aggregate metrics"""
        if not self.agents:
            return {}

        wealths = [a.state["wealth"] for a in self.agents.values()]
        satisfactions = [a.state["satisfaction"] for a in self.agents.values()]
        innovations = [a.state["innovation"] for a in self.agents.values()]

        # Gini coefficient for inequality
        gini = self._gini_coefficient(wealths)

        # Network clustering
        clustering = self._compute_clustering()

        return {
            "mean_wealth": float(np.mean(wealths)),
            "std_wealth": float(np.std(wealths)),
            "gini_coefficient": gini,
            "mean_satisfaction": float(np.mean(satisfactions)),
            "mean_innovation": float(np.mean(innovations)),
            "clustering_coefficient": clustering,
            "n_agents": len(self.agents),
        }

    def _gini_coefficient(self, values: list[float]) -> float:
        """Calculate Gini coefficient for inequality"""
        if not values or sum(values) == 0:
            return 0.0
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        cumsum = np.cumsum(sorted_vals)
        return (n + 1 - 2 * sum(cumsum) / cumsum[-1]) / n if cumsum[-1] > 0 else 0.0

    def _compute_clustering(self) -> float:
        """Compute network clustering coefficient"""
        if not self.agents:
            return 0.0

        coeffs = []
        for agent in self.agents.values():
            neighbors = agent.neighbors
            if len(neighbors) < 2:
                continue

            # Count edges between neighbors
            edges = 0
            for i, ni in enumerate(neighbors):
                for nj in neighbors[i+1:]:
                    if nj in self.agents[ni].neighbors:
                        edges += 1

            possible = len(neighbors) * (len(neighbors) - 1) / 2
            if possible > 0:
                coeffs.append(edges / possible)

        return float(np.mean(coeffs)) if coeffs else 0.0

    def _detect_phase_transition(self, step: int, config: AgentBasedConfig) -> None:
        """Detect phase transitions using change point detection"""
        window = config.emergence_window
        if len(self.metrics_history) < window * 2:
            return

        # Look at recent metrics
        recent = self.metrics_history[-window:]
        previous = self.metrics_history[-window*2:-window]

        # Check for significant changes in key metrics
        for metric in ["mean_wealth", "gini_coefficient", "clustering_coefficient"]:
            recent_vals = [m.get(metric, 0) for m in recent]
            prev_vals = [m.get(metric, 0) for m in previous]

            recent_mean = np.mean(recent_vals)
            prev_mean = np.mean(prev_vals)
            recent_std = np.std(recent_vals)
            prev_std = np.std(prev_vals)

            # Detect significant shift
            if prev_std > 0:
                z_score = abs(recent_mean - prev_mean) / prev_std
                if z_score > 2.0:  # 2 sigma shift
                    self.phase_transitions.append({
                        "step": step,
                        "metric": metric,
                        "previous_mean": prev_mean,
                        "new_mean": recent_mean,
                        "z_score": z_score,
                    })

    def _analyze_results(self, config: AgentBasedConfig) -> dict[str, Any]:
        """Analyze simulation results"""
        if not self.metrics_history:
            return {"metrics": {}, "logs": ["No simulation data"]}

        # Final metrics
        final_metrics = self.metrics_history[-1]

        # Time series analysis
        wealth_series = [m.get("mean_wealth", 0) for m in self.metrics_history]
        gini_series = [m.get("gini_coefficient", 0) for m in self.metrics_history]

        # Trend analysis
        wealth_trend = np.polyfit(range(len(wealth_series)), wealth_series, 1)[0]

        # Equilibrium detection
        last_100 = wealth_series[-100:] if len(wealth_series) >= 100 else wealth_series
        equilibrium_cv = np.std(last_100) / np.mean(last_100) if np.mean(last_100) > 0 else 1.0
        reached_equilibrium = equilibrium_cv < 0.05

        metrics = {
            "final_mean_wealth": final_metrics.get("mean_wealth", 0),
            "final_gini": final_metrics.get("gini_coefficient", 0),
            "final_clustering": final_metrics.get("clustering_coefficient", 0),
            "wealth_trend": float(wealth_trend),
            "equilibrium_reached": float(reached_equilibrium),
            "phase_transitions": len(self.phase_transitions),
            "n_steps": self.step_count,
        }

        logs = [
            f"Simulation ran for {self.step_count} steps",
            f"Final mean wealth: {metrics['final_mean_wealth']:.2f}",
            f"Final Gini coefficient: {metrics['final_gini']:.4f}",
            f"Wealth trend: {metrics['wealth_trend']:.4f} per step",
            f"Equilibrium reached: {reached_equilibrium}",
            f"Phase transitions detected: {len(self.phase_transitions)}",
        ]

        if self.phase_transitions:
            for pt in self.phase_transitions[:3]:  # Show first 3
                logs.append(
                    f"  Step {pt['step']}: {pt['metric']} shifted (z={pt['z_score']:.2f})"
                )

        return {"metrics": metrics, "logs": logs}

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score based on simulation quality"""
        metrics = results["metrics"]

        # Factors contributing to confidence
        factors = []

        # 1. Equilibrium reached (stable system)
        if metrics.get("equilibrium_reached", 0) > 0.5:
            factors.append(0.2)

        # 2. Low variance in final state
        if metrics.get("final_gini", 1.0) < 0.5:
            factors.append(0.2)

        # 3. Clear trends (predictable behavior)
        if abs(metrics.get("wealth_trend", 0)) > 0.01:
            factors.append(0.2)

        # 4. Sufficient steps
        if metrics.get("n_steps", 0) > 500:
            factors.append(0.2)

        # 5. Phase transitions detected (interesting dynamics)
        if metrics.get("phase_transitions", 0) > 0:
            factors.append(0.1)

        return min(0.9, sum(factors))  # Cap at 0.9 for ABM

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        params = hypothesis.parameters
        n_agents = params.get("n_agents", 100)
        n_steps = params.get("n_steps", 1000)

        # Rough estimation: 1000 agent-steps per second
        estimated_time = (n_agents * n_steps) / 1000

        return {
            "cpu_cores": 4,
            "memory_gb": 1.0 + n_agents / 1000,  # ~1MB per agent
            "gpu_required": False,
            "estimated_time_seconds": estimated_time,
        }
