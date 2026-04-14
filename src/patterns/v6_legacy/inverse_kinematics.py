"""
TURBO-CDI v6.0 - Inverse Kinematics Pattern
Jacobian-based IK solvers for robotic manipulators.

Pattern Structure (Christopher Alexander):
- Context: Robotic arm control, animation, biomechanics
- Forces: Accuracy vs computation speed, multiple solutions, singularities
- Solution: Numerical IK with Jacobian pseudo-inverse and redundancy resolution
"""

import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class IKSolver(Enum):
    """Available IK solvers"""

    JACOBIAN_TRANSPOSE = "jacobian_transpose"
    JACOBIAN_PSEUDOINVERSE = "jacobian_pseudoinverse"
    DAMPED_LEAST_SQUARES = "damped_least_squares"
    JACOBIAN_NULLSPACE = "jacobian_nullspace"
    CCD = "ccd"  # Cyclic Coordinate Descent
    FABRIK = "fabrik"  # Forward And Backward Reaching IK


class RobotType(Enum):
    """Predefined robot configurations"""

    PLANAR_2R = "planar_2r"  # 2-link planar
    PLANAR_3R = "planar_3r"  # 3-link planar
    PUMA_560 = "puma_560"  # 6-DOF industrial
    SCARA = "scara"  # 4-DOF SCARA
    CUSTOM = "custom"


@dataclass
class IKConfig:
    """Configuration for Inverse Kinematics"""

    # Robot configuration
    robot_type: RobotType = RobotType.PLANAR_2R
    n_dof: int = 2
    link_lengths: np.ndarray = field(default_factory=lambda: np.array([1.0, 1.0]))
    joint_limits: Optional[np.ndarray] = None  # [min, max] per joint

    # Solver settings
    solver: IKSolver = IKSolver.DAMPED_LEAST_SQUARES
    max_iterations: int = 1000
    tolerance: float = 1e-6
    step_size: float = 0.1

    # DLS damping
    damping_lambda: float = 0.1

    # Nullspace settings
    nullspace_gain: float = 0.1

    # Target
    target_position: np.ndarray = field(default_factory=lambda: np.array([1.0, 1.0]))
    target_orientation: Optional[np.ndarray] = None  # For 6-DOF

    # Simulation
    initial_joint_angles: Optional[np.ndarray] = None

    # Multiple targets for trajectory
    trajectory_targets: Optional[List[np.ndarray]] = None

    # Output
    output_interval: int = 1

    def __post_init__(self):
        """Initialize robot configuration"""
        if self.robot_type == RobotType.PLANAR_2R:
            self.n_dof = 2
            self.link_lengths = np.array([1.0, 1.0])

        elif self.robot_type == RobotType.PLANAR_3R:
            self.n_dof = 3
            self.link_lengths = np.array([1.0, 1.0, 0.5])

        elif self.robot_type == RobotType.PUMA_560:
            self.n_dof = 6
            self.link_lengths = np.array(
                [0.0, 0.4318, 0.0, 0.0, 0.0, 0.0]
            )  # Simplified

        elif self.robot_type == RobotType.SCARA:
            self.n_dof = 4
            self.link_lengths = np.array([0.4, 0.3, 0.0, 0.1])  # x, y, z, rotation

        # Default joint limits
        if self.joint_limits is None:
            self.joint_limits = np.array([[-np.pi, np.pi]] * self.n_dof)

        # Default initial configuration
        if self.initial_joint_angles is None:
            self.initial_joint_angles = np.zeros(self.n_dof)


