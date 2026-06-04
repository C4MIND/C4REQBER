"""
C4REQBER v6.0 - Inverse Kinematics Core
Jacobian-based IK solvers for robotic manipulators.

Pattern[str] Structure (Christopher Alexander):
- Context: Robotic arm control, animation, biomechanics
- Forces: Accuracy vs computation speed, multiple solutions, singularities
- Solution: Numerical IK with Jacobian pseudo-inverse and redundancy resolution
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import numpy as np

from .config import IKConfig, IKSolver


logger = logging.getLogger(__name__)

class RobotKinematics:
    """Forward and differential kinematics for planar robots"""

    def __init__(self, link_lengths: np.ndarray) -> None:
        self.link_lengths = link_lengths
        self.n_dof = len(link_lengths)

    def forward_kinematics(self, q: np.ndarray) -> tuple[np.ndarray, list[np.ndarray]]:
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

    def __init__(self, kinematics: RobotKinematics, config: IKConfig) -> None:
        self.kinematics = kinematics
        self.config = config

    def solve(
        self, target: np.ndarray, q_init: np.ndarray
    ) -> tuple[np.ndarray, bool, int, list[Any]]:
        """
        Solve IK using Cyclic Coordinate Descent (CCD).
        Returns: (q_solution, converged, iterations, trajectory)
        """
        q = q_init.copy()
        trajectory = [q.copy()]
        n_dof = self.kinematics.n_dof

        for iteration in range(self.config.max_iterations):
            _, joint_positions = self.kinematics.forward_kinematics(q)
            end_effector = joint_positions[-1]

            error = np.linalg.norm(target - end_effector)
            if error < self.config.tolerance:
                return q, True, iteration, trajectory

            for i in range(n_dof - 1, -1, -1):
                joint_pos = joint_positions[i]
                to_target = target - joint_pos
                to_end = end_effector - joint_pos

                cos_angle = np.dot(to_end, to_target) / (
                    np.linalg.norm(to_end) * np.linalg.norm(to_target) + 1e-10
                )
                cos_angle = np.clip(cos_angle, -1.0, 1.0)
                angle = np.arccos(cos_angle)

                cross = np.cross(to_end, to_target)
                if cross < 0:
                    angle = -angle

                assert self.config.joint_limits is not None
                q[i] += self.config.step_size * angle
                q[i] = np.clip(
                    q[i],
                    self.config.joint_limits[i, 0],
                    self.config.joint_limits[i, 1],
                )

                _, joint_positions = self.kinematics.forward_kinematics(q)
                end_effector = joint_positions[-1]

            trajectory.append(q.copy())

        return q, False, self.config.max_iterations, trajectory

class JacobianTransposeSolver(IKSolverBase):
    """Jacobian transpose method"""

    def solve(
        self, target: np.ndarray, q_init: np.ndarray
    ) -> tuple[np.ndarray, bool, int, list[Any]]:
        """Solve."""
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
                q, self.config.joint_limits[:, 0], self.config.joint_limits[:, 1]  # type: ignore[index]
            )

            trajectory.append(q.copy())

        return q, False, self.config.max_iterations, trajectory

class JacobianPseudoinverseSolver(IKSolverBase):
    """Jacobian pseudo-inverse method"""

    def solve(
        self, target: np.ndarray, q_init: np.ndarray
    ) -> tuple[np.ndarray, bool, int, list[Any]]:
        """Solve."""
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
            except np.linalg.LinAlgError:
                # Fallback to transpose if singular
                delta_q = self.config.step_size * J.T @ error

            q += delta_q
            q = np.clip(
                q, self.config.joint_limits[:, 0], self.config.joint_limits[:, 1]  # type: ignore[index]
            )

            trajectory.append(q.copy())

        return q, False, self.config.max_iterations, trajectory

class DampedLeastSquaresSolver(IKSolverBase):
    """Damped Least Squares (Levenberg-Marquardt) method"""

    def solve(
        self, target: np.ndarray, q_init: np.ndarray
    ) -> tuple[np.ndarray, bool, int, list[Any]]:
        """Solve."""
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
            except np.linalg.LinAlgError:
                delta_q = self.config.step_size * J.T @ error

            q += self.config.step_size * delta_q
            q = np.clip(
                q, self.config.joint_limits[:, 0], self.config.joint_limits[:, 1]  # type: ignore[index]
            )

            trajectory.append(q.copy())

        return q, False, self.config.max_iterations, trajectory

class JacobianNullspaceSolver(IKSolverBase):
    """Jacobian pseudo-inverse with nullspace optimization"""

    def solve(
        self,
        target: np.ndarray,
        q_init: np.ndarray,
        secondary_objective: Callable[..., Any] | None = None,
    ) -> tuple[np.ndarray, bool, int, list[Any]]:
        """Solve."""
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
                        self.config.joint_limits[:, 0] + self.config.joint_limits[:, 1]  # type: ignore[index]
                    ) / 2
                    delta_q_secondary = self.config.nullspace_gain * (q_center - q)
                else:
                    delta_q_secondary = secondary_objective(q)

                delta_q = delta_q_primary + I_JpinvJ @ delta_q_secondary

            except np.linalg.LinAlgError:
                delta_q = self.config.step_size * J.T @ error

            q += self.config.step_size * delta_q
            q = np.clip(
                q, self.config.joint_limits[:, 0], self.config.joint_limits[:, 1]  # type: ignore[index]
            )

            trajectory.append(q.copy())

        return q, False, self.config.max_iterations, trajectory

class CCDSolver(IKSolverBase):
    """Cyclic Coordinate Descent solver"""

    def solve(
        self, target: np.ndarray, q_init: np.ndarray
    ) -> tuple[np.ndarray, bool, int, list[Any]]:
        """Solve."""
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
                    q[i], self.config.joint_limits[i, 0], self.config.joint_limits[i, 1]  # type: ignore[index]
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

    def __init__(self, config: IKConfig | None = None) -> None:
        self.config = config or IKConfig()
        self.kinematics = RobotKinematics(self.config.link_lengths)
        self.solver: IKSolverBase | None = None
        self.history: dict[str, list[Any]] = {
            "iteration": [],
            "joint_angles": [],
            "end_effector": [],
            "error": [],
            "converged": [],
        }

    def _initialize_solver(self) -> None:
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

    def solve(self, target: np.ndarray | None = None) -> dict[str, Any]:
        """Solve IK for single target"""
        cfg = self.config

        if target is None:
            target = cfg.target_position

        self._initialize_solver()

        q_solution, converged, iterations, trajectory = self.solver.solve(  # type: ignore[union-attr]
            target, cfg.initial_joint_angles  # type: ignore[arg-type]
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

    def run(self, hypothesis: dict[str, Any] = None) -> dict[str, Any]:  # type: ignore[assignment]
        """Run IK for single target or trajectory"""
        cfg = self.config

        logger.info(f"Starting IK: {cfg.robot_type.value}, solver={cfg.solver.value}")

        if cfg.trajectory_targets is None:
            # Single target
            return self.solve()
        else:
            # Trajectory tracking
            results = []
            q_current = cfg.initial_joint_angles.copy()  # type: ignore[union-attr]

            for _i, target in enumerate(cfg.trajectory_targets):
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
    def get_metadata(cls) -> dict[str, Any]:
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
