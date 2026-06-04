"""
C4REQBER v6.0 - Inverse Kinematics Unit Tests
"""

import unittest

import numpy as np

from .config import IKConfig, IKSolver, RobotType
from .core import (
    CCDSolver,
    DampedLeastSquaresSolver,
    InverseKinematicsPattern,
    JacobianTransposeSolver,
    RobotKinematics,
)


class TestRobotKinematics(unittest.TestCase):
    """Unit tests for robot kinematics"""

    def test_fk_2r(self) -> None:
        """Test forward kinematics for 2R planar"""
        kin = RobotKinematics(np.array([1.0, 1.0]))

        # Zero configuration
        q = np.array([0.0, 0.0])
        ee, joints = kin.forward_kinematics(q)

        self.assertAlmostEqual(ee[0], 2.0)
        self.assertAlmostEqual(ee[1], 0.0)

    def test_fk_90_degrees(self) -> None:
        """Test FK with 90 degree joint angles"""
        kin = RobotKinematics(np.array([1.0, 1.0]))

        q = np.array([np.pi / 2, 0.0])
        ee, joints = kin.forward_kinematics(q)

        self.assertAlmostEqual(ee[0], 0.0, places=5)
        self.assertAlmostEqual(ee[1], 1.0, places=5)

    def test_jacobian_shape(self) -> None:
        """Test Jacobian matrix shape"""
        kin = RobotKinematics(np.array([1.0, 1.0, 0.5]))
        q = np.array([0.0, 0.0, 0.0])

        J = kin.jacobian(q)

        self.assertEqual(J.shape, (2, 3))

    def test_jacobian_values(self) -> None:
        """Test Jacobian values at specific configuration"""
        kin = RobotKinematics(np.array([1.0, 1.0]))
        q = np.array([0.0, 0.0])

        J = kin.jacobian(q)

        # At zero config, first joint affects both x and y equally
        self.assertAlmostEqual(J[0, 0], 0.0, places=5)  # d_x/d_q1
        self.assertAlmostEqual(J[1, 0], 2.0, places=5)  # d_y/d_q1

class TestIKSolvers(unittest.TestCase):
    """Unit tests for IK solvers"""

    def test_jacobian_transpose(self) -> None:
        """Test Jacobian transpose solver"""
        config = IKConfig(
            robot_type=RobotType.PLANAR_2R,
            solver=IKSolver.JACOBIAN_TRANSPOSE,
            target_position=np.array([1.0, 1.0]),
            max_iterations=1000,
        )
        kin = RobotKinematics(config.link_lengths)
        solver = JacobianTransposeSolver(kin, config)

        q_init = np.array([0.0, 0.0])
        q, converged, iters, traj = solver.solve(config.target_position, q_init)

        # Check convergence
        ee, _ = kin.forward_kinematics(q)
        error = np.linalg.norm(ee - config.target_position)
        self.assertLess(error, 0.01)

    def test_damped_least_squares(self) -> None:
        """Test DLS solver"""
        config = IKConfig(
            robot_type=RobotType.PLANAR_2R,
            solver=IKSolver.DAMPED_LEAST_SQUARES,
            target_position=np.array([0.5, 1.5]),
            damping_lambda=0.1,
        )
        kin = RobotKinematics(config.link_lengths)
        solver = DampedLeastSquaresSolver(kin, config)

        q_init = np.array([0.0, 0.0])
        q, converged, iters, traj = solver.solve(config.target_position, q_init)

        ee, _ = kin.forward_kinematics(q)
        error = np.linalg.norm(ee - config.target_position)
        self.assertLess(error, 0.01)

    def test_ccd_solver(self) -> None:
        """Test CCD solver"""
        config = IKConfig(
            robot_type=RobotType.PLANAR_3R,
            solver=IKSolver.CCD,
            target_position=np.array([1.5, 0.5]),
        )
        kin = RobotKinematics(config.link_lengths)
        solver = CCDSolver(kin, config)

        q_init = np.array([0.0, 0.0, 0.0])
        q, converged, iters, traj = solver.solve(config.target_position, q_init)

        ee, _ = kin.forward_kinematics(q)
        error = np.linalg.norm(ee - config.target_position)
        self.assertLess(error, 0.01)

