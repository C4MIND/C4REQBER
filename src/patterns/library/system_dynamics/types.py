"""
type[Any] definitions for System Dynamics simulation
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SystemType(Enum):
    """Types of dynamical systems"""
    LINEAR = "linear"
    NONLINEAR = "nonlinear"
    CHAOTIC = "chaotic"
    OSCILLATORY = "oscillatory"
    BISTABLE = "bistable"

@dataclass
class Stock:
    """Stock (state variable) in system dynamics"""
    name: str
    initial_value: float
    min_value: float | None = None
    max_value: float | None = None
    unit: str = ""

@dataclass
class Flow:
    """Flow (rate) in system dynamics"""
    name: str
    source: str | None  # Source stock (None for external)
    sink: str | None    # Sink stock (None for external)
    rate_expression: str   # Mathematical expression

@dataclass
class SystemDynamicsConfig:
    """Configuration for System Dynamics simulation"""
    t_start: float = 0.0
    t_end: float = 100.0
    dt: float = 0.1
    solver: str = "RK45"  # 'RK45', 'RK23', 'DOP853', 'Radau', 'BDF', 'LSODA'
    system_type: str = "nonlinear"

    # Sensitivity analysis
    sensitivity_analysis: bool = True
    parameter_variation: float = 0.1
    n_sensitivity_runs: int = 50

    # Stability analysis
    stability_analysis: bool = True
    find_equilibria: bool = True

    # Chaos detection
    detect_chaos: bool = True
    lyapunov_exponents: bool = False

    # Event detection
    detect_events: bool = True
    threshold_crossings: list[float] | None = None

    random_seed: int | None = None

    def __post_init__(self) -> None:
        if self.threshold_crossings is None:
            self.threshold_crossings = []
