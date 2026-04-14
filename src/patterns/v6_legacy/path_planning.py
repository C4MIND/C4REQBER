"""
TURBO-CDI v6.0 - Path Planning Pattern
RRT*, A*, and Dijkstra algorithms for robot motion planning.

Pattern Structure (Christopher Alexander):
- Context: Robot navigation, autonomous vehicles, game AI
- Forces: Optimality vs computation time, completeness vs probabilistic guarantees
- Solution: Sampling-based and search-based planners with heuristics
"""

import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import heapq

logger = logging.getLogger(__name__)


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
    bounds: Tuple[np.ndarray, np.ndarray] = field(
        default_factory=lambda: (np.array([0.0, 0.0]), np.array([10.0, 10.0]))
    )

    # Obstacles (list of (center, radius) for circles)
    obstacles: List[Tuple[np.ndarray, float]] = field(default_factory=list)
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

    def __post_init__(self):
        """Generate environment if needed"""
        if self.environment_type == EnvironmentType.RANDOM_OBSTACLES:
            self._generate_random_obstacles()
        elif self.environment_type == EnvironmentType.MAZE:
            self._generate_maze()

    def _generate_random_obstacles(self):
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

    def _generate_maze(self):
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


class Node:
    """Node for graph-based planners"""

    def __init__(self, position: np.ndarray, node_id: int = None):
        self.position = position
        self.id = node_id
        self.parent: Optional["Node"] = None
        self.children: List["Node"] = []
        self.cost = 0.0  # Cost from start
        self.neighbors: List[Tuple["Node", float]] = []  # For PRM

    def __lt__(self, other):
        return self.cost < other.cost

    def __eq__(self, other):
        if isinstance(other, Node):
            return np.allclose(self.position, other.position)
        return False

    def __hash__(self):
        return hash(tuple(self.position.round(4)))


