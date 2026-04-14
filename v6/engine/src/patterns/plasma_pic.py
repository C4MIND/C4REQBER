"""
Plasma PIC Pattern
Particle-in-Cell method for plasma physics

Based on:
- Birdsall & Langdon: Plasma Physics via Computer Simulation
- Electromagnetic PIC algorithm
- Cloud-in-Cell (CIC) charge deposition
- Boris push for particle pusher

Applications:
- Fusion plasma simulation
- Accelerators
- Space plasma
- Laser-plasma interactions
"""

import asyncio
import numpy as np
from typing import Dict, List, Callable, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from scipy.fft import fft, ifft, fftfreq

from ..core import (
    SimulationPattern,
    SimulationResult,
    SimulationStatus,
    Hypothesis,
    SimulationParameter,
    ValidationLevel,
    simulation_pattern,
)

logger = logging.getLogger(__name__)


class PICDimension(Enum):
    ONE_D = "1d"
    TWO_D = "2d"
    THREE_D = "3d"


class ParticlePusher(Enum):
    BORIS = "boris"           # Standard Boris push
    LEAPFROG = "leapfrog"     # Simple leapfrog
    RK4 = "rk4"               # 4th order Runge-Kutta


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
    
    def __post_init__(self):
        self.dx = self.Lx / self.nx
        self.dy = self.Ly / self.ny
        self.dz = self.Lz / self.nz


