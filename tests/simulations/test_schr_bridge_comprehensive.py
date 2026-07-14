"""Comprehensive tests for SchrBridge — quantum mechanics engine adapter."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from simulations.schr_bridge import (
    BasePattern,
    QEDConfig,
    SchrBridge,
    SchrodingerConfig,
)


class MockQuantumPattern:
    """Mock pattern for quantum acceleration testing."""

    PATTERN_ID = "schrodinger"
    config = None

    def run(self, hypothesis=None):
        return {"result": "fallback", "pattern": self.PATTERN_ID}


class MockQEDPattern:
    """Mock pattern for QED acceleration testing."""

    PATTERN_ID = "cavity_qed"
    config = None

    def run(self, hypothesis=None):
        return {"result": "fallback"}


class MockQCPattern:
    """Mock pattern for quantum computing acceleration testing."""

    PATTERN_ID = "quantum_circuit"
    config = None

    def run(self, hypothesis=None):
        return {"result": "fallback"}


class TestSchrodingerConfig:
    """Tests for SchrodingerConfig dataclass."""

    def test_default_config(self):
        cfg = SchrodingerConfig()
        assert cfg.n_points == 128
        assert cfg.domain_size == 10.0
        assert cfg.dt == 0.001
        assert cfg.duration == 1.0
        assert cfg.potential_type == "harmonic"
        assert cfg.potential_strength == 1.0
        assert cfg.initial_state == "gaussian"
        assert cfg.boundary_conditions == "periodic"
        assert cfg.integrate is True

    def test_custom_config(self):
        cfg = SchrodingerConfig(n_points=256, domain_size=20.0, potential_type="well")
        assert cfg.n_points == 256
        assert cfg.domain_size == 20.0
        assert cfg.potential_type == "well"


class TestQEDConfig:
    """Tests for QEDConfig dataclass."""

    def test_default_config(self):
        cfg = QEDConfig()
        assert cfg.n_modes == 8
        assert cfg.n_photons_max == 4
        assert cfg.n_levels == 4
        assert cfg.coupling_strength == 1.0
        assert cfg.detuning == 0.0
        assert cfg.dt == 0.01
        assert cfg.duration == 10.0
        assert cfg.initial_state == "ground"

    def test_custom_config(self):
        cfg = QEDConfig(n_modes=16, coupling_strength=2.0, detuning=0.5)
        assert cfg.n_modes == 16
        assert cfg.coupling_strength == 2.0
        assert cfg.detuning == 0.5


class TestSchrBridgeInit:
    """Tests for SchrBridge initialization."""

    def test_init_default_device(self):
        bridge = SchrBridge()
        assert bridge._device_preference == "auto"

    def test_init_custom_device(self):
        bridge = SchrBridge(device="cpu")
        assert bridge._device_preference == "cpu"

    def test_init_unavailable_without_jax(self):
        with patch.dict("sys.modules", {"jax": None}):
            bridge = SchrBridge()
            assert not bridge.is_available()

    def test_check_availability_no_schr(self):
        # Test that _check_availability returns False when schr is not installed
        bridge = SchrBridge()
        with patch.object(bridge, "_check_availability", return_value=False):
            assert not bridge.is_available()

    def test_init_device_cpu(self):
        mock_jax = MagicMock()
        mock_jax.devices.return_value = ["cpu:0"]
        mock_schr = MagicMock()
        with patch.dict("sys.modules", {"jax": mock_jax, "schr": mock_schr}):
            bridge = SchrBridge(device="cpu")
            assert bridge._device == "cpu"

    def test_init_device_tpu(self):
        mock_jax = MagicMock()
        mock_jax.devices.return_value = ["tpu:0"]
        mock_schr = MagicMock()
        with patch.dict("sys.modules", {"jax": mock_jax, "schr": mock_schr}):
            bridge = SchrBridge(device="tpu")
            assert bridge._device == "tpu"


class TestSchrBridgeAvailability:
    """Tests for availability and device queries."""

    def test_available_property_false(self):
        bridge = SchrBridge()
        assert isinstance(bridge.available, bool)

    def test_is_available_returns_bool(self):
        bridge = SchrBridge()
        assert isinstance(bridge.is_available(), bool)

    def test_get_device_unavailable(self):
        bridge = SchrBridge()
        device = bridge.get_device()
        assert device in ("unavailable", "cpu", "gpu", "tpu")


class TestSchrBridgeParseConfig:
    """Tests for configuration parsing."""

    def test_parse_schrodinger_config_defaults(self):
        bridge = SchrBridge()
        cfg = bridge._parse_schrodinger_config({})
        assert cfg.n_points == 128
        assert cfg.domain_size == 10.0
        assert cfg.potential_type == "harmonic"

    def test_parse_schrodinger_config_custom(self):
        bridge = SchrBridge()
        cfg = bridge._parse_schrodinger_config({
            "n_points": 64,
            "domain_size": 5.0,
            "dt": 0.01,
            "duration": 2.0,
            "potential_type": "barrier",
            "potential_strength": 2.0,
            "initial_state": "plane_wave",
            "boundary_conditions": "reflecting",
            "integrate": False,
        })
        assert cfg.n_points == 64
        assert cfg.domain_size == 5.0
        assert cfg.dt == 0.01
        assert cfg.duration == 2.0
        assert cfg.potential_type == "barrier"
        assert cfg.potential_strength == 2.0
        assert cfg.initial_state == "plane_wave"
        assert cfg.boundary_conditions == "reflecting"
        assert cfg.integrate is False

    def test_parse_qed_config_defaults(self):
        bridge = SchrBridge()
        cfg = bridge._parse_qed_config({})
        assert cfg.n_modes == 8
        assert cfg.coupling_strength == 1.0

    def test_parse_qed_config_custom(self):
        bridge = SchrBridge()
        cfg = bridge._parse_qed_config({
            "n_modes": 4,
            "n_photons_max": 2,
            "n_levels": 3,
            "coupling_strength": 0.5,
            "detuning": 0.1,
            "dt": 0.005,
            "duration": 5.0,
            "initial_state": "excited",
        })
        assert cfg.n_modes == 4
        assert cfg.n_photons_max == 2
        assert cfg.n_levels == 3
        assert cfg.coupling_strength == 0.5
        assert cfg.detuning == 0.1
        assert cfg.initial_state == "excited"


class TestSchrBridgeRunSchrodinger:
    """Tests for run_schrodinger method."""

    def test_run_schrodinger_unavailable(self):
        bridge = SchrBridge()
        bridge._available = False
        result = bridge.run_schrodinger({"n_points": 32, "duration": 0.1})
        assert result["status"] == "success"  # fallback
        assert result["engine"] == "schr_fallback"

    def test_run_schrodinger_fallback_integration(self):
        bridge = SchrBridge()
        bridge._available = False
        result = bridge.run_schrodinger({
            "n_points": 32,
            "domain_size": 5.0,
            "dt": 0.01,
            "duration": 0.1,
            "potential_type": "harmonic",
            "integrate": True,
        })
        assert result["status"] == "success"
        assert "trajectory" in result
        assert "energy" in result
        assert "times" in result

    def test_run_schrodinger_fallback_single_step(self):
        bridge = SchrBridge()
        bridge._available = False
        result = bridge.run_schrodinger({
            "n_points": 32,
            "domain_size": 5.0,
            "dt": 0.01,
            "duration": 0.1,
            "potential_type": "well",
            "integrate": False,
        })
        assert result["status"] == "success"
        assert "wave_function" in result
        assert "energy" in result

    def test_run_schrodinger_error_handling(self):
        bridge = SchrBridge()
        # Force an error by passing invalid config that causes issues
        with patch.object(bridge, "_parse_schrodinger_config", side_effect=TypeError("bad config")):
            result = bridge.run_schrodinger({})
            assert result["status"] == "error"
            assert "bad config" in result["message"]

    def test_run_schrodinger_execute_error(self):
        bridge = SchrBridge()
        bridge._available = True
        bridge._schr = MagicMock()
        with patch.object(bridge, "_execute_schrodinger", side_effect=RuntimeError("exec error")):
            result = bridge.run_schrodinger({"n_points": 32, "duration": 0.1})
            assert result["status"] == "error"
            assert "exec error" in result["message"]


class TestSchrBridgeRunQED:
    """Tests for run_qed method."""

    def test_run_qed_unavailable(self):
        bridge = SchrBridge()
        bridge._available = False
        result = bridge.run_qed({"n_modes": 2, "duration": 1.0})
        assert result["status"] == "success"  # fallback
        assert result["engine"] == "schr_fallback"

    def test_run_qed_fallback(self):
        bridge = SchrBridge()
        bridge._available = False
        result = bridge.run_qed({
            "n_modes": 2,
            "n_photons_max": 2,
            "dt": 0.1,
            "duration": 1.0,
            "initial_state": "ground",
        })
        assert result["status"] == "success"
        assert "photon_number" in result
        assert "atomic_population" in result
        assert "entanglement_entropy" in result

    def test_run_qed_error_handling(self):
        bridge = SchrBridge()
        with patch.object(bridge, "_parse_qed_config", side_effect=RuntimeError("qed error")):
            result = bridge.run_qed({})
            assert result["status"] == "error"
            assert "qed error" in result["message"]

    def test_run_qed_execute_error(self):
        bridge = SchrBridge()
        bridge._available = True
        bridge._schr = MagicMock()
        with patch.object(bridge, "_execute_qed", side_effect=RuntimeError("exec error")):
            result = bridge.run_qed({"n_modes": 2, "duration": 1.0})
            assert result["status"] == "error"
            assert "exec error" in result["message"]


class TestSchrBridgeFallbackMethods:
    """Tests for fallback simulation methods."""

    def test_fallback_schrodinger_harmonic(self):
        bridge = SchrBridge()
        cfg = SchrodingerConfig(
            n_points=32,
            domain_size=5.0,
            dt=0.01,
            duration=0.1,
            potential_type="harmonic",
            integrate=True,
        )
        result = bridge._fallback_schrodinger(cfg)
        assert result["status"] == "success"
        assert result["engine"] == "schr_fallback"
        assert result["potential_type"] == "harmonic"

    def test_fallback_schrodinger_well(self):
        bridge = SchrBridge()
        cfg = SchrodingerConfig(
            n_points=32,
            domain_size=5.0,
            dt=0.01,
            duration=0.1,
            potential_type="well",
            integrate=True,
        )
        result = bridge._fallback_schrodinger(cfg)
        assert result["status"] == "success"

    def test_fallback_schrodinger_barrier(self):
        bridge = SchrBridge()
        cfg = SchrodingerConfig(
            n_points=32,
            domain_size=5.0,
            dt=0.01,
            duration=0.1,
            potential_type="barrier",
            integrate=False,
        )
        result = bridge._fallback_schrodinger(cfg)
        assert result["status"] == "success"

    def test_fallback_schrodinger_custom(self):
        bridge = SchrBridge()
        cfg = SchrodingerConfig(
            n_points=32,
            domain_size=5.0,
            dt=0.01,
            duration=0.1,
            potential_type="custom",
            integrate=True,
        )
        result = bridge._fallback_schrodinger(cfg)
        assert result["status"] == "success"

    def test_fallback_qed_ground(self):
        bridge = SchrBridge()
        cfg = QEDConfig(n_modes=2, dt=0.1, duration=1.0, initial_state="ground")
        result = bridge._fallback_qed(cfg)
        assert result["status"] == "success"
        assert result["engine"] == "schr_fallback"

    def test_fallback_qed_excited(self):
        bridge = SchrBridge()
        cfg = QEDConfig(n_modes=2, dt=0.1, duration=1.0, initial_state="excited")
        result = bridge._fallback_qed(cfg)
        assert result["status"] == "success"

    def test_fallback_qed_coherent(self):
        bridge = SchrBridge()
        cfg = QEDConfig(n_modes=2, dt=0.1, duration=1.0, initial_state="coherent")
        result = bridge._fallback_qed(cfg)
        assert result["status"] == "success"

    def test_fallback_qed_with_detuning(self):
        bridge = SchrBridge()
        cfg = QEDConfig(n_modes=2, dt=0.1, duration=1.0, detuning=0.5, initial_state="ground")
        result = bridge._fallback_qed(cfg)
        assert result["status"] == "success"

    def test_fallback_qed_resonant(self):
        bridge = SchrBridge()
        cfg = QEDConfig(n_modes=2, dt=0.1, duration=1.0, detuning=0.0, initial_state="ground")
        result = bridge._fallback_qed(cfg)
        assert result["status"] == "success"


class TestSchrBridgeInitialStates:
    """Tests for initial state creation methods."""

    def test_create_initial_state_numpy_gaussian(self):
        bridge = SchrBridge()
        cfg = SchrodingerConfig(n_points=32, domain_size=5.0, initial_state="gaussian")
        x = np.linspace(-2.5, 2.5, 32)
        dx = 5.0 / 32
        psi = bridge._create_initial_state_numpy(cfg, x, dx)
        assert len(psi) == 32
        assert len(psi) == 32
        # Check normalization
        assert abs(np.sum(np.abs(psi) ** 2) * dx - 1.0) < 1e-6

    def test_create_initial_state_numpy_plane_wave(self):
        bridge = SchrBridge()
        cfg = SchrodingerConfig(n_points=32, domain_size=5.0, initial_state="plane_wave")
        x = np.linspace(-2.5, 2.5, 32)
        dx = 5.0 / 32
        psi = bridge._create_initial_state_numpy(cfg, x, dx)
        assert len(psi) == 32
        assert len(psi) == 32

    def test_create_initial_state_numpy_coherent(self):
        bridge = SchrBridge()
        cfg = SchrodingerConfig(n_points=32, domain_size=5.0, initial_state="coherent")
        x = np.linspace(-2.5, 2.5, 32)
        dx = 5.0 / 32
        psi = bridge._create_initial_state_numpy(cfg, x, dx)
        assert len(psi) == 32
        assert len(psi) == 32

    def test_create_initial_state_numpy_default(self):
        bridge = SchrBridge()
        cfg = SchrodingerConfig(n_points=32, domain_size=5.0, initial_state="unknown")
        x = np.linspace(-2.5, 2.5, 32)
        dx = 5.0 / 32
        psi = bridge._create_initial_state_numpy(cfg, x, dx)
        assert len(psi) == 32
        assert len(psi) == 32


class TestSchrBridgePatternAcceleration:
    """Tests for pattern acceleration."""

    def test_classify_pattern_quantum(self):
        bridge = SchrBridge()
        assert bridge._classify_pattern("schrodinger") == "quantum"
        assert bridge._classify_pattern("quantum_dynamics") == "quantum"
        assert bridge._classify_pattern("harmonic_oscillator") == "quantum"

    def test_classify_pattern_qed(self):
        bridge = SchrBridge()
        assert bridge._classify_pattern("qed") == "qed"
        assert bridge._classify_pattern("cavity_qed") == "qed"
        assert bridge._classify_pattern("jaynes_cummings") == "qed"

    def test_classify_pattern_quantum_computing(self):
        bridge = SchrBridge()
        assert bridge._classify_pattern("quantum_circuit") == "quantum_computing"
        assert bridge._classify_pattern("qubit_dynamics") == "quantum_computing"
        assert bridge._classify_pattern("entanglement") == "quantum_computing"

    def test_classify_pattern_unknown(self):
        bridge = SchrBridge()
        assert bridge._classify_pattern("classical_mechanics") == "unknown"
        assert bridge._classify_pattern("") == "unknown"

    def test_accelerate_pattern_not_available(self):
        bridge = SchrBridge()
        bridge._available = False
        pattern = MockQuantumPattern()
        result = pattern.run({})
        # When not available, should call pattern.run
        accel_result = bridge.accelerate_pattern(pattern, {})
        assert accel_result == result

    def test_accelerate_pattern_quantum(self):
        bridge = SchrBridge()
        bridge._available = True
        bridge._device = "cpu"
        pattern = MockQuantumPattern()
        with patch.object(bridge, "run_schrodinger", return_value={"status": "success"}) as mock_run:
            result = bridge.accelerate_pattern(pattern, {"n_points": 32})
            assert result["pattern_id"] == "schrodinger"
            assert result["accelerated_by"] == "schr"
            mock_run.assert_called_once()

    def test_accelerate_pattern_qed(self):
        bridge = SchrBridge()
        bridge._available = True
        pattern = MockQEDPattern()
        with patch.object(bridge, "run_qed", return_value={"status": "success"}) as mock_run:
            result = bridge.accelerate_pattern(pattern, {"n_modes": 2})
            assert result["pattern_id"] == "cavity_qed"
            assert result["accelerated_by"] == "schr"
            mock_run.assert_called_once()

    def test_accelerate_pattern_qc(self):
        bridge = SchrBridge()
        bridge._available = True
        pattern = MockQCPattern()
        result = bridge.accelerate_pattern(pattern, {})
        assert result["result"] == "fallback"

    def test_accelerate_pattern_unknown(self):
        bridge = SchrBridge()
        bridge._available = True
        pattern = MockQuantumPattern()
        pattern.PATTERN_ID = "classical"
        result = bridge.accelerate_pattern(pattern, {})
        assert result["result"] == "fallback"

    def test_accelerate_qed_with_config(self):
        bridge = SchrBridge()
        bridge._available = True
        pattern = MockQEDPattern()
        pattern.config = MagicMock()
        pattern.config.coupling = 0.5
        pattern.config.modes = 4
        with patch.object(bridge, "run_qed", return_value={"status": "success"}) as mock_run:
            result = bridge._accelerate_qed_pattern(pattern, {})
            call_args = mock_run.call_args[0][0]
            assert call_args["coupling_strength"] == 0.5
            assert call_args["n_modes"] == 4


class TestSchrBridgeBenchmark:
    """Tests for benchmark method."""

    def test_benchmark_legacy_vs_schr_not_available(self):
        bridge = SchrBridge()
        bridge._available = False
        result = bridge.benchmark_legacy_vs_schr("schrodinger", {})
        assert result["schr_available"] is False
        assert result["speedup"] == 1.0
        assert "not installed" in result["message"]

    def test_benchmark_legacy_vs_schr_available(self):
        bridge = SchrBridge()
        bridge._available = True
        bridge._device = "cpu"
        with patch.object(bridge, "run_schrodinger", return_value={"status": "success"}):
            result = bridge.benchmark_legacy_vs_schr("schrodinger", {"n_points": 32})
            assert result["schr_available"] is True
            assert "legacy_time" in result
            assert "schr_time" in result
            assert "speedup" in result

    def test_benchmark_legacy_vs_schr_qed(self):
        bridge = SchrBridge()
        bridge._available = True
        bridge._device = "cpu"
        with patch.object(bridge, "run_qed", return_value={"status": "success"}):
            result = bridge.benchmark_legacy_vs_schr("cavity_qed", {"n_modes": 2})
            assert result["schr_available"] is True


class TestSchrBridgeMetadata:
    """Tests for metadata method."""

    def test_get_metadata(self):
        metadata = SchrBridge.get_metadata()
        assert metadata["name"] == "Schr Bridge"
        assert metadata["license"] == "MIT"
        assert "github" in metadata
        assert "capabilities" in metadata
        assert "limitations" in metadata


class TestSchrBridgePatternTypes:
    """Tests for pattern type constants."""

    def test_quantum_patterns(self):
        assert "schrodinger" in SchrBridge.PATTERN_TYPES_QUANTUM
        assert "quantum_dynamics" in SchrBridge.PATTERN_TYPES_QUANTUM
        assert "harmonic_oscillator" in SchrBridge.PATTERN_TYPES_QUANTUM

    def test_qed_patterns(self):
        assert "qed" in SchrBridge.PATTERN_TYPES_QED
        assert "cavity_qed" in SchrBridge.PATTERN_TYPES_QED
        assert "jaynes_cummings" in SchrBridge.PATTERN_TYPES_QED

    def test_quantum_computing_patterns(self):
        assert "quantum_circuit" in SchrBridge.PATTERN_TYPES_QUANTUM_COMPUTING
        assert "qubit_dynamics" in SchrBridge.PATTERN_TYPES_QUANTUM_COMPUTING
        assert "entanglement" in SchrBridge.PATTERN_TYPES_QUANTUM_COMPUTING
