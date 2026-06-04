"""
c4-cdi-turbo v6.0 - Inverse Kinematics Pattern[str]
Jacobian-based IK solvers for robotic manipulators.
"""

from .config import IKConfig, IKSolver, RobotType
from .core import (
    CCDSolver,
    DampedLeastSquaresSolver,
    IKSolverBase,
    InverseKinematicsPattern,
    JacobianNullspaceSolver,
    JacobianPseudoinverseSolver,
    JacobianTransposeSolver,
    RobotKinematics,
)
from .tests import (
    TestIKSolvers,
    TestInverseKinematicsPattern,
    TestRobotKinematics,
)


__all__ = [
    # Enums and Config
    "IKSolver",
    "RobotType",
    "IKConfig",
    # Core Classes
    "RobotKinematics",
    "IKSolverBase",
    "JacobianTransposeSolver",
    "JacobianPseudoinverseSolver",
    "DampedLeastSquaresSolver",
    "JacobianNullspaceSolver",
    "CCDSolver",
    "InverseKinematicsPattern",
    # Tests
    "TestRobotKinematics",
    "TestIKSolvers",
    "TestInverseKinematicsPattern",
]

__version__ = "6.0.0"