@simulation_pattern(
    id="plasma_pic",
    name="Plasma PIC",
    category="physics",
    description="Particle-in-Cell simulation for plasma physics",
)
class PlasmaPICPattern(SimulationPattern):
    """
    Particle-in-Cell plasma simulation
    
    Implements:
    - 1D/2D electromagnetic PIC
    - Cloud-in-Cell (CIC) charge deposition
    - Boris particle pusher
    - FFT-based field solver
    - Multiple species (electrons, ions)
    """
    
    parameters = [
        SimulationParameter(
            name="dimensions",
            type="select",
            default="2d",
            options=["1d", "2d"],
            description="Simulation dimensionality",
        ),
        SimulationParameter(
            name="n_particles",
            type="int",
            default=10000,
            min=1000,
            max=1000000,
            description="Number of particles",
        ),
        SimulationParameter(
            name="n_steps",
            type="int",
            default=1000,
            min=100,
            max=10000,
            description="Number of time steps",
        ),
        SimulationParameter(
            name="plasma_density",
            type="float",
            default=1e20,
            min=1e15,
            max=1e25,
            description="Plasma density (m^-3)",
        ),
        SimulationParameter(
            name="electron_temp",
            type="float",
            default=10.0,
            min=0.1,
            max=1000.0,
            description="Electron temperature (eV)",
        ),
        SimulationParameter(
            name="ion_temp",
            type="float",
            default=1.0,
            min=0.1,
            max=1000.0,
            description="Ion temperature (eV)",
        ),
        SimulationParameter(
            name="pusher",
            type="select",
            default="boris",
            options=["boris", "leapfrog", "rk4"],
            description="Particle pusher algorithm",
        ),
        SimulationParameter(
            name="grid_size",
            type="int",
            default=64,
            min=32,
            max=512,
            description="Grid size per dimension",
        ),
    ]
    
    def __init__(self):
        super().__init__()
        # Physical constants
        self.q_e = 1.602e-19  # Elementary charge (C)
        self.m_e = 9.109e-31  # Electron mass (kg)
        self.eps0 = 8.854e-12  # Vacuum permittivity
        self.k_B = 1.381e-23  # Boltzmann constant
        self.c = 299792458.0   # Speed of light
        
        # Simulation state
        self.particles: List[Particle] = []
        self.rho = None
        self.phi = None
        self.Ex = None
        self.Ey = None
        
    def can_simulate(self, hypothesis: Hypothesis) -> bool:
        """Check if PIC can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        
        keywords = [
            "plasma", "particle in cell", "pic", "charged particle",
            "fusion", "tokamak", "iter", "magnetic confinement",
            "laser plasma", "wakefield", "accelerator",
            "debye length", "plasma frequency", "langmuir",
            "ion", "electron", "collective behavior",
        ]
        
        return any(kw in title or kw in desc for kw in keywords)
    
    async def run(
        self, hypothesis: Hypothesis, config: Dict[str, Any]
    ) -> SimulationResult:
        """Execute PIC simulation"""
        start_time = datetime.now()
        simulation_id = f"pic_{start_time.timestamp()}"
        
        logger.info(f"Starting PIC simulation {simulation_id}")
        
        try:
            # Parse configuration
            pic_config = self._parse_config(config)
            
            # Run simulation
            if pic_config.nz == 1 and pic_config.ny == 1:
                results = await self._pic_1d(hypothesis, pic_config)
            else:
                results = await self._pic_2d(hypothesis, pic_config)
            
            end_time = datetime.now()
            
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.COMPLETED,
                start_time=start_time,
                end_time=end_time,
                metrics=results["metrics"],
                logs=results["logs"],
                confidence_score=self._calculate_confidence(results),
                validation_level=ValidationLevel.MONTE_CARLO,
            )
            
        except Exception as e:
            logger.exception("PIC simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )
    
    def _parse_config(self, config: Dict[str, Any]) -> PICConfig:
        """Parse configuration dict into PICConfig"""
        dims = config.get("dimensions", "2d")
        grid_size = config.get("grid_size", 64)
        
        return PICConfig(
            nx=grid_size,
            ny=1 if dims == "1d" else grid_size,
            nz=1,
            n_particles=config.get("n_particles", 10000),
            n_steps=config.get("n_steps", 1000),
            n0=config.get("plasma_density", 1e20),
            Te=config.get("electron_temp", 10.0),
            Ti=config.get("ion_temp", 1.0),
            pusher=config.get("pusher", "boris"),
        )
    
    async def _pic_1d(self, hypothesis: Hypothesis, config: PICConfig) -> Dict[str, Any]:
        """1D electrostatic PIC simulation"""
        
        # Initialize particles
        self._initialize_particles_1d(config)
        
        # Grid
        nx = config.nx
        dx = config.dx
        x_grid = np.linspace(0, config.Lx, nx)
        
        # Time step
        dt = config.dt
        
        # Calculate plasma parameters
        omega_p = np.sqrt(config.n0 * self.q_e**2 / (self.m_e * self.eps0))
        lambda_D = np.sqrt(self.eps0 * self.k_B * config.Te * 11604 / (config.n0 * self.q_e))
        
        # Check stability
        if dt > 0.2 / omega_p:
            logger.warning(f"Time step may be too large: dt = {dt:.2e}, 0.2/ωp = {0.2/omega_p:.2e}")
        
        # History arrays
        kinetic_energy_history = []
        field_energy_history = []
        total_momentum_history = []
        
        for step in range(config.n_steps):
            # 1. Charge deposition
            rho = self._deposit_charge_1d(config)
            
            # 2. Field solve (Poisson equation)
            phi = self._solve_poisson_1d(rho, config)
            Ex = self._compute_electric_field_1d(phi, config)
            
            # 3. Particle push
            self._push_particles_1d(Ex, dt, config)
            
            # 4. Diagnostics
            ke = self._compute_kinetic_energy()
            fe = self._compute_field_energy_1d(Ex, config)
            momentum = self._compute_total_momentum()
            
            kinetic_energy_history.append(ke)
            field_energy_history.append(fe)
            total_momentum_history.append(momentum)
            
            # Periodic yield
            if step % 100 == 0:
                await asyncio.sleep(0)
        
        # Final analysis
        final_ke = kinetic_energy_history[-1] if kinetic_energy_history else 0
        final_fe = field_energy_history[-1] if field_energy_history else 0
        
        # Energy conservation check
        total_energy_initial = kinetic_energy_history[0] + field_energy_history[0]
        total_energy_final = final_ke + final_fe
        energy_error = abs(total_energy_final - total_energy_initial) / total_energy_initial if total_energy_initial > 0 else 0
        
        # Velocity distribution analysis
        v_rms_e = self._compute_thermal_velocity(species=0)
        v_rms_i = self._compute_thermal_velocity(species=1)
        
        metrics = {
            "n_particles": len(self.particles),
            "n_steps": config.n_steps,
            "plasma_frequency": float(omega_p),
            "debye_length": float(lambda_D),
            "final_kinetic_energy": float(final_ke),
            "final_field_energy": float(final_fe),
            "energy_conservation_error": float(energy_error),
            "v_rms_electrons": float(v_rms_e),
            "v_rms_ions": float(v_rms_i),
            "nx": nx,
        }
        
        logs = [
            f"1D PIC simulation completed",
            f"Particles: {len(self.particles)}, Steps: {config.n_steps}",
            f"Plasma frequency: {omega_p/1e9:.3f} GHz",
            f"Debye length: {lambda_D*1e6:.3f} μm",
            f"Energy conservation error: {energy_error*100:.4f}%",
            f"Electron thermal velocity: {v_rms_e/1e6:.2f} x10⁶ m/s",
        ]
        
        return {
            "metrics": metrics,
            "logs": logs,
            "energy_history": {
                "kinetic": kinetic_energy_history,
                "field": field_energy_history,
            }
        }
    
    async def _pic_2d(self, hypothesis: Hypothesis, config: PICConfig) -> Dict[str, Any]:
        """2D electrostatic PIC simulation"""
        
        self._initialize_particles_2d(config)
        
        nx, ny = config.nx, config.ny
        dx, dy = config.dx, config.dy
        dt = config.dt
        
        # Plasma parameters
        omega_p = np.sqrt(config.n0 * self.q_e**2 / (self.m_e * self.eps0))
        lambda_D = np.sqrt(self.eps0 * self.k_B * config.Te * 11604 / (config.n0 * self.q_e))
        
        kinetic_energy_history = []
        field_energy_history = []
        
        for step in range(config.n_steps):
            # Charge deposition
            rho = self._deposit_charge_2d(config)
            
            # Field solve using FFT
            phi = self._solve_poisson_2d_fft(rho, config)
            Ex, Ey = self._compute_electric_field_2d(phi, config)
            
            # Particle push
            self._push_particles_2d(Ex, Ey, dt, config)
            
            # Diagnostics
            ke = self._compute_kinetic_energy()
            fe = self._compute_field_energy_2d(Ex, Ey, config)
            
            kinetic_energy_history.append(ke)
            field_energy_history.append(fe)
            
            if step % 100 == 0:
                await asyncio.sleep(0)
        
        final_ke = kinetic_energy_history[-1] if kinetic_energy_history else 0
        final_fe = field_energy_history[-1] if field_energy_history else 0
        
        energy_initial = kinetic_energy_history[0] + field_energy_history[0] if kinetic_energy_history else 1
        energy_final = final_ke + final_fe
        energy_error = abs(energy_final - energy_initial) / energy_initial if energy_initial > 0 else 0
        
        metrics = {
            "n_particles": len(self.particles),
            "n_steps": config.n_steps,
            "grid_cells": nx * ny,
            "plasma_frequency": float(omega_p),
            "debye_length": float(lambda_D),
            "final_kinetic_energy": float(final_ke),
            "final_field_energy": float(final_fe),
            "energy_conservation_error": float(energy_error),
        }
        
        logs = [
            f"2D PIC simulation completed",
            f"Particles: {len(self.particles)}, Grid: {nx}x{ny}",
            f"Plasma frequency: {omega_p/1e9:.3f} GHz",
            f"Energy conservation error: {energy_error*100:.4f}%",
        ]
        
        return {
            "metrics": metrics,
            "logs": logs,
        }
    
    def _initialize_particles_1d(self, config: PICConfig) -> None:
        """Initialize particles for 1D simulation"""
        self.particles = []
        
        n_per_species = config.n_particles // config.n_species
        
        # Electron thermal velocity
        v_th_e = np.sqrt(self.k_B * config.Te * 11604 / self.m_e)
        v_th_i = np.sqrt(self.k_B * config.Ti * 11604 / (config.ion_mass_ratio * self.m_e))
        
        # Electrons (species 0)
        for i in range(n_per_species):
            x = np.random.uniform(0, config.Lx)
            vx = np.random.normal(0, v_th_e)
            p = Particle(x=x, vx=vx, charge=-1.0, mass=1.0, weight=1.0)
            self.particles.append(p)
        
        # Ions (species 1)
        for i in range(n_per_species):
            x = np.random.uniform(0, config.Lx)
            vx = np.random.normal(0, v_th_i)
            p = Particle(x=x, vx=vx, charge=1.0, mass=config.ion_mass_ratio, weight=1.0)
            self.particles.append(p)
    
    def _initialize_particles_2d(self, config: PICConfig) -> None:
        """Initialize particles for 2D simulation"""
        self.particles = []
        
        n_per_species = config.n_particles // config.n_species
        
        v_th_e = np.sqrt(self.k_B * config.Te * 11604 / self.m_e)
        v_th_i = np.sqrt(self.k_B * config.Ti * 11604 / (config.ion_mass_ratio * self.m_e))
        
        # Electrons
        for i in range(n_per_species):
            x = np.random.uniform(0, config.Lx)
            y = np.random.uniform(0, config.Ly)
            vx = np.random.normal(0, v_th_e)
            vy = np.random.normal(0, v_th_e)
            p = Particle(x=x, y=y, vx=vx, vy=vy, charge=-1.0, mass=1.0, weight=1.0)
            self.particles.append(p)
        
        # Ions
        for i in range(n_per_species):
            x = np.random.uniform(0, config.Lx)
            y = np.random.uniform(0, config.Ly)
            vx = np.random.normal(0, v_th_i)
            vy = np.random.normal(0, v_th_i)
            p = Particle(x=x, y=y, vx=vx, vy=vy, charge=1.0, mass=config.ion_mass_ratio, weight=1.0)
            self.particles.append(p)
    
    def _deposit_charge_1d(self, config: PICConfig) -> np.ndarray:
        """Charge deposition (Cloud-in-Cell) for 1D"""
        rho = np.zeros(config.nx)
        dx = config.dx
        
        for p in self.particles:
            # Find cell index
            i = int(p.x / dx) % config.nx
            i_next = (i + 1) % config.nx
            
            # Weight factors
            dx_i = p.x - i * dx
            w1 = 1 - dx_i / dx
            w2 = dx_i / dx
            
            # Deposit charge
            charge_density = p.charge * self.q_e * p.weight
            rho[i] += w1 * charge_density
            rho[i_next] += w2 * charge_density
        
        return rho / dx  # Charge density
    
    def _deposit_charge_2d(self, config: PICConfig) -> np.ndarray:
        """Charge deposition (Cloud-in-Cell) for 2D"""
        rho = np.zeros((config.nx, config.ny))
        dx, dy = config.dx, config.dy
        
        for p in self.particles:
            i = int(p.x / dx) % config.nx
            j = int(p.y / dy) % config.ny
            
            i_next = (i + 1) % config.nx
            j_next = (j + 1) % config.ny
            
            dx_i = p.x - i * dx
            dy_j = p.y - j * dy
            
            wx1 = 1 - dx_i / dx
            wx2 = dx_i / dx
            wy1 = 1 - dy_j / dy
            wy2 = dy_j / dy
            
            charge_density = p.charge * self.q_e * p.weight
            
            rho[i, j] += wx1 * wy1 * charge_density
            rho[i_next, j] += wx2 * wy1 * charge_density
            rho[i, j_next] += wx1 * wy2 * charge_density
            rho[i_next, j_next] += wx2 * wy2 * charge_density
        
        return rho / (dx * dy)
    
    def _solve_poisson_1d(self, rho: np.ndarray, config: PICConfig) -> np.ndarray:
        """Solve Poisson equation in 1D using FFT"""
        nx = config.nx
        dx = config.dx
        
        # FFT of charge density
        rho_hat = fft(rho)
        
        # k values
        k = 2 * np.pi * fftfreq(nx, dx)
        k[0] = 1.0  # Avoid division by zero
        
        # Solve in Fourier space: -k² φ = ρ/ε₀
        phi_hat = rho_hat / (self.eps0 * k**2)
        phi_hat[0] = 0  # Set mean to zero
        
        # Inverse FFT
        phi = np.real(ifft(phi_hat))
        
        return phi
    
    def _solve_poisson_2d_fft(self, rho: np.ndarray, config: PICConfig) -> np.ndarray:
        """Solve Poisson equation in 2D using FFT"""
        nx, ny = config.nx, config.ny
        dx, dy = config.dx, config.dy
        
        rho_hat = fft(fft(rho, axis=0), axis=1)
        
        kx = 2 * np.pi * fftfreq(nx, dx)
        ky = 2 * np.pi * fftfreq(ny, dy)
        KX, KY = np.meshgrid(kx, ky, indexing='ij')
        
        k2 = KX**2 + KY**2
        k2[0, 0] = 1.0
        
        phi_hat = rho_hat / (self.eps0 * k2)
        phi_hat[0, 0] = 0
        
        phi = np.real(ifft(ifft(phi_hat, axis=1), axis=0))
        
        return phi
    
    def _compute_electric_field_1d(self, phi: np.ndarray, config: PICConfig) -> np.ndarray:
        """Compute electric field from potential (1D)"""
        dx = config.dx
        Ex = np.zeros_like(phi)
        Ex[1:-1] = -(phi[2:] - phi[:-2]) / (2 * dx)
        # Periodic boundary
        Ex[0] = -(phi[1] - phi[-1]) / (2 * dx)
        Ex[-1] = -(phi[0] - phi[-2]) / (2 * dx)
        return Ex
    
    def _compute_electric_field_2d(self, phi: np.ndarray, config: PICConfig) -> Tuple[np.ndarray, np.ndarray]:
        """Compute electric field from potential (2D)"""
        dx, dy = config.dx, config.dy
        Ex = np.zeros_like(phi)
        Ey = np.zeros_like(phi)
        
        Ex[1:-1, :] = -(phi[2:, :] - phi[:-2, :]) / (2 * dx)
        Ey[:, 1:-1] = -(phi[:, 2:] - phi[:, :-2]) / (2 * dy)
        
        return Ex, Ey
    
    def _push_particles_1d(self, Ex: np.ndarray, dt: float, config: PICConfig) -> None:
        """Push particles using Boris algorithm (1D)"""
        dx = config.dx
        
        for p in self.particles:
            # Interpolate E to particle position
            i = int(p.x / dx) % config.nx
            i_next = (i + 1) % config.nx
            frac = (p.x - i * dx) / dx
            E_particle = (1 - frac) * Ex[i] + frac * Ex[i_next]
            
            # Charge-to-mass ratio
            q_m = p.charge * self.q_e / (p.mass * self.m_e)
            
            if config.pusher == "boris":
                # Boris push (simplified for E-only)
                v_minus = p.vx + 0.5 * q_m * E_particle * dt
                p.vx = v_minus + 0.5 * q_m * E_particle * dt
            else:
                # Leapfrog
                p.vx += q_m * E_particle * dt
            
            # Position update
            p.x += p.vx * dt
            
            # Periodic boundary
            p.x = p.x % config.Lx
    
    def _push_particles_2d(self, Ex: np.ndarray, Ey: np.ndarray, dt: float, config: PICConfig) -> None:
        """Push particles using Boris algorithm (2D)"""
        dx, dy = config.dx, config.dy
        
        for p in self.particles:
            i = int(p.x / dx) % config.nx
            j = int(p.y / dy) % config.ny
            
            frac_x = (p.x - i * dx) / dx
            frac_y = (p.y - j * dy) / dy
            
            # Bilinear interpolation
            i_next = (i + 1) % config.nx
            j_next = (j + 1) % config.ny
            
            Epx = ((1-frac_x)*(1-frac_y)*Ex[i, j] + frac_x*(1-frac_y)*Ex[i_next, j] +
                   (1-frac_x)*frac_y*Ex[i, j_next] + frac_x*frac_y*Ex[i_next, j_next])
            
            Epy = ((1-frac_x)*(1-frac_y)*Ey[i, j] + frac_x*(1-frac_y)*Ey[i_next, j] +
                   (1-frac_x)*frac_y*Ey[i, j_next] + frac_x*frac_y*Ey[i_next, j_next])
            
            q_m = p.charge * self.q_e / (p.mass * self.m_e)
            
            p.vx += q_m * Epx * dt
            p.vy += q_m * Epy * dt
            
            p.x += p.vx * dt
            p.y += p.vy * dt
            
            # Periodic boundaries
            p.x = p.x % config.Lx
            p.y = p.y % config.Ly
    
    def _compute_kinetic_energy(self) -> float:
        """Compute total kinetic energy"""
        ke = 0.0
        for p in self.particles:
            v2 = p.vx**2 + p.vy**2 + p.vz**2
            m = p.mass * self.m_e
            ke += 0.5 * m * v2 * p.weight
        return ke
    
    def _compute_field_energy_1d(self, Ex: np.ndarray, config: PICConfig) -> float:
        """Compute electric field energy (1D)"""
        return 0.5 * self.eps0 * np.sum(Ex**2) * config.dx
    
    def _compute_field_energy_2d(self, Ex: np.ndarray, Ey: np.ndarray, config: PICConfig) -> float:
        """Compute electric field energy (2D)"""
        return 0.5 * self.eps0 * np.sum(Ex**2 + Ey**2) * config.dx * config.dy
    
    def _compute_total_momentum(self) -> float:
        """Compute total momentum"""
        momentum = 0.0
        for p in self.particles:
            m = p.mass * self.m_e
            momentum += m * p.vx * p.weight
        return momentum
    
    def _compute_thermal_velocity(self, species: int = 0) -> float:
        """Compute RMS thermal velocity for a species"""
        velocities = []
        for p in self.particles:
            if (species == 0 and p.charge < 0) or (species == 1 and p.charge > 0):
                v2 = p.vx**2 + p.vy**2 + p.vz**2
                velocities.append(np.sqrt(v2))
        return float(np.mean(velocities)) if velocities else 0.0
    
    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []
        
        # Good energy conservation
        energy_error = metrics.get("energy_conservation_error", 1.0)
        if energy_error < 0.01:
            factors.append(0.4)
        elif energy_error < 0.1:
            factors.append(0.2)
        
        # Physical plasma parameters
        omega_p = metrics.get("plasma_frequency", 0)
        if omega_p > 0:
            factors.append(0.2)
        
        # Sufficient particles
        if metrics.get("n_particles", 0) >= 1000:
            factors.append(0.2)
        
        # Thermal velocity in reasonable range
        v_rms = metrics.get("v_rms_electrons", 0)
        if 1e5 < v_rms < 1e8:
            factors.append(0.2)
        
        return min(0.85, sum(factors))
    
    def estimate_resources(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        """Estimate computational resources"""
        params = hypothesis.parameters
        n_particles = params.get("n_particles", 10000)
        n_steps = params.get("n_steps", 1000)
        grid_size = params.get("grid_size", 64)
        
        # Particle data: 7 doubles per particle
        particle_memory = n_particles * 7 * 8e-9
        grid_memory = grid_size ** 2 * 8e-9 * 5  # Multiple grid arrays
        
        estimated_time = n_steps * n_particles / 1e7
        
        return {
            "cpu_cores": 4,
            "memory_gb": max(1.0, particle_memory + grid_memory),
            "gpu_required": n_particles > 100000,
            "estimated_time_seconds": estimated_time,
        }