class TestInverseKinematicsPattern(unittest.TestCase):
    """Unit tests for IK pattern"""

    def test_initialization(self) -> None:
        """Test pattern initialization"""
        pattern = InverseKinematicsPattern()
        self.assertIsNotNone(pattern.config)
        self.assertEqual(pattern.config.n_dof, 2)

    def test_solve_2r(self) -> None:
        """Test IK solve for 2R robot"""
        config = IKConfig(
            robot_type=RobotType.PLANAR_2R,
            solver=IKSolver.DAMPED_LEAST_SQUARES,
            target_position=np.array([1.0, 1.0]),
            tolerance=1e-4,
        )
        pattern = InverseKinematicsPattern(config)
        result = pattern.solve()

        self.assertTrue(result["converged"])
        self.assertLess(result["position_error"], 1e-3)
        self.assertEqual(len(result["solution"]), 2)

    def test_solve_3r(self) -> None:
        """Test IK solve for 3R robot"""
        config = IKConfig(
            robot_type=RobotType.PLANAR_3R,
            solver=IKSolver.DAMPED_LEAST_SQUARES,
            target_position=np.array([1.5, 1.0]),
            tolerance=1e-4,
        )
        pattern = InverseKinematicsPattern(config)
        result = pattern.solve()

        self.assertTrue(result["converged"])
        self.assertEqual(len(result["solution"]), 3)

    def test_multiple_solvers(self) -> None:
        """Test different IK solvers"""
        target = np.array([0.8, 1.2])

        for solver in [
            IKSolver.JACOBIAN_TRANSPOSE,
            IKSolver.JACOBIAN_PSEUDOINVERSE,
            IKSolver.DAMPED_LEAST_SQUARES,
        ]:
            config = IKConfig(
                robot_type=RobotType.PLANAR_2R,
                solver=solver,
                target_position=target,
                max_iterations=2000,
            )
            pattern = InverseKinematicsPattern(config)
            result = pattern.solve()

            self.assertLess(
                result["position_error"],
                0.01,
                f"Solver {solver.value} failed to converge",
            )

    def test_joint_limits(self) -> None:
        """Test joint limit enforcement"""
        config = IKConfig(
            robot_type=RobotType.PLANAR_2R,
            solver=IKSolver.DAMPED_LEAST_SQUARES,
            target_position=np.array([1.0, 0.0]),
            joint_limits=np.array([[-np.pi / 4, np.pi / 4], [-np.pi / 4, np.pi / 4]]),
        )
        pattern = InverseKinematicsPattern(config)
        result = pattern.solve()

        # Check solution respects limits
        solution = np.array(result["solution"])
        self.assertGreaterEqual(solution[0], -np.pi / 4 - 1e-6)
        self.assertLessEqual(solution[0], np.pi / 4 + 1e-6)

    def test_run_method(self) -> None:
        """Test full run method"""
        config = IKConfig(
            robot_type=RobotType.PLANAR_2R,
            solver=IKSolver.DAMPED_LEAST_SQUARES,
            target_position=np.array([1.0, 0.5]),
        )
        pattern = InverseKinematicsPattern(config)
        result = pattern.run()

        self.assertIn("target", result)
        self.assertIn("solution", result)
        self.assertIn("trajectory", result)

    def test_trajectory_mode(self) -> None:
        """Test trajectory tracking mode"""
        targets = [np.array([1.0, 0.5]), np.array([0.5, 1.0]), np.array([1.5, 0.0])]
        config = IKConfig(
            robot_type=RobotType.PLANAR_2R,
            solver=IKSolver.DAMPED_LEAST_SQUARES,
            trajectory_targets=targets,
        )
        pattern = InverseKinematicsPattern(config)
        result = pattern.run()

        self.assertTrue(result["trajectory_mode"])
        self.assertEqual(result["n_points"], 3)
        self.assertGreater(result["convergence_rate"], 0.5)

    def test_get_metadata(self) -> None:
        """Test metadata retrieval"""
        metadata = InverseKinematicsPattern.get_metadata()

        self.assertEqual(metadata["id"], "inverse_kinematics")
        self.assertEqual(metadata["category"], "EXTENDED")

if __name__ == "__main__":
    unittest.main(verbosity=2)
