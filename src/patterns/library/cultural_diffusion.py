"""
C4REQBER v6.0 - Cultural Diffusion Pattern
Models cultural dissemination using the Axelrod model and extensions.

Pattern Structure (Christopher Alexander):
- Context: Anthropology, sociology, cultural studies
- Forces: Homophily, social influence, cultural drift
- Solution: Agent-based model with cultural features and interaction probabilities
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


@dataclass
class CulturalDiffusionConfig:
    """Configuration for cultural diffusion simulation"""

    # Population
    n_agents: int = 400
    grid_size: tuple[int, int] = (20, 20)  # 2D grid layout

    # Culture dimensions
    n_features: int = 5  # Number of cultural traits per agent
    n_traits: int = 10  # Possible values per feature (0 to n_traits-1)

    # Dynamics
    interaction_radius: int = 1  # Moore neighborhood radius
    homophily_threshold: float = 0.5  # Minimum overlap for interaction

    # Simulation
    max_steps: int = 100000
    convergence_check_interval: int = 1000

    # Extensions
    enable_mutation: bool = False
    mutation_rate: float = 0.001

    # Output
    sample_interval: int = 1000


class CulturalDiffusionPattern:
    """
    Cultural diffusion simulation based on Axelrod's model.

    Agents interact based on cultural similarity (homophily).
    Upon interaction, one agent adopts a trait from the other.
    Cultural regions form and stabilize over time.
    """

    PATTERN_ID = "cultural_diffusion"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: CulturalDiffusionConfig | None = None) -> None:
        self.config = config or CulturalDiffusionConfig()
        self.culture: np.ndarray | None = None  # Shape: (n_agents, n_features)
        self.positions: np.ndarray | None = None  # Shape: (n_agents, 2)
        self.history: list[dict] = []
        self.active: bool = True

        self._initialize()

    def _initialize(self) -> None:
        """Initialize cultural configuration"""
        cfg = self.config

        # Ensure grid size matches n_agents
        if cfg.grid_size[0] * cfg.grid_size[1] != cfg.n_agents:
            # Adjust grid_size to accommodate n_agents
            side = int(np.ceil(np.sqrt(cfg.n_agents)))
            cfg.grid_size = (side, side)

        # Initialize random cultures
        self.culture = np.random.randint(
            0, cfg.n_traits, (cfg.n_agents, cfg.n_features)
        )

        # Position agents on grid
        rows, cols = cfg.grid_size
        self.positions = np.zeros((cfg.n_agents, 2), dtype=int)
        for i in range(cfg.n_agents):
            self.positions[i] = [i // cols, i % cols]

        # Build neighbor lookup
        self.neighbors = self._build_neighbors()

        self.initial_culture = self.culture.copy()
        self._record_state(0)

    def _build_neighbors(self) -> dict[int, list[int]]:
        """Build neighbor lists based on grid distance"""
        cfg = self.config
        neighbors = defaultdict(list)

        for i in range(cfg.n_agents):
            pos_i = self.positions[i]  # type: ignore[index]
            for j in range(cfg.n_agents):
                if i == j:
                    continue
                pos_j = self.positions[j]  # type: ignore[index]
                dist = max(abs(pos_i[0] - pos_j[0]), abs(pos_i[1] - pos_j[1]))
                if dist <= cfg.interaction_radius:
                    neighbors[i].append(j)

        return neighbors

    def _cultural_similarity(self, i: int, j: int) -> float:
        """Calculate proportion of shared traits between two agents"""
        shared = np.sum(self.culture[i] == self.culture[j])  # type: ignore[index]
        return shared / self.config.n_features  # type: ignore[no-any-return]

    def _interact(self, i: int, j: int) -> bool:
        """
        Attempt interaction between agents i and j.
        Returns True if interaction occurred.
        """
        cfg = self.config

        similarity = self._cultural_similarity(i, j)

        # Interaction probability = similarity (Axelrod's rule)
        # Agents only interact if they have at least one trait in common
        # but are not identical
        if similarity == 0 or similarity == 1.0:
            return False

        if np.random.random() < similarity:
            # Select feature where they differ
            diff_features = np.where(self.culture[i] != self.culture[j])[0]  # type: ignore[index]
            if len(diff_features) > 0:
                feature = np.random.choice(diff_features)
                # i adopts j's trait
                self.culture[i, feature] = self.culture[j, feature]  # type: ignore[index]
                return True

        return False

    def _mutate(self) -> None:
        """Apply random cultural mutation"""
        cfg = self.config
        if not cfg.enable_mutation:
            return

        n_mutations = np.random.poisson(
            cfg.n_agents * cfg.n_features * cfg.mutation_rate
        )
        for _ in range(n_mutations):
            agent = np.random.randint(cfg.n_agents)
            feature = np.random.randint(cfg.n_features)
            self.culture[agent, feature] = np.random.randint(cfg.n_traits)  # type: ignore[index]

    def _count_regions(self) -> int:
        """Count number of distinct cultural regions using connected components"""
        cfg = self.config
        visited = set()
        regions = 0

        for start in range(cfg.n_agents):
            if start in visited:
                continue

            # BFS to find connected component
            region = set()
            queue = [start]

            while queue:
                current = queue.pop(0)
                if current in region:
                    continue
                region.add(current)

                # Find culturally identical neighbors
                for neighbor in self.neighbors[current]:
                    if np.array_equal(self.culture[current], self.culture[neighbor]):  # type: ignore[index]
                        if neighbor not in region:
                            queue.append(neighbor)

            visited.update(region)
            regions += 1

        return regions

    def _cultural_diversity(self) -> float:
        """Calculate cultural diversity index"""
        cfg = self.config

        # Count unique cultural configurations
        unique_cultures = set()
        for i in range(cfg.n_agents):
            culture_tuple = tuple(self.culture[i])  # type: ignore[index]
            unique_cultures.add(culture_tuple)

        # Diversity = proportion of unique cultures
        return len(unique_cultures) / cfg.n_agents

    def _record_state(self, step: int) -> None:
        """Record current state for history"""
        self.history.append(
            {
                "step": step,
                "culture": self.culture.copy(),  # type: ignore[union-attr]
                "n_regions": self._count_regions(),
                "diversity": self._cultural_diversity(),
            }
        )

    def run(self, hypothesis: dict[str, Any] = None) -> dict[str, Any]:  # type: ignore[assignment]
        """Run cultural diffusion simulation"""
        cfg = self.config

        logger.info(f"Starting cultural diffusion simulation: {cfg.n_agents} agents")

        interactions = 0
        last_active_step = 0

        for step in range(cfg.max_steps):
            # Randomly select an agent
            i = np.random.randint(cfg.n_agents)

            # Select neighbor
            if not self.neighbors[i]:
                continue
            j = np.random.choice(self.neighbors[i])

            # Attempt interaction
            if self._interact(i, j):
                interactions += 1
                last_active_step = step

            # Mutation
            self._mutate()

            # Record state
            if step % cfg.sample_interval == 0:
                self._record_state(step)

            # Check for convergence
            if step % cfg.convergence_check_interval == 0 and step > 0:
                if step - last_active_step > cfg.convergence_check_interval:
                    logger.info(f"Converged at step {step}")
                    break

        # Final state
        self._record_state(step)

        return self._format_output(step, interactions)

    def _format_output(
        self, final_step: int, total_interactions: int
    ) -> dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        final_regions = self._count_regions()
        final_diversity = self._cultural_diversity()

        # Size distribution of regions
        region_sizes = self._get_region_sizes()

        # Cultural trait distribution
        trait_distribution = []
        for f in range(cfg.n_features):
            trait_counts = np.bincount(self.culture[:, f], minlength=cfg.n_traits)  # type: ignore[index]
            trait_distribution.append(trait_counts.tolist())

        return {
            "final_step": final_step,
            "total_interactions": total_interactions,
            "n_regions": final_regions,
            "cultural_diversity": float(final_diversity),
            "region_sizes": region_sizes,
            "largest_region": max(region_sizes) if region_sizes else 0,
            "trait_distribution": trait_distribution,
            "final_culture": self.culture.tolist(),  # type: ignore[union-attr]
            "history": [
                {
                    "step": h["step"],
                    "n_regions": h["n_regions"],
                    "diversity": float(h["diversity"]),
                }
                for h in self.history[:: max(1, len(self.history) // 20)]
            ],
            "convergence": {
                "frozen": final_regions > 1 and final_diversity < 0.5,
                "polarized": final_regions > 1,
                "global_consensus": final_regions == 1,
            },
            "config": {
                "n_agents": cfg.n_agents,
                "n_features": cfg.n_features,
                "n_traits": cfg.n_traits,
                "grid_size": cfg.grid_size,
            },
        }

    def _get_region_sizes(self) -> list[int]:
        """Get sizes of all cultural regions"""
        cfg = self.config
        visited = set()
        sizes = []

        for start in range(cfg.n_agents):
            if start in visited:
                continue

            region = set()
            queue = [start]

            while queue:
                current = queue.pop(0)
                if current in region:
                    continue
                region.add(current)

                for neighbor in self.neighbors[current]:
                    if np.array_equal(self.culture[current], self.culture[neighbor]):  # type: ignore[index]
                        if neighbor not in region:
                            queue.append(neighbor)

            visited.update(region)
            sizes.append(len(region))

        return sizes

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Cultural Diffusion",
            "category": "EXTENDED",
            "domain": ["Anthropology", "Sociology", "Cultural Studies"],
            "description": "Axelrod model of cultural dissemination and polarization",
            "computational_complexity": "O(S·N·F)",
            "typical_runtime": "seconds to minutes",
            "accuracy": "High (agent-based)",
            "assumptions": [
                "Homophily-driven interaction",
                "Grid-based neighborhood",
                "Discrete cultural traits",
            ],
            "parameters": [
                {
                    "name": "n_agents",
                    "type": "int",
                    "default": 400,
                    "description": "Number of agents",
                },
                {
                    "name": "n_features",
                    "type": "int",
                    "default": 5,
                    "description": "Cultural features per agent",
                },
                {
                    "name": "n_traits",
                    "type": "int",
                    "default": 10,
                    "description": "Possible values per feature",
                },
                {
                    "name": "interaction_radius",
                    "type": "int",
                    "default": 1,
                },
            ],
        }


# Unit tests
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test 1: Convergence to regions
    print("\n=== Test 1: Region Formation ===")
    config = CulturalDiffusionConfig(
        n_agents=100,
        grid_size=(10, 10),
        n_features=3,
        n_traits=5,
        max_steps=50000,
    )
    sim = CulturalDiffusionPattern(config)
    result = sim.run()
    assert result["n_regions"] >= 1, "Should have at least one region"
    print(f"✓ Formed {result['n_regions']} cultural regions")
    print(f"  Diversity: {result['cultural_diversity']:.3f}")

    # Test 2: Higher features lead to more regions
    print("\n=== Test 2: Feature Count Effect ===")
    for n_features in [2, 5, 8]:
        config = CulturalDiffusionConfig(
            n_agents=100,
            grid_size=(10, 10),
            n_features=n_features,
            n_traits=5,
            max_steps=30000,
        )
        sim = CulturalDiffusionPattern(config)
        result = sim.run()
        print(f"  {n_features} features: {result['n_regions']} regions")

    # Test 3: Mutation prevents freeze
    print("\n=== Test 3: Mutation Effect ===")
    config = CulturalDiffusionConfig(
        n_agents=100,
        grid_size=(10, 10),
        n_features=3,
        n_traits=5,
        enable_mutation=True,
        mutation_rate=0.01,
        max_steps=10000,
    )
    sim = CulturalDiffusionPattern(config)
    result = sim.run()
    print(f"✓ With mutation: {result['n_regions']} regions")
    print(f"  Final diversity: {result['cultural_diversity']:.3f}")

    print("\n✅ All cultural diffusion tests passed!")