class RRTPlanner:
    """RRT and RRT* path planner"""

    def __init__(self, config: PathPlanningConfig):
        self.config = config
        self.nodes: List[Node] = []

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

    def _near_nodes(self, point: np.ndarray, radius: float) -> List[Node]:
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
            return from_pos + (direction / distance) * self.config.step_size

    def plan(self) -> Tuple[Optional[List[np.ndarray]], float, int]:
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

        for iteration in range(cfg.max_iterations):
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
                            min_cost = cost
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
                        near_node.cost = new_cost
                        new_node.children.append(near_node)

            else:
                # Standard RRT
                new_node.parent = nearest
                new_node.cost = nearest.cost + np.linalg.norm(
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
            node = node.parent

        path.reverse()

        # Calculate path length
        path_length = sum(
            np.linalg.norm(path[i + 1] - path[i]) for i in range(len(path) - 1)
        )

        return path, path_length, iteration


class AStarPlanner:
    """A* path planner on grid"""

    def __init__(self, config: PathPlanningConfig):
        self.config = config

    def _world_to_grid(self, point: np.ndarray) -> Tuple[int, int]:
        """Convert world coordinates to grid indices"""
        low, _ = self.config.bounds
        grid_point = ((point - low) / self.config.grid_resolution).astype(int)
        return tuple(grid_point)

    def _grid_to_world(self, grid_idx: Tuple[int, int]) -> np.ndarray:
        """Convert grid indices to world coordinates"""
        low, _ = self.config.bounds
        return low + np.array(grid_idx) * self.config.grid_resolution

    def _is_grid_free(self, grid_idx: Tuple[int, int]) -> bool:
        """Check if grid cell is free"""
        point = self._grid_to_world(grid_idx)
        return self._is_point_free(point)

    def _is_point_free(self, point: np.ndarray) -> bool:
        """Check if point is collision-free"""
        for center, radius in self.config.obstacles:
            if np.linalg.norm(point - center) < radius:
                return False
        return True

    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Euclidean heuristic"""
        return (
            np.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)
            * self.config.grid_resolution
        )

    def _get_neighbors(
        self, grid_idx: Tuple[int, int]
    ) -> List[Tuple[Tuple[int, int], float]]:
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

    def plan(self) -> Tuple[Optional[List[np.ndarray]], float, int]:
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

        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        g_score: Dict[Tuple[int, int], float] = defaultdict(lambda: float("inf"))
        g_score[start_grid] = 0.0
        f_score: Dict[Tuple[int, int], float] = defaultdict(lambda: float("inf"))
        f_score[start_grid] = self._heuristic(start_grid, goal_grid)

        closed_set: Set[Tuple[int, int]] = set()

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


class PathPlanningPattern:
    """
    Path planning pattern with RRT*, A*, and Dijkstra.

    Implements sampling-based and search-based motion planning
    algorithms for robot navigation.
    """

    PATTERN_ID = "path_planning"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: Optional[PathPlanningConfig] = None):
        self.config = config or PathPlanningConfig()
        self.planner = None

    def _initialize_planner(self):
        """Initialize appropriate planner"""
        cfg = self.config

        if cfg.planner_type in [PlannerType.RRT, PlannerType.RRT_STAR]:
            self.planner = RRTPlanner(cfg)
        elif cfg.planner_type in [PlannerType.A_STAR, PlannerType.DIJKSTRA]:
            self.planner = AStarPlanner(cfg)
        else:
            self.planner = RRTPlanner(cfg)

    def run(self, hypothesis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run path planning"""
        cfg = self.config

        logger.info(
            f"Starting path planning: {cfg.planner_type.value}, "
            f"{cfg.environment_type.value}"
        )

        self._initialize_planner()

        import time

        t_start = time.time()

        path, path_length, iterations = self.planner.plan()

        t_plan = time.time() - t_start

        success = path is not None

        # Format output
        result = {
            "planner_type": cfg.planner_type.value,
            "environment_type": cfg.environment_type.value,
            "success": success,
            "planning_time": t_plan,
            "iterations": iterations,
            "path_length": path_length if success else None,
            "start": cfg.start.tolist(),
            "goal": cfg.goal.tolist(),
            "n_obstacles": len(cfg.obstacles),
        }

        if success and cfg.output_waypoints:
            result["path"] = [p.tolist() for p in path]
            result["n_waypoints"] = len(path)

            # Calculate path smoothness
            if len(path) > 2:
                angles = []
                for i in range(1, len(path) - 1):
                    v1 = path[i] - path[i - 1]
                    v2 = path[i + 1] - path[i]
                    if np.linalg.norm(v1) > 1e-10 and np.linalg.norm(v2) > 1e-10:
                        angle = np.arccos(
                            np.clip(
                                np.dot(v1, v2)
                                / (np.linalg.norm(v1) * np.linalg.norm(v2)),
                                -1,
                                1,
                            )
                        )
                        angles.append(angle)
                result["mean_turning_angle"] = float(np.mean(angles)) if angles else 0.0

        return result

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Path Planning",
            "category": "EXTENDED",
            "domain": ["Robotics", "Autonomous Vehicles", "Game AI", "Logistics"],
            "description": "RRT*, A*, and Dijkstra algorithms for robot motion planning",
            "computational_complexity": "O(n log n) for A*, O(n) for RRT",
            "typical_runtime": "milliseconds to seconds",
            "accuracy": "Resolution complete (A*) or probabilistically complete (RRT)",
            "assumptions": [
                "Known environment",
                "Static obstacles",
                "Holonomic robot (for basic algorithms)",
            ],
            "parameters": [
                {
                    "name": "planner_type",
                    "type": "enum",
                    "options": ["rrt", "rrt_star", "a_star", "dijkstra"],
                    "default": "rrt_star",
                },
                {
                    "name": "environment_type",
                    "type": "enum",
                    "options": ["empty", "random_obstacles", "maze", "cluttered"],
                    "default": "random_obstacles",
                },
                {"name": "max_iterations", "type": "int", "default": 5000},
                {"name": "step_size", "type": "float", "default": 0.5},
            ],
        }


