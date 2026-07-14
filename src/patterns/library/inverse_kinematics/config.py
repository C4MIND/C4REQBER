"""
C4REQBER v6.0 - Inverse Kinematics Configuration
Configuration classes and enums for IK solvers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np


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
    joint_limits: np.ndarray | None = None  # [min, max] per joint

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
    target_orientation: np.ndarray | None = None  # For 6-DOF

    # Simulation
    initial_joint_angles: np.ndarray | None = None

    # Multiple targets for trajectory
    trajectory_targets: list[np.ndarray] | None = None

    # Output
    output_interval: int = 1

    def __post_init__(self) -> None:
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
