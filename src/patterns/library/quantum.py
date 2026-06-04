"""
C4REQBER v6.0 - Quantum Simulation Pattern
Quantum mechanical simulations using various methods:
- Schrödinger equation time evolution
- Variational quantum eigensolver (VQE)
- Quantum circuit simulation

Pattern Structure (Christopher Alexander):
- Context: Quantum chemistry, material science, quantum computing
- Forces: Exponential scaling, entanglement, measurement collapse
- Solution: Multiple methods with appropriate approximations
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


class QuantumMethod(Enum):
    """Available quantum simulation methods"""

    SCHRODINGER = "schrodinger"  # Time-dependent Schrödinger equation
    VQE = "vqe"  # Variational Quantum Eigensolver
    CIRCUIT = "circuit"  # Quantum circuit simulation
    DENSITY_MATRIX = "density_matrix"  # Open quantum systems


@dataclass
class QuantumConfig:
    """Configuration for quantum simulation"""

    method: QuantumMethod = QuantumMethod.SCHRODINGER

    # System parameters
    n_qubits: int = 4  # Number of qubits (or basis states)
    dt: float = 0.01  # Time step
    steps: int = 1000  # Number of steps

    # Schrödinger equation
    potential_type: str = "harmonic"  # harmonic, box, double_well

    # VQE parameters
    n_layers: int = 3  # Number of ansatz layers
    optimizer: str = "gradient_descent"
    learning_rate: float = 0.01

    # Circuit parameters
    circuit_depth: int = 5
    gates: list[str] = field(default_factory=lambda: ["H", "CNOT", "RZ", "RX"])

    # Physical constants (atomic units)
    hbar: float = 1.0
    mass: float = 1.0


class QuantumPattern:
    """
    Quantum simulation pattern supporting multiple methods.
    """

    PATTERN_ID = "quantum"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: QuantumConfig | None = None) -> None:
        self.config = config or QuantumConfig()
        self.state: np.ndarray | None = None
        self.hamiltonian: np.ndarray | None = None
        self.energy_history: list[float] = []

        self._initialize_system()

    def _initialize_system(self) -> None:
        """Initialize quantum system based on method"""
        cfg = self.config

        if cfg.method == QuantumMethod.SCHRODINGER:
            self._init_schrodinger()
        elif cfg.method == QuantumMethod.VQE:
            self._init_vqe()
        elif cfg.method == QuantumMethod.CIRCUIT:
            self._init_circuit()
        elif cfg.method == QuantumMethod.DENSITY_MATRIX:
            self._init_density_matrix()

    def _init_schrodinger(self) -> None:
        """Initialize 1D Schrödinger equation simulation"""
        cfg = self.config

        # Spatial grid
        self.x = np.linspace(-10, 10, 2**cfg.n_qubits)
        self.dx = self.x[1] - self.x[0]
        n = len(self.x)

        # Kinetic energy operator (finite difference)
        T = np.zeros((n, n))
        coeff = -(cfg.hbar**2) / (2 * cfg.mass * self.dx**2)
        for i in range(n):
            T[i, i] = -2 * coeff
            if i > 0:
                T[i, i - 1] = coeff
                T[i - 1, i] = coeff

        # Potential
        V = np.diag(self._potential(self.x))

        # Hamiltonian
        self.hamiltonian = T + V

        # Initial state (Gaussian wave packet)
        x0 = -5.0
        sigma = 1.0
        k0 = 2.0
        psi = np.exp(-((self.x - x0) ** 2) / (4 * sigma**2)) * np.exp(1j * k0 * self.x)
        self.state = psi / np.sqrt(np.sum(np.abs(psi) ** 2))

    def _potential(self, x: np.ndarray) -> np.ndarray:
        """Calculate potential energy"""
        cfg = self.config

        if cfg.potential_type == "harmonic":
            return 0.5 * x**2
        elif cfg.potential_type == "box":
            return np.where(np.abs(x) < 5, 0, 1000)
        elif cfg.potential_type == "double_well":
            return 0.25 * (x**2 - 4) ** 2
        elif cfg.potential_type == "barrier":
            V = np.zeros_like(x)
            V[np.abs(x) < 0.5] = 5.0
            return V
        else:
            return 0.5 * x**2

    def _init_vqe(self) -> None:
        """Initialize Variational Quantum Eigensolver"""
        cfg = self.config
        n = 2**cfg.n_qubits

        # Create a simple Hamiltonian (Heisenberg model)
        self.hamiltonian = self._heisenberg_hamiltonian(cfg.n_qubits)

        # Initial parameters for ansatz
        self.ansatz_params = np.random.randn(cfg.n_layers * cfg.n_qubits * 2) * 0.1

    def _heisenberg_hamiltonian(self, n_qubits: int) -> np.ndarray:
        """Create Heisenberg XXZ Hamiltonian"""
        dim = 2**n_qubits
        H = np.zeros((dim, dim), dtype=complex)

        # Pauli matrices
        I = np.eye(2)
        X = np.array([[0, 1], [1, 0]], dtype=complex)
        Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
        Z = np.array([[1, 0], [0, -1]], dtype=complex)

        # Nearest-neighbor interactions
        J = 1.0
        for i in range(n_qubits - 1):
            # Build XX, YY, ZZ operators
            XX = 1
            YY = 1
            ZZ = 1
            for j in range(n_qubits):
                if j == i or j == i + 1:
                    XX = np.kron(XX, X)  # type: ignore[assignment]
                    YY = np.kron(YY, Y)  # type: ignore[assignment]
                    ZZ = np.kron(ZZ, Z)  # type: ignore[assignment]
                else:
                    XX = np.kron(XX, I)  # type: ignore[assignment]
                    YY = np.kron(YY, I)  # type: ignore[assignment]
                    ZZ = np.kron(ZZ, I)  # type: ignore[assignment]

            H += J * (XX + YY + ZZ)

        return H

    def _init_circuit(self) -> None:
        """Initialize quantum circuit simulation"""
        cfg = self.config

        # Initial state |00...0⟩
        self.state = np.zeros(2**cfg.n_qubits, dtype=complex)
        self.state[0] = 1.0

        # Build random circuit
        self.circuit_gates = self._build_random_circuit()

    def _build_random_circuit(self) -> list[tuple[str, list[int], float]]:
        """Build random quantum circuit"""
        cfg = self.config
        gates = []

        for _ in range(cfg.circuit_depth):
            gate_type = np.random.choice(cfg.gates)

            if gate_type == "H":
                qubit = np.random.randint(cfg.n_qubits)
                gates.append(("H", [qubit], 0.0))
            elif gate_type == "CNOT":
                control = np.random.randint(cfg.n_qubits)
                target = np.random.randint(cfg.n_qubits)
                if control != target:
                    gates.append(("CNOT", [control, target], 0.0))
            elif gate_type == "RZ":
                qubit = np.random.randint(cfg.n_qubits)
                angle = np.random.uniform(0, 2 * np.pi)
                gates.append(("RZ", [qubit], angle))
            elif gate_type == "RX":
                qubit = np.random.randint(cfg.n_qubits)
                angle = np.random.uniform(0, 2 * np.pi)
                gates.append(("RX", [qubit], angle))

        return gates

    def _init_density_matrix(self) -> None:
        """Initialize density matrix for open quantum system"""
        cfg = self.config
        n = 2**cfg.n_qubits

        # Pure state density matrix
        self.state = np.zeros((n, n), dtype=complex)
        self.state[0, 0] = 1.0

        # Hamiltonian
        self.hamiltonian = self._heisenberg_hamiltonian(cfg.n_qubits)

        # Lindblad operators (dephasing)
        self.lindblad_ops = self._create_lindblad_operators()

    def _create_lindblad_operators(self) -> list[np.ndarray]:
        """Create Lindblad operators for decoherence"""
        cfg = self.config
        ops = []

        for i in range(cfg.n_qubits):
            # Dephasing operator
            L = np.zeros((2**cfg.n_qubits, 2**cfg.n_qubits), dtype=complex)
            for j in range(2**cfg.n_qubits):
                bit = (j >> i) & 1
                if bit == 1:
                    L[j, j] = 1.0
            ops.append(L)

        return ops

    def _apply_gate(self, gate_type: str, qubits: list[int], angle: float = 0.0) -> None:
        """Apply quantum gate to state"""
        cfg = self.config
        n = 2**cfg.n_qubits

        # Build gate matrix
        if gate_type == "H":
            U = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
        elif gate_type == "X":
            U = np.array([[0, 1], [1, 0]], dtype=complex)
        elif gate_type == "Z":
            U = np.array([[1, 0], [0, -1]], dtype=complex)
        elif gate_type == "RZ":
            U = np.array(
                [[np.exp(-1j * angle / 2), 0], [0, np.exp(1j * angle / 2)]],
                dtype=complex,
            )
        elif gate_type == "RX":
            U = np.array(
                [
                    [np.cos(angle / 2), -1j * np.sin(angle / 2)],
                    [-1j * np.sin(angle / 2), np.cos(angle / 2)],
                ],
                dtype=complex,
            )
        elif gate_type == "CNOT":
            # CNOT is 2-qubit gate
            U = np.eye(4, dtype=complex)
            U[2, 2] = 0
            U[2, 3] = 1
            U[3, 2] = 1
            U[3, 3] = 0
        else:
            return

        # Apply to full Hilbert space
        if gate_type == "CNOT":
            # Two-qubit gate
            full_U = self._expand_two_qubit_gate(U, qubits[0], qubits[1])
        else:
            # Single-qubit gate
            full_U = self._expand_single_qubit_gate(U, qubits[0])

        self.state = full_U @ self.state

    def _expand_single_qubit_gate(self, U: np.ndarray, target: int) -> np.ndarray:
        """Expand single-qubit gate to full Hilbert space"""
        cfg = self.config
        I = np.eye(2, dtype=complex)

        result = np.eye(1, dtype=complex)
        for i in range(cfg.n_qubits):
            if i == target:
                result = np.kron(result, U)
            else:
                result = np.kron(result, I)

        return result

    def _expand_two_qubit_gate(
        self, U: np.ndarray, control: int, target: int
    ) -> np.ndarray:
        """Expand two-qubit gate to full Hilbert space"""
        cfg = self.config
        n = 2**cfg.n_qubits

        # Build full unitary
        full_U = np.eye(n, dtype=complex)

        for i in range(n):
            # Check control qubit
            control_bit = (i >> control) & 1
            if control_bit == 1:
                # Apply X to target
                j = i ^ (1 << target)
                full_U[i, i] = 0
                full_U[i, j] = 1

        return full_U

    def _create_cnot_gate(self, control: int, target: int) -> np.ndarray:
        """Create CNOT gate matrix for given control and target qubits"""
        cfg = self.config
        n = 2**cfg.n_qubits

        # Build full unitary
        full_U = np.eye(n, dtype=complex)

        for i in range(n):
            # Check control qubit
            control_bit = (i >> control) & 1
            if control_bit == 1:
                # Apply X to target
                j = i ^ (1 << target)
                full_U[i, i] = 0
                full_U[i, j] = 1

        return full_U

    def _schrodinger_step(self) -> None:
        """One step of Schrödinger time evolution"""
        cfg = self.config

        # Time evolution operator (Crank-Nicolson)
        I = np.eye(len(self.state))  # type: ignore[arg-type]
        H = self.hamiltonian

        # U = exp(-i H dt / hbar) ≈ (I - i H dt/2) / (I + i H dt/2)
        A = I - 1j * H * cfg.dt / (2 * cfg.hbar)  # type: ignore[operator]
        B = I + 1j * H * cfg.dt / (2 * cfg.hbar)  # type: ignore[operator]

        self.state = np.linalg.solve(B, A @ self.state)  # type: ignore[operator]

        # Normalize
        self.state /= np.sqrt(np.sum(np.abs(self.state) ** 2))

    def _vqe_step(self) -> None:
        """One optimization step of VQE"""
        cfg = self.config

        # Create ansatz state
        psi = self._create_ansatz(self.ansatz_params)

        # Calculate energy
        energy = np.real(np.conj(psi) @ self.hamiltonian @ psi)
        self.energy_history.append(energy)

        # Gradient descent update (simplified)
        grad = self._vqe_gradient()
        self.ansatz_params -= cfg.learning_rate * grad

    def _create_ansatz(self, params: np.ndarray) -> np.ndarray:
        """Create variational ansatz state"""
        cfg = self.config

        # Start from |0...0⟩
        psi = np.zeros(2**cfg.n_qubits, dtype=complex)
        psi[0] = 1.0

        # Apply layers of RX and RZ rotations
        param_idx = 0
        for _ in range(cfg.n_layers):
            for q in range(cfg.n_qubits):
                # RX rotation
                theta = params[param_idx]
                U = np.array(
                    [
                        [np.cos(theta / 2), -1j * np.sin(theta / 2)],
                        [-1j * np.sin(theta / 2), np.cos(theta / 2)],
                    ],
                    dtype=complex,
                )
                full_U = self._expand_single_qubit_gate(U, q)
                psi = full_U @ psi
                param_idx += 1

                # RZ rotation
                phi = params[param_idx]
                U = np.array(
                    [[np.exp(-1j * phi / 2), 0], [0, np.exp(1j * phi / 2)]],
                    dtype=complex,
                )
                full_U = self._expand_single_qubit_gate(U, q)
                psi = full_U @ psi
                param_idx += 1

            # Entangling layer
            for q in range(cfg.n_qubits - 1):
                CNOT = self._create_cnot_gate(q, q + 1)
                psi = CNOT @ psi

        return psi

    def _vqe_gradient(self) -> np.ndarray:
        """Calculate gradient using parameter shift rule"""
        cfg = self.config
        eps = np.pi / 2

        grad = np.zeros_like(self.ansatz_params)

        for i in range(len(self.ansatz_params)):
            # Shift parameter up
            params_plus = self.ansatz_params.copy()
            params_plus[i] += eps
            psi_plus = self._create_ansatz(params_plus)
            E_plus = np.real(np.conj(psi_plus) @ self.hamiltonian @ psi_plus)

            # Shift parameter down
            params_minus = self.ansatz_params.copy()
            params_minus[i] -= eps
            psi_minus = self._create_ansatz(params_minus)
            E_minus = np.real(np.conj(psi_minus) @ self.hamiltonian @ psi_minus)

            # Parameter shift gradient
            grad[i] = (E_plus - E_minus) / 2

        return grad

    def _circuit_step(self) -> None:
        """Execute quantum circuit"""
        # Apply all gates
        for gate_type, qubits, angle in self.circuit_gates:
            self._apply_gate(gate_type, qubits, angle)

    def _density_matrix_step(self) -> None:
        """One step of Lindblad master equation"""
        cfg = self.config

        # Unitary part: -i[H, ρ]
        commutator = self.hamiltonian @ self.state - self.state @ self.hamiltonian  # type: ignore[operator]
        d_rho = -1j * commutator

        # Dissipative part: Σ L ρ L† - ½{L†L, ρ}
        gamma = 0.01  # Decoherence rate
        for L in self.lindblad_ops:
            L_dag = L.conj().T
            d_rho += gamma * (
                L @ self.state @ L_dag
                - 0.5 * (L_dag @ L @ self.state + self.state @ L_dag @ L)
            )

        # Euler step
        self.state += d_rho * cfg.dt

    def _measure(self, observable: np.ndarray | None = None) -> float:
        """Measure expectation value of observable"""
        if observable is None:
            # Measure energy
            observable = self.hamiltonian

        if self.config.method == QuantumMethod.DENSITY_MATRIX:
            # Tr(ρ O)
            return np.real(np.trace(self.state @ observable))  # type: ignore[no-any-return, operator]
        else:
            # ⟨ψ|O|ψ⟩
            return np.real(np.conj(self.state) @ observable @ self.state)  # type: ignore[arg-type, no-any-return]

    def run(self, hypothesis: dict[str, Any] = None) -> dict[str, Any]:  # type: ignore[assignment]
        """Run quantum simulation"""
        cfg = self.config

        logger.info(
            f"Starting quantum simulation: {cfg.method.value}, {cfg.n_qubits} qubits"
        )

        measurements = []
        times = []

        for step in range(cfg.steps):
            if cfg.method == QuantumMethod.SCHRODINGER:
                self._schrodinger_step()
                if step % 10 == 0:
                    E = self._measure()
                    measurements.append(E)
                    times.append(step * cfg.dt)

            elif cfg.method == QuantumMethod.VQE:
                self._vqe_step()
                if step % 10 == 0:
                    measurements.append(self.energy_history[-1])
                    times.append(step)

            elif cfg.method == QuantumMethod.CIRCUIT:
                if step == 0:
                    self._circuit_step()
                # Measure probabilities
                probs = np.abs(self.state) ** 2  # type: ignore[arg-type]
                measurements.append(probs.tolist())
                times.append(step)

            elif cfg.method == QuantumMethod.DENSITY_MATRIX:
                self._density_matrix_step()
                if step % 10 == 0:
                    purity = np.real(np.trace(self.state @ self.state))  # type: ignore[operator]
                    measurements.append(purity)
                    times.append(step * cfg.dt)

        return self._format_output(measurements, times)

    def _format_output(self, measurements: list, times: list[float]) -> dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        output = {
            "method": cfg.method.value,
            "n_qubits": cfg.n_qubits,
            "time_points": times,
            "measurements": measurements,
        }

        if cfg.method == QuantumMethod.SCHRODINGER:
            output.update(
                {
                    "final_state_real": np.real(self.state).tolist(),  # type: ignore[arg-type]
                    "final_state_imag": np.imag(self.state).tolist(),  # type: ignore[arg-type]
                    "position_grid": self.x.tolist(),
                    "final_probability": np.abs(self.state) ** 2,  # type: ignore[arg-type, dict-item]
                    "mean_energy": np.mean(measurements) if measurements else 0,
                }
            )

        elif cfg.method == QuantumMethod.VQE:
            output.update(
                {
                    "final_energy": self.energy_history[-1]  # type: ignore[dict-item]
                    if self.energy_history
                    else 0,
                    "energy_history": self.energy_history,
                    "final_parameters": self.ansatz_params.tolist(),
                    "optimization_steps": len(self.energy_history),
                }
            )

        elif cfg.method == QuantumMethod.CIRCUIT:
            output.update(
                {
                    "final_probabilities": np.abs(self.state) ** 2,  # type: ignore[arg-type, dict-item]
                    "circuit_gates": [
                        (g, q, float(a)) for g, q, a in self.circuit_gates
                    ],
                    "circuit_depth": cfg.circuit_depth,
                }
            )

        elif cfg.method == QuantumMethod.DENSITY_MATRIX:
            output.update(
                {
                    "final_purity": np.real(np.trace(self.state @ self.state)),  # type: ignore[operator]
                    "final_entropy": -np.real(
                        np.trace(self.state @ np.log(self.state + 1e-10))  # type: ignore[operator]
                    ),
                    "lindblad_operators": len(self.lindblad_ops),
                }
            )

        return output

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Quantum Simulation",
            "category": "ON_DEMAND",
            "domain": ["Quantum Physics", "Quantum Chemistry", "Quantum Computing"],
            "description": "Quantum mechanical simulations using various methods",
            "computational_complexity": "O(2^N) for N qubits",
            "typical_runtime": "seconds to hours",
            "accuracy": "High (exact for small systems)",
            "assumptions": [
                "Finite-dimensional Hilbert space",
                "Unitary evolution (closed systems)",
                "Markovian noise (open systems)",
            ],
            "parameters": [
                {
                    "name": "method",
                    "type": "enum",
                    "options": ["schrodinger", "vqe", "circuit", "density_matrix"],
                    "default": "schrodinger",
                },
                {
                    "name": "n_qubits",
                    "type": "int",
                    "default": 4,
                    "description": "Number of qubits",
                },
                {
                    "name": "steps",
                    "type": "int",
                    "default": 1000,
                    "description": "Simulation steps",
                },
                {"name": "potential_type", "type": "string", "default": "harmonic"},
            ],
        }


if __name__ == "__main__":
    # Test quantum pattern
    logging.basicConfig(level=logging.INFO)

    # Test Schrödinger
    config = QuantumConfig(method=QuantumMethod.SCHRODINGER, steps=500)
    quantum = QuantumPattern(config)
    result = quantum.run()
    print(f"Schrödinger: Final energy = {result['mean_energy']:.4f}")

    # Test VQE
    config = QuantumConfig(method=QuantumMethod.VQE, steps=100)
    quantum = QuantumPattern(config)
    result = quantum.run()
    print(f"VQE: Final energy = {result['final_energy']:.4f}")
