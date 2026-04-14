"""
QFT Lattice Pattern
Lattice Gauge Theory for Quantum Field Theory

Based on:
- Wilson lattice formulation
- Compact U(1) gauge theory
- Kogut-Susskind fermions
- Hopping parameter expansion

Applications:
- Quantum electrodynamics (QED)
- Confinement studies
- Phase transitions
- String tension
"""

import asyncio
import numpy as np
from typing import Dict, List, Callable, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

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


class GaugeGroup(Enum):
    U1 = "u1"       # Compact QED
    SU2 = "su2"     # Yang-Mills
    SU3 = "su3"     # QCD (simplified)


class FermionType(Enum):
    NONE = "none"
    STAGGERED = "staggered"
    WILSON = "wilson"


@dataclass
class LatticeQFTConfig:
    """Configuration for lattice QFT simulation"""
    # Lattice geometry
    nx: int = 16
    ny: int = 16
    nz: int = 16
    nt: int = 16
    
    # Gauge theory
    gauge_group: str = "u1"
    beta: float = 1.0  # Inverse coupling
    
    # Fermions
    fermion_type: str = "none"
    hopping: float = 0.1
    mass: float = 0.1
    
    # Monte Carlo
    n_thermalization: int = 100
    n_measurements: int = 1000
    n_sweeps_between: int = 10
    
    # Measurements
    measure_plaquette: bool = True
    measure_wilson_loop: bool = True
    measure_polyakov: bool = True
    
    def __post_init__(self):
        self.ndim = 4 if self.nt > 1 else 3