# =============================================================================
# UNIT TESTS
# =============================================================================

import unittest


class TestRRTPlanner(unittest.TestCase):
    """Unit tests for RRT planner"""

    def test_initialization(self):
        """Test RRT initialization"""
        config = PathPlanningConfig(planner_type=PlannerType.RRT)
        planner = RRTPlanner(config)
        self.assertEqual(len(planner.nodes), 0)

    def test_collision_detection(self):
        """Test collision detection"""
        config = PathPlanningConfig(obstacles=[(np.array([5.0, 5.0]), 1.0)])
        planner = RRTPlanner(config)

        # Point inside obstacle
        self.assertFalse(planner._is_point_free(np.array([5.0, 5.0])))

        # Point outside obstacle
        self.assertTrue(planner._is_point_free(np.array([0.0, 0.0])))

    def test_nearest_neighbor(self):
        """Test nearest neighbor search"""
        config = PathPlanningConfig()
        planner = RRTPlanner(config)

        planner.nodes = [
            Node(np.array([0.0, 0.0])),
            Node(np.array([3.0, 4.0])),
            Node(np.array([1.0, 1.0])),
        ]

        nearest = planner._nearest_neighbor(np.array([1.2, 1.2]))
        np.testing.assert_array_almost_equal(nearest.position, np.array([1.0, 1.0]))

    def test_steering(self):
        """Test steering function"""
        config = PathPlanningConfig(step_size=1.0)
        planner = RRTPlanner(config)

        from_pos = np.array([0.0, 0.0])
        to_pos = np.array([3.0, 4.0])

        new_pos = planner._steer(from_pos, to_pos)

        # Should be step_size away from from_pos
        distance = np.linalg.norm(new_pos - from_pos)
        self.assertAlmostEqual(distance, config.step_size, places=5)

    def test_rrt_planning(self):
        """Test basic RRT planning"""
        config = PathPlanningConfig(
            planner_type=PlannerType.RRT,
            environment_type=EnvironmentType.EMPTY,
            start=np.array([0.5, 0.5]),
            goal=np.array([2.0, 2.0]),
            max_iterations=2000,
            goal_radius=0.5,
        )
        planner = RRTPlanner(config)
        path, length, iters = planner.plan()

        self.assertIsNotNone(path)
        self.assertGreater(len(path), 1)

    def test_rrt_star_planning(self):
        """Test RRT* planning"""
        config = PathPlanningConfig(
            planner_type=PlannerType.RRT_STAR,
            environment_type=EnvironmentType.EMPTY,
            start=np.array([0.5, 0.5]),
            goal=np.array([2.0, 2.0]),
            max_iterations=2000,
        )
        planner = RRTPlanner(config)
        path, length, iters = planner.plan()

        self.assertIsNotNone(path)


class TestAStarPlanner(unittest.TestCase):
    """Unit tests for A* planner"""

    def test_grid_conversion(self):
        """Test world to grid conversion"""
        config = PathPlanningConfig(grid_resolution=0.5)
        planner = AStarPlanner(config)

        point = np.array([1.0, 1.5])
        grid_idx = planner._world_to_grid(point)

        self.assertEqual(grid_idx, (2, 3))

    def test_heuristic(self):
        """Test A* heuristic"""
        config = PathPlanningConfig()
        planner = AStarPlanner(config)

        h = planner._heuristic((0, 0), (3, 4))

        self.assertAlmostEqual(h, 5.0 * config.grid_resolution, places=5)

    def test_a_star_planning(self):
        """Test A* planning in empty environment"""
        config = PathPlanningConfig(
            planner_type=PlannerType.A_STAR,
            environment_type=EnvironmentType.EMPTY,
            start=np.array([0.5, 0.5]),
            goal=np.array([3.0, 3.0]),
            grid_resolution=0.5,
        )
        planner = AStarPlanner(config)
        path, length, iters = planner.plan()

        self.assertIsNotNone(path)
        self.assertGreater(len(path), 1)

    def test_a_star_with_obstacles(self):
        """Test A* with obstacles"""
        config = PathPlanningConfig(
            planner_type=PlannerType.A_STAR,
            environment_type=EnvironmentType.EMPTY,
            start=np.array([0.5, 0.5]),
            goal=np.array([3.0, 3.0]),
            grid_resolution=0.5,
            obstacles=[(np.array([1.5, 1.5]), 0.6)],
        )
        planner = AStarPlanner(config)
        path, length, iters = planner.plan()

        self.assertIsNotNone(path)
        # Check that path avoids obstacle
        for p in path:
            self.assertGreater(np.linalg.norm(p - np.array([1.5, 1.5])), 0.5)


