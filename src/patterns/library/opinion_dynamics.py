"""
C4REQBER v6.0 - Opinion Dynamics Pattern
Models how opinions form and evolve in social networks.
Implements DeGroot and Hegselmann-Krause (bounded confidence) models.

Pattern Structure (Christopher Alexander):
- Context: Social networks, political science, marketing
- Forces: Social influence, bounded confidence, consensus vs polarization
- Solution: Iterative opinion update with network structure
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


class OpinionModel(Enum):
    """Available opinion dynamics models"""

    DEGROOT = "degroot"  # Linear consensus model
    HEGSELMANN_KRAUSE = "hk"  # Bounded confidence model
    FRIEDKIN_JOHNSEN = "fj"  # Stubborn agents model


@dataclass
class OpinionDynamicsConfig:
    """Configuration for opinion dynamics simulation"""

    # Model selection
    model: OpinionModel = OpinionModel.HEGSELMANN_KRAUSE

    # Population
    n_agents: int = 100
    n_issues: int = 1  # Number of opinion dimensions

    # Initial opinions
    opinion_range: tuple[float, float] = (-1.0, 1.0)
    initial_distribution: str = "uniform"  # uniform, normal, polarized

    # Network structure
    network_type: str = "complete"  # complete, ring, random, scale_free
    network_param: float = 0.3  # Probability for random network, etc.

    # DeGroot model
    convergence_threshold: float = 1e-6
    max_iterations: int = 1000

    # Hegselmann-Krause (bounded confidence)
    confidence_bound: float = 0.2  # ε parameter

    # Friedkin-Johnsen
    stubbornness: list[float] = field(
        default_factory=list
    )  # 0 = fully open, 1 = fully stubborn

    # Dynamics
    noise_level: float = 0.0  # Additive noise


def _build_network(n: int, network_type: str, param: float) -> np.ndarray:
    """Build adjacency matrix for social network"""
    adj = np.zeros((n, n))

    if network_type == "complete":
        adj = np.ones((n, n)) - np.eye(n)
    elif network_type == "ring":
        for i in range(n):
            adj[i, (i + 1) % n] = 1
            adj[i, (i - 1) % n] = 1
    elif network_type == "random":
        adj = np.random.random((n, n)) < param  # type: ignore[assignment]
        adj = adj.astype(float)
        adj = np.maximum(adj, adj.T)  # Symmetric
        np.fill_diagonal(adj, 0)
    elif network_type == "scale_free":
        # Barabási-Albert preferential attachment
        m = max(1, int(param))
        adj = np.zeros((n, n))
        degrees = np.ones(n)
        for i in range(m, n):
            probs = degrees[:i] / np.sum(degrees[:i])
            targets = np.random.choice(i, size=m, replace=False, p=probs)
            for j in targets:
                adj[i, j] = 1
                adj[j, i] = 1
                degrees[i] += 1
                degrees[j] += 1
    elif network_type == "small_world":
        # Watts-Strogatz
        k = max(2, int(param * n))
        for i in range(n):
            for j in range(1, k // 2 + 1):
                adj[i, (i + j) % n] = 1
                adj[i, (i - j) % n] = 1
        # Rewire with small probability
        for i in range(n):
            for j in range(i + 1, n):
                if adj[i, j] == 1 and np.random.random() < 0.1:
                    new_j = np.random.randint(n)
                    if new_j != i:
                        adj[i, j] = 0
                        adj[j, i] = 0
                        adj[i, new_j] = 1
                        adj[new_j, i] = 1

    return adj


class OpinionDynamicsPattern:
    """
    Opinion dynamics simulation supporting multiple models.

    Models:
    - DeGroot: Linear consensus through weighted averaging
    - Hegselmann-Krause: Bounded confidence (interact only if opinions close)
    - Friedkin-Johnsen: Stubborn agents resist influence
    """

    PATTERN_ID = "opinion_dynamics"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: OpinionDynamicsConfig | None = None) -> None:
        self.config = config or OpinionDynamicsConfig()
        self.opinions: np.ndarray | None = None
        self.history: list[np.ndarray] = []
        self.network: np.ndarray | None = None
        self.consensus_reached: bool = False

        self._initialize()

    def _initialize(self) -> None:
        """Initialize simulation state"""
        cfg = self.config

        # Initialize opinions
        if cfg.initial_distribution == "uniform":
            self.opinions = np.random.uniform(
                cfg.opinion_range[0], cfg.opinion_range[1], (cfg.n_agents, cfg.n_issues)
            )
        elif cfg.initial_distribution == "normal":
            self.opinions = np.random.normal(0, 0.3, (cfg.n_agents, cfg.n_issues))
            self.opinions = np.clip(
                self.opinions, cfg.opinion_range[0], cfg.opinion_range[1]
            )
        elif cfg.initial_distribution == "polarized":
            # Two clusters
            n_half = cfg.n_agents // 2
            self.opinions = np.zeros((cfg.n_agents, cfg.n_issues))
            self.opinions[:n_half] = np.random.uniform(-1, -0.5, (n_half, cfg.n_issues))
            self.opinions[n_half:] = np.random.uniform(
                0.5, 1, (cfg.n_agents - n_half, cfg.n_issues)
            )

        # Build network
        self.network = _build_network(cfg.n_agents, cfg.network_type, cfg.network_param)

        # Normalize network (row stochastic)
        row_sums = self.network.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1  # Avoid division by zero
        self.influence_matrix = self.network / row_sums

        # Initialize stubbornness for FJ model
        if not cfg.stubbornness:
            self.stubbornness = np.random.beta(2, 5, cfg.n_agents)
        else:
            self.stubbornness = np.array(cfg.stubbornness[: cfg.n_agents])

        self.initial_opinions = self.opinions.copy()  # type: ignore[union-attr]
        self.history = [self.opinions.copy()]  # type: ignore[union-attr]

    def _degroot_step(self) -> np.ndarray:
        """One step of DeGroot model (weighted averaging)"""
        return self.influence_matrix @ self.opinions  # type: ignore[no-any-return]

    def _hk_step(self) -> np.ndarray:
        """One step of Hegselmann-Krause (bounded confidence)"""
        cfg = self.config
        new_opinions = np.zeros_like(self.opinions)

        for i in range(cfg.n_agents):
            # Find agents within confidence bound
            distances = np.linalg.norm(self.opinions - self.opinions[i], axis=1)  # type: ignore[index]
            neighbors = distances < cfg.confidence_bound

            if np.sum(neighbors) > 0:
                # Average opinions of neighbors
                new_opinions[i] = np.mean(self.opinions[neighbors], axis=0)  # type: ignore[index]
            else:
                new_opinions[i] = self.opinions[i]  # type: ignore[index]

        return new_opinions

    def _fj_step(self) -> np.ndarray:
        """One step of Friedkin-Johnsen model"""
        stubborn = self.stubbornness[:, np.newaxis]

        # Weighted combination of influence and stubbornness
        influenced = self.influence_matrix @ self.opinions
        new_opinions = stubborn * self.initial_opinions + (1 - stubborn) * influenced

        return new_opinions  # type: ignore[no-any-return]

    def _add_noise(self, opinions: np.ndarray) -> np.ndarray:
        """Add random noise to opinions"""
        if self.config.noise_level > 0:
            noise = np.random.normal(0, self.config.noise_level, opinions.shape)
            opinions = opinions + noise
            opinions = np.clip(
                opinions, self.config.opinion_range[0], self.config.opinion_range[1]
            )
        return opinions

    def run(self, hypothesis: dict[str, Any] = None) -> dict[str, Any]:  # type: ignore[assignment]
        """Run opinion dynamics simulation"""
        cfg = self.config

        logger.info(f"Starting {cfg.model.value} opinion dynamics simulation")

        iterations = 0
        convergence_history = []

        for step in range(cfg.max_iterations):
            # Update opinions based on model
            if cfg.model == OpinionModel.DEGROOT:
                new_opinions = self._degroot_step()
            elif cfg.model == OpinionModel.HEGSELMANN_KRAUSE:
                new_opinions = self._hk_step()
            elif cfg.model == OpinionModel.FRIEDKIN_JOHNSEN:
                new_opinions = self._fj_step()
            else:
                new_opinions = self._hk_step()  # type: ignore[unreachable]

            # Add noise
            new_opinions = self._add_noise(new_opinions)

            # Check convergence
            max_change = np.max(np.abs(new_opinions - self.opinions))
            convergence_history.append(max_change)

            self.opinions = new_opinions
            self.history.append(self.opinions.copy())

            iterations = step + 1

            if max_change < cfg.convergence_threshold:
                self.consensus_reached = True
                logger.info(f"Converged after {iterations} iterations")
                break

        return self._format_output(iterations, convergence_history)

    def _format_output(
        self, iterations: int, convergence_history: list[float]
    ) -> dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        # Calculate final statistics
        final_opinions = self.opinions.flatten()  # type: ignore[union-attr]
        opinion_variance = np.var(final_opinions)
        opinion_range = float(np.max(final_opinions) - np.min(final_opinions))

        # Count clusters (simple threshold-based)
        sorted_opinions = np.sort(final_opinions)
        n_clusters = 1
        for i in range(1, len(sorted_opinions)):
            if sorted_opinions[i] - sorted_opinions[i - 1] > cfg.confidence_bound:
                n_clusters += 1

        # Network metrics
        network_density = np.sum(self.network) / (cfg.n_agents * (cfg.n_agents - 1))  # type: ignore[arg-type]

        return {
            "model": cfg.model.value,
            "iterations": iterations,
            "consensus_reached": self.consensus_reached,
            "final_opinions": self.opinions.tolist(),  # type: ignore[union-attr]
            "opinion_history": [
                h.tolist() for h in self.history[:: max(1, len(self.history) // 100)]
            ],
            "convergence_history": convergence_history,
            "statistics": {
                "mean_opinion": float(np.mean(final_opinions)),
                "opinion_variance": float(opinion_variance),
                "opinion_range": opinion_range,
                "n_clusters": n_clusters,
                "polarization_index": float(
                    opinion_range / 2.0
                ),  # Normalized to [0, 1]
            },
            "network": {
                "density": float(network_density),
                "type": cfg.network_type,
                "adjacency": self.network.tolist() if cfg.n_agents <= 20 else None,  # type: ignore[union-attr]
            },
            "config": {
                "n_agents": cfg.n_agents,
                "confidence_bound": cfg.confidence_bound,
                "max_iterations": cfg.max_iterations,
            },
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Opinion Dynamics",
            "category": "EXTENDED",
            "domain": ["Social Science", "Political Science", "Marketing"],
            "description": "Models opinion formation and evolution in social networks",
            "computational_complexity": "O(T·N²·D)",
            "typical_runtime": "seconds",
            "accuracy": "High (model-dependent)",
            "assumptions": [
                "Social influence through network",
                "Bounded confidence for HK model",
                "Static network structure",
            ],
            "parameters": [
                {
                    "name": "model",
                    "type": "enum",
                    "options": ["degroot", "hk", "fj"],
                    "default": "hk",
                },
                {
                    "name": "n_agents",
                    "type": "int",
                    "default": 100,
                    "description": "Number of agents",
                },
                {
                    "name": "confidence_bound",
                    "type": "float",
                    "default": 0.2,
                    "description": "Bounded confidence threshold",
                },
                {
                    "name": "network_type",
                    "type": "string",
                    "default": "complete",
                    "options": [
                        "complete",
                        "ring",
                        "random",
                        "scale_free",
                        "small_world",
                    ],
                },
            ],
        }


# Unit tests
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test 1: DeGroot model consensus
    print("\n=== Test 1: DeGroot Consensus ===")
    config = OpinionDynamicsConfig(
        model=OpinionModel.DEGROOT,
        n_agents=50,
        initial_distribution="uniform",
        max_iterations=500,
    )
    sim = OpinionDynamicsPattern(config)
    result = sim.run()
    assert result["consensus_reached"], (
        "DeGroot should reach consensus on complete graph"
    )
    assert result["statistics"]["opinion_variance"] < 0.01, (
        "Variance should be near zero"
    )
    print(f"✓ Consensus reached in {result['iterations']} iterations")
    print(f"  Final variance: {result['statistics']['opinion_variance']:.6f}")

    # Test 2: Hegselmann-Krause polarization
    print("\n=== Test 2: HK Polarization ===")
    config = OpinionDynamicsConfig(
        model=OpinionModel.HEGSELMANN_KRAUSE,
        n_agents=100,
        initial_distribution="polarized",
        confidence_bound=0.3,
        network_type="complete",
    )
    sim = OpinionDynamicsPattern(config)
    result = sim.run()
    assert result["statistics"]["n_clusters"] >= 2, (
        "Polarized initial should lead to clusters"
    )
    print(f"✓ Formed {result['statistics']['n_clusters']} opinion clusters")
    print(f"  Polarization index: {result['statistics']['polarization_index']:.3f}")

    # Test 3: Friedkin-Johnsen stubbornness
    print("\n=== Test 3: Friedkin-Johnsen Stubbornness ===")
    config = OpinionDynamicsConfig(
        model=OpinionModel.FRIEDKIN_JOHNSEN,
        n_agents=50,
        initial_distribution="uniform",
        stubbornness=[0.0] * 25 + [0.9] * 25,  # Half stubborn
        max_iterations=500,
    )
    sim = OpinionDynamicsPattern(config)
    result = sim.run()
    # Stubborn agents should prevent full consensus
    assert result["statistics"]["opinion_variance"] > 0.01, (
        "Stubborn agents prevent consensus"
    )
    print("✓ Stubbornness prevents full consensus")
    print(f"  Final variance: {result['statistics']['opinion_variance']:.3f}")

    # Test 4: Network structure effects
    print("\n=== Test 4: Network Effects ===")
    for network_type in ["ring", "random", "scale_free"]:
        config = OpinionDynamicsConfig(
            model=OpinionModel.DEGROOT,
            n_agents=100,
            network_type=network_type,
            network_param=0.3,
            max_iterations=1000,
        )
        sim = OpinionDynamicsPattern(config)
        result = sim.run()
        print(
            f"  {network_type}: {result['iterations']} iterations, density={result['network']['density']:.3f}"
        )

    print("\n✅ All opinion dynamics tests passed!")