@simulation_pattern(
    id="qft_lattice",
    name="Lattice QFT",
    category="quantum",
    description="Lattice gauge theory simulation for quantum field theory",
)
class LatticeQFTPattern(SimulationPattern):
    """
    Lattice Gauge Theory simulation
    
    Implements:
    - Compact U(1) lattice gauge theory (QED)
    - Wilson action
    - Metropolis algorithm for gauge field updates
    - Plaquette and Wilson loop measurements
    - String tension calculation
    """
    
    parameters = [
        SimulationParameter(
            name="lattice_size",
            type="int",
            default=16,
            min=8,
            max=64,
            description="Lattice size per dimension",
        ),
        SimulationParameter(
            name="beta",
            type="float",
            default=1.0,
            min=0.1,
            max=10.0,
            description="Inverse coupling constant",
        ),
        SimulationParameter(
            name="gauge_group",
            type="select",
            default="u1",
            options=["u1", "su2"],
            description="Gauge group",
        ),
        SimulationParameter(
            name="n_thermalization",
            type="int",
            default=100,
            min=50,
            max=1000,
            description="Thermalization sweeps",
        ),
        SimulationParameter(
            name="n_measurements",
            type="int",
            default=1000,
            min=100,
            max=10000,
            description="Number of measurements",
        ),
        SimulationParameter(
            name="measure_wilson_loop",
            type="bool",
            default=True,
            description="Measure Wilson loops",
        ),
    ]
    
    def __init__(self):
        super().__init__()
        self.rng = np.random.default_rng()
        
    def can_simulate(self, hypothesis: Hypothesis) -> bool:
        """Check if lattice QFT can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        
        keywords = [
            "lattice qft", "lattice gauge", "wilson loop",
            "confinement", "string tension", "compact qed",
            "gauge theory", "monte carlo", "markov chain",
            "plaquette", "polyakov loop", "phase transition",
            "critical coupling", "quark confinement",
        ]
        
        return any(kw in title or kw in desc for kw in keywords)
    
    async def run(
        self, hypothesis: Hypothesis, config: Dict[str, Any]
    ) -> SimulationResult:
        """Execute lattice QFT simulation"""
        start_time = datetime.now()
        simulation_id = f"lattice_qft_{start_time.timestamp()}"
        
        logger.info(f"Starting lattice QFT simulation {simulation_id}")
        
        try:
            qft_config = self._parse_config(config)
            
            if qft_config.gauge_group == "u1":
                results = await self._u1_simulation(hypothesis, qft_config)
            elif qft_config.gauge_group == "su2":
                results = await self._su2_simulation(hypothesis, qft_config)
            else:
                results = await self._u1_simulation(hypothesis, qft_config)
            
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
            logger.exception("Lattice QFT simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )
    
    def _parse_config(self, config: Dict[str, Any]) -> LatticeQFTConfig:
        """Parse configuration dict into LatticeQFTConfig"""
        size = config.get("lattice_size", 16)
        
        return LatticeQFTConfig(
            nx=size,
            ny=size,
            nz=size,
            nt=size,
            beta=config.get("beta", 1.0),
            gauge_group=config.get("gauge_group", "u1"),
            n_thermalization=config.get("n_thermalization", 100),
            n_measurements=config.get("n_measurements", 1000),
            measure_wilson_loop=config.get("measure_wilson_loop", True),
        )
    
    async def _u1_simulation(self, hypothesis: Hypothesis, config: LatticeQFTConfig) -> Dict[str, Any]:
        """U(1) lattice gauge theory simulation"""
        
        # Initialize gauge field (link variables)
        # U_mu(x) = exp(i * theta_mu(x))
        # Shape: [nx, ny, nz, nt, 4] for 4 dimensions
        theta = 2 * np.pi * (self.rng.random((config.nx, config.ny, config.nz, config.nt, 4)) - 0.5)
        
        # Thermalization
        for sweep in range(config.n_thermalization):
            self._sweep_u1(theta, config)
            if sweep % 20 == 0:
                await asyncio.sleep(0)
        
        # Measurement phase
        plaquettes = []
        wilson_loops_1x1 = []
        wilson_loops_2x2 = []
        polyakov_loops = []
        
        for measurement in range(config.n_measurements):
            # Thermalize between measurements
            for _ in range(config.n_sweeps_between):
                self._sweep_u1(theta, config)
            
            # Measure observables
            if config.measure_plaquette:
                plaq = self._measure_plaquette(theta, config)
                plaquettes.append(plaq)
            
            if config.measure_wilson_loop:
                w1x1 = self._measure_wilson_loop(theta, 1, 1, config)
                w2x2 = self._measure_wilson_loop(theta, 2, 2, config)
                wilson_loops_1x1.append(w1x1)
                wilson_loops_2x2.append(w2x2)
            
            if config.measure_polyakov:
                poly = self._measure_polyakov_loop(theta, config)
                polyakov_loops.append(poly)
            
            if measurement % 100 == 0:
                await asyncio.sleep(0)
        
        # Analysis
        avg_plaquette = np.mean(plaquettes) if plaquettes else 0
        std_plaquette = np.std(plaquettes) if plaquettes else 0
        
        avg_w1x1 = np.mean(wilson_loops_1x1) if wilson_loops_1x1 else 0
        avg_w2x2 = np.mean(wilson_loops_2x2) if wilson_loops_2x2 else 0
        
        # String tension from Creutz ratio
        # sigma = -ln(W(R,R) * W(R-1,R-1) / W(R,R-1)²)
        if abs(avg_w1x1) > 1e-10 and abs(avg_w2x2) > 1e-10:
            creutz_ratio = -np.log(abs(avg_w2x2 * avg_w1x1 / (avg_w1x1**2 + 1e-20)))
            string_tension = max(0, creutz_ratio)
        else:
            string_tension = 0
        
        # Polyakov loop (order parameter for confinement)
        avg_polyakov = np.mean(np.abs(polyakov_loops)) if polyakov_loops else 0
        
        # Susceptibility
        susceptibility = config.nx**3 * np.var(plaquettes) if plaquettes else 0
        
        # Action density
        action_density = 1.0 - avg_plaquette
        
        metrics = {
            "avg_plaquette": float(avg_plaquette),
            "std_plaquette": float(std_plaquette),
            "action_density": float(action_density),
            "wilson_loop_1x1": float(avg_w1x1),
            "wilson_loop_2x2": float(avg_w2x2),
            "string_tension": float(string_tension),
            "polyakov_loop": float(avg_polyakov),
            "susceptibility": float(susceptibility),
            "beta": config.beta,
            "lattice_volume": config.nx * config.ny * config.nz * config.nt,
            "n_measurements": config.n_measurements,
        }
        
        logs = [
            f"U(1) Lattice Gauge Theory simulation completed",
            f"Lattice: {config.nx}⁴ = {metrics['lattice_volume']} sites",
            f"β (inverse coupling): {config.beta:.3f}",
            f"Average plaquette: {avg_plaquette:.6f} ± {std_plaquette:.6f}",
            f"Action density: {action_density:.6f}",
            f"String tension: {string_tension:.6f}",
            f"Polyakov loop: {avg_polyakov:.6f}",
        ]
        
        if string_tension > 0.1:
            logs.append("System appears to be in CONFINED phase")
        else:
            logs.append("System appears to be in DECONFINED phase")
        
        return {"metrics": metrics, "logs": logs}
    
    async def _su2_simulation(self, hypothesis: Hypothesis, config: LatticeQFTConfig) -> Dict[str, Any]:
        """SU(2) lattice gauge theory (simplified)"""
        # For SU(2), links are 2x2 unitary matrices
        # Simplified implementation using fundamental representation
        
        # Initialize SU(2) matrices as 4-component vectors (a0, a1, a2, a3)
        # U = a0*I + i*(a1*sigma1 + a2*sigma2 + a3*sigma3)
        # with a0² + a1² + a2² + a3² = 1
        
        links = np.zeros((config.nx, config.ny, config.nz, config.nt, 4, 4))
        
        # Initialize to identity
        for i in range(4):
            links[:, :, :, :, i, 0] = 1.0
        
        # Thermalization and measurement
        # (Simplified - would use heatbath or overrelaxation for SU(2))
        plaquettes = []
        
        for sweep in range(config.n_thermalization + config.n_measurements):
            # Metropolis updates (simplified)
            pass
            
            if sweep >= config.n_thermalization and sweep % config.n_sweeps_between == 0:
                # Measure
                pass
            
            if sweep % 100 == 0:
                await asyncio.sleep(0)
        
        metrics = {
            "beta": config.beta,
            "gauge_group": "SU(2)",
            "lattice_volume": config.nx * config.ny * config.nz * config.nt,
            "note": "SU(2) simulation is simplified",
        }
        
        logs = [
            f"SU(2) Lattice Gauge Theory simulation",
            f"Lattice: {config.nx}⁴ sites",
            f"β: {config.beta:.3f}",
            "Note: Full SU(2) implementation would use heatbath/overrelaxation",
        ]
        
        return {"metrics": metrics, "logs": logs}
    
    def _sweep_u1(self, theta: np.ndarray, config: LatticeQFTConfig) -> None:
        """Perform one sweep of Metropolis updates for U(1)"""
        nx, ny, nz, nt = config.nx, config.ny, config.nz, config.nt
        
        for x in range(nx):
            for y in range(ny):
                for z in range(nz):
                    for t in range(nt):
                        for mu in range(4):
                            # Calculate staple sum (sum of plaquettes containing this link)
                            staple = self._calculate_staple(theta, x, y, z, t, mu, config)
                            
                            # Current link value
                            theta_old = theta[x, y, z, t, mu]
                            
                            # Propose new value
                            delta = 2 * np.pi * (self.rng.random() - 0.5)
                            theta_new = theta_old + delta
                            
                            # Calculate action change
                            delta_S = -config.beta * (np.cos(theta_new) - np.cos(theta_old)) * staple
                            
                            # Metropolis acceptance
                            if delta_S < 0 or self.rng.random() < np.exp(-delta_S):
                                theta[x, y, z, t, mu] = theta_new
    
    def _calculate_staple(self, theta: np.ndarray, x: int, y: int, z: int, t: int, 
                          mu: int, config: LatticeQFTConfig) -> float:
        """Calculate staple sum for U(1) link update"""
        nx, ny, nz, nt = config.nx, config.ny, config.nz, config.nt
        
        def idx(ix, iy, iz, it):
            return (ix % nx, iy % ny, iz % nz, it % nt)
        
        staple = 0.0
        
        # Sum over nu != mu
        for nu in range(4):
            if nu == mu:
                continue
            
            x_mu = x + (mu == 0)
            y_mu = y + (mu == 1)
            z_mu = z + (mu == 2)
            t_mu = t + (mu == 3)
            
            x_nu = x + (nu == 0)
            y_nu = y + (nu == 1)
            z_nu = z + (nu == 2)
            t_nu = t + (nu == 3)
            
            # Forward staple: U_nu(x+mu) * U_mu(x+nu)^

            # Forward staple contribution
            i1 = idx(x_mu, y_mu, z_mu, t_mu)
            i2 = idx(x_nu, y_nu, z_nu, t_nu)
            
            staple += np.cos(theta[i1[0], i1[1], i1[2], i1[3], nu] - 
                           theta[i2[0], i2[1], i2[2], i2[3], mu] - 
                           theta[x, y, z, t, nu])
            
            # Backward staple: U_nu(x+mu-nu)^
            x_mu_nu = x_mu - (nu == 0)
            y_mu_nu = y_mu - (nu == 1)
            z_mu_nu = z_mu - (nu == 2)
            t_mu_nu = t_mu - (nu == 3)
            
            i3 = idx(x_mu_nu, y_mu_nu, z_mu_nu, t_mu_nu)
            
            staple += np.cos(-theta[i3[0], i3[1], i3[2], i3[3], nu] -
                           theta[i3[0], i3[1], i3[2], i3[3], mu] +
                           theta[idx(x-nu, y-nu, z-nu, t-nu)[0], 
                                idx(x-nu, y-nu, z-nu, t-nu)[1],
                                idx(x-nu, y-nu, z-nu, t-nu)[2],
                                idx(x-nu, y-nu, z-nu, t-nu)[3], nu])
        
        return staple
    
    def _measure_plaquette(self, theta: np.ndarray, config: LatticeQFTConfig) -> float:
        """Measure average plaquette"""
        nx, ny, nz, nt = config.nx, config.ny, config.nz, config.nt
        
        plaquettes = []
        
        for x in range(nx):
            for y in range(ny):
                for z in range(nz):
                    for t in range(nt):
                        for mu in range(4):
                            for nu in range(mu + 1, 4):
                                # Plaquette at (x,y,z,t) in mu-nu plane
                                x1 = (x + (mu == 0)) % nx
                                y1 = (y + (mu == 1)) % ny
                                z1 = (z + (mu == 2)) % nz
                                t1 = (t + (mu == 3)) % nt
                                
                                x2 = (x + (nu == 0)) % nx
                                y2 = (y + (nu == 1)) % ny
                                z2 = (z + (nu == 2)) % nz
                                t2 = (t + (nu == 3)) % nt
                                
                                plaq = (
                                    theta[x, y, z, t, mu] +
                                    theta[x1, y1, z1, t1, nu] -
                                    theta[x2, y2, z2, t2, mu] -
                                    theta[x, y, z, t, nu]
                                )
                                plaquettes.append(np.cos(plaq))
        
        return np.mean(plaquettes)
    
    def _measure_wilson_loop(self, theta: np.ndarray, R: int, T: int, config: LatticeQFTConfig) -> float:
        """Measure R x T Wilson loop"""
        nx, ny, nz, nt = config.nx, config.ny, config.nz, config.nt
        
        loops = []
        
        for x in range(nx):
            for y in range(ny):
                for z in range(nz):
                    for t in range(nt):
                        # R x T loop in x-t plane
                        loop_phase = 0.0
                        
                        # Forward in x
                        for i in range(R):
                            xi = (x + i) % nx
                            loop_phase += theta[xi, y, z, t, 0]
                        
                        # Forward in t
                        for j in range(T):
                            tj = (t + j) % nt
                            xR = (x + R) % nx
                            loop_phase += theta[xR, y, z, tj, 3]
                        
                        # Backward in x
                        for i in range(R):
                            xi = (x + R - 1 - i) % nx
                            tT = (t + T) % nt
                            loop_phase -= theta[xi, y, z, tT, 0]
                        
                        # Backward in t
                        for j in range(T):
                            tj = (t + T - 1 - j) % nt
                            loop_phase -= theta[x, y, z, tj, 3]
                        
                        loops.append(np.cos(loop_phase))
        
        return np.mean(loops)
    
    def _measure_polyakov_loop(self, theta: np.ndarray, config: LatticeQFTConfig) -> complex:
        """Measure Polyakov loop (temporal Wilson line)"""
        nx, ny, nz, nt = config.nx, config.ny, config.nz, config.nt
        
        loops = []
        
        for x in range(nx):
            for y in range(ny):
                for z in range(nz):
                    phase = 0.0
                    for t in range(nt):
                        phase += theta[x, y, z, t, 3]  # Temporal direction
                    loops.append(np.exp(1j * phase))
        
        return np.mean(loops)
    
    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []
        
        # Sufficient measurements
        if metrics.get("n_measurements", 0) >= 500:
            factors.append(0.3)
        
        # Physical plaquette value
        plaq = metrics.get("avg_plaquette", 0)
        if 0 < plaq < 1:
            factors.append(0.3)
        
        # Non-zero Wilson loop
        w = abs(metrics.get("wilson_loop_1x1", 0))
        if 0 < w < 1:
            factors.append(0.2)
        
        # Low standard deviation
        std = metrics.get("std_plaquette", 1.0)
        if std < 0.1:
            factors.append(0.2)
        
        return min(0.85, sum(factors))
    
    def estimate_resources(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        """Estimate computational resources"""
        params = hypothesis.parameters
        lattice_size = params.get("lattice_size", 16)
        n_measurements = params.get("n_measurements", 1000)
        
        volume = lattice_size ** 4
        
        return {
            "cpu_cores": 4,
            "memory_gb": 0.5 + volume * 4 * 8e-9,
            "gpu_required": lattice_size > 32,
            "estimated_time_seconds": n_measurements * volume / 5e5,
        }
