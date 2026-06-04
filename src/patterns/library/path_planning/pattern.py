"""
C4REQBER v6.0 - Path Planning Pattern[str]
Main pattern class for path planning with RRT*, A*, and Dijkstra algorithms.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import numpy as np

from .config import PathPlanningConfig, PlannerType
from .core import AStarPlanner, RRTPlanner


logger = logging.getLogger(__name__)

class PathPlanningPattern:
    """
    Path planning pattern with RRT*, A*, and Dijkstra.

    Implements sampling-based and search-based motion planning
    algorithms for robot navigation.
    """

    PATTERN_ID = "path_planning"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: PathPlanningConfig | None = None) -> None:
        self.config = config or PathPlanningConfig()
        self.planner = None

    def _initialize_planner(self) -> None:
        """Initialize appropriate planner"""
        cfg = self.config

        if cfg.planner_type in [PlannerType.RRT, PlannerType.RRT_STAR]:
            self.planner = RRTPlanner(cfg)  # type: ignore[assignment]
        elif cfg.planner_type in [PlannerType.A_STAR, PlannerType.DIJKSTRA]:
            self.planner = AStarPlanner(cfg)  # type: ignore[assignment]
        else:
            self.planner = RRTPlanner(cfg)  # type: ignore[assignment]

    def run(self, hypothesis: dict[str, Any] = None) -> dict[str, Any]:  # type: ignore[assignment]
        """Run path planning"""
        cfg = self.config

        logger.info(
            f"Starting path planning: {cfg.planner_type.value}, "
            f"{cfg.environment_type.value}"
        )

        self._initialize_planner()

        t_start = time.time()

        path, path_length, iterations = self.planner.plan()  # type: ignore[attr-defined]

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
    def get_metadata(cls) -> dict[str, Any]:
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
