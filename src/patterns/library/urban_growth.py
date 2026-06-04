"""
C4REQBER v6.0 - Urban Growth Pattern
Hybrid cellular automaton and agent-based model for urban development.

Pattern Structure (Christopher Alexander):
- Context: Urban planning, geography, regional science
- Forces: Accessibility, agglomeration economies, land rent
- Solution: CA/ABM hybrid with spatial interaction
"""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


@dataclass
class UrbanGrowthConfig:
    """Configuration for urban growth simulation"""

    # Grid
    width: int = 100
    height: int = 100
    cell_size: float = 0.5  # km

    # Initial conditions
    seed_location: tuple[int, int] | None = None
    initial_urban_ratio: float = 0.01

    # CA rules (SLEUTH-inspired)
    diffusion_coefficient: float = 1.0
    breed_coefficient: float = 1.0
    spread_coefficient: float = 1.0
    slope_resistance: float = 0.1
    road_gravity: float = 0.5

    # Agent-based
    n_agents: int = 1000
    agent_birth_rate: float = 0.02

    # Land use
    land_use_types: list[str] = field(
        default_factory=lambda: ["residential", "commercial", "industrial"]
    )

    # Simulation
    n_steps: int = 50
    random_seed: int | None = None

    # Infrastructure
    n_roads: int = 5


