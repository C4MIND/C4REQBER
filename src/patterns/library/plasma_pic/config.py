"""
Plasma PIC Pattern[str] Configuration
Configuration classes for Particle-in-Cell simulation.
"""

from dataclasses import dataclass
from enum import Enum


class PICDimension(Enum):
    """PICDimension."""
    ONE_D = "1d"
    TWO_D = "2d"
    THREE_D = "3d"

class ParticlePusher(Enum):
    """ParticlePusher."""
    BORIS = "boris"
    LEAPFROG = "leapfrog"
    RK4 = "rk4"

@dataclass
class Particle:
    """Single plasma particle"""
    x: float
    y: float = 0.0
    z: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0
    weight: float = 1.0  # Macroparticle weight
    charge: float = -1.0  # In units of elementary charge
    mass: float = 1.0     # In units of electron mass

@dataclass
class PICConfig:
    """Configuration for PIC simulation"""
    # Grid
    nx: int = 64
    ny: int = 64
    nz: int = 1
    Lx: float = 1e-3  # Domain size (1 mm)
    Ly: float = 1e-3
    Lz: float = 1e-3

    # Particles
    n_particles: int = 10000
    n_species: int = 2  # electrons and ions

    # Plasma parameters
    n0: float = 1e20  # Background density (m^-3)
    Te: float = 10.0   # Electron temperature (eV)
    Ti: float = 1.0    # Ion temperature (eV)

    # Time stepping
    dt: float = 1e-12  # Time step (1 ps)
    n_steps: int = 1000

    # Algorithm
    pusher: str = "boris"
    deposit_scheme: str = "cic"  # Cloud-in-Cell

    # Physics
    ion_mass_ratio: float = 1836.0  # m_ion / m_e (proton)

    def __post_init__(self) -> None:
        self.dx = self.Lx / self.nx
        self.dy = self.Ly / self.ny
        self.dz = self.Lz / self.nz
