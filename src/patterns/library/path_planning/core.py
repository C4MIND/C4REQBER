"""
C4REQBER v6.0 - Path Planning Pattern[str] Core
Core algorithm implementations for RRT, RRT*, A*, and Dijkstra.
"""

from __future__ import annotations

import heapq
import logging
from collections import defaultdict
from typing import Any

import numpy as np

from .config import PathPlanningConfig, PlannerType


logger = logging.getLogger(__name__)

class Node:
    """Node for graph-based planners"""

    def __init__(self, position: np.ndarray, node_id: int | None = None) -> None:
        self.position = position
        self.id = node_id
        self.parent: Node | None = None
        self.children: list[Node] = []
        self.cost = 0.0  # Cost from start
        self.neighbors: list[tuple[Node, float]] = []  # For PRM

    def __lt__(self, other: Any) -> Any:
        return self.cost < other.cost

    def __eq__(self, other: Any) -> Any:
        if isinstance(other, Node):
            return np.allclose(self.position, other.position)
        return False

    def __hash__(self) -> Any:
        return hash(tuple(self.position.round(4)))

class RRTPlanner:
    """RRT and RRT* path planner"""

    def __init__(self, config: PathPlanningConfig) -> None:
        self.config = config
        self.nodes: list[Node] = []

    def _is_collision_free(self, p1: np.ndarray, p2: np.ndarray) -> bool:
        """Check if path between two points is collision-free"""
        # Check line segment against all obstacles
        direction = p2 - p1
        distance = np.linalg.norm(direction)

        if distance < 1e-10:
            return self._is_point_free(p1)

        direction = direction / distance

        # Check multiple points along the line
        n_checks = max(2, int(distance / (self.config.obstacle_radius / 2)))
        for i in range(n_checks + 1):
            t = i / n_checks
            point = p1 + t * direction * distance
            if not self._is_point_free(point):
                return False

        return True

    def _is_point_free(self, point: np.ndarray) -> bool:
        """Check if point is collision-free"""
        for center, radius in self.config.obstacles:
            if np.linalg.norm(point - center) < radius:
                return False
        return True

    def _nearest_neighbor(self, point: np.ndarray) -> Node:
        """Find nearest node to point"""
        nearest = self.nodes[0]
        min_dist = np.linalg.norm(point - nearest.position)

        for node in self.nodes[1:]:
            dist = np.linalg.norm(point - node.position)
            if dist < min_dist:
                min_dist = dist
                nearest = node

        return nearest

    def _near_nodes(self, point: np.ndarray, radius: float) -> list[Node]:
        """Find all nodes within radius"""
        near = []
        for node in self.nodes:
            if np.linalg.norm(point - node.position) < radius:
                near.append(node)
        return near

    def _steer(self, from_pos: np.ndarray, to_pos: np.ndarray) -> np.ndarray:
        """Steer from one position toward another with step size limit"""
        direction = to_pos - from_pos
        distance = np.linalg.norm(direction)

        if distance < self.config.step_size:
            return to_pos
        else:
            return from_pos + (direction / distance) * self.config.step_size  # type: ignore[no-any-return]

    def plan(self) -> tuple[list[np.ndarray] | None, float, int]:
        """
        Run RRT/RRT* planning.
        Returns: (path, path_length, iterations)
        """
        cfg = self.config

        # Initialize tree with start node
        start_node = Node(cfg.start, 0)
        start_node.cost = 0.0
        self.nodes = [start_node]

        low, high = cfg.bounds
        goal_node = None

        for iteration in range(cfg.max_iterations):  # noqa: B007
            # Sample random point
            if np.random.random() < 0.1:
                # Bias toward goal
                random_point = cfg.goal
            else:
                random_point = np.random.uniform(low, high)

            # Find nearest node
            nearest = self._nearest_neighbor(random_point)

            # Steer toward random point
            new_pos = self._steer(nearest.position, random_point)

            # Check collision
            if not self._is_collision_free(nearest.position, new_pos):
                continue

            if not self._is_point_free(new_pos):
                continue

            # Create new node
            new_node = Node(new_pos, len(self.nodes))

            if cfg.planner_type == PlannerType.RRT_STAR:
                # RRT* rewiring
                near_nodes = self._near_nodes(
                    new_pos,
                    cfg.rewire_factor
                    * cfg.step_size
                    * np.sqrt(np.log(len(self.nodes)) / len(self.nodes)),
                )

                # Find best parent
                min_cost = float("inf")
                best_parent = nearest

                for near_node in near_nodes:
                    if self._is_collision_free(near_node.position, new_pos):
                        cost = near_node.cost + np.linalg.norm(
                            new_pos - near_node.position
                        )
                        if cost < min_cost:
                            min_cost = cost  # type: ignore[assignment]
                            best_parent = near_node

                new_node.parent = best_parent
                new_node.cost = min_cost
                best_parent.children.append(new_node)

                # Rewire near nodes through new node
                for near_node in near_nodes:
                    if near_node == best_parent:
                        continue
                    new_cost = new_node.cost + np.linalg.norm(
                        near_node.position - new_pos
                    )
                    if new_cost < near_node.cost and self._is_collision_free(
                        new_pos, near_node.position
                    ):
                        # Rewire
                        if near_node.parent:
                            near_node.parent.children.remove(near_node)
                        near_node.parent = new_node
                        near_node.cost = new_cost  # type: ignore[assignment]
                        new_node.children.append(near_node)

            else:
                # Standard RRT
                new_node.parent = nearest
                new_node.cost = nearest.cost + np.linalg.norm(  # type: ignore[assignment]
                    new_pos - nearest.position
                )
                nearest.children.append(new_node)

            self.nodes.append(new_node)

            # Check if reached goal
            if np.linalg.norm(new_pos - cfg.goal) < cfg.goal_radius:
                goal_node = new_node
                if cfg.planner_type != PlannerType.RRT_STAR:
                    break  # RRT stops at first solution

        # Extract path
        if goal_node is None:
            # Try to find nearest node to goal
            goal_node = self._nearest_neighbor(cfg.goal)
            if np.linalg.norm(goal_node.position - cfg.goal) > cfg.goal_radius:
                return None, float("inf"), iteration

        path = []
        node = goal_node
        while node is not None:
            path.append(node.position)
            node = node.parent  # type: ignore[assignment]

        path.reverse()  # type: ignore[unreachable]

        # Calculate path length
        path_length = sum(
            np.linalg.norm(path[i + 1] - path[i]) for i in range(len(path) - 1)
        )

        return path, path_length, iteration

