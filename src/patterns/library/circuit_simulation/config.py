"""
Circuit Simulation Pattern[str] Configuration
Configuration and data classes for circuit simulation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class ComponentType(Enum):
    """Types of circuit components"""
    RESISTOR = auto()
    CAPACITOR = auto()
    INDUCTOR = auto()
    VOLTAGE_SOURCE = auto()
    CURRENT_SOURCE = auto()
    DIODE = auto()
    TRANSISTOR_NPN = auto()
    TRANSISTOR_PNP = auto()
    MOSFET = auto()
    OPAMP = auto()

class AnalysisType(Enum):
    """Types of circuit analyses"""
    DC = "dc"
    AC = "ac"
    TRANSIENT = "transient"
    OP = "operating_point"
    NOISE = "noise"
    DISTORTION = "distortion"
    SENSITIVITY = "sensitivity"

@dataclass
class Component:
    """Circuit component"""
    name: str
    component_type: ComponentType
    nodes: list[str]
    value: float
    parameters: dict[str, Any] = field(default_factory=dict[str, Any])
    model: str | None = None

@dataclass
class CircuitConfig:
    """Configuration for circuit simulation"""
    analysis_type: AnalysisType = AnalysisType.TRANSIENT

    # Transient analysis parameters
    t_start: float = 0.0
    t_stop: float = 1e-3
    t_step: float = 1e-6

    # AC analysis parameters
    f_start: float = 1.0
    f_stop: float = 1e6
    n_points: int = 100

    # DC analysis parameters
    v_start: float = 0.0
    v_stop: float = 5.0
    v_step: float = 0.1
    source_name: str = "V1"

    # Convergence
    reltol: float = 1e-3
    abstol: float = 1e-12
    max_iter: int = 100

    # Temperature
    temperature: float = 27.0  # Celsius

    # Monte Carlo
    monte_carlo_runs: int = 0
    tolerance: float = 0.05  # 5% component tolerance

    # Optimization
    optimize: bool = False
    target_metric: str = "power"
    target_value: float = 0.0

    random_seed: int | None = None
