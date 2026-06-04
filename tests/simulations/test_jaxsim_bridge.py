"""Tests for src/simulations/jaxsim_bridge.py."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import numpy as np
import pytest


# Skip if optional dependency not available
try:
    import jax
    HAS_JAX = True
except ImportError:
    HAS_JAX = False

pytestmark = pytest.mark.skipif(not HAS_JAX, reason="jax not installed")

from simulations.jaxsim_bridge import (
    InverseDynamicsConfig,
    JaxSimBridge,
    RigidBodyConfig,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def bridge_unavailable():
    """JaxSimBridge with availability forced to False."""
    with patch.object(JaxSimBridge, "_check_availability", return_value=False):
        bridge = JaxSimBridge(device="cpu")
        bridge._available = False
        bridge._device = "cpu"
        yield bridge


@pytest.fixture
def bridge_available():
    """JaxSimBridge with mocked backend."""
    bridge = JaxSimBridge(device="cpu")
    bridge._available = True
    bridge._device = "cpu"
    bridge._jax = MagicMock()
    bridge._jaxsim = MagicMock()
    return bridge


@pytest.fixture
def mock_pattern():
    """Mock pattern with PATTERN_ID and run method."""
    pattern = MagicMock()
    pattern.PATTERN_ID = "robot_arm_test"
    pattern.run = MagicMock(return_value={"status": "ok", "source": "pattern"})
    return pattern


# ═══════════════════════════════════════════════════════════════════
# Initialization & Availability
# ═══════════════════════════════════════════════════════════════════


class TestJaxSimBridgeInit:
    """Test JaxSimBridge initialization."""

    def test_init_default(self):
        with patch.object(JaxSimBridge, "_check_availability", return_value=False):
            bridge = JaxSimBridge()
            assert bridge._device_preference == "auto"

    def test_init_explicit_device(self):
        with patch.object(JaxSimBridge, "_check_availability", return_value=False):
            bridge = JaxSimBridge(device="gpu")
            assert bridge._device_preference == "gpu"

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
        bridge = JaxSimBridge(device="auto")
        with patch.object(bridge, "_jax", mock_jax):
            bridge._init_device()
            assert bridge._device == "gpu"

    def test_init_device_with_tpu(self):
        mock_jax = MagicMock()
        mock_jax.devices.return_value = ["tpu:0"]
        bridge = JaxSimBridge(device="auto")
        with patch.object(bridge, "_jax", mock_jax):
            bridge._init_device()
            assert bridge._device == "tpu"

    def test_init_device_with_mps(self):
        mock_jax = MagicMock()
        mock_jax.devices.return_value = ["mps:0"]
        bridge = JaxSimBridge(device="auto")
        with patch.object(bridge, "_jax", mock_jax):
            bridge._init_device()
            assert bridge._device == "mps"

    def test_init_device_explicit(self):
        mock_jax = MagicMock()
        bridge = JaxSimBridge(device="tpu")
        with patch.object(bridge, "_jax", mock_jax):
            bridge._init_device()
            assert bridge._device == "tpu"

    def test_check_availability_no_jax(self):
        bridge = JaxSimBridge()
        with patch("builtins.__import__", side_effect=ImportError("no jax")):
            assert bridge._check_availability() is False

    def test_check_availability_no_jaxsim(self):
        bridge = JaxSimBridge()

        def fake_import(name, *args, **kwargs):
            if name == "jaxsim":
                raise ImportError("no jaxsim")
            return MagicMock()

        with patch("builtins.__import__", side_effect=fake_import):
            with patch("simulations.jaxsim_bridge.logger"):
                assert bridge._check_availability() is False


# ═══════════════════════════════════════════════════════════════════
# Config Parsing
# ═══════════════════════════════════════════════════════════════════


class TestConfigParsing:
    """Test configuration parsing."""

    def test_parse_rigid_body_defaults(self, bridge_available):
        cfg = bridge_available._parse_rigid_body_config({})
        assert isinstance(cfg, RigidBodyConfig)
        assert cfg.model_path is None
        assert cfg.dt == 0.001
        assert cfg.duration == 5.0
        assert cfg.gravity == (0.0, 0.0, -9.81)
        assert cfg.contact_model == "soft"
        assert cfg.friction_coefficient == 0.5
        assert cfg.restitution == 0.0
        assert cfg.integrate is True

    def test_parse_rigid_body_custom(self, bridge_available):
        cfg = bridge_available._parse_rigid_body_config({
            "model_path": "/path/to/robot.urdf",
            "initial_joint_positions": [0.1, 0.2, 0.3],
            "initial_joint_velocities": [0.0, 0.0, 0.0],
            "dt": 0.002,
            "duration": 10.0,
            "gravity": [0.0, 0.0, -9.8],
            "contact_model": "rigid",
            "friction_coefficient": 0.8,
            "restitution": 0.5,
            "integrate": False,
        })
        assert cfg.model_path == "/path/to/robot.urdf"
        assert np.allclose(cfg.initial_joint_positions, [0.1, 0.2, 0.3])
        assert np.allclose(cfg.initial_joint_velocities, [0.0, 0.0, 0.0])
        assert cfg.dt == 0.002
        assert cfg.duration == 10.0
        assert cfg.gravity == (0.0, 0.0, -9.8)
        assert cfg.contact_model == "rigid"
        assert cfg.friction_coefficient == 0.8
        assert cfg.restitution == 0.5
        assert cfg.integrate is False

    def test_parse_inverse_dynamics_defaults(self, bridge_available):
        cfg = bridge_available._parse_inverse_dynamics_config({})
        assert isinstance(cfg, InverseDynamicsConfig)
        assert cfg.model_path is None
        assert cfg.joint_positions is None
        assert cfg.joint_velocities is None
        assert cfg.joint_accelerations is None
        assert cfg.include_gravity is True
        assert cfg.include_coriolis is True

    def test_parse_inverse_dynamics_custom(self, bridge_available):
        cfg = bridge_available._parse_inverse_dynamics_config({
            "model_path": "/path/to/robot.urdf",
            "joint_positions": [0.1, 0.2],
            "joint_velocities": [0.01, 0.02],
            "joint_accelerations": [0.001, 0.002],
            "include_gravity": False,
            "include_coriolis": False,
        })
        assert np.allclose(cfg.joint_positions, [0.1, 0.2])
        assert np.allclose(cfg.joint_velocities, [0.01, 0.02])
        assert np.allclose(cfg.joint_accelerations, [0.001, 0.002])
        assert cfg.include_gravity is False
        assert cfg.include_coriolis is False


# ═══════════════════════════════════════════════════════════════════
# List Supported Models
# ═══════════════════════════════════════════════════════════════════


class TestListSupportedModels:
    """Test list_supported_models method."""

    def test_unavailable(self, bridge_unavailable):
        assert bridge_unavailable.list_supported_models() == []

    def test_available(self, bridge_available):
        models = bridge_available.list_supported_models()
        assert "urdf" in models
        assert "sdf" in models
        assert "mjcf" in models


# ═══════════════════════════════════════════════════════════════════
# Fallback Simulations
# ═══════════════════════════════════════════════════════════════════


class TestFallbackSimulations:
    """Test fallback simulation methods."""

    def test_fallback_integrate_true(self, bridge_unavailable):
        cfg = RigidBodyConfig(
            initial_joint_positions=np.array([0.1, 0.2, 0.3]),
            dt=0.01,
            duration=0.1,
            integrate=True,
        )
        result = bridge_unavailable._fallback_simulation(cfg)
        assert result["status"] == "success"
        assert result["engine"] == "jaxsim_fallback"
        assert result["device"] == "cpu"
        assert "trajectory_q" in result
        assert "trajectory_qd" in result
        assert "energy_kinetic" in result
        assert "energy_potential" in result

    def test_fallback_integrate_false(self, bridge_unavailable):
        cfg = RigidBodyConfig(
            initial_joint_positions=np.array([0.1, 0.2]),
            dt=0.01,
            duration=0.1,
            integrate=False,
        )
        result = bridge_unavailable._fallback_simulation(cfg)
        assert result["status"] == "success"
        assert "q" in result
        assert "qd" in result
        assert "qdd" in result
        assert "trajectory_q" not in result

    def test_fallback_no_initial_positions(self, bridge_unavailable):
        cfg = RigidBodyConfig(
            initial_joint_positions=None,
            dt=0.01,
            duration=0.1,
            integrate=True,
        )
        result = bridge_unavailable._fallback_simulation(cfg)
        assert result["status"] == "success"
        assert result["n_dof"] == 6

    def test_run_rigid_body_unavailable(self, bridge_unavailable):
        result = bridge_unavailable.run_rigid_body_simulation({
            "initial_joint_positions": [0.1, 0.2],
            "duration": 0.1,
            "dt": 0.01,
        })
        assert result["status"] == "success"
        assert result["engine"] == "jaxsim_fallback"

    def test_run_rigid_body_error_handling(self, bridge_unavailable):
        with patch.object(bridge_unavailable, "_parse_rigid_body_config", side_effect=TypeError("bad config")):
            result = bridge_unavailable.run_rigid_body_simulation({})
            assert result["status"] == "error"
            assert "bad config" in result["message"]


# ═══════════════════════════════════════════════════════════════════
# Fallback Inverse Dynamics
# ═══════════════════════════════════════════════════════════════════


class TestFallbackInverseDynamics:
    """Test fallback inverse dynamics."""

    def test_fallback_with_gravity(self, bridge_unavailable):
        cfg = InverseDynamicsConfig(
            joint_positions=np.array([0.1, 0.2]),
            joint_velocities=np.array([0.01, 0.02]),
            joint_accelerations=np.array([0.001, 0.002]),
            include_gravity=True,
            include_coriolis=True,
        )
        result = bridge_unavailable._fallback_inverse_dynamics(cfg, 2)
        assert result["status"] == "success"
        assert result["engine"] == "jaxsim_fallback"
        assert "joint_torques" in result
        assert len(result["joint_torques"]) == 2

    def test_fallback_without_gravity(self, bridge_unavailable):
        cfg = InverseDynamicsConfig(
            joint_positions=np.array([0.1]),
            include_gravity=False,
        )
        result = bridge_unavailable._fallback_inverse_dynamics(cfg, 1)
        assert result["status"] == "success"

    def test_run_inverse_dynamics_unavailable(self, bridge_unavailable):
        result = bridge_unavailable.run_inverse_dynamics({
            "joint_positions": [0.1, 0.2],
        })
        assert result["status"] == "success"
        assert result["engine"] == "jaxsim_fallback"

    def test_run_inverse_dynamics_error(self, bridge_unavailable):
        with patch.object(bridge_unavailable, "_parse_inverse_dynamics_config", side_effect=TypeError("bad")):
            result = bridge_unavailable.run_inverse_dynamics({})
            assert result["status"] == "error"
            assert "bad" in result["message"]


# ═══════════════════════════════════════════════════════════════════
# Execute Rigid Body (with mocked backend)
# ═══════════════════════════════════════════════════════════════════


class TestExecuteRigidBody:
    """Test _execute_rigid_body_simulation with mocked jaxsim."""

    def test_execute_no_model_path(self, bridge_available):
        cfg = RigidBodyConfig(model_path=None, dt=0.01, duration=0.05, integrate=True)
        result = bridge_available._execute_rigid_body_simulation(cfg)
        assert result["status"] == "success"
        assert result["engine"] == "jaxsim_fallback"

    def test_execute_no_jaxsim(self, bridge_available):
        bridge_available._jaxsim = None
        cfg = RigidBodyConfig(model_path="robot.urdf", dt=0.01, duration=0.05)
        result = bridge_available._execute_rigid_body_simulation(cfg)
        assert result["status"] == "error"
        assert "not available" in result["message"]


# ═══════════════════════════════════════════════════════════════════
# Execute Inverse Dynamics (with mocked backend)
# ═══════════════════════════════════════════════════════════════════


class TestExecuteInverseDynamics:
    """Test _execute_inverse_dynamics with mocked jaxsim."""

    def test_execute_no_jaxsim(self, bridge_available):
        bridge_available._jaxsim = None
        cfg = InverseDynamicsConfig(joint_positions=np.array([0.1, 0.2]))
        result = bridge_available._execute_inverse_dynamics(cfg)
        assert result["status"] == "error"
        assert "not available" in result["message"]

    def test_execute_no_positions(self, bridge_available):
        cfg = InverseDynamicsConfig(joint_positions=None)
        result = bridge_available._execute_inverse_dynamics(cfg)
        assert result["status"] == "error"
        assert "missing joint positions" in result["message"]

    def test_execute_no_model_path(self, bridge_available):
        cfg = InverseDynamicsConfig(joint_positions=np.array([0.1, 0.2]))
        result = bridge_available._execute_inverse_dynamics(cfg)
        assert result["status"] == "success"
        assert result["engine"] == "jaxsim_fallback"


# ═══════════════════════════════════════════════════════════════════
# Pattern Acceleration
# ═══════════════════════════════════════════════════════════════════


class TestAcceleratePattern:
    """Test pattern acceleration logic."""

    def test_accelerate_unavailable(self, bridge_unavailable, mock_pattern):
        result = bridge_unavailable.accelerate_pattern(mock_pattern, {})
        mock_pattern.run.assert_called_once()
        assert result["source"] == "pattern"

    def test_classify_robotics(self, bridge_available):
        assert bridge_available._classify_pattern("robot_arm") == "robotics"
        assert bridge_available._classify_pattern("double_pendulum") == "robotics"
        assert bridge_available._classify_pattern("legged_robot") == "robotics"

    def test_classify_agent(self, bridge_available):
        assert bridge_available._classify_pattern("agent_based") == "agent"
        assert bridge_available._classify_pattern("swarm") == "agent"

    def test_classify_deformable(self, bridge_available):
        assert bridge_available._classify_pattern("soft_body") == "deformable"
        assert bridge_available._classify_pattern("elasticity_3d") == "deformable"

    def test_classify_unknown(self, bridge_available):
        assert bridge_available._classify_pattern("random") == "unknown"

    def test_accelerate_robotics(self, bridge_available, mock_pattern):
        mock_pattern.PATTERN_ID = "robot_arm_test"
        mock_pattern.config = MagicMock()
        mock_pattern.config.model_path = "robot.urdf"
        mock_pattern.config.dt = 0.01
        mock_pattern.config.t_max = 0.1

        with patch.object(bridge_available, "run_rigid_body_simulation", return_value={"status": "success"}):
            result = bridge_available.accelerate_pattern(mock_pattern, {})
            assert result["pattern_id"] == "robot_arm_test"
            assert result["accelerated_by"] == "jaxsim"

    def test_accelerate_agent(self, bridge_available, mock_pattern):
        mock_pattern.PATTERN_ID = "agent_based_test"
        result = bridge_available.accelerate_pattern(mock_pattern, {})
        mock_pattern.run.assert_called_once()

    def test_accelerate_deformable(self, bridge_available, mock_pattern):
        mock_pattern.PATTERN_ID = "soft_body_test"
        result = bridge_available.accelerate_pattern(mock_pattern, {})
        mock_pattern.run.assert_called_once()

    def test_accelerate_unknown(self, bridge_available, mock_pattern):
        mock_pattern.PATTERN_ID = "weather_forecast"
        result = bridge_available.accelerate_pattern(mock_pattern, {})
        mock_pattern.run.assert_called_once()


# ═══════════════════════════════════════════════════════════════════
# Benchmark
# ═══════════════════════════════════════════════════════════════════


class TestBenchmark:
    """Test benchmark method."""

    def test_benchmark_not_available(self, bridge_unavailable):
        result = bridge_unavailable.benchmark_legacy_vs_jaxsim("robot_test", {})
        assert result["jaxsim_available"] is False
        assert result["speedup"] == 1.0

    def test_benchmark_available(self, bridge_available):
        with patch.object(bridge_available, "run_rigid_body_simulation", return_value={"status": "success"}):
            result = bridge_available.benchmark_legacy_vs_jaxsim("robot_test", {})
            assert result["jaxsim_available"] is True
            assert "speedup" in result
            assert "jaxsim_time" in result


# ═══════════════════════════════════════════════════════════════════
# Metadata
# ═══════════════════════════════════════════════════════════════════


class TestMetadata:
    """Test get_metadata classmethod."""

    def test_get_metadata(self):
        meta = JaxSimBridge.get_metadata()
        assert meta["name"] == "JaxSim Bridge"
        assert meta["license"] == "BSD-3"
        assert "github" in meta
        assert "supported_devices" in meta
        assert "cpu" in meta["supported_devices"]
        assert "gpu" in meta["supported_devices"]
        assert "mps" in meta["supported_devices"]
        assert "capabilities" in meta
        assert "limitations" in meta


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
