"""Tests for quantum pattern module."""

import numpy as np
import pytest

from src.patterns.library.quantum import QuantumConfig, QuantumPattern, QuantumMethod



class TestQuantumConfig:
    def test_default_values(self):
        cfg = QuantumConfig()
        assert cfg.method == QuantumMethod.SCHRODINGER
        assert cfg.n_qubits == 4
        assert cfg.dt == 0.01
        assert cfg.steps == 1000
        assert cfg.potential_type == "harmonic"

    def test_custom_values(self):
        cfg = QuantumConfig(method=QuantumMethod.VQE, n_qubits=3, steps=100)
        assert cfg.method == QuantumMethod.VQE
        assert cfg.n_qubits == 3
        assert cfg.steps == 100


class TestQuantumPattern:
    @pytest.fixture
    def schrodinger_pattern(self):
        return QuantumPattern(QuantumConfig(method=QuantumMethod.SCHRODINGER, steps=100))

    @pytest.fixture
    def vqe_pattern(self):
        return QuantumPattern(QuantumConfig(method=QuantumMethod.VQE, steps=50))

    @pytest.fixture
    def circuit_pattern(self):
        return QuantumPattern(QuantumConfig(method=QuantumMethod.CIRCUIT, steps=10))

    def test_pattern_id(self):
        assert QuantumPattern.PATTERN_ID == "quantum"
        assert QuantumPattern.PATTERN_VERSION == "6.0.0"

    def test_init_schrodinger(self, schrodinger_pattern):
        assert schrodinger_pattern.state is not None
        assert schrodinger_pattern.hamiltonian is not None
        assert len(schrodinger_pattern.x) == 2**4

    def test_init_vqe(self, vqe_pattern):
        assert vqe_pattern.hamiltonian is not None
        assert vqe_pattern.ansatz_params is not None

    def test_init_circuit(self, circuit_pattern):
        assert circuit_pattern.state is not None
        assert len(circuit_pattern.circuit_gates) > 0

    def test_potential_harmonic(self, schrodinger_pattern):
        x = np.array([-2.0, 0.0, 2.0])
        V = schrodinger_pattern._potential(x)
        assert np.allclose(V, 0.5 * x**2)

    def test_potential_box(self):
        pattern = QuantumPattern(QuantumConfig(potential_type="box"))
        x = np.array([-6.0, 0.0, 6.0])
        V = pattern._potential(x)
        assert V[1] == 0
        assert V[0] == 1000
        assert V[2] == 1000

    def test_potential_double_well(self):
        pattern = QuantumPattern(QuantumConfig(potential_type="double_well"))
        x = np.array([-2.0, 0.0, 2.0])
        V = pattern._potential(x)
        assert V[1] == 4.0  # 0.25 * (0 - 4)^2 = 4

    def test_heisenberg_hamiltonian(self, schrodinger_pattern):
        H = schrodinger_pattern._heisenberg_hamiltonian(2)
        assert H.shape == (4, 4)
        assert np.allclose(H, H.conj().T)  # Hermitian

    def test_apply_gate_h(self, circuit_pattern):
        state_before = circuit_pattern.state.copy()
        circuit_pattern._apply_gate("H", [0])
        assert not np.allclose(circuit_pattern.state, state_before)

    def test_apply_gate_x(self, circuit_pattern):
        circuit_pattern._apply_gate("X", [0])
        assert np.isclose(np.sum(np.abs(circuit_pattern.state)**2), 1.0)

    def test_apply_gate_cnot(self, circuit_pattern):
        circuit_pattern._apply_gate("CNOT", [0, 1])
        assert np.isclose(np.sum(np.abs(circuit_pattern.state)**2), 1.0)

    def test_expand_single_qubit_gate(self, circuit_pattern):
        U = np.array([[1, 0], [0, 1]], dtype=complex)
        full_U = circuit_pattern._expand_single_qubit_gate(U, 0)
        assert full_U.shape == (16, 16)

    def test_expand_two_qubit_gate(self, circuit_pattern):
        U = np.eye(4, dtype=complex)
        full_U = circuit_pattern._expand_two_qubit_gate(U, 0, 1)
        assert full_U.shape == (16, 16)

    def test_create_cnot_gate(self, circuit_pattern):
        U = circuit_pattern._create_cnot_gate(0, 1)
        assert U.shape == (16, 16)

    def test_schrodinger_step(self, schrodinger_pattern):
        state_before = schrodinger_pattern.state.copy()
        schrodinger_pattern._schrodinger_step()
        assert not np.allclose(schrodinger_pattern.state, state_before)
        assert np.isclose(np.sum(np.abs(schrodinger_pattern.state)**2), 1.0)

    def test_vqe_step(self, vqe_pattern):
        params_before = vqe_pattern.ansatz_params.copy()
        vqe_pattern._vqe_step()
        assert not np.allclose(vqe_pattern.ansatz_params, params_before)
        assert len(vqe_pattern.energy_history) > 0

    def test_create_ansatz(self, vqe_pattern):
        psi = vqe_pattern._create_ansatz(vqe_pattern.ansatz_params)
        assert len(psi) == 2**vqe_pattern.config.n_qubits
        assert np.isclose(np.sum(np.abs(psi)**2), 1.0)

    def test_vqe_gradient(self, vqe_pattern):
        grad = vqe_pattern._vqe_gradient()
        assert len(grad) == len(vqe_pattern.ansatz_params)
        assert np.all(np.isfinite(grad))

    def test_circuit_step(self, circuit_pattern):
        state_before = circuit_pattern.state.copy()
        circuit_pattern._circuit_step()
        assert not np.allclose(circuit_pattern.state, state_before)

    def test_measure(self, schrodinger_pattern):
        E = schrodinger_pattern._measure()
        assert isinstance(E, float)
        assert np.isfinite(E)

    def test_run_schrodinger(self):
        pattern = QuantumPattern(QuantumConfig(method=QuantumMethod.SCHRODINGER, steps=50))
        result = pattern.run()
        assert result["method"] == "schrodinger"
        assert "final_probability" in result
        assert "mean_energy" in result

    def test_run_vqe(self):
        pattern = QuantumPattern(QuantumConfig(method=QuantumMethod.VQE, steps=20, n_qubits=3))
        result = pattern.run()
        assert result["method"] == "vqe"
        assert "final_energy" in result
        assert "energy_history" in result

    def test_run_circuit(self):
        pattern = QuantumPattern(QuantumConfig(method=QuantumMethod.CIRCUIT, steps=5, n_qubits=3))
        result = pattern.run()
        assert result["method"] == "circuit"
        assert "final_probabilities" in result

    def test_run_density_matrix(self):
        pattern = QuantumPattern(QuantumConfig(method=QuantumMethod.DENSITY_MATRIX, steps=20, n_qubits=3))
        result = pattern.run()
        assert result["method"] == "density_matrix"
        assert "final_purity" in result

    def test_run_with_custom_signal(self):
        pattern = QuantumPattern(QuantumConfig(method=QuantumMethod.SCHRODINGER, steps=20))
        result = pattern.run({"signal": np.random.randn(16)})
        assert result["method"] == "schrodinger"

    def test_metadata(self):
        metadata = QuantumPattern.get_metadata()
        assert metadata["id"] == "quantum"
        assert "parameters" in metadata
        assert len(metadata["assumptions"]) > 0
