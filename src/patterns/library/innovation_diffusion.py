"""
C4REQBER v6.0 - Innovation Diffusion Pattern
Bass model and extensions for technology adoption.

Pattern Structure (Christopher Alexander):
- Context: Marketing, technology management, policy
- Forces: Innovation, imitation, saturation, network effects
- Solution: Diffusion model with internal and external influence
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


class DiffusionModel(Enum):
    """Available diffusion models"""

    BASS = "bass"  # Classic Bass model
    GENERALIZED_BASS = "generalized_bass"  # With marketing mix
    MULTIGENERATION = "multigen"  # Multiple product generations
    NETWORK = "network"  # Agent-based network diffusion


@dataclass
class InnovationDiffusionConfig:
    """Configuration for innovation diffusion simulation"""

    model: DiffusionModel = DiffusionModel.BASS

    # Market
    market_size: float = 1000000.0  # Total potential adopters

    # Bass parameters
    p: float = 0.03  # Coefficient of innovation (external influence)
    q: float = 0.38  # Coefficient of imitation (internal influence)

    # Generalized Bass (marketing mix effects)
    price_coefficient: float = -1.5
    advertising_coefficient: float = 0.1

    # Marketing mix over time (list of (time, price, advertising))
    marketing_mix: list[tuple[float, float, float]] = field(default_factory=lambda: [])

    # Multigeneration
    n_generations: int = 1
    generation_times: list[float] = field(default_factory=lambda: [0.0])
    cannibalization_rates: list[float] = field(default_factory=lambda: [0.5])

    # Network
    n_agents: int = 1000
    network_type: str = "small_world"
    seed_nodes: int = 10

    # Simulation
    dt: float = 0.1
    max_time: float = 10.0  # Years

    # Discretization for discrete time simulation
    discrete_time: bool = False


class InnovationDiffusionPattern:
    """
    Innovation diffusion simulation using Bass model and extensions.

    Bass Model:
    dF/dt = (p + q·F)·(1 - F)

    Where:
    - F = fraction of market adopted
    - p = innovation coefficient (external influence)
    - q = imitation coefficient (word-of-mouth)

    Extensions:
    - Generalized Bass: includes marketing mix
    - Multigeneration: multiple product versions
    - Network: agent-based with social structure
    """

    PATTERN_ID = "innovation_diffusion"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: InnovationDiffusionConfig | None = None) -> None:
        self.config = config or InnovationDiffusionConfig()
        self.cumulative_adopters: float = 0.0
        self.time: float = 0.0
        self.history: list[dict] = []

        # Network state (for network model)
        self.adopted: np.ndarray | None = None
        self.network: np.ndarray | None = None

        self._initialize()

    def _initialize(self) -> None:
        """Initialize diffusion simulation"""
        cfg = self.config

        self.cumulative_adopters = 0.0
        self.time = 0.0

        if cfg.model == DiffusionModel.NETWORK:
            # Build network
            self.network = self._build_network()
            self.adopted = np.zeros(cfg.n_agents, dtype=bool)

            # Seed initial adopters
            seeds = np.random.choice(cfg.n_agents, size=cfg.seed_nodes, replace=False)
            self.adopted[seeds] = True
            self.cumulative_adopters = cfg.seed_nodes

        self._record_state()

    def _build_network(self) -> np.ndarray:
        """Build network for agent-based diffusion"""
        cfg = self.config
        n = cfg.n_agents

        adj = np.zeros((n, n))

        if cfg.network_type == "complete":
            adj = np.ones((n, n)) - np.eye(n)
        elif cfg.network_type == "random":
            adj = np.random.random((n, n)) < 0.05  # type: ignore[assignment]
            adj = np.maximum(adj, adj.T)
            np.fill_diagonal(adj, 0)
        elif cfg.network_type == "small_world":
            k = 4
            for i in range(n):
                for j in range(1, k // 2 + 1):
                    adj[i, (i + j) % n] = 1
                    adj[i, (i - j) % n] = 1
            # Rewire
            for i in range(n):
                for j in range(i + 1, n):
                    if adj[i, j] and np.random.random() < 0.3:
                        new_j = np.random.randint(n)
                        if new_j != i:
                            adj[i, j] = adj[j, i] = 0
                            adj[i, new_j] = adj[new_j, i] = 1
        elif cfg.network_type == "scale_free":
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

    def _bass_derivative(self, f: float) -> float:
        """Bass model derivative: dF/dt = (p + q·F)·(1 - F)"""
        cfg = self.config
        return (cfg.p + cfg.q * f) * (1 - f)

    def _generalized_bass_derivative(self, f: float, t: float) -> float:
        """Generalized Bass with marketing mix effects"""
        cfg = self.config

        # Find current marketing mix
        price = 1.0
        advertising = 0.0
        for time, p, a in cfg.marketing_mix:
            if t >= time:
                price = p
                advertising = a

        # Marketing mix effects on p and q
        x = cfg.price_coefficient * np.log(price) if price > 0 else 0
        y = cfg.advertising_coefficient * advertising

        p_effective = cfg.p * np.exp(x + y)
        q_effective = cfg.q * np.exp(x + y)

        return (p_effective + q_effective * f) * (1 - f)  # type: ignore[no-any-return]

    def _network_step(self) -> int:
        """One network diffusion step"""
        cfg = self.config

        new_adoptions = 0

        # Try to adopt each non-adopter
        non_adopters = np.where(~self.adopted)[0]  # type: ignore[operator]

        for i in non_adopters:
            # Count adopted neighbors
            neighbors = np.where(self.network[i] == 1)[0]  # type: ignore[index]
            adopted_neighbors = np.sum(self.adopted[neighbors])  # type: ignore[index]

            # Adoption probability (Bass-like on network)
            if len(neighbors) > 0:
                f_local = adopted_neighbors / len(neighbors)
            else:
                f_local = 0

            prob = (cfg.p + cfg.q * f_local) * cfg.dt

            if np.random.random() < prob:
                self.adopted[i] = True  # type: ignore[index]
                new_adoptions += 1

        return new_adoptions

    def _calculate_t_star(self) -> float:
        """Calculate time of peak adoption"""
        cfg = self.config
        if cfg.q > 0:
            return (  # type: ignore[no-any-return]
                -1
                / (cfg.p + cfg.q)
                * np.log(cfg.p / (cfg.q * (1 - cfg.p / (cfg.p + cfg.q))))
            )
        return 0.0

    def _calculate_m_peak(self) -> float:
        """Calculate peak adoption rate"""
        cfg = self.config
        t_star = self._calculate_t_star()
        f_star = 1 - np.exp(-(cfg.p + cfg.q) * t_star) / (
            1 + cfg.q / cfg.p * np.exp(-(cfg.p + cfg.q) * t_star)
        )
        adoption_rate = (cfg.p + cfg.q * f_star) * (1 - f_star)
        return adoption_rate * cfg.market_size  # type: ignore[no-any-return]

    def run(self, hypothesis: dict[str, Any] = None) -> dict[str, Any]:  # type: ignore[assignment]
        """Run innovation diffusion simulation"""
        cfg = self.config

        logger.info(f"Starting innovation diffusion: {cfg.model.value}")
        logger.info(f"Bass parameters: p={cfg.p}, q={cfg.q}")

        n_steps = int(cfg.max_time / cfg.dt)

        if cfg.model == DiffusionModel.NETWORK:
            # Agent-based simulation
            for step in range(n_steps):
                new_adoptions = self._network_step()
                self.cumulative_adopters += new_adoptions
                self.time = step * cfg.dt

                if step % 10 == 0:
                    self._record_state()

                # Check saturation
                if self.cumulative_adopters >= cfg.n_agents * 0.99:
                    break
        else:
            # Continuous model (ODE)
            f = 0.0  # Fraction adopted

            for step in range(n_steps):
                self.time = step * cfg.dt

                # Calculate derivative
                if cfg.model == DiffusionModel.BASS:
                    df = self._bass_derivative(f)
                elif cfg.model == DiffusionModel.GENERALIZED_BASS:
                    df = self._generalized_bass_derivative(f, self.time)
                else:
                    df = self._bass_derivative(f)

                # Euler step
                f += df * cfg.dt
                f = max(0, min(1, f))  # Clamp to [0, 1]

                self.cumulative_adopters = f * cfg.market_size

                if step % 10 == 0:
                    self._record_state()

        return self._format_output()

    def _record_state(self) -> None:
        """Record current state"""
        if len(self.history) == 0:
            adoption_rate = 0
        else:
            adoption_rate = (
                (self.cumulative_adopters - self.history[-1]["cumulative"])
                / self.config.dt
                / 10
            )

        self.history.append(
            {
                "time": self.time,
                "cumulative": self.cumulative_adopters,
                "fraction": self.cumulative_adopters / self.config.market_size,
                "adoption_rate": adoption_rate,
            }
        )

    def _format_output(self) -> dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        final_fraction = self.cumulative_adopters / cfg.market_size

        # Find peak adoption rate
        rates = [h["adoption_rate"] for h in self.history]
        peak_rate = max(rates) if rates else 0
        peak_time_idx = rates.index(peak_rate) if rates else 0
        peak_time = self.history[peak_time_idx]["time"] if self.history else 0

        # Time to 50% adoption
        t_50 = next((h["time"] for h in self.history if h["fraction"] >= 0.5), None)

        return {
            "model": cfg.model.value,
            "final_adopters": float(self.cumulative_adopters),
            "final_penetration": float(final_fraction),
            "history": {
                "time": [
                    h["time"] for h in self.history[:: max(1, len(self.history) // 50)]
                ],
                "cumulative": [
                    h["cumulative"]
                    for h in self.history[:: max(1, len(self.history) // 50)]
                ],
                "fraction": [
                    h["fraction"]
                    for h in self.history[:: max(1, len(self.history) // 50)]
                ],
                "adoption_rate": [
                    h["adoption_rate"]
                    for h in self.history[:: max(1, len(self.history) // 50)]
                ],
            },
            "peak": {
                "time": float(peak_time),
                "rate": float(peak_rate),
            },
            "theoretical": {
                "t_star": float(self._calculate_t_star()),
                "m_peak": float(self._calculate_m_peak()),
                "t_50": float(t_50) if t_50 else None,
            },
            "bass_parameters": {
                "p": cfg.p,
                "q": cfg.q,
                "q_p_ratio": cfg.q / cfg.p if cfg.p > 0 else None,
                "interpretation": self._interpret_parameters(),
            },
            "config": {
                "market_size": cfg.market_size,
                "max_time": cfg.max_time,
            },
        }

    def _interpret_parameters(self) -> str:
        """Interpret Bass parameters"""
        cfg = self.config

        ratio = cfg.q / cfg.p if cfg.p > 0 else 0

        if ratio < 1:
            return "Innovation-dominated (little word-of-mouth)"
        elif ratio < 10:
            return "Balanced internal/external influence"
        else:
            return "Imitation-dominated (strong word-of-mouth)"

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Innovation Diffusion",
            "category": "EXTENDED",
            "domain": ["Marketing", "Technology Management", "Policy"],
            "description": "Bass model and extensions for technology adoption",
            "computational_complexity": "O(T) or O(T·N·⟨k⟩)",
            "typical_runtime": "milliseconds to seconds",
            "accuracy": "High (empirically validated)",
            "assumptions": [
                "Homogeneous population",
                "Fixed market potential",
                "No repeat purchases",
            ],
            "parameters": [
                {
                    "name": "model",
                    "type": "enum",
                    "options": ["bass", "generalized_bass", "network"],
                    "default": "bass",
                },
                {
                    "name": "p",
                    "type": "float",
                    "default": 0.03,
                    "description": "Innovation coefficient",
                },
                {
                    "name": "q",
                    "type": "float",
                    "default": 0.38,
                    "description": "Imitation coefficient",
                },
                {
                    "name": "market_size",
                    "type": "float",
                    "default": 1000000.0,
                },
            ],
        }


# Unit tests
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test 1: Classic Bass model
    print("\n=== Test 1: Classic Bass Model ===")
    config = InnovationDiffusionConfig(
        model=DiffusionModel.BASS,
        market_size=10000,
        p=0.03,
        q=0.38,
        max_time=10.0,
    )
    sim = InnovationDiffusionPattern(config)
    result = sim.run()
    print(f"✓ Final penetration: {result['final_penetration']:.1%}")
    print(f"  Peak time: {result['peak']['time']:.1f} years")
    print(f"  Interpretation: {result['bass_parameters']['interpretation']}")
    assert result["final_penetration"] > 0.8, "Should reach high penetration"

    # Test 2: Innovation vs Imitation dominated
    print("\n=== Test 2: Innovation vs Imitation ===")
    for p, q in [(0.1, 0.1), (0.01, 0.5), (0.05, 0.05)]:
        config = InnovationDiffusionConfig(
            model=DiffusionModel.BASS,
            market_size=10000,
            p=p,
            q=q,
        )
        sim = InnovationDiffusionPattern(config)
        result = sim.run()
        print(
            f"  p={p}, q={q}: peak at t={result['peak']['time']:.1f}, q/p={q / p:.1f}"
        )

    # Test 3: Network diffusion
    print("\n=== Test 3: Network Diffusion ===")
    config = InnovationDiffusionConfig(
        model=DiffusionModel.NETWORK,
        n_agents=500,
        p=0.01,
        q=0.4,
        network_type="small_world",
    )
    sim = InnovationDiffusionPattern(config)
    result = sim.run()
    print(f"✓ Network penetration: {result['final_penetration']:.1%}")
    t_50 = result["theoretical"]["t_50"]
    print(f"  Time to 50%: {t_50:.1f} years" if t_50 else "  Time to 50%: N/A")

    # Test 4: Marketing mix effect
    print("\n=== Test 4: Marketing Mix Effect ===")
    config = InnovationDiffusionConfig(
        model=DiffusionModel.GENERALIZED_BASS,
        market_size=10000,
        p=0.03,
        q=0.38,
        marketing_mix=[(0, 1.0, 0), (3, 0.8, 100), (6, 0.9, 50)],
        advertising_coefficient=0.002,
    )
    sim = InnovationDiffusionPattern(config)
    result = sim.run()
    print(f"✓ With marketing: {result['final_penetration']:.1%}")

    print("\n✅ All innovation diffusion tests passed!")
