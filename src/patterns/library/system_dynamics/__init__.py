"""
System Dynamics Simulation Pattern[str]
Production-grade differential equation simulation

Based on:
- Jay Forrester's System Dynamics
- Stella/iThink methodology
- Modern ODE solvers (scipy.integrate)
"""

from .core import SystemDynamicsPattern
from .types import Flow, Stock, SystemDynamicsConfig, SystemType


__all__ = [
    "SystemType",
    "Stock",
    "Flow",
    "SystemDynamicsConfig",
    "SystemDynamicsPattern",
]
