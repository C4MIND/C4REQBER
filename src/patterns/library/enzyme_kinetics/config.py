"""
Enzyme Kinetics Pattern[str] Configuration
Configuration classes for enzyme kinetics simulation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class KineticModel(Enum):
    """Available kinetic models"""
    MICHAELIS_MENTEN = "michaelis_menten"
    BRIGGS_HALDANE = "briggs_haldane"
    COMPETITIVE_INHIBITION = "competitive_inhibition"
    HILL = "hill"
    MWC = "mwc"  # Monod-Wyman-Changeux

@dataclass
class EnzymeKineticsConfig:
    """Enzyme kinetics configuration"""
    # Model selection
    model: KineticModel = KineticModel.MICHAELIS_MENTEN

    # Michaelis-Menten parameters
    Vmax: float = 100.0  # Maximum reaction rate (uM/s)
    Km: float = 50.0  # Michaelis constant (uM)

    # Enzyme and substrate
    E0: float = 1.0  # Initial enzyme concentration (uM)
    S0: float = 100.0  # Initial substrate concentration (uM)
    P0: float = 0.0  # Initial product concentration (uM)
    ES0: float = 0.0  # Initial enzyme-substrate complex (uM)

    # Briggs-Haldane individual rate constants
    k1: float = 100.0  # E + S -> ES (1/uM/s)
    k_1: float = 50.0  # ES -> E + S (1/s)
    k2: float = 50.0  # ES -> E + P (1/s)

    # Inhibition
    I0: float = 0.0  # Inhibitor concentration (uM)
    Ki: float = 10.0  # Inhibition constant (uM)

    # Hill equation
    n: float = 1.0  # Hill coefficient
    Kd: float = 50.0  # Dissociation constant

    # MWC parameters
    L: float = 1000.0  # Allosteric constant (T/R ratio)
    c: float = 0.01  # Non-exclusive binding factor

    # Simulation
    t_max: float = 100.0  # seconds
    dt: float = 0.01  # seconds

    # Multiple substrate concentrations for curve
    substrate_range: tuple[float, float] = (1.0, 1000.0)  # (min, max) uM
    num_points: int = 20  # Number of substrate concentrations

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model.value,
            "Vmax": self.Vmax,
            "Km": self.Km,
            "E0": self.E0,
            "S0": self.S0,
            "P0": self.P0,
            "ES0": self.ES0,
            "k1": self.k1,
            "k_1": self.k_1,
            "k2": self.k2,
            "I0": self.I0,
            "Ki": self.Ki,
            "n": self.n,
            "Kd": self.Kd,
            "L": self.L,
            "c": self.c,
            "t_max": self.t_max,
            "dt": self.dt,
            "substrate_range": self.substrate_range,
            "num_points": self.num_points,
        }
