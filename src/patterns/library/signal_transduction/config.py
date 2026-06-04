"""
Signal Transduction Configuration
Configuration dataclass and enums for signaling models
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class SignalingModel(Enum):
    """SignalingModel."""
    MAPK_CASCADE = "mapk_cascade"
    GPCR = "gpcr"
    ADAPTATION = "adaptation"
    REPRESSILATOR = "repressilator"
    TOGGLE_SWITCH = "toggle_switch"

@dataclass
class SignalTransductionConfig:
    """Signal transduction configuration"""
    # Model selection
    model: SignalingModel = SignalingModel.MAPK_CASCADE

    # General parameters
    t_max: float = 1000.0  # seconds
    dt: float = 0.1  # seconds

    # MAPK cascade parameters
    E1_total: float = 0.1  # uM - MAPKKK kinase
    E2_total: float = 0.1  # uM - MAPKKK phosphatase
    MAPKK_total: float = 10.0  # uM
    MAPK_total: float = 10.0  # uM

    # Kinetic constants
    k1: float = 0.01  # 1/(uM*s)
    k2: float = 0.1  # 1/s
    k3: float = 0.01  # 1/(uM*s)
    k4: float = 0.1  # 1/s

    # GPCR parameters
    R_total: float = 1.0  # uM - Receptor
    G_total: float = 1.0  # uM - G-protein
    ligand_conc: float = 0.1  # uM - Stimulus

    # Adaptation parameters
    stimulus_amp: float = 1.0
    stimulus_duration: float = 100.0
    adaptation_rate: float = 0.1

    # Repressilator parameters
    n_genes: int = 3
    alpha: float = 250.0  # Promoter strength
    beta: float = 5.0  # mRNA decay / protein decay ratio
    n_hill: float = 2.0  # Hill coefficient

    # Toggle switch parameters
    gamma: float = 1.0  # Degradation rate
    K: float = 1.0  # Threshold

    # Analysis
    num_stimulus_levels: int = 10

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model.value,
            "t_max": self.t_max,
            "dt": self.dt,
            "E1_total": self.E1_total,
            "E2_total": self.E2_total,
            "MAPKK_total": self.MAPKK_total,
            "MAPK_total": self.MAPK_total,
            "k1": self.k1,
            "k2": self.k2,
            "k3": self.k3,
            "k4": self.k4,
            "R_total": self.R_total,
            "G_total": self.G_total,
            "ligand_conc": self.ligand_conc,
            "stimulus_amp": self.stimulus_amp,
            "stimulus_duration": self.stimulus_duration,
            "adaptation_rate": self.adaptation_rate,
            "n_genes": self.n_genes,
            "alpha": self.alpha,
            "beta": self.beta,
            "n_hill": self.n_hill,
            "gamma": self.gamma,
            "K": self.K,
            "num_stimulus_levels": self.num_stimulus_levels,
        }
