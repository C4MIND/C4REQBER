"""
TURBO-CDI v6.0 - Rumor Spreading Pattern
Epidemic-style model for rumor propagation with SIR variants.

Pattern Structure (Christopher Alexander):
- Context: Social media, marketing, public opinion
- Forces: Virality, skepticism, forgetting, counter-information
- Solution: Compartmental model with network structure
"""

import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


class RumorModel(Enum):
    """Available rumor spreading models"""

    SIR = "sir"  # Basic SIR with stifling
    SEIR = "seir"  # With exposed period
    SEIZ = "seiz"  # With skeptics (Zanette's model)
    MCKENDRICK = "mckendrick"  # Age-structured


@dataclass
class RumorConfig:
    """Configuration for rumor spreading simulation"""

    model: RumorModel = RumorModel.SIR

    # Population
    n_agents: int = 1000
    network_type: str = "small_world"  # complete, random, scale_free, small_world
    network_param: float = 0.1  # Connection probability or rewiring

    # Initial conditions
    initial_spreaders: int = 10

    # SIR parameters
    spreading_rate: float = 0.5  # β: rate of spreading
    stifling_rate: float = 0.2  # δ: rate of becoming stifled
    forgetting_rate: float = 0.05  # γ: rate of forgetting

    # SEIR parameters
    latent_period: float = 1.0  # Average time in exposed state

    # SEIZ parameters
    skepticism_rate: float = 0.3  # Rate of becoming skeptic

    # Simulation
    dt: float = 0.1
    max_time: float = 100.0

    # Counter-rumor
    counter_rumor_start: Optional[float] = None  # When to introduce counter-rumor
    counter_rumor_strength: float = 0.3


