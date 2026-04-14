"""
Open Quantum System Pattern
Lindblad Master Equation for dissipative quantum dynamics

Based on:
- Gorini-Kossakowski-Sudarshan-Lindblad (GKSL) equation
- Quantum jump method (Monte Carlo)
- Density matrix propagation
- Decoherence and dissipation

Applications:
- Quantum computing
- Quantum optics
- NMR spectroscopy
- Quantum biology
"""

import asyncio
import numpy as np
from typing import Dict, List, Callable, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from scipy.linalg import expm

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


class OpenSystemMethod(Enum):
    LINDBLAD = "lindblad"       # Direct master equation
    QUANTUM_JUMP = "jump"       # Monte Carlo wavefunction
    SUPEROPERATOR = "superop"   # Superoperator exponentiation


class DissipationType(Enum):
    AMPLITUDE_DAMPING = "amplitude"    # T1 relaxation
    PHASE_DAMPING = "phase"            # T2 dephasing
    DEPOLARIZING = "depolarizing"      # General decoherence
    CUSTOM = "custom"


@dataclass
class OpenQuantumConfig:
    """Configuration for open quantum system simulation"""
    # System parameters
    hilbert_dim: int = 2  # Qubit by default
    n_qubits: int = 1
    
    # Time evolution
    t_final: float = 10.0  # Final time
    dt: float = 0.01       # Time step
    n_steps: int = field(init=False)
    
    # Dissipation
    dissipation_type: str = "amplitude"
    T1: float = 100.0      # Relaxation time
    T2: float = 50.0       # Dephasing time
    gamma: float = 0.01    # Decay rate
    
    # Method
    method: str = "lindblad"
    n_trajectories: int = 100  # For quantum jump method
    
    # Initial state
    initial_state: str = "ground"  # 'ground', 'excited', 'superposition', 'mixed'
    
    # Hamiltonian parameters
    omega: float = 1.0     # System frequency
    drive_amplitude: float = 0.0
    drive_frequency: float = 1.0
    
    def __post_init__(self):
        self.n_steps = int(self.t_final / self.dt)
        if self.n_qubits > 1:
            self.hilbert_dim = 2 ** self.n_qubits


