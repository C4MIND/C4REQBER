"""Tests for src/patterns/library/quantum.py"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from patterns.library.quantum import QuantumConfig, QuantumMethod, QuantumPattern


class TestQuantumConfig:
    def test_defaults(self):
        cfg = QuantumConfig()
        assert cfg.method == QuantumMethod.SCHRODINGER
        assert cfg.n_qubits == 4
        assert cfg.potential_type == "harmonic"

    def test_custom_values(self):
        cfg = QuantumConfig(method=QuantumMethod.VQE, n_qubits=3, steps=100)
        assert cfg.method == QuantumMethod.VQE
        assert cfg.n_qubits == 3
        assert cfg.steps == 100


class TestQuantumPatternInit:
    def test_init_default(self):
        pattern = QuantumPattern()
        assert pattern.config.method == QuantumMethod.SCHRODINGER
        assert pattern.state is not None
        assert pattern.hamiltonian is not None

    def test_init_vqe(self):
        cfg = QuantumConfig(method=QuantumMethod.VQE, n_qubits=2, n_layers=2)
        pattern = QuantumPattern(cfg)
        assert pattern.ansatz_params is not None

    def test_init_circuit(self):
        cfg = QuantumConfig(method=QuantumMethod.CIRCUIT, n_qubits=2, circuit_depth=3)
        pattern = QuantumPattern(cfg)
        assert pattern.circuit_gates is not None

    def test_init_density_matrix(self):
        cfg = QuantumConfig(method=QuantumMethod.DENSITY_MATRIX, n_qubits=2)
        pattern = QuantumPattern(cfg)
        assert pattern.lindblad_ops is not None


class TestQuantumPatternPotential:
    def test_harmonic_potential(self):
        pattern = QuantumPattern(QuantumConfig(potential_type="harmonic"))
        x = np.array([0.0, 1.0, 2.0])
        V = pattern._potential(x)
        np.testing.assert_array_almost_equal(V, [0.0, 0.5, 2.0])

    def test_box_potential(self):
        pattern = QuantumPattern(QuantumConfig(potential_type="box"))
        x = np.array([0.0, 10.0])
        V = pattern._potential(x)
        assert V[0] == 0
        assert V[1] == 1000

    def test_double_well_potential(self):
        pattern = QuantumPattern(QuantumConfig(potential_type="double_well"))
        x = np.array([0.0])
        V = pattern._potential(x)
        assert V[0] > 0

    def test_barrier_potential(self):
        pattern = QuantumPattern(QuantumConfig(potential_type="barrier"))
        x = np.array([0.0, 1.0])
        V = pattern._potential(x)
        assert V[0] == 5.0
        assert V[1] == 0.0

    def test_unknown_potential_defaults_harmonic(self):
        pattern = QuantumPattern(QuantumConfig(potential_type="unknown"))
        x = np.array([1.0])
        V = pattern._potential(x)
        assert V[0] == 0.5


class TestQuantumPatternGates:
    def test_apply_gate_hadamard(self):
        cfg = QuantumConfig(method=QuantumMethod.CIRCUIT, n_qubits=1)
        pattern = QuantumPattern(cfg)
        pattern._apply_gate("H", [0])
        assert np.isclose(np.sum(np.abs(pattern.state) ** 2), 1.0)

    def test_apply_gate_x(self):
        cfg = QuantumConfig(method=QuantumMethod.CIRCUIT, n_qubits=1)
        pattern = QuantumPattern(cfg)
        pattern._apply_gate("X", [0])
        assert np.isclose(np.sum(np.abs(pattern.state) ** 2), 1.0)

    def test_apply_gate_z(self):
        cfg = QuantumConfig(method=QuantumMethod.CIRCUIT, n_qubits=1)
        pattern = QuantumPattern(cfg)
        pattern._apply_gate("Z", [0])
        assert np.isclose(np.sum(np.abs(pattern.state) ** 2), 1.0)

    def test_apply_gate_rz(self):
        cfg = QuantumConfig(method=QuantumMethod.CIRCUIT, n_qubits=1)
        pattern = QuantumPattern(cfg)
        pattern._apply_gate("RZ", [0], angle=np.pi)
        assert np.isclose(np.sum(np.abs(pattern.state) ** 2), 1.0)

    def test_apply_gate_rx(self):
        cfg = QuantumConfig(method=QuantumMethod.CIRCUIT, n_qubits=1)
        pattern = QuantumPattern(cfg)
        pattern._apply_gate("RX", [0], angle=np.pi / 2)
        assert np.isclose(np.sum(np.abs(pattern.state) ** 2), 1.0)

    def test_apply_gate_cnot(self):
        cfg = QuantumConfig(method=QuantumMethod.CIRCUIT, n_qubits=2)
        pattern = QuantumPattern(cfg)
        pattern._apply_gate("CNOT", [0, 1])
        assert np.isclose(np.sum(np.abs(pattern.state) ** 2), 1.0)

    def test_apply_gate_unknown(self):
        cfg = QuantumConfig(method=QuantumMethod.CIRCUIT, n_qubits=1)
        pattern = QuantumPattern(cfg)
        before = pattern.state.copy()
        pattern._apply_gate("UNKNOWN", [0])
        np.testing.assert_array_equal(pattern.state, before)

    def test_expand_single_qubit_gate(self):
        cfg = QuantumConfig(method=QuantumMethod.CIRCUIT, n_qubits=2)
        pattern = QuantumPattern(cfg)
        U = np.array([[0, 1], [1, 0]], dtype=complex)
        full = pattern._expand_single_qubit_gate(U, 0)
        assert full.shape == (4, 4)

    def test_expand_two_qubit_gate(self):
        cfg = QuantumConfig(method=QuantumMethod.CIRCUIT, n_qubits=3)
        pattern = QuantumPattern(cfg)
        U = np.eye(4, dtype=complex)
        full = pattern._expand_two_qubit_gate(U, 0, 1)
        assert full.shape == (8, 8)

    def test_create_cnot_gate(self):
        cfg = QuantumConfig(method=QuantumMethod.CIRCUIT, n_qubits=2)
        pattern = QuantumPattern(cfg)
        U = pattern._create_cnot_gate(0, 1)
        assert U.shape == (4, 4)


class TestQuantumPatternRun:
    def test_run_schrodinger(self):
        cfg = QuantumConfig(method=QuantumMethod.SCHRODINGER, steps=20, n_qubits=2)
        pattern = QuantumPattern(cfg)
        result = pattern.run()
        assert result["method"] == "schrodinger"
        assert "final_state_real" in result
        assert "mean_energy" in result

    def test_run_vqe(self):
        cfg = QuantumConfig(method=QuantumMethod.VQE, steps=20, n_qubits=2, n_layers=1)
        pattern = QuantumPattern(cfg)
        result = pattern.run()
        assert result["method"] == "vqe"
        assert "final_energy" in result
        assert "energy_history" in result

    def test_run_circuit(self):
        cfg = QuantumConfig(method=QuantumMethod.CIRCUIT, steps=10, n_qubits=2, circuit_depth=2)
        pattern = QuantumPattern(cfg)
        result = pattern.run()
        assert result["method"] == "circuit"
        assert "final_probabilities" in result
        assert "circuit_gates" in result

    def test_run_density_matrix(self):
        cfg = QuantumConfig(method=QuantumMethod.DENSITY_MATRIX, steps=20, n_qubits=2)
        pattern = QuantumPattern(cfg)
        result = pattern.run()
        assert result["method"] == "density_matrix"
        assert "final_purity" in result
        assert "final_entropy" in result

    def test_run_with_hypothesis(self):
        cfg = QuantumConfig(steps=10, n_qubits=2)
        pattern = QuantumPattern(cfg)
        result = pattern.run(hypothesis={"text": "test"})
        assert result["method"] == "schrodinger"


class TestQuantumPatternHeisenberg:
    def test_heisenberg_hamiltonian_shape(self):
        cfg = QuantumConfig(method=QuantumMethod.VQE, n_qubits=3)
        pattern = QuantumPattern(cfg)
        H = pattern._heisenberg_hamiltonian(3)
        assert H.shape == (8, 8)

    def test_heisenberg_hermitian(self):
        cfg = QuantumConfig(method=QuantumMethod.VQE, n_qubits=3)
        pattern = QuantumPattern(cfg)
        H = pattern._heisenberg_hamiltonian(3)
        np.testing.assert_allclose(H, H.conj().T, atol=1e-10)


class TestQuantumPatternAnsatz:
    def test_create_ansatz(self):
        cfg = QuantumConfig(method=QuantumMethod.VQE, n_qubits=2, n_layers=1)
        pattern = QuantumPattern(cfg)
        params = np.zeros(4)
        psi = pattern._create_ansatz(params)
        assert len(psi) == 4
        assert np.isclose(np.sum(np.abs(psi) ** 2), 1.0)

    def test_vqe_gradient(self):
        cfg = QuantumConfig(method=QuantumMethod.VQE, n_qubits=2, n_layers=1, learning_rate=0.01)
        pattern = QuantumPattern(cfg)
        pattern.ansatz_params = np.zeros(4)
        grad = pattern._vqe_gradient()
        assert grad.shape == (4,)


class TestQuantumPatternMeasure:
    def test_measure_default(self):
        cfg = QuantumConfig(method=QuantumMethod.SCHRODINGER, n_qubits=2)
        pattern = QuantumPattern(cfg)
        E = pattern._measure()
        assert isinstance(E, float)

    def test_measure_density_matrix(self):
        cfg = QuantumConfig(method=QuantumMethod.DENSITY_MATRIX, n_qubits=2)
        pattern = QuantumPattern(cfg)
        E = pattern._measure()
        assert isinstance(E, float)

    def test_measure_with_observable(self):
        cfg = QuantumConfig(method=QuantumMethod.SCHRODINGER, n_qubits=2)
        pattern = QuantumPattern(cfg)
        obs = np.eye(4)
        E = pattern._measure(obs)
        assert isinstance(E, float)


class TestQuantumPatternStepMethods:
    def test_schrodinger_step(self):
        cfg = QuantumConfig(method=QuantumMethod.SCHRODINGER, steps=2, n_qubits=2)
        pattern = QuantumPattern(cfg)
        before = pattern.state.copy()
        pattern._schrodinger_step()
        assert not np.allclose(pattern.state, before)
        assert np.isclose(np.sum(np.abs(pattern.state) ** 2), 1.0)

    def test_density_matrix_step(self):
        cfg = QuantumConfig(method=QuantumMethod.DENSITY_MATRIX, steps=2, n_qubits=2, dt=0.001)
        pattern = QuantumPattern(cfg)
        before = pattern.state.copy()
        pattern._density_matrix_step()
        assert pattern.state is not None
        assert np.all(np.isfinite(pattern.state))

    def test_circuit_step(self):
        cfg = QuantumConfig(method=QuantumMethod.CIRCUIT, steps=2, n_qubits=2, circuit_depth=2)
        pattern = QuantumPattern(cfg)
        before = pattern.state.copy()
        pattern._circuit_step()
        assert not np.allclose(pattern.state, before)

    def test_vqe_step(self):
        cfg = QuantumConfig(method=QuantumMethod.VQE, steps=2, n_qubits=2, n_layers=1)
        pattern = QuantumPattern(cfg)
        before = pattern.ansatz_params.copy()
        pattern._vqe_step()
        assert not np.allclose(pattern.ansatz_params, before)


class TestQuantumPatternLindblad:
    def test_create_lindblad_operators(self):
        cfg = QuantumConfig(method=QuantumMethod.DENSITY_MATRIX, n_qubits=3)
        pattern = QuantumPattern(cfg)
        ops = pattern._create_lindblad_operators()
        assert len(ops) == 3
        for op in ops:
            assert op.shape == (8, 8)


class TestQuantumPatternMetadata:
    def test_get_metadata(self):
        meta = QuantumPattern.get_metadata()
        assert meta["id"] == "quantum"
        assert "parameters" in meta
        assert "assumptions" in meta
        assert "domain" in meta


class TestQuantumPatternBuildRandomCircuit:
    def test_build_random_circuit(self):
        cfg = QuantumConfig(method=QuantumMethod.CIRCUIT, n_qubits=2, circuit_depth=5)
        pattern = QuantumPattern(cfg)
        gates = pattern._build_random_circuit()
        assert len(gates) <= 5
        for g in gates:
            assert len(g) == 3

    def test_build_random_circuit_gates_in_list(self):
        cfg = QuantumConfig(method=QuantumMethod.CIRCUIT, n_qubits=2, circuit_depth=10, gates=["H", "CNOT"])
        pattern = QuantumPattern(cfg)
        gates = pattern._build_random_circuit()
        for g, _, _ in gates:
            assert g in ["H", "CNOT"]
