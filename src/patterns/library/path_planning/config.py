"""
C4REQBER v6.0 - Path Planning Pattern[str] Configuration
Configuration classes for path planning algorithms.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np


class PlannerType(Enum):
    """Available path planning algorithms"""

    RRT = "rrt"
    RRT_STAR = "rrt_star"
    A_STAR = "a_star"
    DIJKSTRA = "dijkstra"
    PRM = "prm"  # Probabilistic Roadmap

class EnvironmentType(Enum):
    """Environment types"""

    EMPTY = "empty"
    RANDOM_OBSTACLES = "random_obstacles"
    MAZE = "maze"
    CLUTTERED = "cluttered"
    CUSTOM = "custom"

@dataclass
class PathPlanningConfig:
    """Configuration for path planning"""

    # Planner selection
    planner_type: PlannerType = PlannerType.RRT_STAR

    # Environment
    environment_type: EnvironmentType = EnvironmentType.RANDOM_OBSTACLES
    dimensions: int = 2
    bounds: tuple[np.ndarray, np.ndarray] = field(
        default_factory=lambda: (np.array([0.0, 0.0]), np.array([10.0, 10.0]))
    )

    # Obstacles (list[Any] of (center, radius) for circles)
    obstacles: list[tuple[np.ndarray, float]] = field(default_factory=list[Any])
    n_obstacles: int = 10
    obstacle_radius: float = 0.5

    # Start and goal
    start: np.ndarray = field(default_factory=lambda: np.array([0.5, 0.5]))
    goal: np.ndarray = field(default_factory=lambda: np.array([9.5, 9.5]))
    goal_radius: float = 0.5

    # RRT/RRT* parameters
    max_iterations: int = 5000
    step_size: float = 0.5
    rewire_factor: float = 1.5  # For RRT*

    # A*/Dijkstra parameters
    grid_resolution: float = 0.5

    # PRM parameters
    n_samples: int = 500
    connection_radius: float = 2.0

    # Output
    output_waypoints: bool = True

    def __post_init__(self) -> None:
        """Generate environment if needed"""
        if self.environment_type == EnvironmentType.RANDOM_OBSTACLES:
            self._generate_random_obstacles()
        elif self.environment_type == EnvironmentType.MAZE:
            self._generate_maze()

    def _generate_random_obstacles(self) -> None:
        """Generate random circular obstacles"""
        np.random.seed(42)
        low, high = self.bounds

        for _ in range(self.n_obstacles):
            center = np.random.uniform(low, high)
            # Ensure start and goal are not inside obstacles
            if (
                np.linalg.norm(center - self.start) > 2 * self.obstacle_radius
                and np.linalg.norm(center - self.goal) > 2 * self.obstacle_radius
            ):
                self.obstacles.append((center, self.obstacle_radius))

    def _generate_maze(self) -> None:
        """Generate simple maze-like obstacles"""
        # Create grid of walls
        low, high = self.bounds
        size = high - low

        # Vertical walls
        for i in range(1, 5):
            x = low[0] + i * size[0] / 5
            gap_y = low[1] + (i % 2) * size[1] / 2

            # Wall with gap
            if self.dimensions == 2:
                # Top part
                self.obstacles.append((np.array([x, gap_y + size[1] / 4]), 0.3))
                self.obstacles.append((np.array([x, gap_y + size[1] / 4 + 0.6]), 0.3))
                # Bottom part
                self.obstacles.append((np.array([x, gap_y - size[1] / 4]), 0.3))
                self.obstacles.append((np.array([x, gap_y - size[1] / 4 - 0.6]), 0.3))