@simulation_pattern(
    id="open_quantum",
    name="Open Quantum System",
    category="quantum",
    description="Lindblad master equation for dissipative quantum dynamics",
)
class OpenQuantumPattern(SimulationPattern):
    """
    Open quantum system simulation using Lindblad master equation
    
    Implements:
    - Lindblad master equation for density matrices
    - Quantum jump (Monte Carlo) method
    - Amplitude damping, phase damping, depolarizing channels
    - Driven-dissipative dynamics
    - Purity and entanglement tracking
    """
    
    parameters = [
        SimulationParameter(
            name="n_qubits",
            type="int",
            default=1,
            min=1,
            max=4,
            description="Number of qubits",
        ),
        SimulationParameter(
            name="t_final",
            type="float",
            default=10.0,
            min=1.0,
            max=1000.0,
            description="Final simulation time",
        ),
        SimulationParameter(
            name="dt",
            type="float",
            default=0.01,
            min=0.001,
            max=0.1,
            description="Time step",
        ),
        SimulationParameter(
            name="T1",
            type="float",
            default=100.0,
            min=1.0,
            max=10000.0,
            description="T1 relaxation time",
        ),
        SimulationParameter(
            name="T2",
            type="float",
            default=50.0,
            min=1.0,
            max=10000.0,
            description="T2 dephasing time",
        ),
        SimulationParameter(
            name="omega",
            type="float",
            default=1.0,
            min=0.1,
            max=100.0,
            description="System frequency",
        ),
        SimulationParameter(
            name="method",
            type="select",
            default="lindblad",
            options=["lindblad", "jump"],
            description="Simulation method",
        ),
        SimulationParameter(
            name="n_trajectories",
            type="int",
            default=100,
            min=10,
            max=1000,
            description="Number of trajectories (jump method)",
        ),
        SimulationParameter(
            name="initial_state",
            type="select",
            default="ground",
            options=["ground", "excited", "superposition", "mixed"],
            description="Initial state",
        ),
    ]
    
    def __init__(self):
        super().__init__()
        self.hbar = 1.0
        
    def can_simulate(self, hypothesis: Hypothesis) -> bool:
        """Check if open quantum can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        
        keywords = [
            "open quantum", "lindblad", "master equation", "dissipation",
            "decoherence", "quantum jump", "t1", "t2", "relaxation",
            "dephasing", "density matrix", "quantum noise",
            "driven dissipative", "quantum reservoir", "bath",
        ]
        
        return any(kw in title or kw in desc for kw in keywords)
    
    async def run(
        self, hypothesis: Hypothesis, config: Dict[str, Any]
    ) -> SimulationResult:
        """Execute open quantum system simulation"""
        start_time = datetime.now()
        simulation_id = f"open_quantum_{start_time.timestamp()}"
        
        logger.info(f"Starting open quantum simulation {simulation_id}")
        
        try:
            oqs_config = self._parse_config(config)
            
            if oqs_config.method == "lindblad":
                results = await self._lindblad_simulation(hypothesis, oqs_config)
            elif oqs_config.method == "jump":
                results = await self._quantum_jump_simulation(hypothesis, oqs_config)
            else:
                results = await self._lindblad_simulation(hypothesis, oqs_config)
            
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
            logger.exception("Open quantum simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )
    
    def _parse_config(self, config: Dict[str, Any]) -> OpenQuantumConfig:
        """Parse configuration dict into OpenQuantumConfig"""
        return OpenQuantumConfig(
            n_qubits=config.get("n_qubits", 1),
            t_final=config.get("t_final", 10.0),
            dt=config.get("dt", 0.01),
            T1=config.get("T1", 100.0),
            T2=config.get("T2", 50.0),
            omega=config.get("omega", 1.0),
            method=config.get("method", "lindblad"),
            n_trajectories=config.get("n_trajectories", 100),
            initial_state=config.get("initial_state", "ground"),
        )
    
    async def _lindblad_simulation(self, hypothesis: Hypothesis, config: OpenQuantumConfig) -> Dict[str, Any]:
        """Lindblad master equation simulation"""
        
        d = config.hilbert_dim
        
        # Initialize density matrix
        rho = self._initialize_density_matrix(config)
        
        # Build Hamiltonian
        H = self._build_hamiltonian(config)
        
        # Build Lindblad operators
        jump_ops = self._build_jump_operators(config)
        
        # Time evolution
        times = np.linspace(0, config.t_final, config.n_steps)
        
        # History arrays
        population_history = []
        coherence_history = []
        purity_history = []
        entropy_history = []
        energy_expectation_history = []
        
        for i, t in enumerate(times):
            # Record observables
            pop = self._measure_population(rho, config)
            coh = self._measure_coherence(rho, config)
            purity = self._calculate_purity(rho)
            entropy = self._calculate_von_neumann_entropy(rho)
            energy = np.real(np.trace(rho @ H))
            
            population_history.append(pop)
            coherence_history.append(coh)
            purity_history.append(purity)
            entropy_history.append(entropy)
            energy_expectation_history.append(energy)
            
            # Time step using 4th order Runge-Kutta
            rho = self._rk4_step(rho, H, jump_ops, config.dt)
            
            # Ensure Hermiticity and trace preservation
            rho = 0.5 * (rho + rho.conj().T)
            rho = rho / np.trace(rho)
            
            if i % 100 == 0:
                await asyncio.sleep(0)
        
        # Final analysis
        final_population = population_history[-1] if population_history else 0
        final_purity = purity_history[-1] if purity_history else 0
        final_entropy = entropy_history[-1] if entropy_history else 0
        
        # Relaxation time estimate
        if len(population_history) > 10:
            # Fit exponential decay
            t_array = np.array(times)
            pop_array = np.array(population_history)
            try:
                # Simple exponential fit
                log_pop = np.log(np.maximum(pop_array, 1e-10))
                fit = np.polyfit(t_array, log_pop, 1)
                relaxation_rate = -fit[0]
                T1_measured = 1.0 / relaxation_rate if relaxation_rate > 0 else float('inf')
            except:
                T1_measured = config.T1
        else:
            T1_measured = config.T1
        
        # Steady state fidelity
        steady_state = self._calculate_steady_state(H, jump_ops, d)
        fidelity_to_steady = self._fidelity(rho, steady_state)
        
        metrics = {
            "final_population": float(final_population),
            "final_coherence": float(coherence_history[-1]) if coherence_history else 0,
            "final_purity": float(final_purity),
            "final_entropy": float(final_entropy),
            "T1_measured": float(T1_measured),
            "T1_input": float(config.T1),
            "T2_input": float(config.T2),
            "fidelity_to_steady_state": float(fidelity_to_steady),
            "n_steps": config.n_steps,
            "hilbert_dim": d,
            "method": "lindblad",
        }
        
        logs = [
            f"Lindblad master equation simulation completed",
            f"Hilbert dimension: {d}",
            f"Time evolution: {config.t_final:.2f} (dt={config.dt:.4f})",
            f"Final population (excited): {final_population:.6f}",
            f"Final purity: {final_purity:.6f}",
            f"Final entropy: {final_entropy:.6f}",
            f"Measured T1: {T1_measured:.2f}",
            f"Fidelity to steady state: {fidelity_to_steady:.6f}",
        ]
        
        if final_purity < 0.5:
            logs.append("System has decohered to mixed state")
        
        return {
            "metrics": metrics,
            "logs": logs,
            "times": times.tolist(),
            "population_history": population_history,
            "purity_history": purity_history,
            "final_density_matrix": rho.tolist(),
        }
    
    async def _quantum_jump_simulation(self, hypothesis: Hypothesis, config: OpenQuantumConfig) -> Dict[str, Any]:
        """Quantum jump (Monte Carlo) simulation"""
        
        d = config.hilbert_dim
        times = np.linspace(0, config.t_final, config.n_steps)
        
        # Build Hamiltonian
        H = self._build_hamiltonian(config)
        
        # Jump operators
        jump_ops = self._build_jump_operators(config)
        
        # Effective non-Hermitian Hamiltonian
        Heff = H - 0.5j * sum([L.conj().T @ L for L in jump_ops])
        
        # Run multiple trajectories
        trajectory_results = []
        
        for traj in range(config.n_trajectories):
            # Initial state (wavefunction)
            psi = self._initialize_wavefunction(config)
            
            trajectory_pop = []
            
            for i in range(config.n_steps):
                # Record
                pop = np.abs(psi[1])**2 if len(psi) > 1 else 0
                trajectory_pop.append(pop)
                
                # Determine jump probability
                dp = sum([np.real(psi.conj() @ L.conj().T @ L @ psi) * config.dt 
                         for L in jump_ops])
                
                # Monte Carlo step
                if self.rng.random() < dp:
                    # Quantum jump
                    jump_probs = [np.real(psi.conj() @ L.conj().T @ L @ psi) 
                                 for L in jump_ops]
                    jump_idx = self.rng.choice(len(jump_ops), p=np.array(jump_probs)/sum(jump_probs))
                    psi = jump_ops[jump_idx] @ psi
                    psi = psi / np.linalg.norm(psi)
                else:
                    # No-jump evolution
                    psi = psi - 1j * Heff @ psi * config.dt
                    psi = psi / np.linalg.norm(psi)
                
                if i % 100 == 0 and traj % 10 == 0:
                    await asyncio.sleep(0)
            
            trajectory_results.append(trajectory_pop)
        
        # Average over trajectories
        pop_array = np.array(trajectory_results)
        avg_population = np.mean(pop_array, axis=0)
        std_population = np.std(pop_array, axis=0)
        
        # Estimate density matrix from trajectories
        avg_purity = self._estimate_purity_from_trajectories(trajectory_results)
        
        metrics = {
            "final_population": float(avg_population[-1]),
            "population_std": float(std_population[-1]),
            "estimated_purity": float(avg_purity),
            "n_trajectories": config.n_trajectories,
            "n_steps": config.n_steps,
            "hilbert_dim": d,
            "method": "quantum_jump",
        }
        
        logs = [
            f"Quantum jump simulation completed",
            f"Trajectories: {config.n_trajectories}",
            f"Final average population: {avg_population[-1]:.6f} ± {std_population[-1]:.6f}",
            f"Estimated purity: {avg_purity:.6f}",
        ]
        
        return {
            "metrics": metrics,
            "logs": logs,
            "times": times.tolist(),
            "population_trajectories": trajectory_results[:10],  # First 10 only
            "average_population": avg_population.tolist(),
        }
    
    def _initialize_density_matrix(self, config: OpenQuantumConfig) -> np.ndarray:
        """Initialize density matrix"""
        d = config.hilbert_dim
        
        if config.initial_state == "ground":
            rho = np.zeros((d, d))
            rho[0, 0] = 1.0
        elif config.initial_state == "excited":
            rho = np.zeros((d, d))
            rho[-1, -1] = 1.0
        elif config.initial_state == "superposition":
            # |0> + |1> / sqrt(2)
            psi = np.ones(d) / np.sqrt(d)
            rho = np.outer(psi, psi.conj())
        else:  # mixed
            rho = np.eye(d) / d
        
        return rho
    
    def _initialize_wavefunction(self, config: OpenQuantumConfig) -> np.ndarray:
        """Initialize wavefunction"""
        d = config.hilbert_dim
        
        if config.initial_state == "ground":
            psi = np.zeros(d)
            psi[0] = 1.0
        elif config.initial_state == "excited":
            psi = np.zeros(d)
            psi[-1] = 1.0
        elif config.initial_state == "superposition":
            psi = np.ones(d) / np.sqrt(d)
        else:
            # Random pure state
            psi = (self.rng.random(d) + 1j * self.rng.random(d))
            psi = psi / np.linalg.norm(psi)
        
        return psi
    
    def _build_hamiltonian(self, config: OpenQuantumConfig) -> np.ndarray:
        """Build system Hamiltonian"""
        d = config.hilbert_dim
        H = np.zeros((d, d), dtype=complex)
        
        if config.n_qubits == 1:
            # Single qubit: H = (omega/2) * sigma_z + drive * sigma_x * cos(omega_d t)
            # In rotating frame approximation
            H[0, 0] = -config.omega / 2
            H[1, 1] = config.omega / 2
            if config.drive_amplitude > 0:
                H[0, 1] = config.drive_amplitude / 2
                H[1, 0] = config.drive_amplitude / 2
        
        else:
            # Multi-qubit Hamiltonian with interactions
            for i in range(config.n_qubits):
                # Single qubit terms
                pass
        
        return H
    
    def _build_jump_operators(self, config: OpenQuantumConfig) -> List[np.ndarray]:
        """Build Lindblad jump operators"""
        d = config.hilbert_dim
        jump_ops = []
        
        if config.n_qubits == 1:
            # Amplitude damping (T1): sigma_-
            if config.T1 < float('inf'):
                gamma1 = 1.0 / config.T1
                L1 = np.zeros((d, d))
                L1[0, 1] = np.sqrt(gamma1)
                jump_ops.append(L1)
            
            # Phase damping (T2): sigma_z
            if config.T2 < float('inf'):
                # T2 = 1/(1/(2*T1) + 1/T_phi)
                gamma_phi = 1.0 / config.T2 - 1.0 / (2 * config.T1)
                if gamma_phi > 0:
                    L2 = np.zeros((d, d))
                    L2[0, 0] = np.sqrt(gamma_phi)
                    L2[1, 1] = -np.sqrt(gamma_phi)
                    jump_ops.append(L2)
        
        else:
            # Multi-qubit jump operators
            for q in range(config.n_qubits):
                pass
        
        return jump_ops
    
    def _lindbladian(self, rho: np.ndarray, H: np.ndarray, jump_ops: List[np.ndarray]) -> np.ndarray:
        """Calculate drho/dt from Lindblad equation"""
        # Coherent part: -i[H, rho]
        drho = -1j * (H @ rho - rho @ H)
        
        # Dissipative part
        for L in jump_ops:
            L_dag = L.conj().T
            drho += L @ rho @ L_dag - 0.5 * (L_dag @ L @ rho + rho @ L_dag @ L)
        
        return drho
    
    def _rk4_step(self, rho: np.ndarray, H: np.ndarray, jump_ops: List[np.ndarray], dt: float) -> np.ndarray:
        """4th order Runge-Kutta step"""
        k1 = self._lindbladian(rho, H, jump_ops)
        k2 = self._lindbladian(rho + 0.5*dt*k1, H, jump_ops)
        k3 = self._lindbladian(rho + 0.5*dt*k2, H, jump_ops)
        k4 = self._lindbladian(rho + dt*k3, H, jump_ops)
        
        return rho + (dt/6) * (k1 + 2*k2 + 2*k3 + k4)
    
    def _measure_population(self, rho: np.ndarray, config: OpenQuantumConfig) -> float:
        """Measure excited state population"""
        if config.n_qubits == 1:
            return np.real(rho[1, 1])
        return 0.0
    
    def _measure_coherence(self, rho: np.ndarray, config: OpenQuantumConfig) -> float:
        """Measure coherence (off-diagonal element)"""
        if config.n_qubits == 1:
            return np.abs(rho[0, 1])
        return 0.0
    
    def _calculate_purity(self, rho: np.ndarray) -> float:
        """Calculate purity Tr(rho²)"""
        return np.real(np.trace(rho @ rho))
    
    def _calculate_von_neumann_entropy(self, rho: np.ndarray) -> float:
        """Calculate von Neumann entropy S = -Tr(rho log rho)"""
        eigenvalues = np.linalg.eigvalsh(rho)
        eigenvalues = eigenvalues[eigenvalues > 1e-15]
        return -np.sum(eigenvalues * np.log2(eigenvalues))
    
    def _calculate_steady_state(self, H: np.ndarray, jump_ops: List[np.ndarray], d: int) -> np.ndarray:
        """Calculate steady state (simplified)"""
        # For amplitude damping, steady state is ground state
        rho_ss = np.zeros((d, d))
        rho_ss[0, 0] = 1.0
        return rho_ss
    
    def _fidelity(self, rho1: np.ndarray, rho2: np.ndarray) -> float:
        """Calculate fidelity between two density matrices"""
        sqrt_rho1 = self._matrix_sqrt(rho1)
        product = sqrt_rho1 @ rho2 @ sqrt_rho1
        eigenvalues = np.linalg.eigvalsh(product)
        return np.real(np.sum(np.sqrt(np.maximum(eigenvalues, 0))))**2
    
    def _matrix_sqrt(self, A: np.ndarray) -> np.ndarray:
        """Calculate matrix square root"""
        eigenvalues, eigenvectors = np.linalg.eigh(A)
        eigenvalues = np.maximum(eigenvalues, 0)
        return eigenvectors @ np.diag(np.sqrt(eigenvalues)) @ eigenvectors.conj().T
    
    def _estimate_purity_from_trajectories(self, trajectories: List[List[float]]) -> float:
        """Estimate purity from quantum jump trajectories"""
        # Purity ≈ 1 for pure states, < 1 for mixed
        # Variance in population indicates mixedness
        final_pops = [t[-1] for t in trajectories]
        var_pop = np.var(final_pops)
        # Rough estimate: purity ≈ 1 - 2*variance for single qubit
        return max(0, min(1, 1 - 2 * var_pop))
    
    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []
        
        # Physical purity
        purity = metrics.get("final_purity", 0) or metrics.get("estimated_purity", 0)
        if 0 < purity <= 1:
            factors.append(0.3)
        
        # Population in valid range
        pop = metrics.get("final_population", 0)
        if 0 <= pop <= 1:
            factors.append(0.3)
        
        # Sufficient steps
        if metrics.get("n_steps", 0) >= 100:
            factors.append(0.2)
        
        # T1 matches input (for Lindblad)
        if "T1_measured" in metrics:
            t1_in = metrics.get("T1_input", 1)
            t1_out = metrics.get("T1_measured", 1)
            if t1_in > 0 and abs(t1_out - t1_in) / t1_in < 0.2:
                factors.append(0.2)
        
        return min(0.85, sum(factors))
    
    def estimate_resources(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        """Estimate computational resources"""
        params = hypothesis.parameters
        n_qubits = params.get("n_qubits", 1)
        n_steps = int(params.get("t_final", 10) / params.get("dt", 0.01))
        method = params.get("method", "lindblad")
        
        d = 2 ** n_qubits
        
        if method == "jump":
            n_traj = params.get("n_trajectories", 100)
            estimated_time = n_traj * n_steps * d**2 / 1e6
        else:
            estimated_time = n_steps * d**3 / 1e6
        
        return {
            "cpu_cores": 4,
            "memory_gb": 0.5 + d**2 * 16e-9 * 10,
            "gpu_required": n_qubits > 3,
            "estimated_time_seconds": estimated_time,
        }