class RobotKinematics:
    """Forward and differential kinematics for planar robots"""

    def __init__(self, link_lengths: np.ndarray):
        self.link_lengths = link_lengths
        self.n_dof = len(link_lengths)

    def forward_kinematics(self, q: np.ndarray) -> Tuple[np.ndarray, List[np.ndarray]]:
        """
        Compute forward kinematics for planar manipulator.
        Returns end-effector position and joint positions.
        """
        x, y = 0.0, 0.0
        theta = 0.0
        joint_positions = [np.array([0.0, 0.0])]

        for i in range(self.n_dof):
            theta += q[i]
            x += self.link_lengths[i] * np.cos(theta)
            y += self.link_lengths[i] * np.sin(theta)
            joint_positions.append(np.array([x, y]))

        end_effector = np.array([x, y])
        return end_effector, joint_positions

    def jacobian(self, q: np.ndarray) -> np.ndarray:
        """
        Compute Jacobian matrix for planar manipulator.
        J[i] = [-sum(l_k * sin(sum(q_j))), sum(l_k * cos(sum(q_j)))]
        """
        J = np.zeros((2, self.n_dof))

        for i in range(self.n_dof):
            # Sum of angles from joint i to end
            angle_sum = np.sum(q[i:])
            # Sum of link lengths from joint i to end
            length_sum = np.sum(self.link_lengths[i:])

            J[0, i] = -length_sum * np.sin(angle_sum)
            J[1, i] = length_sum * np.cos(angle_sum)

        return J

    def jacobian_3d(self, q: np.ndarray) -> np.ndarray:
        """
        Compute Jacobian for 3D manipulator (simplified).
        For 6-DOF, returns 6xn Jacobian [linear; angular].
        """
        if self.n_dof == 6:
            # Simplified PUMA 560 Jacobian
            J = np.zeros((6, 6))
            # Fill with approximate values
            for i in range(6):
                J[0, i] = -np.sin(q[i]) * self.link_lengths[i]
                J[1, i] = np.cos(q[i]) * self.link_lengths[i]
                J[5, i] = 1.0  # Rotation about z
            return J
        else:
            return self.jacobian(q)


class IKSolverBase:
    """Base class for IK solvers"""

    def __init__(self, kinematics: RobotKinematics, config: IKConfig):
        self.kinematics = kinematics
        self.config = config

    def solve(
        self, target: np.ndarray, q_init: np.ndarray
    ) -> Tuple[np.ndarray, bool, int, List]:
        """
        Solve IK.
        Returns: (q_solution, converged, iterations, trajectory)
        """
        raise NotImplementedError


class JacobianTransposeSolver(IKSolverBase):
    """Jacobian transpose method"""

    def solve(
        self, target: np.ndarray, q_init: np.ndarray
    ) -> Tuple[np.ndarray, bool, int, List]:
        q = q_init.copy()
        trajectory = [q.copy()]

        for iteration in range(self.config.max_iterations):
            # Current position
            current, _ = self.kinematics.forward_kinematics(q)

            # Position error
            error = target - current

            # Check convergence
            if np.linalg.norm(error) < self.config.tolerance:
                return q, True, iteration, trajectory

            # Jacobian transpose update
            J = self.kinematics.jacobian(q)
            delta_q = self.config.step_size * J.T @ error

            # Update
            q += delta_q

            # Apply joint limits
            q = np.clip(
                q, self.config.joint_limits[:, 0], self.config.joint_limits[:, 1]
            )

            trajectory.append(q.copy())

        return q, False, self.config.max_iterations, trajectory


class JacobianPseudoinverseSolver(IKSolverBase):
    """Jacobian pseudo-inverse method"""

    def solve(
        self, target: np.ndarray, q_init: np.ndarray
    ) -> Tuple[np.ndarray, bool, int, List]:
        q = q_init.copy()
        trajectory = [q.copy()]

        for iteration in range(self.config.max_iterations):
            current, _ = self.kinematics.forward_kinematics(q)
            error = target - current

            if np.linalg.norm(error) < self.config.tolerance:
                return q, True, iteration, trajectory

            J = self.kinematics.jacobian(q)

            # Pseudo-inverse
            try:
                J_pinv = np.linalg.pinv(J)
                delta_q = self.config.step_size * J_pinv @ error
            except:
                # Fallback to transpose if singular
                delta_q = self.config.step_size * J.T @ error

            q += delta_q
            q = np.clip(
                q, self.config.joint_limits[:, 0], self.config.joint_limits[:, 1]
            )

            trajectory.append(q.copy())

        return q, False, self.config.max_iterations, trajectory


