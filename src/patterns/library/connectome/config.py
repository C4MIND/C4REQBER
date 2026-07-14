"""
Connectome Pattern[str] Configuration
Configuration classes for connectome simulation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class NetworkModel(Enum):
    """Available network dynamics models"""
    KURAMOTO = "kuramoto"
    WILSON_COWAN = "wilson_cowan"
    HOPF = "hopf"
    FITZHUGH_NAGUMO = "fitzhugh_nagumo"

@dataclass
class ConnectomeConfig:
    """Connectome simulation configuration"""
    # Network
    num_regions: int = 68  # Number of brain regions (Desikan-Killiany atlas)
    connection_density: float = 0.3  # Structural connectivity density

    # Model parameters
    model: NetworkModel = NetworkModel.KURAMOTO
    coupling_strength: float = 0.5  # Global coupling
    noise_level: float = 0.01  # Intrinsic noise

    # Kuramoto parameters
    omega_mean: float = 40.0  # Mean intrinsic frequency (Hz)
    omega_std: float = 5.0  # Frequency diversity

    # Wilson-Cowan parameters
    tau_exc: float = 0.01  # Excitatory time constant (s)
    tau_inh: float = 0.02  # Inhibitory time constant (s)

    # Hopf parameters
    a: float = 0.0  # Bifurcation parameter

    # Simulation
    # t_max=30s keeps the full sim (68 regions, dt=1ms) at ~29s wall-clock,
    # comfortably under the pipeline's simulation_timeout_seconds=60 budget
    # (t_max=60 measured ~71s and would be killed). 20s of post-transient
    # signal is ample for Kuramoto synchronization metrics.
    t_max: float = 30.0  # seconds
    dt: float = 0.001  # seconds (1 ms)
    transient: float = 10.0  # Discard initial transient (s)

    # Analysis
    fmin: float = 0.01  # Min frequency for FC (Hz)
    fmax: float = 0.1  # Max frequency for FC (Hz)

    # Modulation
    stimulation_site: int | None = None  # Stimulated region
    stimulation_amp: float = 0.0  # Stimulation amplitude
    stimulation_freq: float = 10.0  # Stimulation frequency (Hz)

    def to_dict(self) -> dict[str, Any]:
        return {
            "num_regions": self.num_regions,
            "connection_density": self.connection_density,
            "model": self.model.value,
            "coupling_strength": self.coupling_strength,
            "noise_level": self.noise_level,
            "omega_mean": self.omega_mean,
            "omega_std": self.omega_std,
            "tau_exc": self.tau_exc,
            "tau_inh": self.tau_inh,
            "a": self.a,
            "t_max": self.t_max,
            "dt": self.dt,
            "transient": self.transient,
            "fmin": self.fmin,
            "fmax": self.fmax,
            "stimulation_site": self.stimulation_site,
            "stimulation_amp": self.stimulation_amp,
            "stimulation_freq": self.stimulation_freq,
        }
