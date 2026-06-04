"""
Tests for src/patterns/library/path_planning.py

Covers:
- PlannerType and EnvironmentType enums
- PathPlanningConfig dataclass and defaults
- Node class (comparison, hashing)
- RRTPlanner initialization and methods
- AStarPlanner initialization and methods
- PathPlanningPattern initialization and run()
- get_metadata()
- Edge cases: empty environment, zero step size, same start/goal
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.path_planning import (

    AStarPlanner,
    EnvironmentType,
    Node,
    PathPlanningConfig,
    PathPlanningPattern,
    PlannerType,
    RRTPlanner,
)


# ═══════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════


class TestPlannerType:
    def test_enum_values(self):
        assert PlannerType.RRT.value == "rrt"
        assert PlannerType.RRT_STAR.value == "rrt_star"
        assert PlannerType.A_STAR.value == "a_star"
        assert PlannerType.DIJKSTRA.value == "dijkstra"
        assert PlannerType.PRM.value == "prm"


class TestEnvironmentType:
    def test_enum_values(self):
        assert EnvironmentType.EMPTY.value == "empty"
        assert EnvironmentType.RANDOM_OBSTACLES.value == "random_obstacles"
        assert EnvironmentType.MAZE.value == "maze"
        assert EnvironmentType.CLUTTERED.value == "cluttered"
        assert EnvironmentType.CUSTOM.value == "custom"


# ═══════════════════════════════════════════════════════════════════
# PathPlanningConfig
# ═══════════════════════════════════════════════════════════════════


class TestPathPlanningConfig:
    def test_default_init(self):
        cfg = PathPlanningConfig()
        assert cfg.planner_type == PlannerType.RRT_STAR
        assert cfg.environment_type == EnvironmentType.RANDOM_OBSTACLES
        assert cfg.dimensions == 2
        assert cfg.max_iterations == 5000
        assert cfg.step_size == 0.5
        assert cfg.goal_radius == 0.5

    def test_custom_init(self):
        cfg = PathPlanningConfig(
            planner_type=PlannerType.A_STAR,
            environment_type=EnvironmentType.EMPTY,
            max_iterations=1000,
            step_size=1.0,
        )
        assert cfg.planner_type == PlannerType.A_STAR
        assert cfg.environment_type == EnvironmentType.EMPTY
        assert cfg.max_iterations == 1000
        assert cfg.step_size == 1.0

    def test_bounds_default(self):
        cfg = PathPlanningConfig()
        low, high = cfg.bounds
        np.testing.assert_array_equal(low, np.array([0.0, 0.0]))
        np.testing.assert_array_equal(high, np.array([10.0, 10.0]))

    def test_start_goal_default(self):
        cfg = PathPlanningConfig()
        np.testing.assert_array_equal(cfg.start, np.array([0.5, 0.5]))
        np.testing.assert_array_equal(cfg.goal, np.array([9.5, 9.5]))

    def test_empty_environment_no_obstacles(self):
        cfg = PathPlanningConfig(environment_type=EnvironmentType.EMPTY)
        assert len(cfg.obstacles) == 0

    def test_random_obstacles_generated(self):
        cfg = PathPlanningConfig(
            environment_type=EnvironmentType.RANDOM_OBSTACLES,
            n_obstacles=5,
        )
        assert len(cfg.obstacles) <= 5

    def test_maze_generation(self):
        cfg = PathPlanningConfig(environment_type=EnvironmentType.MAZE)
        assert len(cfg.obstacles) > 0


# ═══════════════════════════════════════════════════════════════════
# Node
# ═══════════════════════════════════════════════════════════════════


class TestNode:
    def test_init(self):
        node = Node(np.array([1.0, 2.0]), node_id=5)
        np.testing.assert_array_equal(node.position, np.array([1.0, 2.0]))
        assert node.id == 5
        assert node.parent is None
        assert node.children == []
        assert node.cost == 0.0
        assert node.neighbors == []

    def test_lt(self):
        n1 = Node(np.array([0.0, 0.0]))
        n1.cost = 1.0
        n2 = Node(np.array([1.0, 1.0]))
        n2.cost = 2.0
        assert n1 < n2

    def test_eq_close_positions(self):
        n1 = Node(np.array([1.0, 2.0]))
        n2 = Node(np.array([1.0, 2.0]))
        assert n1 == n2

    def test_eq_different_positions(self):
        n1 = Node(np.array([1.0, 2.0]))
        n2 = Node(np.array([3.0, 4.0]))
        assert n1 != n2

    def test_hash(self):
        n1 = Node(np.array([1.0, 2.0]))
        n2 = Node(np.array([1.0, 2.0]))
        assert hash(n1) == hash(n2)

    def test_hash_consistency(self):
        node = Node(np.array([1.2345, 6.7890]))
        assert hash(node) == hash(node)


# ═══════════════════════════════════════════════════════════════════
# RRTPlanner
# ═══════════════════════════════════════════════════════════════════


class TestRRTPlanner:
    def test_init(self):
        cfg = PathPlanningConfig(planner_type=PlannerType.RRT)
        planner = RRTPlanner(cfg)
        assert planner.config == cfg
        assert planner.nodes == []

    def test_is_point_free_no_obstacles(self):
        cfg = PathPlanningConfig(environment_type=EnvironmentType.EMPTY)
        planner = RRTPlanner(cfg)
        assert planner._is_point_free(np.array([5.0, 5.0])) is True

    def test_is_point_free_inside_obstacle(self):
        cfg = PathPlanningConfig(
            environment_type=EnvironmentType.EMPTY,
            obstacles=[(np.array([5.0, 5.0]), 1.0)],
        )
        planner = RRTPlanner(cfg)
        assert planner._is_point_free(np.array([5.0, 5.0])) is False
        assert planner._is_point_free(np.array([5.5, 5.5])) is False

    def test_is_point_free_outside_obstacle(self):
        cfg = PathPlanningConfig(
            environment_type=EnvironmentType.EMPTY,
            obstacles=[(np.array([5.0, 5.0]), 1.0)],
        )
        planner = RRTPlanner(cfg)
        assert planner._is_point_free(np.array([0.0, 0.0])) is True
        assert planner._is_point_free(np.array([7.0, 7.0])) is True

    def test_is_collision_free_no_obstacles(self):
        cfg = PathPlanningConfig(environment_type=EnvironmentType.EMPTY)
        planner = RRTPlanner(cfg)
        assert planner._is_collision_free(np.array([0.0, 0.0]), np.array([5.0, 5.0])) is True

    def test_is_collision_free_through_obstacle(self):
        cfg = PathPlanningConfig(
            environment_type=EnvironmentType.EMPTY,
            obstacles=[(np.array([2.5, 2.5]), 1.0)],
        )
        planner = RRTPlanner(cfg)
        assert planner._is_collision_free(np.array([0.0, 0.0]), np.array([5.0, 5.0])) is False

    def test_nearest_neighbor(self):
        cfg = PathPlanningConfig()
        planner = RRTPlanner(cfg)
        planner.nodes = [
            Node(np.array([0.0, 0.0])),
            Node(np.array([3.0, 4.0])),
            Node(np.array([1.0, 1.0])),
        ]
        nearest = planner._nearest_neighbor(np.array([1.2, 1.2]))
        np.testing.assert_array_almost_equal(nearest.position, np.array([1.0, 1.0]))

    def test_near_nodes(self):
        cfg = PathPlanningConfig()
        planner = RRTPlanner(cfg)
        planner.nodes = [
            Node(np.array([0.0, 0.0])),
            Node(np.array([1.0, 0.0])),
            Node(np.array([5.0, 5.0])),
        ]
        near = planner._near_nodes(np.array([0.0, 0.0]), 2.0)
        assert len(near) == 2

    def test_steer_within_step(self):
        cfg = PathPlanningConfig(step_size=2.0)
        planner = RRTPlanner(cfg)
        new_pos = planner._steer(np.array([0.0, 0.0]), np.array([1.0, 0.0]))
        np.testing.assert_array_almost_equal(new_pos, np.array([1.0, 0.0]))

    def test_steer_beyond_step(self):
        cfg = PathPlanningConfig(step_size=1.0)
        planner = RRTPlanner(cfg)
        new_pos = planner._steer(np.array([0.0, 0.0]), np.array([3.0, 4.0]))
        distance = np.linalg.norm(new_pos - np.array([0.0, 0.0]))
        assert distance == pytest.approx(1.0, abs=1e-5)

    def test_plan_rrt_empty(self):
        cfg = PathPlanningConfig(
            planner_type=PlannerType.RRT,
            environment_type=EnvironmentType.EMPTY,
            start=np.array([0.5, 0.5]),
            goal=np.array([2.0, 2.0]),
            max_iterations=2000,
            goal_radius=0.5,
        )
        planner = RRTPlanner(cfg)
        path, length, iters = planner.plan()
        assert path is not None
        assert len(path) > 1
        assert length > 0
        assert iters >= 0

    def test_plan_rrt_star_empty(self):
        cfg = PathPlanningConfig(
            planner_type=PlannerType.RRT_STAR,
            environment_type=EnvironmentType.EMPTY,
            start=np.array([0.5, 0.5]),
            goal=np.array([2.0, 2.0]),
            max_iterations=2000,
            goal_radius=0.5,
        )
        planner = RRTPlanner(cfg)
        path, length, iters = planner.plan()
        assert path is not None
        assert len(path) > 1

    def test_plan_with_obstacles(self):
        cfg = PathPlanningConfig(
            planner_type=PlannerType.RRT,
            environment_type=EnvironmentType.EMPTY,
            start=np.array([0.5, 0.5]),
            goal=np.array([5.0, 5.0]),
            max_iterations=3000,
            obstacles=[(np.array([2.5, 2.5]), 1.0)],
        )
        planner = RRTPlanner(cfg)
        path, length, iters = planner.plan()
        # May or may not find path depending on obstacle placement
        if path is not None:
            assert len(path) > 1

    def test_plan_same_start_goal(self):
        cfg = PathPlanningConfig(
            planner_type=PlannerType.RRT,
            environment_type=EnvironmentType.EMPTY,
            start=np.array([1.0, 1.0]),
            goal=np.array([1.0, 1.0]),
            max_iterations=100,
            goal_radius=0.5,
        )
        planner = RRTPlanner(cfg)
        path, length, iters = planner.plan()
        assert path is not None
        assert len(path) >= 1


# ═══════════════════════════════════════════════════════════════════
# AStarPlanner
# ═══════════════════════════════════════════════════════════════════


class TestAStarPlanner:
    def test_init(self):
        cfg = PathPlanningConfig(planner_type=PlannerType.A_STAR)
        planner = AStarPlanner(cfg)
        assert planner.config == cfg

    def test_world_to_grid(self):
        cfg = PathPlanningConfig(grid_resolution=0.5)
        planner = AStarPlanner(cfg)
        grid_idx = planner._world_to_grid(np.array([1.0, 1.5]))
        assert grid_idx == (2, 3)

    def test_grid_to_world(self):
        cfg = PathPlanningConfig(grid_resolution=0.5)
        planner = AStarPlanner(cfg)
        world = planner._grid_to_world((2, 3))
        np.testing.assert_array_equal(world, np.array([1.0, 1.5]))

    def test_heuristic(self):
        cfg = PathPlanningConfig(grid_resolution=0.5)
        planner = AStarPlanner(cfg)
        h = planner._heuristic((0, 0), (3, 4))
        assert h == pytest.approx(2.5, abs=1e-5)

    def test_is_point_free(self):
        cfg = PathPlanningConfig(
            environment_type=EnvironmentType.EMPTY,
            obstacles=[(np.array([2.0, 2.0]), 1.0)],
        )
        planner = AStarPlanner(cfg)
        assert planner._is_point_free(np.array([0.0, 0.0])) is True
        assert planner._is_point_free(np.array([2.0, 2.0])) is False

    def test_plan_empty(self):
        cfg = PathPlanningConfig(
            planner_type=PlannerType.A_STAR,
            environment_type=EnvironmentType.EMPTY,
            start=np.array([0.5, 0.5]),
            goal=np.array([3.0, 3.0]),
            grid_resolution=0.5,
        )
        planner = AStarPlanner(cfg)
        path, length, iters = planner.plan()
        assert path is not None
        assert len(path) > 1
        assert length > 0
        assert iters > 0

    def test_plan_with_obstacles(self):
        cfg = PathPlanningConfig(
            planner_type=PlannerType.A_STAR,
            environment_type=EnvironmentType.EMPTY,
            start=np.array([0.5, 0.5]),
            goal=np.array([3.0, 3.0]),
            grid_resolution=0.5,
            obstacles=[(np.array([1.5, 1.5]), 0.6)],
        )
        planner = AStarPlanner(cfg)
        path, length, iters = planner.plan()
        assert path is not None
        # Path should avoid obstacle center
        for p in path:
            assert np.linalg.norm(p - np.array([1.5, 1.5])) > 0.5

    def test_plan_blocked_goal(self):
        cfg = PathPlanningConfig(
            planner_type=PlannerType.A_STAR,
            environment_type=EnvironmentType.EMPTY,
            start=np.array([0.5, 0.5]),
            goal=np.array([2.0, 2.0]),
            grid_resolution=0.5,
            obstacles=[(np.array([2.0, 2.0]), 1.0)],
        )
        planner = AStarPlanner(cfg)
        path, length, iters = planner.plan()
        assert path is None
        assert length == float("inf")


# ═══════════════════════════════════════════════════════════════════
# PathPlanningPattern
# ═══════════════════════════════════════════════════════════════════


class TestPathPlanningPatternInit:
    def test_default_init(self):
        pattern = PathPlanningPattern()
        assert pattern.config is not None
        assert pattern.planner is None

    def test_custom_config(self):
        cfg = PathPlanningConfig(planner_type=PlannerType.A_STAR)
        pattern = PathPlanningPattern(cfg)
        assert pattern.config.planner_type == PlannerType.A_STAR


class TestPathPlanningPatternRun:
    def test_run_rrt(self):
        cfg = PathPlanningConfig(
            planner_type=PlannerType.RRT,
            environment_type=EnvironmentType.EMPTY,
            max_iterations=2000,
        )
        pattern = PathPlanningPattern(cfg)
        result = pattern.run()
        assert result["planner_type"] == "rrt"
        assert result["success"] is True
        assert "path" in result
        assert "planning_time" in result
        assert result["iterations"] >= 0

    def test_run_rrt_star(self):
        cfg = PathPlanningConfig(
            planner_type=PlannerType.RRT_STAR,
            environment_type=EnvironmentType.EMPTY,
            max_iterations=2000,
        )
        pattern = PathPlanningPattern(cfg)
        result = pattern.run()
        assert result["success"] is True
        assert result["path_length"] is not None
        assert "path" in result

    def test_run_a_star(self):
        cfg = PathPlanningConfig(
            planner_type=PlannerType.A_STAR,
            environment_type=EnvironmentType.EMPTY,
            grid_resolution=0.5,
        )
        pattern = PathPlanningPattern(cfg)
        result = pattern.run()
        assert result["planner_type"] == "a_star"
        assert result["success"] is True
        assert "path" in result

    def test_run_dijkstra(self):
        cfg = PathPlanningConfig(
            planner_type=PlannerType.DIJKSTRA,
            environment_type=EnvironmentType.EMPTY,
            grid_resolution=0.5,
        )
        pattern = PathPlanningPattern(cfg)
        result = pattern.run()
        assert result["success"] is True
        assert "path" in result

    def test_run_with_obstacles(self):
        cfg = PathPlanningConfig(
            planner_type=PlannerType.RRT_STAR,
            environment_type=EnvironmentType.RANDOM_OBSTACLES,
            n_obstacles=3,
            max_iterations=3000,
        )
        pattern = PathPlanningPattern(cfg)
        result = pattern.run()
        assert "n_obstacles" in result
        assert result["n_obstacles"] > 0

    def test_run_no_waypoints(self):
        cfg = PathPlanningConfig(
            planner_type=PlannerType.A_STAR,
            environment_type=EnvironmentType.EMPTY,
            grid_resolution=0.5,
            output_waypoints=False,
        )
        pattern = PathPlanningPattern(cfg)
        result = pattern.run()
        assert result["success"] is True
        assert "path" not in result

    def test_run_path_smoothness(self):
        cfg = PathPlanningConfig(
            planner_type=PlannerType.A_STAR,
            environment_type=EnvironmentType.EMPTY,
            start=np.array([0.5, 0.5]),
            goal=np.array([5.0, 5.0]),
            grid_resolution=0.5,
        )
        pattern = PathPlanningPattern(cfg)
        result = pattern.run()
        assert result["success"] is True
        if result.get("n_waypoints", 0) > 2:
            assert "mean_turning_angle" in result

    def test_run_failure_no_path(self):
        cfg = PathPlanningConfig(
            planner_type=PlannerType.A_STAR,
            environment_type=EnvironmentType.EMPTY,
            start=np.array([0.5, 0.5]),
            goal=np.array([1.0, 1.0]),
            grid_resolution=0.5,
            obstacles=[(np.array([1.0, 1.0]), 1.0)],
        )
        pattern = PathPlanningPattern(cfg)
        result = pattern.run()
        assert result["success"] is False
        assert result["path_length"] is None


class TestPathPlanningPatternMetadata:
    def test_metadata_structure(self):
        meta = PathPlanningPattern.get_metadata()
        assert meta["id"] == "path_planning"
        assert meta["version"] == "6.0.0"
        assert meta["name"] == "Path Planning"
        assert meta["category"] == "EXTENDED"
        assert "parameters" in meta
        assert len(meta["parameters"]) > 0

    def test_metadata_parameters(self):
        meta = PathPlanningPattern.get_metadata()
        param_names = [p["name"] for p in meta["parameters"]]
        assert "planner_type" in param_names
        assert "environment_type" in param_names
        assert "max_iterations" in param_names
        assert "step_size" in param_names


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_zero_step_size(self):
        cfg = PathPlanningConfig(step_size=0.0)
        planner = RRTPlanner(cfg)
        new_pos = planner._steer(np.array([0.0, 0.0]), np.array([3.0, 4.0]))
        # With zero step size, should return to_pos if distance < step_size (0)
        # or from_pos + direction * 0 = from_pos
        np.testing.assert_array_almost_equal(new_pos, np.array([0.0, 0.0]))

    def test_collision_free_same_point(self):
        cfg = PathPlanningConfig()
        planner = RRTPlanner(cfg)
        assert planner._is_collision_free(np.array([1.0, 1.0]), np.array([1.0, 1.0])) is True

    def test_node_eq_non_node(self):
        node = Node(np.array([1.0, 2.0]))
        assert node != "not a node"
        assert node != 42

    def test_empty_bounds(self):
        cfg = PathPlanningConfig(
            bounds=(np.array([0.0, 0.0]), np.array([0.0, 0.0])),
            environment_type=EnvironmentType.EMPTY,
        )
        pattern = PathPlanningPattern(cfg)
        result = pattern.run()
        # Should still complete even with zero bounds
        assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