class DampedLeastSquaresSolver(IKSolverBase):
    """Damped Least Squares (Levenberg-Marquardt) method"""

    def solve(
        self, target: np.ndarray, q_init: np.ndarray
    ) -> Tuple[np.ndarray, bool, int, List]:
        q = q_init.copy()
        trajectory = [q.copy()]
        lambda_sq = self.config.damping_lambda**2

        for iteration in range(self.config.max_iterations):
            current, _ = self.kinematics.forward_kinematics(q)
            error = target - current

            if np.linalg.norm(error) < self.config.tolerance:
                return q, True, iteration, trajectory

            J = self.kinematics.jacobian(q)

            # DLS: delta_q = J^T (J J^T + lambda^2 I)^-1 error
            try:
                JJT = J @ J.T
                damping = lambda_sq * np.eye(JJT.shape[0])
                delta_q = J.T @ np.linalg.solve(JJT + damping, error)
            except:
                delta_q = self.config.step_size * J.T @ error

            q += self.config.step_size * delta_q
            q = np.clip(
                q, self.config.joint_limits[:, 0], self.config.joint_limits[:, 1]
            )

            trajectory.append(q.copy())

        return q, False, self.config.max_iterations, trajectory


class JacobianNullspaceSolver(IKSolverBase):
    """Jacobian pseudo-inverse with nullspace optimization"""

    def solve(
        self,
        target: np.ndarray,
        q_init: np.ndarray,
        secondary_objective: Optional[Callable] = None,
    ) -> Tuple[np.ndarray, bool, int, List]:
        q = q_init.copy()
        trajectory = [q.copy()]

        for iteration in range(self.config.max_iterations):
            current, _ = self.kinematics.forward_kinematics(q)
            error = target - current

            if np.linalg.norm(error) < self.config.tolerance:
                return q, True, iteration, trajectory

            J = self.kinematics.jacobian(q)

            try:
                J_pinv = np.linalg.pinv(J)

                # Primary task
                delta_q_primary = J_pinv @ error

                # Nullspace projection
                I_JpinvJ = np.eye(self.kinematics.n_dof) - J_pinv @ J

                # Secondary objective: joint centering
                if secondary_objective is None:
                    q_center = (
                        self.config.joint_limits[:, 0] + self.config.joint_limits[:, 1]
                    ) / 2
                    delta_q_secondary = self.config.nullspace_gain * (q_center - q)
                else:
                    delta_q_secondary = secondary_objective(q)

                delta_q = delta_q_primary + I_JpinvJ @ delta_q_secondary

            except:
                delta_q = self.config.step_size * J.T @ error

            q += self.config.step_size * delta_q
            q = np.clip(
                q, self.config.joint_limits[:, 0], self.config.joint_limits[:, 1]
            )

            trajectory.append(q.copy())

        return q, False, self.config.max_iterations, trajectory


class CCDSolver(IKSolverBase):
    """Cyclic Coordinate Descent solver"""

    def solve(
        self, target: np.ndarray, q_init: np.ndarray
    ) -> Tuple[np.ndarray, bool, int, List]:
        q = q_init.copy()
        trajectory = [q.copy()]

        for iteration in range(self.config.max_iterations):
            converged = True

            # Iterate through joints from end to base
            for i in range(self.kinematics.n_dof - 1, -1, -1):
                # Get current joint position
                _, joint_positions = self.kinematics.forward_kinematics(q)
                joint_pos = joint_positions[i]

                # Vectors
                to_end = joint_positions[-1] - joint_pos
                to_target = target - joint_pos

                # Angle between vectors
                cos_angle = np.dot(to_end, to_target) / (
                    np.linalg.norm(to_end) * np.linalg.norm(to_target) + 1e-10
                )
                cos_angle = np.clip(cos_angle, -1.0, 1.0)
                angle = np.arccos(cos_angle)

                # Direction
                cross = np.cross(to_end, to_target)
                if cross < 0:
                    angle = -angle

                # Update joint angle
                q[i] += self.config.step_size * angle
                q[i] = np.clip(
                    q[i], self.config.joint_limits[i, 0], self.config.joint_limits[i, 1]
                )

                # Check convergence for this joint
                if abs(angle) > self.config.tolerance:
                    converged = False

            trajectory.append(q.copy())

            # Check overall convergence
            current, _ = self.kinematics.forward_kinematics(q)
            if np.linalg.norm(target - current) < self.config.tolerance:
                return q, True, iteration, trajectory

        return q, False, self.config.max_iterations, trajectory


