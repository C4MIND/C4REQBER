"""Tests for src/simulations/schr_bridge.py."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import numpy as np
import pytest

from simulations.schr_bridge import (
    QEDConfig,
    SchrBridge,
    SchrodingerConfig,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def bridge_unavailable():
    """SchrBridge with availability forced to False."""
    with patch.object(SchrBridge, "_check_availability", return_value=False):
        bridge = SchrBridge(device="cpu")
        bridge._available = False
        bridge._device = "cpu"
        yield bridge


@pytest.fixture
def bridge_available():
    """SchrBridge with mocked jax/schr backend."""
    bridge = SchrBridge(device="cpu")
    bridge._available = True
    bridge._device = "cpu"
    bridge._jax = MagicMock()
    bridge._schr = MagicMock()
    return bridge


@pytest.fixture
def mock_pattern():
    """Mock pattern with PATTERN_ID and run method."""
    pattern = MagicMock()
    pattern.PATTERN_ID = "quantum_dynamics_test"
    pattern.run = MagicMock(return_value={"status": "ok", "source": "pattern"})
    return pattern


# ═══════════════════════════════════════════════════════════════════
# Initialization & Availability
# ═══════════════════════════════════════════════════════════════════


class TestSchrBridgeInit:
    """Test SchrBridge initialization."""

    def test_init_unavailable_no_jax(self):
        with patch("simulations.schr_bridge.logger"):
            bridge = SchrBridge(device="cpu")
            assert bridge._device_preference == "cpu"
            assert bridge.get_device() in ("cpu", "unavailable")

    def test_init_auto_device(self):
        with patch("simulations.schr_bridge.logger"):
            bridge = SchrBridge(device="auto")
            assert bridge._device_preference == "auto"

    def test_available_property(self, bridge_available):
        assert bridge_available.available is True
        assert bridge_available.is_available() is True

    def test_available_property_unavailable(self, bridge_unavailable):
        assert bridge_unavailable.available is False
        assert bridge_unavailable.is_available() is False

    def test_get_device(self, bridge_available):
        assert bridge_available.get_device() == "cpu"

    def test_get_device_unavailable(self, bridge_unavailable):
        assert bridge_unavailable.get_device() == "cpu"

    def test_init_device_with_gpu(self):
        mock_jax = MagicMock()
        mock_jax.devices.return_value = ["gpu:0"]
        bridge = SchrBridge(device="auto")
        with patch.object(bridge, "_jax", mock_jax):
            bridge._init_device()
            assert bridge._device == "gpu"

    def test_init_device_with_tpu(self):
        mock_jax = MagicMock()
        mock_jax.devices.return_value = ["tpu:0"]
        bridge = SchrBridge(device="auto")
        with patch.object(bridge, "_jax", mock_jax):
            bridge._init_device()
            assert bridge._device == "tpu"

    def test_init_device_explicit(self):
        mock_jax = MagicMock()
        bridge = SchrBridge(device="gpu")
        with patch.object(bridge, "_jax", mock_jax):
            bridge._init_device()
            assert bridge._device == "gpu"


# ═══════════════════════════════════════════════════════════════════
# Schrodinger Config Parsing
# ═══════════════════════════════════════════════════════════════════


class TestSchrodingerConfig:
    """Test Schrodinger configuration parsing."""

    def test_parse_defaults(self, bridge_available):
        cfg = bridge_available._parse_schrodinger_config({})
        assert isinstance(cfg, SchrodingerConfig)
        assert cfg.n_points == 128
        assert cfg.domain_size == 10.0
        assert cfg.dt == 0.001
        assert cfg.duration == 1.0
        assert cfg.potential_type == "harmonic"
        assert cfg.potential_strength == 1.0
        assert cfg.initial_state == "gaussian"
        assert cfg.boundary_conditions == "periodic"
        assert cfg.integrate is True

    def test_parse_custom_values(self, bridge_available):
        cfg = bridge_available._parse_schrodinger_config({
            "n_points": 256,
            "domain_size": 20.0,
            "dt": 0.0005,
            "duration": 2.0,
            "potential_type": "barrier",
            "potential_strength": 5.0,
            "initial_state": "plane_wave",
            "boundary_conditions": "reflecting",
            "integrate": False,
        })
        assert cfg.n_points == 256
        assert cfg.domain_size == 20.0
        assert cfg.dt == 0.0005
        assert cfg.duration == 2.0
        assert cfg.potential_type == "barrier"
        assert cfg.potential_strength == 5.0
        assert cfg.initial_state == "plane_wave"
        assert cfg.boundary_conditions == "reflecting"
        assert cfg.integrate is False


# ═══════════════════════════════════════════════════════════════════
# QED Config Parsing
# ═══════════════════════════════════════════════════════════════════


class TestQEDConfig:
    """Test QED configuration parsing."""

    def test_parse_defaults(self, bridge_available):
        cfg = bridge_available._parse_qed_config({})
        assert isinstance(cfg, QEDConfig)
        assert cfg.n_modes == 8
        assert cfg.n_photons_max == 4
        assert cfg.n_levels == 4
        assert cfg.coupling_strength == 1.0
        assert cfg.detuning == 0.0
        assert cfg.dt == 0.01
        assert cfg.duration == 10.0
        assert cfg.initial_state == "ground"

    def test_parse_custom_values(self, bridge_available):
        cfg = bridge_available._parse_qed_config({
            "n_modes": 16,
            "n_photons_max": 8,
            "n_levels": 8,
            "coupling_strength": 2.5,
            "detuning": 0.5,
            "dt": 0.005,
            "duration": 5.0,
            "initial_state": "excited",
        })
        assert cfg.n_modes == 16
        assert cfg.n_photons_max == 8
        assert cfg.n_levels == 8
        assert cfg.coupling_strength == 2.5
        assert cfg.detuning == 0.5
        assert cfg.dt == 0.005
        assert cfg.duration == 5.0
        assert cfg.initial_state == "excited"


# ═══════════════════════════════════════════════════════════════════
# Fallback Schrödinger Simulation
# ═══════════════════════════════════════════════════════════════════


class TestFallbackSchrodinger:
    """Test fallback Schrödinger simulation (no schr/jax)."""

    def test_fallback_integrate_true(self, bridge_unavailable):
        cfg = SchrodingerConfig(n_points=64, domain_size=10.0, dt=0.01, duration=0.1, integrate=True)
        result = bridge_unavailable._fallback_schrodinger(cfg)
        assert result["status"] == "success"
        assert result["engine"] == "schr_fallback"
        assert result["device"] == "cpu"
        assert "wave_function" in result
        assert "probability_density" in result
        assert "trajectory" in result
        assert "energy" in result
        assert "position_expectation" in result
        assert "momentum_expectation" in result
        assert "times" in result
        assert result["potential_type"] == "harmonic"

    def test_fallback_integrate_false(self, bridge_unavailable):
        cfg = SchrodingerConfig(n_points=64, domain_size=10.0, dt=0.01, duration=0.1, integrate=False)
        result = bridge_unavailable._fallback_schrodinger(cfg)
        assert result["status"] == "success"
        assert result["engine"] == "schr_fallback"
        assert "wave_function" in result
        assert "probability_density" in result
        assert "energy" in result
        assert "trajectory" not in result

    def test_fallback_well_potential(self, bridge_unavailable):
        cfg = SchrodingerConfig(potential_type="well", n_points=32, dt=0.01, duration=0.05, integrate=False)
        result = bridge_unavailable._fallback_schrodinger(cfg)
        assert result["status"] == "success"

    def test_fallback_barrier_potential(self, bridge_unavailable):
        cfg = SchrodingerConfig(potential_type="barrier", n_points=32, dt=0.01, duration=0.05, integrate=False)
        result = bridge_unavailable._fallback_schrodinger(cfg)
        assert result["status"] == "success"

    def test_fallback_custom_potential(self, bridge_unavailable):
        cfg = SchrodingerConfig(potential_type="custom", n_points=32, dt=0.01, duration=0.05, integrate=False)
        result = bridge_unavailable._fallback_schrodinger(cfg)
        assert result["status"] == "success"

    def test_run_schrodinger_unavailable(self, bridge_unavailable):
        result = bridge_unavailable.run_schrodinger({"n_points": 32, "duration": 0.05})
        assert result["status"] == "success"
        assert result["engine"] == "schr_fallback"

    def test_run_schrodinger_error_handling(self, bridge_unavailable):
        with patch.object(bridge_unavailable, "_parse_schrodinger_config", side_effect=TypeError("bad config")):
            result = bridge_unavailable.run_schrodinger({})
            assert result["status"] == "error"
            assert "bad config" in result["message"]
            assert result["engine"] == "schr"


# ═══════════════════════════════════════════════════════════════════
# Fallback QED Simulation
# ═══════════════════════════════════════════════════════════════════


class TestFallbackQED:
    """Test fallback QED simulation."""

    def test_fallback_ground_state(self, bridge_unavailable):
        cfg = QEDConfig(initial_state="ground", duration=0.1, dt=0.01)
        result = bridge_unavailable._fallback_qed(cfg)
        assert result["status"] == "success"
        assert result["engine"] == "schr_fallback"
        assert "photon_number" in result
        assert "atomic_population" in result
        assert "entanglement_entropy" in result

    def test_fallback_excited_state(self, bridge_unavailable):
        cfg = QEDConfig(initial_state="excited", duration=0.1, dt=0.01)
        result = bridge_unavailable._fallback_qed(cfg)
        assert result["status"] == "success"

    def test_fallback_coherent_state(self, bridge_unavailable):
        cfg = QEDConfig(initial_state="coherent", duration=0.1, dt=0.01)
        result = bridge_unavailable._fallback_qed(cfg)
        assert result["status"] == "success"

    def test_fallback_zero_detuning(self, bridge_unavailable):
        cfg = QEDConfig(detuning=0.0, duration=0.1, dt=0.01)
        result = bridge_unavailable._fallback_qed(cfg)
        assert result["status"] == "success"

    def test_fallback_nonzero_detuning(self, bridge_unavailable):
        cfg = QEDConfig(detuning=1.0, duration=0.1, dt=0.01)
        result = bridge_unavailable._fallback_qed(cfg)
        assert result["status"] == "success"

    def test_run_qed_unavailable(self, bridge_unavailable):
        result = bridge_unavailable.run_qed({"duration": 0.1, "dt": 0.01})
        assert result["status"] == "success"
        assert result["engine"] == "schr_fallback"

    def test_run_qed_error_handling(self, bridge_unavailable):
        with patch.object(bridge_unavailable, "_parse_qed_config", side_effect=TypeError("bad qed")):
            result = bridge_unavailable.run_qed({})
            assert result["status"] == "error"
            assert "bad qed" in result["message"]


# ═══════════════════════════════════════════════════════════════════
# Initial State Creation
# ═══════════════════════════════════════════════════════════════════


class TestInitialStateCreation:
    """Test initial wave function creation."""

    def test_create_initial_state_numpy_gaussian(self, bridge_unavailable):
        cfg = SchrodingerConfig(initial_state="gaussian", n_points=128, domain_size=10.0)
        x = np.linspace(-5, 5, 128)
        dx = 10.0 / 128
        psi = bridge_unavailable._create_initial_state_numpy(cfg, x, dx)
        assert psi.shape == (128,)
        assert np.isclose(np.sum(np.abs(psi) ** 2) * dx, 1.0, rtol=0.1)

    def test_create_initial_state_numpy_plane_wave(self, bridge_unavailable):
        cfg = SchrodingerConfig(initial_state="plane_wave", n_points=128, domain_size=10.0)
        x = np.linspace(-5, 5, 128)
        dx = 10.0 / 128
        psi = bridge_unavailable._create_initial_state_numpy(cfg, x, dx)
        assert psi.shape == (128,)

    def test_create_initial_state_numpy_coherent(self, bridge_unavailable):
        cfg = SchrodingerConfig(initial_state="coherent", n_points=128, domain_size=10.0)
        x = np.linspace(-5, 5, 128)
        dx = 10.0 / 128
        psi = bridge_unavailable._create_initial_state_numpy(cfg, x, dx)
        assert psi.shape == (128,)

    def test_create_initial_state_numpy_unknown(self, bridge_unavailable):
        cfg = SchrodingerConfig(initial_state="unknown", n_points=128, domain_size=10.0)
        x = np.linspace(-5, 5, 128)
        dx = 10.0 / 128
        psi = bridge_unavailable._create_initial_state_numpy(cfg, x, dx)
        assert psi.shape == (128,)


# ═══════════════════════════════════════════════════════════════════
# Pattern Acceleration
# ═══════════════════════════════════════════════════════════════════


class TestAcceleratePattern:
    """Test pattern acceleration logic."""

    def test_accelerate_unavailable(self, bridge_unavailable, mock_pattern):
        result = bridge_unavailable.accelerate_pattern(mock_pattern, {})
        assert result["source"] == "pattern"
        mock_pattern.run.assert_called_once()

    def test_classify_quantum(self, bridge_available):
        assert bridge_available._classify_pattern("schrodinger_test") == "quantum"
        assert bridge_available._classify_pattern("quantum_dynamics") == "quantum"
        assert bridge_available._classify_pattern("wave_function") == "quantum"

    def test_classify_qed(self, bridge_available):
        assert bridge_available._classify_pattern("qed_test") == "qed"
        assert bridge_available._classify_pattern("cavity_qed") == "qed"
        assert bridge_available._classify_pattern("jaynes_cummings") == "qed"

    def test_classify_quantum_computing(self, bridge_available):
        assert bridge_available._classify_pattern("quantum_circuit") == "quantum_computing"
        assert bridge_available._classify_pattern("qubit_dynamics") == "quantum_computing"

    def test_classify_unknown(self, bridge_available):
        assert bridge_available._classify_pattern("random_pattern") == "unknown"

    def test_accelerate_quantum_pattern(self, bridge_available, mock_pattern):
        mock_pattern.PATTERN_ID = "quantum_dynamics_test"
        mock_pattern.config = MagicMock()
        mock_pattern.config.n_points = 64
        mock_pattern.config.dt = 0.01
        mock_pattern.config.t_max = 0.1
        mock_pattern.config.potential = "harmonic"

        with patch.object(bridge_available, "run_schrodinger", return_value={"status": "success"}):
            result = bridge_available.accelerate_pattern(mock_pattern, {"duration": 0.1})
            assert result["accelerated_by"] == "schr"
            assert result["pattern_id"] == "quantum_dynamics_test"

    def test_accelerate_qed_pattern(self, bridge_available, mock_pattern):
        mock_pattern.PATTERN_ID = "cavity_qed_test"
        mock_pattern.config = MagicMock()
        mock_pattern.config.coupling = 1.5
        mock_pattern.config.modes = 4

        with patch.object(bridge_available, "run_qed", return_value={"status": "success"}):
            result = bridge_available.accelerate_pattern(mock_pattern, {})
            assert result["accelerated_by"] == "schr"

    def test_accelerate_qc_pattern(self, bridge_available, mock_pattern):
        mock_pattern.PATTERN_ID = "quantum_circuit_test"
        result = bridge_available.accelerate_pattern(mock_pattern, {})
        mock_pattern.run.assert_called_once()

    def test_accelerate_unknown_pattern(self, bridge_available, mock_pattern):
        mock_pattern.PATTERN_ID = "random_pattern"
        result = bridge_available.accelerate_pattern(mock_pattern, {})
        mock_pattern.run.assert_called_once()


# ═══════════════════════════════════════════════════════════════════
# Execute Schrödinger (with mocked backend)
# ═══════════════════════════════════════════════════════════════════


class TestExecuteSchrodinger:
    """Test _execute_schrodinger with mocked schr backend."""

    def test_execute_schrodinger_integrate_true(self, bridge_available):
        cfg = SchrodingerConfig(n_points=32, domain_size=10.0, dt=0.01, duration=0.05, integrate=True)
        mock_solver = MagicMock()
        mock_psi = np.ones(32, dtype=complex) / np.sqrt(32)
        mock_solver.step.return_value = mock_psi
        mock_solver.energy.return_value = 1.0
        mock_solver.position_expectation.return_value = 0.5
        mock_solver.momentum_expectation.return_value = 0.1

        mock_schr_mod = MagicMock()
        mock_schr_mod.SchrodingerSolver.return_value = mock_solver
        mock_jnp = MagicMock()
        mock_jnp.linspace.return_value = np.linspace(-5, 5, 32)

        with patch.dict("sys.modules", {"schr": mock_schr_mod, "jax": MagicMock(), "jax.numpy": mock_jnp}):
            result = bridge_available._execute_schrodinger(cfg)
            assert result["status"] == "success"
            assert result["engine"] == "schr"
            assert "wave_function" in result
            assert "trajectory" in result

    def test_execute_schrodinger_integrate_false(self, bridge_available):
        cfg = SchrodingerConfig(n_points=32, domain_size=10.0, dt=0.01, duration=0.05, integrate=False)
        mock_solver = MagicMock()
        mock_psi = np.ones(32, dtype=complex) / np.sqrt(32)
        mock_solver.step.return_value = mock_psi
        mock_solver.energy.return_value = 1.0

        mock_schr_mod = MagicMock()
        mock_schr_mod.SchrodingerSolver.return_value = mock_solver
        mock_jnp = MagicMock()
        mock_jnp.linspace.return_value = np.linspace(-5, 5, 32)

        with patch.dict("sys.modules", {"schr": mock_schr_mod, "jax": MagicMock(), "jax.numpy": mock_jnp}):
            result = bridge_available._execute_schrodinger(cfg)
            assert result["status"] == "success"
            assert "trajectory" not in result

    def test_execute_schrodinger_no_schr(self, bridge_available):
        bridge_available._schr = None
        cfg = SchrodingerConfig(n_points=32, dt=0.01, duration=0.05)
        result = bridge_available._execute_schrodinger(cfg)
        assert result["status"] == "error"
        assert "not available" in result["message"]


# ═══════════════════════════════════════════════════════════════════
# Execute QED (with mocked backend)
# ═══════════════════════════════════════════════════════════════════


class TestExecuteQED:
    """Test _execute_qed with mocked schr backend."""

    def test_execute_qed_success(self, bridge_available):
        cfg = QEDConfig(n_modes=2, n_photons_max=2, n_levels=2, duration=0.05, dt=0.01)
        mock_solver = MagicMock()
        mock_solver.step.return_value = np.eye(4)
        mock_solver.photon_number.return_value = 1.0
        mock_solver.atomic_population.return_value = np.array([0.5, 0.5])
        mock_solver.entanglement_entropy.return_value = 0.5
        mock_solver.purity.return_value = 1.0

        mock_schr_mod = MagicMock()
        mock_schr_mod.QEDSolver.return_value = mock_solver
        mock_jnp = MagicMock()
        mock_jnp.zeros.return_value = np.zeros(16, dtype=complex)
        mock_jnp.outer.return_value = np.eye(16)
        mock_jnp.conj.return_value = np.zeros(16, dtype=complex)

        with patch.dict("sys.modules", {"schr": mock_schr_mod, "jax": MagicMock(), "jax.numpy": mock_jnp}):
            result = bridge_available._execute_qed(cfg)
            assert result["status"] == "success"
            assert result["engine"] == "schr"
            assert "photon_number" in result
            assert "atomic_population" in result

    def test_execute_qed_no_schr(self, bridge_available):
        bridge_available._schr = None
        cfg = QEDConfig()
        result = bridge_available._execute_qed(cfg)
        assert result["status"] == "error"
        assert "not available" in result["message"]


# ═══════════════════════════════════════════════════════════════════
# Benchmark
# ═══════════════════════════════════════════════════════════════════


class TestBenchmark:
    """Test benchmark method."""

    def test_benchmark_not_available(self, bridge_unavailable):
        result = bridge_unavailable.benchmark_legacy_vs_schr("quantum_test", {})
        assert result["schr_available"] is False
        assert result["speedup"] == 1.0

    def test_benchmark_available(self, bridge_available):
        with patch.object(bridge_available, "run_schrodinger", return_value={"status": "success"}):
            result = bridge_available.benchmark_legacy_vs_schr("quantum_test", {})
            assert result["schr_available"] is True
            assert "speedup" in result

    def test_benchmark_qed(self, bridge_available):
        with patch.object(bridge_available, "run_qed", return_value={"status": "success"}):
            result = bridge_available.benchmark_legacy_vs_schr("qed_test", {})
            assert result["schr_available"] is True


# ═══════════════════════════════════════════════════════════════════
# Metadata
# ═══════════════════════════════════════════════════════════════════


class TestMetadata:
    """Test get_metadata classmethod."""

    def test_get_metadata(self):
        meta = SchrBridge.get_metadata()
        assert meta["name"] == "Schr Bridge"
        assert meta["license"] == "MIT"
        assert "github" in meta
        assert "capabilities" in meta
        assert "limitations" in meta


# ═══════════════════════════════════════════════════════════════════
# Create QED Initial State
# ═══════════════════════════════════════════════════════════════════


class TestCreateQEDInitialState:
    """Test _create_qed_initial_state with mocked jax."""

    def test_ground_state(self, bridge_available):
        mock_jnp = MagicMock()
        mock_jnp.zeros.return_value = np.zeros(8, dtype=complex)
        mock_jnp.outer.return_value = np.eye(8)
        mock_jnp.conj.return_value = np.zeros(8, dtype=complex)
        with patch.dict("sys.modules", {"jax": MagicMock(), "jax.numpy": mock_jnp}):
            cfg = QEDConfig(n_modes=1, n_photons_max=1, n_levels=2, initial_state="ground")
            result = bridge_available._create_qed_initial_state(cfg)
            assert result is not None

    def test_excited_state(self, bridge_available):
        mock_jnp = MagicMock()
        mock_jnp.zeros.return_value = np.zeros(8, dtype=complex)
        with patch.dict("sys.modules", {"jax": MagicMock(), "jax.numpy": mock_jnp}):
            cfg = QEDConfig(n_modes=1, n_photons_max=1, n_levels=2, initial_state="excited")
            result = bridge_available._create_qed_initial_state(cfg)
            assert result is not None

    def test_coherent_state(self, bridge_available):
        mock_jnp = MagicMock()
        mock_jnp.ones.return_value = np.ones(8, dtype=complex)
        with patch.dict("sys.modules", {"jax": MagicMock(), "jax.numpy": mock_jnp}):
            cfg = QEDConfig(n_modes=1, n_photons_max=1, n_levels=2, initial_state="coherent")
            result = bridge_available._create_qed_initial_state(cfg)
            assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