class TestPathPlanningPattern(unittest.TestCase):
    """Unit tests for path planning pattern"""

    def test_initialization(self):
        """Test pattern initialization"""
        pattern = PathPlanningPattern()
        self.assertIsNotNone(pattern.config)

    def test_rrt_run(self):
        """Test RRT run"""
        config = PathPlanningConfig(
            planner_type=PlannerType.RRT,
            environment_type=EnvironmentType.EMPTY,
            max_iterations=2000,
        )
        pattern = PathPlanningPattern(config)
        result = pattern.run()

        self.assertEqual(result["planner_type"], "rrt")
        self.assertTrue(result["success"])
        self.assertIn("path", result)

    def test_rrt_star_run(self):
        """Test RRT* run"""
        config = PathPlanningConfig(
            planner_type=PlannerType.RRT_STAR,
            environment_type=EnvironmentType.EMPTY,
            max_iterations=2000,
        )
        pattern = PathPlanningPattern(config)
        result = pattern.run()

        self.assertTrue(result["success"])
        self.assertIsNotNone(result["path_length"])

    def test_a_star_run(self):
        """Test A* run"""
        config = PathPlanningConfig(
            planner_type=PlannerType.A_STAR,
            environment_type=EnvironmentType.EMPTY,
            grid_resolution=0.5,
        )
        pattern = PathPlanningPattern(config)
        result = pattern.run()

        self.assertEqual(result["planner_type"], "a_star")
        self.assertTrue(result["success"])

    def test_obstacle_environment(self):
        """Test planning with obstacles"""
        config = PathPlanningConfig(
            planner_type=PlannerType.RRT_STAR,
            environment_type=EnvironmentType.RANDOM_OBSTACLES,
            n_obstacles=5,
            max_iterations=3000,
        )
        pattern = PathPlanningPattern(config)
        result = pattern.run()

        self.assertIn("n_obstacles", result)

    def test_get_metadata(self):
        """Test metadata retrieval"""
        metadata = PathPlanningPattern.get_metadata()

        self.assertEqual(metadata["id"], "path_planning")
        self.assertEqual(metadata["category"], "EXTENDED")


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2, exit=False)

    # Demo
    logging.basicConfig(level=logging.INFO)
    print("\n" + "=" * 60)
    print("Path Planning Pattern Demo")
    print("=" * 60)

    for planner in [PlannerType.RRT, PlannerType.RRT_STAR, PlannerType.A_STAR]:
        print(f"\n--- {planner.value.upper()} ---")
        config = PathPlanningConfig(
            planner_type=planner,
            environment_type=EnvironmentType.RANDOM_OBSTACLES,
            n_obstacles=8,
            max_iterations=3000,
            grid_resolution=0.3,
        )
        pattern = PathPlanningPattern(config)
        result = pattern.run()

        print(f"Success: {result['success']}")
        print(f"Planning Time: {result['planning_time'] * 1000:.2f} ms")
        print(f"Iterations: {result['iterations']}")
        if result["success"]:
            print(f"Path Length: {result['path_length']:.3f}")
            print(f"Waypoints: {result['n_waypoints']}")