class InverseKinematicsPattern:
    """
    Inverse Kinematics pattern for robotic manipulators.

    Implements multiple IK solvers including Jacobian-based
    methods and geometric approaches.
    """

    PATTERN_ID = "inverse_kinematics"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: Optional[IKConfig] = None):
        self.config = config or IKConfig()
        self.kinematics = RobotKinematics(self.config.link_lengths)
        self.solver: Optional[IKSolverBase] = None
        self.history: Dict[str, List] = {
            "iteration": [],
            "joint_angles": [],
            "end_effector": [],
            "error": [],
            "converged": [],
        }

    def _initialize_solver(self):
        """Initialize IK solver"""
        cfg = self.config

        if cfg.solver == IKSolver.JACOBIAN_TRANSPOSE:
            self.solver = JacobianTransposeSolver(self.kinematics, cfg)
        elif cfg.solver == IKSolver.JACOBIAN_PSEUDOINVERSE:
            self.solver = JacobianPseudoinverseSolver(self.kinematics, cfg)
        elif cfg.solver == IKSolver.DAMPED_LEAST_SQUARES:
            self.solver = DampedLeastSquaresSolver(self.kinematics, cfg)
        elif cfg.solver == IKSolver.JACOBIAN_NULLSPACE:
            self.solver = JacobianNullspaceSolver(self.kinematics, cfg)
        elif cfg.solver == IKSolver.CCD:
            self.solver = CCDSolver(self.kinematics, cfg)
        else:
            self.solver = DampedLeastSquaresSolver(self.kinematics, cfg)

    def solve(self, target: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """Solve IK for single target"""
        cfg = self.config

        if target is None:
            target = cfg.target_position

        self._initialize_solver()

        q_solution, converged, iterations, trajectory = self.solver.solve(
            target, cfg.initial_joint_angles
        )

        # Final forward kinematics
        final_position, joint_positions = self.kinematics.forward_kinematics(q_solution)

        # Calculate error
        position_error = np.linalg.norm(target - final_position)

        # Store trajectory
        for i, q in enumerate(trajectory):
            pos, _ = self.kinematics.forward_kinematics(q)
            self.history["iteration"].append(i)
            self.history["joint_angles"].append(q.tolist())
            self.history["end_effector"].append(pos.tolist())
            self.history["error"].append(np.linalg.norm(target - pos))

        return {
            "target": target.tolist(),
            "solution": q_solution.tolist(),
            "final_position": final_position.tolist(),
            "joint_positions": [jp.tolist() for jp in joint_positions],
            "converged": converged,
            "iterations": iterations,
            "position_error": float(position_error),
            "trajectory": {
                "iteration": self.history["iteration"],
                "joint_angles": self.history["joint_angles"],
                "end_effector": self.history["end_effector"],
                "error": self.history["error"],
            },
            "config": {
                "robot_type": cfg.robot_type.value,
                "solver": cfg.solver.value,
                "n_dof": cfg.n_dof,
                "link_lengths": cfg.link_lengths.tolist(),
            },
        }

    def run(self, hypothesis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run IK for single target or trajectory"""
        cfg = self.config

        logger.info(f"Starting IK: {cfg.robot_type.value}, solver={cfg.solver.value}")

        if cfg.trajectory_targets is None:
            # Single target
            return self.solve()
        else:
            # Trajectory tracking
            results = []
            q_current = cfg.initial_joint_angles.copy()

            for i, target in enumerate(cfg.trajectory_targets):
                # Update initial guess
                cfg.initial_joint_angles = q_current

                result = self.solve(target)
                results.append(result)

                # Use solution as next initial guess
                q_current = np.array(result["solution"])

            return {
                "trajectory_mode": True,
                "n_points": len(cfg.trajectory_targets),
                "results": results,
                "mean_error": np.mean([r["position_error"] for r in results]),
                "convergence_rate": np.mean([r["converged"] for r in results]),
            }

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Inverse Kinematics",
            "category": "EXTENDED",
            "domain": ["Robotics", "Animation", "Biomechanics", "Computer Graphics"],
            "description": "Jacobian-based IK solvers for robotic manipulators",
            "computational_complexity": "O(n²) per iteration",
            "typical_runtime": "microseconds to milliseconds",
            "accuracy": "High (depends on tolerance)",
            "assumptions": [
                "Known forward kinematics",
                "Continuous joint space",
                "Non-singular configurations",
            ],
            "parameters": [
                {
                    "name": "robot_type",
                    "type": "enum",
                    "options": ["planar_2r", "planar_3r", "puma_560", "scara"],
                    "default": "planar_2r",
                },
                {
                    "name": "solver",
                    "type": "enum",
                    "options": [
                        "jacobian_transpose",
                        "jacobian_pseudoinverse",
                        "damped_least_squares",
                        "jacobian_nullspace",
                        "ccd",
                    ],
                    "default": "damped_least_squares",
                },
                {"name": "tolerance", "type": "float", "default": 1e-6},
                {"name": "max_iterations", "type": "int", "default": 1000},
            ],
        }


# =============================================================================
# UNIT TESTS
# =============================================================================

import unittest


class TestRobotKinematics(unittest.TestCase):
    """Unit tests for robot kinematics"""

    def test_fk_2r(self):
        """Test forward kinematics for 2R planar"""
        kin = RobotKinematics(np.array([1.0, 1.0]))

        # Zero configuration
        q = np.array([0.0, 0.0])
        ee, joints = kin.forward_kinematics(q)

        self.assertAlmostEqual(ee[0], 2.0)
        self.assertAlmostEqual(ee[1], 0.0)

    def test_fk_90_degrees(self):
        """Test FK with 90 degree joint angles"""
        kin = RobotKinematics(np.array([1.0, 1.0]))

        q = np.array([np.pi / 2, 0.0])
        ee, joints = kin.forward_kinematics(q)

        self.assertAlmostEqual(ee[0], 0.0, places=5)
        self.assertAlmostEqual(ee[1], 1.0, places=5)

    def test_jacobian_shape(self):
        """Test Jacobian matrix shape"""
        kin = RobotKinematics(np.array([1.0, 1.0, 0.5]))
        q = np.array([0.0, 0.0, 0.0])

        J = kin.jacobian(q)

        self.assertEqual(J.shape, (2, 3))

    def test_jacobian_values(self):
        """Test Jacobian values at specific configuration"""
        kin = RobotKinematics(np.array([1.0, 1.0]))
        q = np.array([0.0, 0.0])

        J = kin.jacobian(q)

        # At zero config, first joint affects both x and y equally
        self.assertAlmostEqual(J[0, 0], 0.0, places=5)  # d_x/d_q1
        self.assertAlmostEqual(J[1, 0], 2.0, places=5)  # d_y/d_q1


class TestIKSolvers(unittest.TestCase):
    """Unit tests for IK solvers"""

    def test_jacobian_transpose(self):
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

    def test_damped_least_squares(self):
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

    def test_ccd_solver(self):
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

    def test_initialization(self):
        """Test pattern initialization"""
        pattern = InverseKinematicsPattern()
        self.assertIsNotNone(pattern.config)
        self.assertEqual(pattern.config.n_dof, 2)

    def test_solve_2r(self):
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

    def test_solve_3r(self):
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

    def test_multiple_solvers(self):
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

    def test_joint_limits(self):
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

    def test_run_method(self):
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

    def test_trajectory_mode(self):
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

    def test_get_metadata(self):
        """Test metadata retrieval"""
        metadata = InverseKinematicsPattern.get_metadata()

        self.assertEqual(metadata["id"], "inverse_kinematics")
        self.assertEqual(metadata["category"], "EXTENDED")


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2, exit=False)

    # Demo
    logging.basicConfig(level=logging.INFO)
    print("\n" + "=" * 60)
    print("Inverse Kinematics Pattern Demo")
    print("=" * 60)

    for solver in [IKSolver.JACOBIAN_TRANSPOSE, IKSolver.DAMPED_LEAST_SQUARES]:
        print(f"\n--- {solver.value.upper()} ---")
        config = IKConfig(
            robot_type=RobotType.PLANAR_3R,
            solver=solver,
            target_position=np.array([1.5, 1.0]),
            tolerance=1e-5,
        )
        pattern = InverseKinematicsPattern(config)
        result = pattern.solve()

        print(f"Target: {result['target']}")
        print(f"Solution (rad): {[f'{q:.4f}' for q in result['solution']]}")
        print(f"Final Position: {result['final_position']}")
        print(f"Position Error: {result['position_error']:.6f}")
        print(f"Converged: {result['converged']}")
        print(f"Iterations: {result['iterations']}")
