"""
Connectome Pattern
Brain network dynamics on structural connectivity

Based on:
- Hagmann et al. (2008) - Structural core of human cerebral cortex
- Honey et al. (2009) - Predicting human resting-state functional connectivity
- Deco et al. (2013) - RSNs emerge from collective dynamics
- Breakspear et al. - Dynamic models of large-scale brain activity
"""

import asyncio
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
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


class NetworkModel(Enum):
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
    t_max: float = 60.0  # seconds
    dt: float = 0.001  # seconds (1 ms)
    transient: float = 10.0  # Discard initial transient (s)
    
    # Analysis
    fmin: float = 0.01  # Min frequency for FC (Hz)
    fmax: float = 0.1  # Max frequency for FC (Hz)
    
    # Modulation
    stimulation_site: Optional[int] = None  # Stimulated region
    stimulation_amp: float = 0.0  # Stimulation amplitude
    stimulation_freq: float = 10.0  # Stimulation frequency (Hz)
    
    def to_dict(self) -> Dict[str, Any]:
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


@simulation_pattern(
    id="connectome",
    name="Connectome Network Dynamics",
    category="neuroscience",
    description="Large-scale brain network dynamics on structural connectivity",
)
class ConnectomePattern(SimulationPattern):
    """
    Whole-brain connectome dynamics simulation
    
    Simulates neural activity across the brain's structural connectivity
    network to study resting-state networks, functional connectivity,
    and network dynamics.
    
    Models supported:
    1. Kuramoto: Phase oscillator model for synchronization
    2. Wilson-Cowan: Firing rate model with excitation/inhibition
    3. Hopf: Normal form of supercritical Hopf bifurcation
    4. FitzHugh-Nagumo: Simplified action potential model
    
    Applications:
    - Resting-state fMRI simulation
    - Functional connectivity analysis
    - Network perturbation/stimulation
    - Disease modeling (AD, Parkinson's)
    """
    
    parameters = [
        SimulationParameter(
            name="num_regions",
            type="int",
            default=68,
            min=10,
            max=1000,
            description="Number of brain regions (nodes)",
        ),
        SimulationParameter(
            name="model",
            type="select",
            default="kuramoto",
            options=["kuramoto", "wilson_cowan", "hopf", "fitzhugh_nagumo"],
            description="Network dynamics model",
        ),
        SimulationParameter(
            name="coupling_strength",
            type="float",
            default=0.5,
            min=0.0,
            max=2.0,
            description="Global coupling strength",
        ),
        SimulationParameter(
            name="noise_level",
            type="float",
            default=0.01,
            min=0.0,
            max=1.0,
            description="Intrinsic noise amplitude",
        ),
        SimulationParameter(
            name="omega_mean",
            type="float",
            default=40.0,
            min=1.0,
            max=100.0,
            description="Mean intrinsic frequency (Hz)",
        ),
        SimulationParameter(
            name="t_max",
            type="float",
            default=60.0,
            min=10.0,
            max=600.0,
            description="Simulation duration (seconds)",
        ),
        SimulationParameter(
            name="stimulation_site",
            type="int",
            default=-1,
            min=-1,
            max=999,
            description="Stimulated region (-1 for none)",
        ),
        SimulationParameter(
            name="stimulation_amp",
            type="float",
            default=0.0,
            min=0.0,
            max=10.0,
            description="Stimulation amplitude",
        ),
    ]
    
    def __init__(self):
        super().__init__()
        self.config: ConnectomeConfig = ConnectomeConfig()
        self.rng = np.random.default_rng(seed=42)
        self.structural_connectivity: Optional[np.ndarray] = None
        
    def can_simulate(self, hypothesis: Hypothesis) -> bool:
        """Check if connectome can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        
        keywords = [
            "connectome", "connectivity", "network", "brain", "rsn",
            "resting state", "functional connectivity", "structural connectivity",
            "fmri", "meg", "eeg", "synchronization", "kuramoto",
            "graph", "node", "edge", "community", "module",
            "stimulation", "tms", "tdcs", "perturbation",
        ]
        
        return any(kw in title or kw in desc for kw in keywords)
    
    async def run(
        self, hypothesis: Hypothesis, config: Dict[str, Any]
    ) -> SimulationResult:
        """Execute connectome simulation"""
        start_time = datetime.now()
        simulation_id = f"conn_{start_time.timestamp()}"
        
        logger.info(f"Starting connectome simulation {simulation_id}")
        
        try:
            # Parse configuration
            self.config = self._parse_config(config)
            
            # Generate structural connectivity
            self.structural_connectivity = self._generate_connectivity()
            
            # Run simulation based on model type
            if self.config.model == NetworkModel.KURAMOTO:
                results = await self._kuramoto_simulation()
            elif self.config.model == NetworkModel.WILSON_COWAN:
                results = await self._wilson_cowan_simulation()
            elif self.config.model == NetworkModel.HOPF:
                results = await self._hopf_simulation()
            else:
                results = await self._fitzhugh_nagumo_simulation()
            
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
            logger.exception("Connectome simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )
    
    def _parse_config(self, config: Dict[str, Any]) -> ConnectomeConfig:
        """Parse configuration dictionary"""
        cfg = ConnectomeConfig()
        
        if "num_regions" in config:
            cfg.num_regions = int(config["num_regions"])
        if "connection_density" in config:
            cfg.connection_density = float(config["connection_density"])
        if "model" in config:
            cfg.model = NetworkModel(config["model"])
        if "coupling_strength" in config:
            cfg.coupling_strength = float(config["coupling_strength"])
        if "noise_level" in config:
            cfg.noise_level = float(config["noise_level"])
        if "omega_mean" in config:
            cfg.omega_mean = float(config["omega_mean"])
        if "omega_std" in config:
            cfg.omega_std = float(config["omega_std"])
        if "tau_exc" in config:
            cfg.tau_exc = float(config["tau_exc"])
        if "tau_inh" in config:
            cfg.tau_inh = float(config["tau_inh"])
        if "a" in config:
            cfg.a = float(config["a"])
        if "t_max" in config:
            cfg.t_max = float(config["t_max"])
        if "dt" in config:
            cfg.dt = float(config["dt"])
        if "transient" in config:
            cfg.transient = float(config["transient"])
        if "fmin" in config:
            cfg.fmin = float(config["fmin"])
        if "fmax" in config:
            cfg.fmax = float(config["fmax"])
        if "stimulation_site" in config:
            site = config["stimulation_site"]
            cfg.stimulation_site = int(site) if site >= 0 else None
        if "stimulation_amp" in config:
            cfg.stimulation_amp = float(config["stimulation_amp"])
        if "stimulation_freq" in config:
            cfg.stimulation_freq = float(config["stimulation_freq"])
            
        return cfg
    
    def _generate_connectivity(self) -> np.ndarray:
        """Generate synthetic structural connectivity matrix"""
        cfg = self.config
        N = cfg.num_regions
        
        # Generate random connectivity with realistic properties
        # Real brain networks are sparse, modular, and have heavy-tailed degree distribution
        
        # Base connectivity (sparse random)
        SC = self.rng.random((N, N))
        SC = (SC < cfg.connection_density).astype(float)
        
        # Remove self-connections
        np.fill_diagonal(SC, 0)
        
        # Make symmetric (undirected)
        SC = (SC + SC.T) / 2
        SC = (SC > 0).astype(float)
        
        # Add weights (log-normal distribution)
        weights = np.exp(self.rng.normal(0, 1, (N, N)))
        SC = SC * weights
        
        # Normalize rows
        row_sums = SC.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1
        SC = SC / row_sums
        
        return SC
    
    async def _kuramoto_simulation(self) -> Dict[str, Any]:
        """Kuramoto oscillator model on connectome"""
        
        cfg = self.config
        N = cfg.num_regions
        SC = self.structural_connectivity
        
        # Initialize phases
        theta = self.rng.uniform(0, 2*np.pi, N)
        
        # Intrinsic frequencies
        omega = self.rng.normal(cfg.omega_mean * 2 * np.pi, cfg.omega_std * 2 * np.pi, N)
        
        # Time arrays
        t_max = cfg.t_max
        dt = cfg.dt
        n_steps = int(t_max / dt)
        transient_steps = int(cfg.transient / dt)
        
        # Store activity
        theta_history = []
        
        # Simulation
        for step in range(n_steps):
            t = step * dt
            
            # Stimulation
            stim = 0.0
            if cfg.stimulation_site is not None and cfg.stimulation_amp > 0:
                stim = cfg.stimulation_amp * np.sin(2 * np.pi * cfg.stimulation_freq * t)
            
            # Phase differences
            phase_diff = theta[:, None] - theta[None, :]
            
            # Kuramoto dynamics
            dtheta = omega + cfg.coupling_strength * (SC * np.sin(phase_diff)).sum(axis=1)
            
            # Add noise
            dtheta += self.rng.normal(0, cfg.noise_level, N)
            
            # Stimulation
            if cfg.stimulation_site is not None:
                dtheta[cfg.stimulation_site] += stim
            
            # Update
            theta += dtheta * dt
            theta = np.mod(theta, 2 * np.pi)
            
            # Store after transient
            if step >= transient_steps:
                theta_history.append(theta.copy())
            
            if step % 1000 == 0:
                await asyncio.sleep(0)
        
        # Convert to array
        theta_arr = np.array(theta_history)
        
        # Calculate functional connectivity (phase synchronization)
        fc = self._calculate_fc_kuramoto(theta_arr)
        
        # Calculate order parameters
        order_global, order_local = self._calculate_order_parameters(theta_arr, SC)
        
        # Calculate metrics
        metrics = self._calculate_network_metrics(theta_arr, fc, SC, order_global, order_local)
        
        logs = [
            f"Kuramoto connectome simulation completed",
            f"Network: {N} regions, {np.sum(SC > 0)//2} connections",
            f"Global order parameter: {np.mean(order_global):.4f}",
            f"Mean FC correlation: {metrics['fc_mean']:.4f}",
            f"FC variance: {metrics['fc_variance']:.4f}",
        ]
        
        return {
            "metrics": metrics,
            "logs": logs,
            "functional_connectivity": fc.tolist(),
            "structural_connectivity": SC.tolist(),
            "order_global": order_global.tolist(),
        }
    
    def _calculate_fc_kuramoto(self, theta: np.ndarray) -> np.ndarray:
        """Calculate functional connectivity from phase time series"""
        N = theta.shape[1]
        fc = np.zeros((N, N))
        
        # Phase locking value (PLV)
        for i in range(N):
            for j in range(i+1, N):
                phase_diff = theta[:, i] - theta[:, j]
                plv = np.abs(np.mean(np.exp(1j * phase_diff)))
                fc[i, j] = plv
                fc[j, i] = plv
        
        return fc
    
    def _calculate_order_parameters(
        self, theta: np.ndarray, SC: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate global and local order parameters"""
        
        N = theta.shape[1]
        
        # Global order parameter
        r_global = np.abs(np.mean(np.exp(1j * theta), axis=1))
        
        # Local order parameter (neighbors)
        r_local = np.zeros(len(theta))
        for t in range(len(theta)):
            for i in range(N):
                neighbors = SC[i] > 0
                if np.sum(neighbors) > 0:
                    r_local[t] += np.abs(np.mean(np.exp(1j * theta[t, neighbors])))
            r_local[t] /= N
        
        return r_global, r_local
    
    async def _wilson_cowan_simulation(self) -> Dict[str, Any]:
        """Wilson-Cowan firing rate model"""
        
        cfg = self.config
        N = cfg.num_regions
        SC = self.structural_connectivity
        
        # Initialize
        E = self.rng.uniform(0, 0.1, N)  # Excitatory activity
        I = self.rng.uniform(0, 0.1, N)  # Inhibitory activity
        
        n_steps = int(cfg.t_max / cfg.dt)
        transient_steps = int(cfg.transient / cfg.dt)
        
        E_history = []
        
        for step in range(n_steps):
            # Wilson-Cowan equations with connectivity
            # dE/dt = -E + S(c1*E - c2*I + coupling + P)
            # dI/dt = -I + S(c3*E - c4*I + Q)
            
            # Coupling term
            coupling = cfg.coupling_strength * (SC @ E)
            
            # Sigmoid
            S_E = 1 / (1 + np.exp(-(E - I + coupling - 4)))
            S_I = 1 / (1 + np.exp(-(E - I - 2)))
            
            # Update
            dE = (-E + S_E) / cfg.tau_exc * cfg.dt
            dI = (-I + S_I) / cfg.tau_inh * cfg.dt
            
            E += dE
            I += dI
            
            # Add noise
            E += self.rng.normal(0, cfg.noise_level, N)
            I += self.rng.normal(0, cfg.noise_level, N)
            
            E = np.clip(E, 0, 1)
            I = np.clip(I, 0, 1)
            
            if step >= transient_steps:
                E_history.append(E.copy())
            
            if step % 1000 == 0:
                await asyncio.sleep(0)
        
        E_arr = np.array(E_history)
        
        # FC as correlation
        fc = np.corrcoef(E_arr.T)
        
        metrics = {
            "mean_activity": float(np.mean(E_arr)),
            "fc_mean": float(np.mean(fc[np.triu_indices_from(fc, k=1)])),
            "fc_variance": float(np.var(fc[np.triu_indices_from(fc, k=1)])),
            "model": "wilson_cowan",
        }
        
        logs = [
            f"Wilson-Cowan connectome simulation completed",
            f"Mean activity: {metrics['mean_activity']:.4f}",
        ]
        
        return {
            "metrics": metrics,
            "logs": logs,
            "functional_connectivity": fc.tolist(),
        }
    
    async def _hopf_simulation(self) -> Dict[str, Any]:
        """Hopf bifurcation model"""
        
        cfg = self.config
        N = cfg.num_regions
        SC = self.structural_connectivity
        
        # Complex state variables
        z = self.rng.normal(0, 0.1, N) + 1j * self.rng.normal(0, 0.1, N)
        
        n_steps = int(cfg.t_max / cfg.dt)
        transient_steps = int(cfg.transient / cfg.dt)
        
        z_history = []
        
        for step in range(n_steps):
            # Hopf normal form with coupling
            # dz/dt = (a + i*omega)*z - |z|^2*z + coupling
            
            omega = cfg.omega_mean * 2 * np.pi
            coupling = cfg.coupling_strength * (SC @ z)
            noise = self.rng.normal(0, cfg.noise_level, N) + 1j * self.rng.normal(0, cfg.noise_level, N)
            
            dz = (cfg.a + 1j * omega) * z - np.abs(z)**2 * z + coupling + noise
            z += dz * cfg.dt
            
            if step >= transient_steps:
                z_history.append(z.copy())
            
            if step % 1000 == 0:
                await asyncio.sleep(0)
        
        z_arr = np.array(z_history)
        x_arr = np.real(z_arr)
        
        fc = np.corrcoef(x_arr.T)
        
        metrics = {
            "mean_amplitude": float(np.mean(np.abs(z_arr))),
            "fc_mean": float(np.mean(fc[np.triu_indices_from(fc, k=1)])),
            "model": "hopf",
        }
        
        logs = [
            f"Hopf connectome simulation completed",
            f"Mean amplitude: {metrics['mean_amplitude']:.4f}",
        ]
        
        return {
            "metrics": metrics,
            "logs": logs,
            "functional_connectivity": fc.tolist(),
        }
    
    async def _fitzhugh_nagumo_simulation(self) -> Dict[str, Any]:
        """FitzHugh-Nagumo model on network"""
        
        cfg = self.config
        N = cfg.num_regions
        SC = self.structural_connectivity
        
        # Initialize
        v = self.rng.normal(-1, 0.1, N)  # Membrane potential
        w = self.rng.normal(0, 0.1, N)   # Recovery variable
        
        # Parameters
        a = 0.7
        b = 0.8
        c = 3.0
        I = 0.5
        
        n_steps = int(cfg.t_max / cfg.dt)
        transient_steps = int(cfg.transient / cfg.dt)
        
        v_history = []
        
        for step in range(n_steps):
            # FitzHugh-Nagumo equations
            coupling = cfg.coupling_strength * (SC @ v)
            
            dv = (c * (v - v**3/3 + w + I) + coupling) * cfg.dt
            dw = (-(v - a + b * w) / c) * cfg.dt
            
            v += dv
            w += dw
            
            if step >= transient_steps:
                v_history.append(v.copy())
            
            if step % 1000 == 0:
                await asyncio.sleep(0)
        
        v_arr = np.array(v_history)
        fc = np.corrcoef(v_arr.T)
        
        metrics = {
            "mean_activity": float(np.mean(v_arr)),
            "fc_mean": float(np.mean(fc[np.triu_indices_from(fc, k=1)])),
            "model": "fitzhugh_nagumo",
        }
        
        return {
            "metrics": metrics,
            "logs": ["FitzHugh-Nagumo connectome simulation completed"],
            "functional_connectivity": fc.tolist(),
        }
    
    def _calculate_network_metrics(
        self, activity: np.ndarray, fc: np.ndarray,
        sc: np.ndarray, order_global: np.ndarray, order_local: np.ndarray
    ) -> Dict[str, float]:
        """Calculate network metrics"""
        
        # Basic FC metrics
        fc_triu = fc[np.triu_indices_from(fc, k=1)]
        fc_mean = float(np.mean(fc_triu))
        fc_var = float(np.var(fc_triu))
        
        # SC-FC correlation
        sc_triu = sc[np.triu_indices_from(sc, k=1)]
        if np.std(sc_triu) > 0 and np.std(fc_triu) > 0:
            sc_fc_corr = float(np.corrcoef(sc_triu, fc_triu)[0, 1])
        else:
            sc_fc_corr = 0.0
        
        # Synchronization metrics
        mean_order = float(np.mean(order_global))
        var_order = float(np.var(order_global))
        
        # Metastability (variability of synchrony over time)
        metastability = float(np.std(order_global))
        
        # Integration (mean FC)
        integration = fc_mean
        
        # Segregation (modularity would require community detection)
        # Simplified: variance of FC
        segregation = fc_var
        
        return {
            "fc_mean": fc_mean,
            "fc_variance": fc_var,
            "sc_fc_correlation": sc_fc_corr,
            "mean_order_parameter": mean_order,
            "order_variance": var_order,
            "metastability": metastability,
            "integration": integration,
            "segregation": segregation,
            "mean_activity": float(np.mean(activity)),
            "activity_variance": float(np.var(activity)),
        }
    
    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []
        
        # Reasonable FC values
        fc_mean = metrics.get("fc_mean", 0)
        if 0 < fc_mean < 1:
            factors.append(0.3)
        
        # SC-FC correlation (should be positive in real brain)
        sc_fc = metrics.get("sc_fc_correlation", 0)
        if 0 < sc_fc < 1:
            factors.append(0.3)
        
        # Order parameter in reasonable range
        order = metrics.get("mean_order_parameter", 0.5)
        if 0.1 < order < 0.9:
            factors.append(0.2)
        
        # Activity present
        activity = metrics.get("mean_activity", 0)
        if activity > 0:
            factors.append(0.2)
        
        return min(0.95, sum(factors))
    
    def estimate_resources(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        """Estimate computational resources"""
        params = hypothesis.parameters
        N = params.get("num_regions", 68)
        t_max = params.get("t_max", 60)
        dt = params.get("dt", 0.001)
        
        n_steps = int(t_max / dt)
        
        return {
            "cpu_cores": 1,
            "memory_gb": 0.5 + N * N * 1e-5,
            "gpu_required": False,
            "estimated_time_seconds": n_steps * N / 1e5,
        }
    
    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Get pattern metadata"""
        return {
            "id": cls.id,
            "name": cls.name,
            "category": cls.category,
            "description": cls.description,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "default": p.default,
                    "min": p.min,
                    "max": p.max,
                    "options": p.options,
                    "description": p.description,
                }
                for p in cls.parameters
            ],
            "references": [
                "Hagmann, P. et al. (2008). Mapping the structural core of human cerebral cortex",
                "Honey, C.J. et al. (2009). Predicting human resting-state functional connectivity",
                "Deco, G. et al. (2013). RSNs emerge from collective dynamics",
            ],
        }
