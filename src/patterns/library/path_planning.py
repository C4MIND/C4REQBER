"""
Path Planning Pattern
RRT, RRT*, A*, Dijkstra, and PRM path planning algorithms
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

from .base import BaseConfig, BasePattern


logger = logging.getLogger(__name__)


class PlannerType(Enum):
    """PlannerType."""
    RRT = "rrt"
    RRT_STAR = "rrt_star"
    A_STAR = "a_star"
    DIJKSTRA = "dijkstra"
    PRM = "prm"


class EnvironmentType(Enum):
    """EnvironmentType."""
    EMPTY = "empty"
    RANDOM_OBSTACLES = "random_obstacles"
    MAZE = "maze"
    CLUTTERED = "cluttered"
    CUSTOM = "custom"


@dataclass
class PathPlanningConfig(BaseConfig):
    """Configuration for path planning"""
    planner_type: PlannerType = PlannerType.RRT_STAR
    environment_type: EnvironmentType = EnvironmentType.RANDOM_OBSTACLES
    dimensions: int = 2
    max_iterations: int = 5000
    step_size: float = 0.5
    goal_radius: float = 0.5
    grid_resolution: float = 0.5
    bounds: tuple = field(default_factory=lambda: (np.array([0.0, 0.0]), np.array([10.0, 10.0])))
    start: np.ndarray = field(default_factory=lambda: np.array([0.5, 0.5]))
    goal: np.ndarray = field(default_factory=lambda: np.array([9.5, 9.5]))
    obstacles: list = field(default_factory=list)
    n_obstacles: int = 5
    output_waypoints: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.start, np.ndarray):
            self.start = np.array(self.start, dtype=float)
        if not isinstance(self.goal, np.ndarray):
            self.goal = np.array(self.goal, dtype=float)
        if self.environment_type == EnvironmentType.RANDOM_OBSTACLES and not self.obstacles:
            rng = np.random.default_rng(42)
            low, high = self.bounds
            for _ in range(self.n_obstacles):
                center = rng.random(self.dimensions) * (high - low) + low
                radius = 0.3 + rng.random() * 0.7
                self.obstacles.append((center, radius))
        elif self.environment_type == EnvironmentType.MAZE and not self.obstacles:
            # Simple maze-like obstacles
            for i in range(5):
                self.obstacles.append((np.array([2.0 + i * 1.5, 5.0]), 0.5))


class Node:
    """Node in a path planning tree/graph"""

    def __init__(self, position: np.ndarray, node_id: int | None = None) -> None:
        self.position = np.array(position, dtype=float)
        self.id = node_id
        self.parent: Node | None = None
        self.children: list[Node] = []
        self.cost = 0.0
        self.neighbors: list[Node] = []

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Node):
            return self.cost < other.cost
        return NotImplemented

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Node):
            return np.allclose(self.position, other.position, atol=1e-6)
        return False

    def __hash__(self) -> int:
        return hash(tuple(np.round(self.position, 6)))


class RRTPlanner:
    """RRT and RRT* planner"""

    def __init__(self, config: PathPlanningConfig) -> None:
        self.config = config
        self.nodes: list[Node] = []
        self.rng = np.random.default_rng(42)

    def _is_point_free(self, point: np.ndarray) -> bool:
        for center, radius in self.config.obstacles:
            if np.linalg.norm(point - center) < radius:
                return False
        return True

    def _is_collision_free(self, from_pos: np.ndarray, to_pos: np.ndarray) -> bool:
        if not self._is_point_free(to_pos):
            return False
        # Check intermediate points
        dist = np.linalg.norm(to_pos - from_pos)
        if dist < 1e-10:
            return True
        n_checks = max(2, int(dist / self.config.step_size))
        for i in range(n_checks + 1):
            t = i / n_checks
            point = from_pos + t * (to_pos - from_pos)
            if not self._is_point_free(point):
                return False
        return True

    def _nearest_neighbor(self, point: np.ndarray) -> Node:
        nearest = self.nodes[0]
        min_dist = np.linalg.norm(point - nearest.position)
        for node in self.nodes[1:]:
            dist = np.linalg.norm(point - node.position)
            if dist < min_dist:
                min_dist = dist
                nearest = node
        return nearest

    def _near_nodes(self, point: np.ndarray, radius: float) -> list[Node]:
        return [n for n in self.nodes if np.linalg.norm(n.position - point) <= radius]

    def _steer(self, from_pos: np.ndarray, to_pos: np.ndarray) -> np.ndarray:
        direction = to_pos - from_pos
        dist = np.linalg.norm(direction)
        if dist <= self.config.step_size or dist < 1e-10:
            return to_pos
        return from_pos + direction / dist * self.config.step_size

    def plan(self) -> tuple[list[np.ndarray] | None, float, int]:
        """Plan."""
        low, high = self.config.bounds
        self.nodes = [Node(self.config.start.copy())]
        goal_node = Node(self.config.goal.copy())

        for iteration in range(self.config.max_iterations):
            if self.rng.random() < 0.1:
                random_point = self.config.goal.copy()
            else:
                random_point = self.rng.random(self.config.dimensions) * (high - low) + low

            nearest = self._nearest_neighbor(random_point)
            new_pos = self._steer(nearest.position, random_point)

            if not self._is_collision_free(nearest.position, new_pos):
                continue

            new_node = Node(new_pos)
            new_node.parent = nearest
            new_node.cost = nearest.cost + np.linalg.norm(new_pos - nearest.position)

            if self.config.planner_type == PlannerType.RRT_STAR:
                near_radius = min(5.0 * self.config.step_size, 2.0)
                near_nodes = self._near_nodes(new_pos, near_radius)
                for near in near_nodes:
                    if self._is_collision_free(near.position, new_pos):
                        new_cost = near.cost + np.linalg.norm(new_pos - near.position)
                        if new_cost < new_node.cost:
                            new_node.parent = near
                            new_node.cost = new_cost
                for near in near_nodes:
                    if near == new_node.parent:
                        continue
                    if self._is_collision_free(new_pos, near.position):
                        new_cost = new_node.cost + np.linalg.norm(near.position - new_pos)
                        if new_cost < near.cost:
                            near.parent = new_node
                            near.cost = new_cost

            self.nodes.append(new_node)

            if np.linalg.norm(new_pos - self.config.goal) <= self.config.goal_radius:
                # Reconstruct path
                path = []
                node = new_node
                while node is not None:
                    path.append(node.position.copy())
                    node = node.parent
                path.reverse()
                path_length = sum(np.linalg.norm(path[i+1] - path[i]) for i in range(len(path)-1))
                return path, path_length, iteration

        return None, float("inf"), self.config.max_iterations


class AStarPlanner:
    """A* and Dijkstra planner on grid"""

    def __init__(self, config: PathPlanningConfig) -> None:
        self.config = config

    def _world_to_grid(self, point: np.ndarray) -> tuple[int, ...]:
        low, _ = self.config.bounds
        return tuple(int((p - l) / self.config.grid_resolution) for p, l in zip(point, low, strict=False))

    def _grid_to_world(self, grid_idx: tuple) -> np.ndarray:
        low, _ = self.config.bounds
        return np.array([l + g * self.config.grid_resolution for l, g in zip(low, grid_idx, strict=False)])

    def _heuristic(self, a: tuple, b: tuple) -> float:
        return np.sqrt(sum((x - y)**2 for x, y in zip(a, b, strict=False))) * self.config.grid_resolution

    def _is_point_free(self, point: np.ndarray) -> bool:
        for center, radius in self.config.obstacles:
            if np.linalg.norm(point - center) < radius:
                return False
        return True

    def plan(self) -> tuple[list[np.ndarray] | None, float, int]:
        """Plan."""
        low, high = self.config.bounds
        start_grid = self._world_to_grid(self.config.start)
        goal_grid = self._world_to_grid(self.config.goal)

        dims = self.config.dimensions
        grid_size = tuple(int((h - l) / self.config.grid_resolution) + 1 for h, l in zip(high, low, strict=False))

        open_set: dict[tuple, float] = {start_grid: 0.0}
        came_from: dict[tuple, tuple | None] = {start_grid: None}
        g_score: dict[tuple, float] = {start_grid: 0.0}
        iteration = 0

        while open_set:
            current = min(open_set, key=lambda x: open_set[x])
            if current == goal_grid or self._heuristic(current, goal_grid) < self.config.goal_radius:
                path = []
                node = current
                while node is not None:
                    path.append(self._grid_to_world(node))
                    node = came_from.get(node)
                path.reverse()
                path_length = sum(np.linalg.norm(path[i+1] - path[i]) for i in range(len(path)-1))
                return path, path_length, iteration

            del open_set[current]
            iteration += 1

            # Neighbors
            for di in [-1, 0, 1]:
                for dj in [-1, 0, 1]:
                    if di == 0 and dj == 0:
                        continue
                    neighbor = (current[0] + di, current[1] + dj)
                    if any(n < 0 or n >= gs for n, gs in zip(neighbor, grid_size, strict=False)):
                        continue
                    neighbor_pos = self._grid_to_world(neighbor)
                    if not self._is_point_free(neighbor_pos):
                        continue
                    tentative_g = g_score[current] + np.linalg.norm(neighbor_pos - self._grid_to_world(current))
                    if neighbor not in g_score or tentative_g < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g
                        f_score = tentative_g
                        if self.config.planner_type == PlannerType.A_STAR:
                            f_score += self._heuristic(neighbor, goal_grid)
                        open_set[neighbor] = f_score

        return None, float("inf"), iteration


class PathPlanningPattern(BasePattern):
    """Path planning with multiple algorithms"""

    PATTERN_ID = "path_planning"
    PATTERN_VERSION = "6.0.0"

    def _validate_config(self) -> None:
        pass

    def __init__(self, config: PathPlanningConfig | None = None) -> None:
        BasePattern.__init__(self, config or PathPlanningConfig())
        self.config: PathPlanningConfig = self.config
        self.planner: RRTPlanner | AStarPlanner | None = None

    def run(self, hypothesis: dict[str, Any] | None = None) -> dict[str, Any]:
        """Run."""
        start_time = time.perf_counter()
        planner_type = self.config.planner_type

        if planner_type in (PlannerType.RRT, PlannerType.RRT_STAR, PlannerType.PRM):
            self.planner = RRTPlanner(self.config)
        else:
            self.planner = AStarPlanner(self.config)

        path, length, iterations = self.planner.plan()
        elapsed = time.perf_counter() - start_time

        success = path is not None
        result: dict[str, Any] = {
            "planner_type": planner_type.value,
            "success": success,
            "path_length": float(length) if success else None,
            "iterations": iterations,
            "planning_time": elapsed,
            "n_obstacles": len(self.config.obstacles),
        }

        if success and path is not None:
            if self.config.output_waypoints:
                result["path"] = [p.tolist() for p in path]
                result["n_waypoints"] = len(path)
                if len(path) > 2:
                    angles = []
                    for i in range(1, len(path) - 1):
                        v1 = path[i] - path[i-1]
                        v2 = path[i+1] - path[i]
                        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-10)
                        angles.append(np.arccos(np.clip(cos_angle, -1, 1)))
                    result["mean_turning_angle"] = float(np.mean(angles)) if angles else 0.0

        return result

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Path Planning",
            "category": "EXTENDED",
            "parameters": [
                {"name": "planner_type", "type": "enum", "options": ["rrt", "rrt_star", "a_star", "dijkstra", "prm"], "default": "rrt_star"},
                {"name": "environment_type", "type": "enum", "options": ["empty", "random_obstacles", "maze", "cluttered", "custom"], "default": "random_obstacles"},
                {"name": "max_iterations", "type": "int", "default": 5000},
                {"name": "step_size", "type": "float", "default": 0.5},
            ],
        }