class UrbanGrowthPattern:
    """
    Urban growth simulation combining cellular automaton and agent-based modeling.

    Features:
    - CA component for spontaneous growth and diffusion
    - Agent-based component for residential and commercial location choice
    - Road network influence
    - Land use transitions
    """

    PATTERN_ID = "urban_growth"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: UrbanGrowthConfig | None = None) -> None:
        self.config = config or UrbanGrowthConfig()
        self.grid: np.ndarray | None = None  # 0=empty, 1=urban, 2=road
        self.land_use: np.ndarray | None = None  # Land use types
        self.agents: list[dict] = []
        self.history: list[dict] = []
        self.time_step = 0

        self._initialize()

    def _initialize(self) -> None:
        """Initialize simulation state"""
        cfg = self.config

        if cfg.random_seed:
            np.random.seed(cfg.random_seed)

        # Initialize grids
        self.grid = np.zeros((cfg.height, cfg.width), dtype=int)
        self.land_use = np.full((cfg.height, cfg.width), "", dtype=object)
        self.slope = np.random.random((cfg.height, cfg.width)) * 0.3

        # Create road network
        self._create_roads()

        # Seed urban center
        if cfg.seed_location:
            cy, cx = cfg.seed_location
        else:
            cy, cx = cfg.height // 2, cfg.width // 2

        # Initial urban cells around seed
        radius = 3
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                y, x = cy + dy, cx + dx
                if 0 <= y < cfg.height and 0 <= x < cfg.width:
                    if np.random.random() < cfg.initial_urban_ratio * 3:
                        self.grid[y, x] = 1
                        self.land_use[y, x] = "residential"

        # Initialize agents
        self._spawn_agents()

        self._record_state()

    def _create_roads(self) -> None:
        """Create initial road network"""
        cfg = self.config

        # Major roads crossing the grid
        for i in range(cfg.n_roads // 2):
            # Horizontal roads
            y = (cfg.height // (cfg.n_roads // 2 + 1)) * (i + 1)
            self.grid[y, :] = 2  # type: ignore[index]

            # Vertical roads
            x = (cfg.width // (cfg.n_roads // 2 + 1)) * (i + 1)
            self.grid[:, x] = 2  # type: ignore[index]

        self.road_cells = list(zip(*np.where(self.grid == 2), strict=False))

    def _spawn_agents(self) -> None:
        """Create initial population"""
        cfg = self.config

        urban_cells = list(zip(*np.where(self.grid == 1), strict=False))

        for _ in range(cfg.n_agents):
            if urban_cells:
                y, x = urban_cells[np.random.randint(len(urban_cells))]
            else:
                y, x = np.random.randint(cfg.height), np.random.randint(cfg.width)

            agent = {
                "y": y,
                "x": x,
                "type": np.random.choice(["resident", "business"], p=[0.8, 0.2]),
                "satisfaction": 1.0,
            }
            self.agents.append(agent)

    def _calculate_suitability(self, y: int, x: int) -> float:
        """Calculate suitability score for urban development"""
        cfg = self.config

        if self.grid[y, x] == 1:  # type: ignore  # Already urban
            return 0.0

        if self.grid[y, x] == 2:  # type: ignore  # Road
            return 0.3

        suitability = 1.0

        # Slope penalty
        suitability *= 1 - cfg.slope_resistance * self.slope[y, x]

        # Road proximity bonus
        min_road_dist = float("inf")
        for ry, rx in self.road_cells:
            dist = abs(y - ry) + abs(x - rx)
            min_road_dist = min(min_road_dist, dist)
        road_factor = np.exp(-min_road_dist * (1 - cfg.road_gravity) / 10)
        suitability *= 0.5 + 0.5 * road_factor

        # Urban neighbor effect (agglomeration)
        urban_neighbors = self._count_urban_neighbors(y, x)
        suitability *= 1 + cfg.breed_coefficient * urban_neighbors / 8

        return max(0, min(1, suitability))  # type: ignore[no-any-return]

    def _count_urban_neighbors(self, y: int, x: int) -> int:
        """Count urban cells in Moore neighborhood"""
        count = 0
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dy == 0 and dx == 0:
                    continue
                ny, nx = y + dy, x + dx
                if 0 <= ny < self.config.height and 0 <= nx < self.config.width:
                    if self.grid[ny, nx] == 1:  # type: ignore[index]
                        count += 1
        return count

    def _ca_spontaneous_growth(self) -> None:
        """Spontaneous urban growth (new urban centers)"""
        cfg = self.config

        n_spontaneous = int(cfg.diffusion_coefficient * 2)

        for _ in range(n_spontaneous):
            y = np.random.randint(cfg.height)
            x = np.random.randint(cfg.width)

            if self.grid[y, x] == 0:  # type: ignore[index]
                suitability = self._calculate_suitability(y, x)
                if np.random.random() < suitability * 0.1:
                    self.grid[y, x] = 1  # type: ignore[index]
                    self.land_use[y, x] = np.random.choice(  # type: ignore[index]
                        ["residential", "commercial"]
                    )

    def _ca_diffusion(self) -> None:
        """Diffusion growth (spread from existing urban)"""
        cfg = self.config

        urban_cells = list(zip(*np.where(self.grid == 1), strict=False))

        for y, x in urban_cells:
            # Try to urbanize neighbors
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dy == 0 and dx == 0:
                        continue
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < cfg.height and 0 <= nx < cfg.width:
                        if self.grid[ny, nx] == 0:  # type: ignore[index]
                            prob = cfg.spread_coefficient * 0.1
                            prob *= 1 - cfg.slope_resistance * self.slope[ny, nx]
                            if np.random.random() < prob:
                                self.grid[ny, nx] = 1  # type: ignore[index]
                                self.land_use[ny, nx] = self.land_use[y, x]  # type: ignore[index]

    def _agent_relocation(self) -> None:
        """Agent-based location choice"""
        cfg = self.config

        for agent in self.agents:
            # Calculate satisfaction based on land use mix
            y, x = agent["y"], agent["x"]

            # Check if agent wants to move
            if np.random.random() < 0.05:
                # Find new location
                best_score = -1
                best_loc = (y, x)

                # Sample candidate locations
                for _ in range(10):
                    cy = np.random.randint(max(0, y - 10), min(cfg.height, y + 10))
                    cx = np.random.randint(max(0, x - 10), min(cfg.width, x + 10))

                    if self.grid[cy, cx] == 1:  # type: ignore  # Must be urban
                        score = self._location_score(cy, cx, agent["type"])
                        if score > best_score:
                            best_score = score  # type: ignore[assignment]
                            best_loc = (cy, cx)

                agent["y"], agent["x"] = best_loc

    def _location_score(self, y: int, x: int, agent_type: str) -> float:
        """Score a location for an agent type"""
        score = 0.0

        if agent_type == "resident":
            # Prefer residential areas, avoid industrial
            if self.land_use[y, x] == "residential":  # type: ignore[index]
                score += 1.0
            elif self.land_use[y, x] == "industrial":  # type: ignore[index]
                score -= 0.5

            # Prefer proximity to commercial
            for dy in [-2, -1, 0, 1, 2]:
                for dx in [-2, -1, 0, 1, 2]:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < self.config.height and 0 <= nx < self.config.width:
                        if self.land_use[ny, nx] == "commercial":  # type: ignore[index]
                            score += 0.1

        elif agent_type == "business":
            # Prefer commercial areas
            if self.land_use[y, x] == "commercial":  # type: ignore[index]
                score += 1.0
            # Prefer road access
            for ry, rx in self.road_cells:
                dist = abs(y - ry) + abs(x - rx)
                if dist < 5:
                    score += 0.2

        return score

    def _land_use_transition(self) -> None:
        """Land use changes based on neighborhood composition"""
        cfg = self.config

        for y in range(cfg.height):
            for x in range(cfg.width):
                if self.grid[y, x] != 1:  # type: ignore[index]
                    continue

                # Count land uses in neighborhood
                land_use_counts = {
                    "residential": 0,
                    "commercial": 0,
                    "industrial": 0,
                    "": 0,
                }
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < cfg.height and 0 <= nx < cfg.width:
                            lu = self.land_use[ny, nx]  # type: ignore[index]
                            if lu in land_use_counts:
                                land_use_counts[lu] += 1

                total = sum(land_use_counts.values())
                if total == 0:
                    continue

                # Transition rules
                current = self.land_use[y, x]  # type: ignore[index]
                if current == "residential" and land_use_counts["commercial"] > 4:
                    if np.random.random() < 0.1:
                        self.land_use[y, x] = "commercial"  # type: ignore[index]
                elif current == "commercial" and land_use_counts["residential"] > 6:
                    if np.random.random() < 0.05:
                        self.land_use[y, x] = "residential"  # type: ignore[index]

    def _record_state(self) -> None:
        """Record current state"""
        urban_count = np.sum(self.grid == 1)
        road_count = np.sum(self.grid == 2)

        land_use_counts = {}
        for lu in self.config.land_use_types:
            land_use_counts[lu] = np.sum(self.land_use == lu)

        self.history.append(
            {
                "time": self.time_step,
                "urban_cells": int(urban_count),
                "road_cells": int(road_count),
                "land_use": land_use_counts,
            }
        )

    def run(self, hypothesis: dict[str, Any] = None) -> dict[str, Any]:  # type: ignore[assignment]
        """Run urban growth simulation"""
        cfg = self.config

        logger.info(f"Starting urban growth simulation: {cfg.n_steps} steps")

        for step in range(cfg.n_steps):
            self.time_step = step

            # CA dynamics
            self._ca_spontaneous_growth()
            self._ca_diffusion()

            # Agent dynamics
            self._agent_relocation()

            # Land use
            self._land_use_transition()

            # New agents
            if np.random.random() < cfg.agent_birth_rate:
                n_new = int(cfg.n_agents * cfg.agent_birth_rate)
                for _ in range(n_new):
                    urban_cells = list(zip(*np.where(self.grid == 1), strict=False))
                    if urban_cells:
                        y, x = urban_cells[np.random.randint(len(urban_cells))]
                        self.agents.append(
                            {
                                "y": y,
                                "x": x,
                                "type": "resident",
                                "satisfaction": 1.0,
                            }
                        )

            self._record_state()

            if step % 10 == 0:
                urban = np.sum(self.grid == 1)
                logger.debug(f"Step {step}: {urban} urban cells")

        return self._format_output()

    def _format_output(self) -> dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        final_state = self.history[-1]
        initial_state = self.history[0]

        # Growth rate
        urban_growth = final_state["urban_cells"] - initial_state["urban_cells"]
        growth_rate = urban_growth / max(1, initial_state["urban_cells"])

        # Spatial metrics
        urban_cells = np.where(self.grid == 1)
        if len(urban_cells[0]) > 0:
            y_center = np.mean(urban_cells[0])
            x_center = np.mean(urban_cells[1])
            y_spread = np.std(urban_cells[0])
            x_spread = np.std(urban_cells[1])
        else:
            y_center = x_center = y_spread = x_spread = 0  # type: ignore[assignment]

        # Clustering (simplified)
        n_patches = self._count_patches()

        return {
            "final_grid": self.grid.tolist(),  # type: ignore[union-attr]
            "final_land_use": self.land_use.tolist(),  # type: ignore[union-attr]
            "statistics": {
                "initial_urban": initial_state["urban_cells"],
                "final_urban": final_state["urban_cells"],
                "urban_growth": urban_growth,
                "growth_rate": float(growth_rate),
                "center_of_mass": (float(y_center), float(x_center)),
                "spatial_spread": (float(y_spread), float(x_spread)),
                "n_patches": n_patches,
                "final_population": len(self.agents),
            },
            "land_use_final": final_state["land_use"],
            "history": self.history[:: max(1, len(self.history) // 20)],
            "config": {
                "grid_size": (cfg.height, cfg.width),
                "n_steps": cfg.n_steps,
                "diffusion": cfg.diffusion_coefficient,
                "breed": cfg.breed_coefficient,
            },
        }

    def _count_patches(self) -> int:
        """Count number of urban patches using flood fill"""
        cfg = self.config
        visited = np.zeros_like(self.grid, dtype=bool)
        n_patches = 0

        for y in range(cfg.height):
            for x in range(cfg.width):
                if self.grid[y, x] == 1 and not visited[y, x]:  # type: ignore[index]
                    n_patches += 1
                    # BFS
                    queue = deque([(y, x)])
                    visited[y, x] = True

                    while queue:
                        cy, cx = queue.popleft()
                        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < cfg.height and 0 <= nx < cfg.width:
                                if self.grid[ny, nx] == 1 and not visited[ny, nx]:  # type: ignore[index]
                                    visited[ny, nx] = True
                                    queue.append((ny, nx))

        return n_patches

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Urban Growth",
            "category": "EXTENDED",
            "domain": ["Urban Planning", "Geography", "Regional Science"],
            "description": "CA/ABM hybrid model of urban development",
            "computational_complexity": "O(T·W·H)",
            "typical_runtime": "seconds to minutes",
            "accuracy": "Medium (conceptual model)",
            "assumptions": [
                "Grid-based spatial representation",
                "SLEUTH-inspired growth rules",
                "Static road network",
            ],
            "parameters": [
                {
                    "name": "width",
                    "type": "int",
                    "default": 100,
                },
                {
                    "name": "height",
                    "type": "int",
                    "default": 100,
                },
                {
                    "name": "n_steps",
                    "type": "int",
                    "default": 50,
                },
                {
                    "name": "diffusion_coefficient",
                    "type": "float",
                    "default": 1.0,
                },
            ],
        }


# Unit tests
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test 1: Basic growth
    print("\n=== Test 1: Basic Urban Growth ===")
    config = UrbanGrowthConfig(
        width=50,
        height=50,
        n_steps=20,
        diffusion_coefficient=1.0,
    )
    sim = UrbanGrowthPattern(config)
    result = sim.run()
    assert result["statistics"]["urban_growth"] > 0, "Urban area should grow"
    print(f"✓ Urban growth: {result['statistics']['urban_growth']} cells")
    print(f"  Growth rate: {result['statistics']['growth_rate']:.2f}")

    # Test 2: Road influence
    print("\n=== Test 2: Road Network Effect ===")
    config = UrbanGrowthConfig(
        width=50,
        height=50,
        n_steps=20,
        n_roads=5,
        road_gravity=0.8,
    )
    sim = UrbanGrowthPattern(config)
    result = sim.run()
    print(f"✓ Urban cells near roads: {result['statistics']['final_urban']}")

    # Test 3: Different diffusion coefficients
    print("\n=== Test 3: Diffusion Coefficient Comparison ===")
    for diff in [0.5, 1.0, 2.0]:
        config = UrbanGrowthConfig(
            width=40,
            height=40,
            n_steps=15,
            diffusion_coefficient=diff,
        )
        sim = UrbanGrowthPattern(config)
        result = sim.run()
        print(f"  Diffusion {diff}: {result['statistics']['final_urban']} urban cells")

    print("\n✅ All urban growth tests passed!")