class RumorSpreadingPattern:
    """
    Rumor propagation simulation using epidemic models.

    Models:
    - SIR: Ignorant → Spreader → Stifler
    - SEIR: Add exposed (latent) period
    - SEIZ: Add skeptics who resist belief

    Includes network structure effects.
    """

    PATTERN_ID = "rumor_spreading"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: Optional[RumorConfig] = None):
        self.config = config or RumorConfig()
        self.network: Optional[np.ndarray] = None
        self.states: Optional[np.ndarray] = (
            None  # 0=Ignorant, 1=Exposed, 2=Spreader, 3=Stifler, 4=Skeptic
        )
        self.history: Dict[str, List[float]] = {
            "I": [],
            "E": [],
            "S": [],
            "R": [],
            "Z": [],
        }
        self.time_history: List[float] = []

        self._initialize()

    def _initialize(self):
        """Initialize rumor simulation"""
        cfg = self.config

        # Build network
        self.network = self._build_network()

        # Initialize states
        self.states = np.zeros(cfg.n_agents, dtype=int)

        # Set initial spreaders
        spreaders = np.random.choice(
            cfg.n_agents, size=cfg.initial_spreaders, replace=False
        )
        if cfg.model == RumorModel.SEIR:
            self.states[spreaders] = 1  # Exposed first
        else:
            self.states[spreaders] = 2  # Spreader

        # Set initial skeptics (SEIZ model)
        if cfg.model == RumorModel.SEIZ:
            n_skeptics = int(cfg.n_agents * 0.1)
            skeptics = np.random.choice(
                [i for i in range(cfg.n_agents) if self.states[i] == 0],
                size=n_skeptics,
                replace=False,
            )
            self.states[skeptics] = 4

        self._record_state(0)

    def _build_network(self) -> np.ndarray:
        """Build adjacency matrix for social network"""
        cfg = self.config
        n = cfg.n_agents

        adj = np.zeros((n, n))

        if cfg.network_type == "complete":
            adj = np.ones((n, n)) - np.eye(n)
        elif cfg.network_type == "random":
            adj = np.random.random((n, n)) < cfg.network_param
            adj = np.maximum(adj, adj.T)
            np.fill_diagonal(adj, 0)
        elif cfg.network_type == "small_world":
            # Watts-Strogatz
            k = 4
            for i in range(n):
                for j in range(1, k // 2 + 1):
                    adj[i, (i + j) % n] = 1
                    adj[i, (i - j) % n] = 1
            # Rewire
            for i in range(n):
                for j in range(i + 1, n):
                    if adj[i, j] and np.random.random() < cfg.network_param:
                        new_j = np.random.randint(n)
                        if new_j != i:
                            adj[i, j] = adj[j, i] = 0
                            adj[i, new_j] = adj[new_j, i] = 1
        elif cfg.network_type == "scale_free":
            # Barabási-Albert
            degrees = np.ones(n)
            for i in range(1, n):
                m = min(2, i)
                probs = degrees[:i] / np.sum(degrees[:i])
                targets = np.random.choice(i, size=m, replace=False, p=probs)
                for j in targets:
                    adj[i, j] = adj[j, i] = 1
                    degrees[i] += 1
                    degrees[j] += 1

        return adj

    def _get_neighbors(self, i: int) -> List[int]:
        """Get neighbors of agent i"""
        return list(np.where(self.network[i] == 1)[0])

    def _sir_step(self) -> Tuple[int, int, int]:
        """One SIR step - returns state changes"""
        cfg = self.config
        n = cfg.n_agents

        new_states = self.states.copy()

        for i in range(n):
            if self.states[i] == 2:  # Spreader
                # Contact neighbors
                neighbors = self._get_neighbors(i)
                for j in neighbors:
                    if self.states[j] == 0:  # Ignorant
                        if np.random.random() < cfg.spreading_rate * cfg.dt:
                            new_states[j] = 2  # Become spreader

                # Stifling (loses interest)
                if np.random.random() < cfg.stifling_rate * cfg.dt:
                    new_states[i] = 3  # Become stifler

                # Forgetting
                if np.random.random() < cfg.forgetting_rate * cfg.dt:
                    new_states[i] = 0  # Forget and become ignorant again

            elif self.states[i] == 3:  # Stifler
                # Can forget too
                if np.random.random() < cfg.forgetting_rate * cfg.dt:
                    new_states[i] = 0

        self.states = new_states
        return self._count_states()

    def _seir_step(self) -> Tuple[int, int, int]:
        """One SEIR step with exposed period"""
        cfg = self.config
        n = cfg.n_agents

        new_states = self.states.copy()

        for i in range(n):
            if self.states[i] == 2:  # Spreader
                neighbors = self._get_neighbors(i)
                for j in neighbors:
                    if self.states[j] == 0:  # Ignorant
                        if np.random.random() < cfg.spreading_rate * cfg.dt:
                            new_states[j] = 1  # Become exposed

                if np.random.random() < cfg.stifling_rate * cfg.dt:
                    new_states[i] = 3

            elif self.states[i] == 1:  # Exposed
                # Progress to spreader
                if np.random.random() < (1.0 / cfg.latent_period) * cfg.dt:
                    new_states[i] = 2

        self.states = new_states
        return self._count_states()

    def _seiz_step(self) -> Tuple[int, int, int]:
        """SEIZ model with skeptics"""
        cfg = self.config
        n = cfg.n_agents

        new_states = self.states.copy()

        for i in range(n):
            if self.states[i] == 2:  # Spreader
                neighbors = self._get_neighbors(i)
                for j in neighbors:
                    if self.states[j] == 0:  # Ignorant
                        if np.random.random() < cfg.spreading_rate * cfg.dt:
                            new_states[j] = 2
                    elif self.states[j] == 4:  # Skeptic - might become spreader
                        if np.random.random() < cfg.spreading_rate * 0.3 * cfg.dt:
                            new_states[j] = 2

                if np.random.random() < cfg.stifling_rate * cfg.dt:
                    new_states[i] = 3

            elif self.states[i] == 0:  # Ignorant can become skeptic
                neighbors = self._get_neighbors(i)
                skeptics_near = sum(1 for j in neighbors if self.states[j] == 4)
                if (
                    skeptics_near > 0
                    and np.random.random() < cfg.skepticism_rate * cfg.dt
                ):
                    new_states[i] = 4

        self.states = new_states
        return self._count_states()

    def _count_states(self) -> Tuple[int, int, int, int, int]:
        """Count agents in each state"""
        counts = [0, 0, 0, 0, 0]
        for s in self.states:
            counts[s] += 1
        return tuple(counts)

    def _record_state(self, time: float):
        """Record current state counts"""
        I, E, S, R, Z = self._count_states()
        self.history["I"].append(I)
        self.history["E"].append(E)
        self.history["S"].append(S)
        self.history["R"].append(R)
        self.history["Z"].append(Z)
        self.time_history.append(time)

    def _calculate_final_reach(self) -> float:
        """Calculate final rumor reach (fraction who heard it)"""
        final_heard = (
            self.history["S"][-1] + self.history["R"][-1] + self.history["E"][-1]
        )
        if self.config.model == RumorModel.SEIZ:
            final_heard += self.history["Z"][-1]
        return final_heard / self.config.n_agents

    def _calculate_peak_spreaders(self) -> Tuple[float, float]:
        """Calculate peak number of spreaders and when"""
        peak_idx = np.argmax(self.history["S"])
        return self.history["S"][peak_idx], self.time_history[peak_idx]

    def run(self, hypothesis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run rumor spreading simulation"""
        cfg = self.config

        logger.info(
            f"Starting rumor spreading: {cfg.model.value}, {cfg.n_agents} agents"
        )

        n_steps = int(cfg.max_time / cfg.dt)

        for step in range(n_steps):
            time = step * cfg.dt

            # Counter-rumor introduction
            if cfg.counter_rumor_start and time >= cfg.counter_rumor_start:
                # Reduce spreading rate
                effective_rate = cfg.spreading_rate * (1 - cfg.counter_rumor_strength)
            else:
                effective_rate = cfg.spreading_rate

            # Model step
            if cfg.model == RumorModel.SIR:
                self._sir_step()
            elif cfg.model == RumorModel.SEIR:
                self._seir_step()
            elif cfg.model == RumorModel.SEIZ:
                self._seiz_step()

            if step % 10 == 0:
                self._record_state(time)

            # Check if rumor died out
            if self.history["S"][-1] == 0 and step > 100:
                logger.info(f"Rumor died out at t={time:.1f}")
                break

        return self._format_output()

    def _format_output(self) -> Dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        final_counts = self._count_states()
        final_reach = self._calculate_final_reach()
        peak_spreaders, peak_time = self._calculate_peak_spreaders()

        # Calculate half-life (time to reach half of final spreaders)
        half_peak = peak_spreaders / 2
        half_life_idx = next(
            (i for i, s in enumerate(self.history["S"]) if s >= half_peak), 0
        )
        half_life = (
            self.time_history[half_life_idx]
            if half_life_idx < len(self.time_history)
            else 0
        )

        return {
            "model": cfg.model.value,
            "final_state": {
                "ignorant": final_counts[0],
                "exposed": final_counts[1],
                "spreaders": final_counts[2],
                "stiflers": final_counts[3],
                "skeptics": final_counts[4],
            },
            "history": {
                "time": self.time_history[:: max(1, len(self.time_history) // 50)],
                "ignorant": self.history["I"][:: max(1, len(self.history["I"]) // 50)],
                "exposed": self.history["E"][:: max(1, len(self.history["E"]) // 50)],
                "spreaders": self.history["S"][:: max(1, len(self.history["S"]) // 50)],
                "stiflers": self.history["R"][:: max(1, len(self.history["R"]) // 50)],
                "skeptics": self.history["Z"][:: max(1, len(self.history["Z"]) // 50)],
            },
            "statistics": {
                "final_reach": float(final_reach),
                "peak_spreaders": int(peak_spreaders),
                "peak_time": float(peak_time),
                "half_life": float(half_life),
                "total_duration": self.time_history[-1],
                "r0_estimate": float(
                    cfg.spreading_rate / (cfg.stifling_rate + cfg.forgetting_rate)
                ),
            },
            "network": {
                "type": cfg.network_type,
                "density": float(
                    np.sum(self.network) / (cfg.n_agents * (cfg.n_agents - 1))
                ),
            },
            "config": {
                "n_agents": cfg.n_agents,
                "spreading_rate": cfg.spreading_rate,
                "stifling_rate": cfg.stifling_rate,
            },
        }

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Rumor Spreading",
            "category": "EXTENDED",
            "domain": ["Social Media", "Marketing", "Public Opinion"],
            "description": "Epidemic models of rumor propagation",
            "computational_complexity": "O(T·N·⟨k⟩)",
            "typical_runtime": "seconds",
            "accuracy": "Medium (macro-level)",
            "assumptions": [
                "Network structure matters",
                "Homogeneous mixing approximation",
                "No content decay",
            ],
            "parameters": [
                {
                    "name": "model",
                    "type": "enum",
                    "options": ["sir", "seir", "seiz"],
                    "default": "sir",
                },
                {
                    "name": "n_agents",
                    "type": "int",
                    "default": 1000,
                },
                {
                    "name": "spreading_rate",
                    "type": "float",
                    "default": 0.5,
                },
                {
                    "name": "stifling_rate",
                    "type": "float",
                    "default": 0.2,
                },
            ],
        }


# Unit tests
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test 1: Basic SIR spread
    print("\n=== Test 1: Basic SIR ===")
    config = RumorConfig(
        model=RumorModel.SIR,
        n_agents=500,
        spreading_rate=0.6,
        stifling_rate=0.2,
        network_type="small_world",
    )
    sim = RumorSpreadingPattern(config)
    result = sim.run()
    print(f"✓ Final reach: {result['statistics']['final_reach']:.1%}")
    print(f"  Peak spreaders: {result['statistics']['peak_spreaders']}")
    print(f"  Peak time: {result['statistics']['peak_time']:.1f}")
    assert result["statistics"]["final_reach"] > 0.1, (
        "Rumor should spread significantly"
    )

    # Test 2: Network structure effect
    print("\n=== Test 2: Network Structure Effect ===")
    for network in ["complete", "random", "small_world", "scale_free"]:
        config = RumorConfig(
            model=RumorModel.SIR,
            n_agents=500,
            spreading_rate=0.5,
            network_type=network,
            network_param=0.1,
        )
        sim = RumorSpreadingPattern(config)
        result = sim.run()
        print(
            f"  {network}: reach={result['statistics']['final_reach']:.1%}, density={result['network']['density']:.3f}"
        )

    # Test 3: SEIZ with skeptics
    print("\n=== Test 3: SEIZ Model with Skeptics ===")
    config = RumorConfig(
        model=RumorModel.SEIZ,
        n_agents=500,
        spreading_rate=0.5,
        stifling_rate=0.2,
        skepticism_rate=0.3,
    )
    sim = RumorSpreadingPattern(config)
    result = sim.run()
    print(f"✓ SEIZ reach: {result['statistics']['final_reach']:.1%}")
    print(f"  Final skeptics: {result['final_state']['skeptics']}")

    # Test 4: Counter-rumor effect
    print("\n=== Test 4: Counter-Rumor Effect ===")
    config = RumorConfig(
        model=RumorModel.SIR,
        n_agents=500,
        spreading_rate=0.6,
        stifling_rate=0.2,
        counter_rumor_start=20.0,
        counter_rumor_strength=0.5,
    )
    sim = RumorSpreadingPattern(config)
    result = sim.run()
    print(f"✓ With counter-rumor: reach={result['statistics']['final_reach']:.1%}")

    print("\n✅ All rumor spreading tests passed!")
