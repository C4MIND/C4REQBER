"""Type definitions and enums for Model Predictive Control."""

from enum import Enum


class QPSolver(Enum):
    """Available QP solvers"""

    OSQP = "osqp"  # Operator Splitting QP (if available)
    ECOS = "ecos"  # Embedded Conic Solver (if available)
    ACTIVE_SET = "active_set"  # Custom active set[Any] method
    INTERIOR_POINT = "interior_point"  # Custom interior point method
    SQP = "sqp"  # Sequential Quadratic Programming

class SystemType(Enum):
    """Predefined system types"""

    DOUBLE_INTEGRATOR = "double_integrator"
    INVERTED_PENDULUM = "inverted_pendulum"
    MIMO_SYSTEM = "mimo_system"
    QUADROTOR = "quadrotor"
    CUSTOM = "custom"