class AStarPlanner:
    """A* path planner on grid"""

    def __init__(self, config: PathPlanningConfig) -> None:
        self.config = config

    def _world_to_grid(self, point: np.ndarray) -> tuple[int, int]:
        """Convert world coordinates to grid indices"""
        low, _ = self.config.bounds
        grid_point = ((point - low) / self.config.grid_resolution).astype(int)
        return tuple(grid_point)

    def _grid_to_world(self, grid_idx: tuple[int, int]) -> np.ndarray:
        """Convert grid indices to world coordinates"""
        low, _ = self.config.bounds
        return low + np.array(grid_idx) * self.config.grid_resolution  # type: ignore[no-any-return]

    def _is_grid_free(self, grid_idx: tuple[int, int]) -> bool:
        """Check if grid cell is free"""
        point = self._grid_to_world(grid_idx)
        return self._is_point_free(point)

    def _is_point_free(self, point: np.ndarray) -> bool:
        """Check if point is collision-free"""
        for center, radius in self.config.obstacles:
            if np.linalg.norm(point - center) < radius:
                return False
        return True

    def _heuristic(self, a: tuple[int, int], b: tuple[int, int]) -> float:
        """Euclidean heuristic"""
        return (  # type: ignore[no-any-return]
            np.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)
            * self.config.grid_resolution
        )

    def _get_neighbors(
        self, grid_idx: tuple[int, int]
    ) -> list[tuple[tuple[int, int], float]]:
        """Get neighboring grid cells"""
        neighbors = []

        # 8-connected grid
        for dx, dy in [
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, -1),
            (0, 1),
            (1, -1),
            (1, 0),
            (1, 1),
        ]:
            neighbor = (grid_idx[0] + dx, grid_idx[1] + dy)

            if self._is_grid_free(neighbor):
                cost = np.sqrt(dx**2 + dy**2) * self.config.grid_resolution
                neighbors.append((neighbor, cost))

        return neighbors

    def plan(self) -> tuple[list[np.ndarray] | None, float, int]:
        """
        Run A* planning.
        Returns: (path, path_length, iterations)
        """
        cfg = self.config

        start_grid = self._world_to_grid(cfg.start)
        goal_grid = self._world_to_grid(cfg.goal)

        # Check start and goal
        if not self._is_grid_free(start_grid) or not self._is_grid_free(goal_grid):
            return None, float("inf"), 0

        # A* search
        open_set = [(0.0, 0, start_grid)]  # (f_score, tie_breaker, node)
        counter = 0

        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        g_score: dict[tuple[int, int], float] = defaultdict(lambda: float("inf"))
        g_score[start_grid] = 0.0
        f_score: dict[tuple[int, int], float] = defaultdict(lambda: float("inf"))
        f_score[start_grid] = self._heuristic(start_grid, goal_grid)

        closed_set: set[tuple[int, int]] = set()

        iterations = 0

        while open_set:
            iterations += 1

            _, _, current = heapq.heappop(open_set)

            if current in closed_set:
                continue

            closed_set.add(current)

            # Check goal
            if (
                current == goal_grid
                or self._heuristic(current, goal_grid)
                < cfg.goal_radius / cfg.grid_resolution
            ):
                # Reconstruct path
                path = []
                node = current
                while node in came_from:
                    path.append(self._grid_to_world(node))
                    node = came_from[node]
                path.append(cfg.start)
                path.reverse()

                path_length = g_score[current]
                return path, path_length, iterations

            # Expand neighbors
            for neighbor, cost in self._get_neighbors(current):
                if neighbor in closed_set:
                    continue

                tentative_g = g_score[current] + cost

                if tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self._heuristic(
                        neighbor, goal_grid
                    )
                    counter += 1
                    heapq.heappush(open_set, (f_score[neighbor], counter, neighbor))

        return None, float("inf"), iterations
