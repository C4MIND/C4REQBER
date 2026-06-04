"""
c4-cdi-turbo v6.0 - Model Predictive Control Pattern[str]
MPC with Quadratic Programming solver for constrained optimal control.

Pattern[str] Structure (Christopher Alexander):
- Context: Multi-variable control with constraints (physical limits, safety)
- Forces: Optimality vs computation time, constraint satisfaction vs performance
- Solution: Receding horizon optimization with QP solver
"""

from .config import MPCConfig
from .core import ModelPredictivePattern
from .solvers import ActiveSetSolver, QPSolverBase
from .types import QPSolver, SystemType


__all__ = [
    "QPSolver",
    "SystemType",
    "MPCConfig",
    "QPSolverBase",
    "ActiveSetSolver",
    "ModelPredictivePattern",
]
