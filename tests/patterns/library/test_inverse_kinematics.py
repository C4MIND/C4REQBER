"""
Tests for src/patterns/library/inverse_kinematics.py

Covers: RobotKinematics, all IKSolver classes, InverseKinematicsPattern
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.patterns.library.inverse_kinematics import (

    CCDSolver,
    DampedLeastSquaresSolver,
    IKConfig,
    IKSolver,
    InverseKinematicsPattern,
    JacobianNullspaceSolver,
    JacobianPseudoinverseSolver,
    JacobianTransposeSolver,
    RobotKinematics,
    RobotType,
)


# ═══════════════════════════════════════════════════════════════════
# RobotKinematics
# ═══════════════════════════════════════════════════════════════════


class TestRobotKinematics:
    def test_init(self):
        kin = RobotKinematics(np.array([1.0, 1.0]))
        assert kin.n_dof == 2
        np.testing.assert_array_equal(kin.link_lengths, np.array([1.0, 1.0]))

    def test_forward_kinematics_2r_zero(self):
        kin = RobotKinematics(np.array([1.0, 1.0]))
        q = np.array([0.0, 0.0])
        ee, joints = kin.forward_kinematics(q)
        assert ee[0] == pytest.approx(2.0)
        assert ee[1] == pytest.approx(0.0)
        assert len(joints) == 3  # base + 2 joints + end? No, base + n_dof

    def test_forward_kinematics_2r_90_deg(self):
        kin = RobotKinematics(np.array([1.0, 1.0]))
        q = np.array([np.pi / 2, 0.0])
        ee, joints = kin.forward_kinematics(q)
        # theta=pi/2: x = cos(pi/2) + cos(pi/2) = 0, y = sin(pi/2) + sin(pi/2) = 2
        assert ee[0] == pytest.approx(0.0, abs=1e-5)
        assert ee[1] == pytest.approx(2.0, abs=1e-5)

    def test_forward_kinematics_3r(self):
        kin = RobotKinematics(np.array([1.0, 1.0, 0.5]))
        q = np.array([0.0, 0.0, 0.0])
        ee, joints = kin.forward_kinematics(q)
        assert ee[0] == pytest.approx(2.5)
        assert ee[1] == pytest.approx(0.0)

    def test_jacobian_shape_2r(self):
        kin = RobotKinematics(np.array([1.0, 1.0]))
        q = np.array([0.0, 0.0])
        J = kin.jacobian(q)
        assert J.shape == (2, 2)

    def test_jacobian_shape_3r(self):
        kin = RobotKinematics(np.array([1.0, 1.0, 0.5]))
        q = np.array([0.0, 0.0, 0.0])
        J = kin.jacobian(q)
        assert J.shape == (2, 3)

    def test_jacobian_values_zero_config(self):
        kin = RobotKinematics(np.array([1.0, 1.0]))
        q = np.array([0.0, 0.0])
        J = kin.jacobian(q)
        assert J[0, 0] == pytest.approx(0.0, abs=1e-5)
        assert J[1, 0] == pytest.approx(2.0, abs=1e-5)
        assert J[0, 1] == pytest.approx(0.0, abs=1e-5)
        assert J[1, 1] == pytest.approx(1.0, abs=1e-5)

    def test_jacobian_3d_6dof(self):
        kin = RobotKinematics(np.array([0.0, 0.4318, 0.0, 0.0, 0.0, 0.0]))
        q = np.zeros(6)
        J = kin.jacobian_3d(q)
        assert J.shape == (6, 6)

    def test_jacobian_3d_fallback(self):
        kin = RobotKinematics(np.array([1.0, 1.0]))
        q = np.array([0.0, 0.0])
        J = kin.jacobian_3d(q)
        assert J.shape == (2, 2)


# ═══════════════════════════════════════════════════════════════════
# IKConfig
# ═══════════════════════════════════════════════════════════════════


class TestIKConfig:
    def test_default(self):
        cfg = IKConfig()
        assert cfg.robot_type == RobotType.PLANAR_2R
        assert cfg.n_dof == 2
        assert cfg.solver == IKSolver.DAMPED_LEAST_SQUARES

    def test_planar_3r(self):
        cfg = IKConfig(robot_type=RobotType.PLANAR_3R)
        assert cfg.n_dof == 3
        np.testing.assert_array_equal(cfg.link_lengths, np.array([1.0, 1.0, 0.5]))

    def test_puma_560(self):
        cfg = IKConfig(robot_type=RobotType.PUMA_560)
        assert cfg.n_dof == 6

    def test_scara(self):
        cfg = IKConfig(robot_type=RobotType.SCARA)
        assert cfg.n_dof == 4

    def test_custom(self):
        cfg = IKConfig(
            robot_type=RobotType.CUSTOM, n_dof=3, link_lengths=np.array([2.0, 1.0, 0.5])
        )
        assert cfg.n_dof == 3

    def test_default_joint_limits(self):
        cfg = IKConfig()
        assert cfg.joint_limits is not None
        assert cfg.joint_limits.shape == (2, 2)

    def test_default_initial_angles(self):
        cfg = IKConfig()
        np.testing.assert_array_equal(cfg.initial_joint_angles, np.zeros(2))


# ═══════════════════════════════════════════════════════════════════
# Jacobian Transpose Solver
# ═══════════════════════════════════════════════════════════════════


class TestJacobianTransposeSolver:
    def test_convergence(self):
        cfg = IKConfig(
            robot_type=RobotType.PLANAR_2R,
            solver=IKSolver.JACOBIAN_TRANSPOSE,
            target_position=np.array([1.0, 1.0]),
            max_iterations=1000,
            tolerance=1e-4,
        )
        kin = RobotKinematics(cfg.link_lengths)
        solver = JacobianTransposeSolver(kin, cfg)
        q_init = np.array([0.0, 0.0])
        q, converged, iters, traj = solver.solve(cfg.target_position, q_init)
        ee, _ = kin.forward_kinematics(q)
        error = np.linalg.norm(ee - cfg.target_position)
        assert error < 0.01
        assert len(traj) > 0

    def test_joint_limits(self):
        cfg = IKConfig(
            robot_type=RobotType.PLANAR_2R,
            solver=IKSolver.JACOBIAN_TRANSPOSE,
            target_position=np.array([1.0, 0.0]),
            joint_limits=np.array([[-np.pi / 4, np.pi / 4], [-np.pi / 4, np.pi / 4]]),
        )
        kin = RobotKinematics(cfg.link_lengths)
        solver = JacobianTransposeSolver(kin, cfg)
        q, _, _, _ = solver.solve(cfg.target_position, np.zeros(2))
        assert q[0] >= -np.pi / 4 - 1e-6
        assert q[0] <= np.pi / 4 + 1e-6


# ═══════════════════════════════════════════════════════════════════
# Jacobian Pseudoinverse Solver
# ═══════════════════════════════════════════════════════════════════


class TestJacobianPseudoinverseSolver:
    def test_convergence(self):
        cfg = IKConfig(
            robot_type=RobotType.PLANAR_2R,
            solver=IKSolver.JACOBIAN_PSEUDOINVERSE,
            target_position=np.array([1.0, 1.0]),
            tolerance=1e-4,
            max_iterations=2000,
            step_size=0.5,
        )
        kin = RobotKinematics(cfg.link_lengths)
        solver = JacobianPseudoinverseSolver(kin, cfg)
        q_init = np.array([0.5, 0.5])
        q, converged, iters, traj = solver.solve(cfg.target_position, q_init)
        ee, _ = kin.forward_kinematics(q)
        error = np.linalg.norm(ee - cfg.target_position)
        assert error < 0.01

    def test_fallback_on_singular(self):
        # Near singular configuration
        cfg = IKConfig(
            robot_type=RobotType.PLANAR_2R,
            solver=IKSolver.JACOBIAN_PSEUDOINVERSE,
            target_position=np.array([2.0, 0.0]),
            tolerance=1e-4,
        )
        kin = RobotKinematics(cfg.link_lengths)
        solver = JacobianPseudoinverseSolver(kin, cfg)
        # Fully extended is singular-ish
        q, converged, iters, traj = solver.solve(cfg.target_position, np.zeros(2))
        assert len(traj) > 0


# ═══════════════════════════════════════════════════════════════════
# Damped Least Squares Solver
# ═══════════════════════════════════════════════════════════════════


class TestDampedLeastSquaresSolver:
    def test_convergence(self):
        cfg = IKConfig(
            robot_type=RobotType.PLANAR_2R,
            solver=IKSolver.DAMPED_LEAST_SQUARES,
            target_position=np.array([1.0, 1.0]),
            damping_lambda=0.1,
            tolerance=1e-4,
        )
        kin = RobotKinematics(cfg.link_lengths)
        solver = DampedLeastSquaresSolver(kin, cfg)
        q, converged, iters, traj = solver.solve(cfg.target_position, np.zeros(2))
        ee, _ = kin.forward_kinematics(q)
        error = np.linalg.norm(ee - cfg.target_position)
        assert error < 0.01

    def test_3r_convergence(self):
        cfg = IKConfig(
            robot_type=RobotType.PLANAR_3R,
            solver=IKSolver.DAMPED_LEAST_SQUARES,
            target_position=np.array([1.5, 1.0]),
            tolerance=1e-4,
        )
        kin = RobotKinematics(cfg.link_lengths)
        solver = DampedLeastSquaresSolver(kin, cfg)
        q, converged, iters, traj = solver.solve(cfg.target_position, np.zeros(3))
        ee, _ = kin.forward_kinematics(q)
        error = np.linalg.norm(ee - cfg.target_position)
        assert error < 0.01


# ═══════════════════════════════════════════════════════════════════
# Jacobian Nullspace Solver
# ═══════════════════════════════════════════════════════════════════


class TestJacobianNullspaceSolver:
    def test_convergence(self):
        cfg = IKConfig(
            robot_type=RobotType.PLANAR_3R,
            solver=IKSolver.JACOBIAN_NULLSPACE,
            target_position=np.array([1.5, 0.5]),
            tolerance=1e-4,
            nullspace_gain=0.1,
        )
        kin = RobotKinematics(cfg.link_lengths)
        solver = JacobianNullspaceSolver(kin, cfg)
        q, converged, iters, traj = solver.solve(cfg.target_position, np.zeros(3))
        ee, _ = kin.forward_kinematics(q)
        error = np.linalg.norm(ee - cfg.target_position)
        assert error < 0.01

    def test_secondary_objective(self):
        cfg = IKConfig(
            robot_type=RobotType.PLANAR_3R,
            solver=IKSolver.JACOBIAN_NULLSPACE,
            target_position=np.array([1.5, 0.5]),
            tolerance=1e-4,
        )
        kin = RobotKinematics(cfg.link_lengths)
        solver = JacobianNullspaceSolver(kin, cfg)
        secondary = lambda q: np.zeros_like(q)
        q, converged, iters, traj = solver.solve(
            cfg.target_position, np.zeros(3), secondary_objective=secondary
        )
        assert len(traj) > 0


# ═══════════════════════════════════════════════════════════════════
# CCD Solver
# ═══════════════════════════════════════════════════════════════════


class TestCCDSolver:
    def test_convergence(self):
        cfg = IKConfig(
            robot_type=RobotType.PLANAR_3R,
            solver=IKSolver.CCD,
            target_position=np.array([1.5, 0.5]),
            tolerance=1e-4,
        )
        kin = RobotKinematics(cfg.link_lengths)
        solver = CCDSolver(kin, cfg)
        q, converged, iters, traj = solver.solve(cfg.target_position, np.zeros(3))
        ee, _ = kin.forward_kinematics(q)
        error = np.linalg.norm(ee - cfg.target_position)
        assert error < 0.01

    def test_2r_convergence(self):
        cfg = IKConfig(
            robot_type=RobotType.PLANAR_2R,
            solver=IKSolver.CCD,
            target_position=np.array([1.0, 1.0]),
            tolerance=1e-4,
        )
        kin = RobotKinematics(cfg.link_lengths)
        solver = CCDSolver(kin, cfg)
        q, converged, iters, traj = solver.solve(cfg.target_position, np.zeros(2))
        ee, _ = kin.forward_kinematics(q)
        error = np.linalg.norm(ee - cfg.target_position)
        assert error < 0.01


# ═══════════════════════════════════════════════════════════════════
# InverseKinematicsPattern
# ═══════════════════════════════════════════════════════════════════


class TestInverseKinematicsPattern:
    def test_init(self):
        pattern = InverseKinematicsPattern()
        assert pattern.config.n_dof == 2
        assert pattern.solver is None

    def test_solve_2r_dls(self):
        cfg = IKConfig(
            robot_type=RobotType.PLANAR_2R,
            solver=IKSolver.DAMPED_LEAST_SQUARES,
            target_position=np.array([1.0, 1.0]),
            tolerance=1e-4,
        )
        pattern = InverseKinematicsPattern(cfg)
        result = pattern.solve()
        assert result["converged"] is True
        assert result["position_error"] < 1e-3
        assert len(result["solution"]) == 2
        assert "trajectory" in result
        assert len(result["trajectory"]["iteration"]) > 0

    def test_solve_3r(self):
        cfg = IKConfig(
            robot_type=RobotType.PLANAR_3R,
            solver=IKSolver.DAMPED_LEAST_SQUARES,
            target_position=np.array([1.5, 1.0]),
            tolerance=1e-4,
        )
        pattern = InverseKinematicsPattern(cfg)
        result = pattern.solve()
        assert result["converged"] is True
        assert len(result["solution"]) == 3

    def test_solve_with_target_override(self):
        cfg = IKConfig(
            robot_type=RobotType.PLANAR_2R,
            solver=IKSolver.DAMPED_LEAST_SQUARES,
            target_position=np.array([1.0, 1.0]),
        )
        pattern = InverseKinematicsPattern(cfg)
        result = pattern.solve(target=np.array([0.5, 1.5]))
        assert result["target"] == [0.5, 1.5]

    def test_run_single_target(self):
        cfg = IKConfig(
            robot_type=RobotType.PLANAR_2R,
            solver=IKSolver.DAMPED_LEAST_SQUARES,
            target_position=np.array([1.0, 0.5]),
        )
        pattern = InverseKinematicsPattern(cfg)
        result = pattern.run()
        assert "target" in result
        assert "solution" in result
        assert "trajectory" in result

    def test_run_trajectory_mode(self):
        targets = [
            np.array([1.0, 0.5]),
            np.array([0.5, 1.0]),
            np.array([1.5, 0.0]),
        ]
        cfg = IKConfig(
            robot_type=RobotType.PLANAR_2R,
            solver=IKSolver.DAMPED_LEAST_SQUARES,
            trajectory_targets=targets,
        )
        pattern = InverseKinematicsPattern(cfg)
        result = pattern.run()
        assert result["trajectory_mode"] is True
        assert result["n_points"] == 3
        assert len(result["results"]) == 3

    def test_multiple_solvers(self):
        target = np.array([0.8, 1.2])
        for solver in [
            IKSolver.JACOBIAN_TRANSPOSE,
            IKSolver.JACOBIAN_PSEUDOINVERSE,
            IKSolver.DAMPED_LEAST_SQUARES,
        ]:
            cfg = IKConfig(
                robot_type=RobotType.PLANAR_2R,
                solver=solver,
                target_position=target,
                max_iterations=2000,
            )
            pattern = InverseKinematicsPattern(cfg)
            result = pattern.solve()
            assert result["position_error"] < 0.01, f"Solver {solver.value} failed"

    def test_joint_limits(self):
        cfg = IKConfig(
            robot_type=RobotType.PLANAR_2R,
            solver=IKSolver.DAMPED_LEAST_SQUARES,
            target_position=np.array([1.0, 0.0]),
            joint_limits=np.array(
                [[-np.pi / 4, np.pi / 4], [-np.pi / 4, np.pi / 4]]
            ),
        )
        pattern = InverseKinematicsPattern(cfg)
        result = pattern.solve()
        solution = np.array(result["solution"])
        assert solution[0] >= -np.pi / 4 - 1e-6
        assert solution[0] <= np.pi / 4 + 1e-6

    def test_metadata(self):
        meta = InverseKinematicsPattern.get_metadata()
        assert meta["id"] == "inverse_kinematics"
        assert meta["category"] == "EXTENDED"
        assert "parameters" in meta

    def test_history_populated(self):
        cfg = IKConfig(
            robot_type=RobotType.PLANAR_2R,
            solver=IKSolver.DAMPED_LEAST_SQUARES,
            target_position=np.array([1.0, 1.0]),
        )
        pattern = InverseKinematicsPattern(cfg)
        pattern.solve()
        assert len(pattern.history["iteration"]) > 0
        assert len(pattern.history["joint_angles"]) > 0
        assert len(pattern.history["end_effector"]) > 0
        assert len(pattern.history["error"]) > 0
