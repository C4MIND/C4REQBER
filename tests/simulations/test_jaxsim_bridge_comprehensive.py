"""Comprehensive tests for JaxSimBridge — differentiable robotics physics engine."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

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
    BasePattern,
    InverseDynamicsConfig,
    JaxSimBridge,
    RigidBodyConfig,
)


class MockRoboticsPattern:
    """Mock pattern for robotics acceleration testing."""

    PATTERN_ID = "robot_arm"
    config = None

    def run(self, hypothesis=None):
        return {"result": "fallback", "pattern": self.PATTERN_ID}


class MockAgentPattern:
    """Mock pattern for agent acceleration testing."""

    PATTERN_ID = "swarm"
    config = None

    def run(self, hypothesis=None):
        return {"result": "fallback"}


class MockDeformablePattern:
    """Mock pattern for deformable body testing."""

    PATTERN_ID = "soft_body"
    config = None

    def run(self, hypothesis=None):
        return {"result": "fallback"}


class TestRigidBodyConfig:
    """Tests for RigidBodyConfig dataclass."""

    def test_default_config(self):
        cfg = RigidBodyConfig()
        assert cfg.model_path is None
        assert cfg.initial_joint_positions is None
        assert cfg.initial_joint_velocities is None
        assert cfg.dt == 0.001
        assert cfg.duration == 5.0
        assert cfg.gravity == (0.0, 0.0, -9.81)
        assert cfg.contact_model == "soft"
        assert cfg.friction_coefficient == 0.5
        assert cfg.restitution == 0.0
        assert cfg.integrate is True

    def test_custom_config(self):
        cfg = RigidBodyConfig(
            model_path="robot.urdf",
            dt=0.01,
            duration=10.0,
            gravity=(0.0, 0.0, -9.8),
            contact_model="rigid",
            friction_coefficient=0.8,
        )
        assert cfg.model_path == "robot.urdf"
        assert cfg.dt == 0.01
        assert cfg.duration == 10.0
        assert cfg.gravity == (0.0, 0.0, -9.8)
        assert cfg.contact_model == "rigid"
        assert cfg.friction_coefficient == 0.8


class TestInverseDynamicsConfig:
    """Tests for InverseDynamicsConfig dataclass."""

    def test_default_config(self):
        cfg = InverseDynamicsConfig()
        assert cfg.model_path is None
        assert cfg.joint_positions is None
        assert cfg.joint_velocities is None
        assert cfg.joint_accelerations is None
        assert cfg.include_gravity is True
        assert cfg.include_coriolis is True

    def test_custom_config(self):
        cfg = InverseDynamicsConfig(
            model_path="robot.urdf",
            joint_positions=np.array([0.1, 0.2]),
            include_gravity=False,
        )
        assert cfg.model_path == "robot.urdf"
        assert np.allclose(cfg.joint_positions, [0.1, 0.2])
        assert cfg.include_gravity is False


class TestJaxSimBridgeInit:
    """Tests for JaxSimBridge initialization."""

    def test_init_default_device(self):
        bridge = JaxSimBridge()
        assert bridge._device_preference == "auto"

    def test_init_custom_device(self):
        bridge = JaxSimBridge(device="gpu")
        assert bridge._device_preference == "gpu"

    def test_init_unavailable_without_jax(self):
        with patch.dict("sys.modules", {"jax": None}):
            bridge = JaxSimBridge()
            assert not bridge.is_available()

    def test_init_device_mps(self):
        mock_jax = MagicMock()
        mock_jax.devices.return_value = ["mps:0"]
        mock_jaxsim = MagicMock()
        with patch.dict("sys.modules", {"jax": mock_jax, "jaxsim": mock_jaxsim}):
            bridge = JaxSimBridge(device="mps")
            assert bridge._device == "mps"

    def test_init_device_auto_gpu(self):
        mock_jax = MagicMock()
        mock_jax.devices.return_value = ["gpu:0"]
        mock_jaxsim = MagicMock()
        with patch.dict("sys.modules", {"jax": mock_jax, "jaxsim": mock_jaxsim}):
            bridge = JaxSimBridge(device="auto")
            assert bridge._device == "gpu"


class TestJaxSimBridgeAvailability:
    """Tests for availability and device queries."""

    def test_available_property(self):
        bridge = JaxSimBridge()
        assert isinstance(bridge.available, bool)

    def test_is_available_returns_bool(self):
        bridge = JaxSimBridge()
        assert isinstance(bridge.is_available(), bool)

    def test_get_device_unavailable(self):
        bridge = JaxSimBridge()
        device = bridge.get_device()
        assert device in ("unavailable", "cpu", "gpu", "tpu", "mps")

    def test_list_supported_models_unavailable(self):
        bridge = JaxSimBridge()
        bridge._available = False
        models = bridge.list_supported_models()
        assert models == []

    def test_list_supported_models_available(self):
        bridge = JaxSimBridge()
        bridge._available = True
        models = bridge.list_supported_models()
        assert isinstance(models, list)
        assert "urdf" in models


class TestJaxSimBridgeParseConfig:
    """Tests for configuration parsing."""

    def test_parse_rigid_body_config_defaults(self):
        bridge = JaxSimBridge()
        cfg = bridge._parse_rigid_body_config({})
        assert cfg.model_path is None
        assert cfg.dt == 0.001
        assert cfg.duration == 5.0
        assert cfg.gravity == (0.0, 0.0, -9.81)

    def test_parse_rigid_body_config_with_arrays(self):
        bridge = JaxSimBridge()
        cfg = bridge._parse_rigid_body_config({
            "model_path": "robot.urdf",
            "initial_joint_positions": [0.1, 0.2, 0.3],
            "initial_joint_velocities": [0.0, 0.0, 0.0],
            "dt": 0.01,
            "duration": 10.0,
            "gravity": [0.0, 0.0, -9.8],
            "contact_model": "rigid",
            "friction_coefficient": 0.8,
            "restitution": 0.1,
            "integrate": False,
        })
        assert cfg.model_path == "robot.urdf"
        assert np.allclose(cfg.initial_joint_positions, [0.1, 0.2, 0.3])
        assert np.allclose(cfg.initial_joint_velocities, [0.0, 0.0, 0.0])
        assert cfg.dt == 0.01
        assert cfg.duration == 10.0
        assert cfg.gravity == (0.0, 0.0, -9.8)
        assert cfg.contact_model == "rigid"
        assert cfg.friction_coefficient == 0.8
        assert cfg.restitution == 0.1
        assert cfg.integrate is False

    def test_parse_inverse_dynamics_config_defaults(self):
        bridge = JaxSimBridge()
        cfg = bridge._parse_inverse_dynamics_config({})
        assert cfg.model_path is None
        assert cfg.joint_positions is None
        assert cfg.include_gravity is True

    def test_parse_inverse_dynamics_config_with_arrays(self):
        bridge = JaxSimBridge()
        cfg = bridge._parse_inverse_dynamics_config({
            "model_path": "robot.urdf",
            "joint_positions": [0.1, 0.2],
            "joint_velocities": [0.0, 0.0],
            "joint_accelerations": [0.5, 0.5],
            "include_gravity": False,
            "include_coriolis": False,
        })
        assert cfg.model_path == "robot.urdf"
        assert np.allclose(cfg.joint_positions, [0.1, 0.2])
        assert np.allclose(cfg.joint_velocities, [0.0, 0.0])
        assert np.allclose(cfg.joint_accelerations, [0.5, 0.5])
        assert cfg.include_gravity is False
        assert cfg.include_coriolis is False


class TestJaxSimBridgeRigidBody:
    """Tests for rigid body simulation."""

    def test_run_rigid_body_unavailable(self):
        bridge = JaxSimBridge()
        bridge._available = False
        result = bridge.run_rigid_body_simulation({
            "dt": 0.001,
            "duration": 0.1,
            "integrate": False,
        })
        assert result["status"] == "success"  # fallback
        assert result["engine"] == "jaxsim_fallback"

    def test_run_rigid_body_fallback_integration(self):
        bridge = JaxSimBridge()
        bridge._available = False
        result = bridge.run_rigid_body_simulation({
            "dt": 0.001,
            "duration": 0.1,
            "initial_joint_positions": [0.0, 0.0, 0.0],
            "integrate": True,
        })
        assert result["status"] == "success"
        assert "trajectory_q" in result
        assert "trajectory_qd" in result
        assert "energy_kinetic" in result
        assert "energy_potential" in result

    def test_run_rigid_body_fallback_no_integration(self):
        bridge = JaxSimBridge()
        bridge._available = False
        result = bridge.run_rigid_body_simulation({
            "dt": 0.001,
            "duration": 0.1,
            "initial_joint_positions": [0.1, 0.2],
            "integrate": False,
        })
        assert result["status"] == "success"
        assert "q" in result
        assert "qd" in result
        assert "qdd" in result

    def test_run_rigid_body_error_handling(self):
        bridge = JaxSimBridge()
        with patch.object(bridge, "_parse_rigid_body_config", side_effect=TypeError("bad config")):
            result = bridge.run_rigid_body_simulation({})
            assert result["status"] == "error"
            assert "bad config" in result["message"]

    def test_run_rigid_body_execute_error(self):
        bridge = JaxSimBridge()
        bridge._available = True
        bridge._jaxsim = MagicMock()
        with patch.object(bridge, "_execute_rigid_body_simulation", side_effect=RuntimeError("exec error")):
            result = bridge.run_rigid_body_simulation({"dt": 0.001, "duration": 0.1, "integrate": False})
            assert result["status"] == "error"
            assert "exec error" in result["message"]


class TestJaxSimBridgeInverseDynamics:
    """Tests for inverse dynamics computation."""

    def test_run_inverse_dynamics_unavailable(self):
        bridge = JaxSimBridge()
        bridge._available = False
        result = bridge.run_inverse_dynamics({
            "joint_positions": [0.1, 0.2, 0.3],
        })
        assert result["status"] == "success"  # fallback
        assert result["engine"] == "jaxsim_fallback"
        assert "joint_torques" in result

    def test_run_inverse_dynamics_no_positions(self):
        bridge = JaxSimBridge()
        bridge._available = True
        bridge._jaxsim = MagicMock()
        result = bridge.run_inverse_dynamics({})
        assert result["status"] == "error"
        assert "missing" in result["message"].lower()

    def test_run_inverse_dynamics_error_handling(self):
        bridge = JaxSimBridge()
        with patch.object(bridge, "_parse_inverse_dynamics_config", side_effect=RuntimeError("dyn error")):
            result = bridge.run_inverse_dynamics({})
            assert result["status"] == "error"
            assert "dyn error" in result["message"]

    def test_run_inverse_dynamics_execute_error(self):
        bridge = JaxSimBridge()
        bridge._available = True
        bridge._jaxsim = MagicMock()
        with patch.object(bridge, "_execute_inverse_dynamics", side_effect=RuntimeError("exec error")):
            result = bridge.run_inverse_dynamics({"joint_positions": [0.1, 0.2]})
            assert result["status"] == "error"
            assert "exec error" in result["message"]


class TestJaxSimBridgeFallbackMethods:
    """Tests for fallback simulation methods."""

    def test_fallback_simulation_integration(self):
        bridge = JaxSimBridge()
        cfg = RigidBodyConfig(
            initial_joint_positions=np.array([0.1, 0.2]),
            initial_joint_velocities=np.array([0.0, 0.0]),
            dt=0.001,
            duration=0.1,
            gravity=(0.0, 0.0, -9.81),
            integrate=True,
        )
        result = bridge._fallback_simulation(cfg)
        assert result["status"] == "success"
        assert result["engine"] == "jaxsim_fallback"
        assert "trajectory_q" in result
        assert "trajectory_qd" in result

    def test_fallback_simulation_no_integration(self):
        bridge = JaxSimBridge()
        cfg = RigidBodyConfig(
            initial_joint_positions=np.array([0.1, 0.2]),
            dt=0.001,
            duration=0.1,
            integrate=False,
        )
        result = bridge._fallback_simulation(cfg)
        assert result["status"] == "success"
        assert "q" in result
        assert "qd" in result
        assert "qdd" in result

    def test_fallback_simulation_no_initial_positions(self):
        bridge = JaxSimBridge()
        cfg = RigidBodyConfig(
            dt=0.001,
            duration=0.1,
            integrate=True,
        )
        result = bridge._fallback_simulation(cfg)
        assert result["status"] == "success"
        assert result["n_dof"] == 6

    def test_fallback_inverse_dynamics(self):
        bridge = JaxSimBridge()
        cfg = InverseDynamicsConfig(
            joint_positions=np.array([0.1, 0.2]),
            joint_velocities=np.array([0.0, 0.0]),
            joint_accelerations=np.array([0.5, 0.5]),
            include_gravity=True,
            include_coriolis=True,
        )
        result = bridge._fallback_inverse_dynamics(cfg, n_dof=2)
        assert result["status"] == "success"
        assert result["engine"] == "jaxsim_fallback"
        assert "joint_torques" in result
        assert len(result["joint_torques"]) == 2

    def test_fallback_inverse_dynamics_no_gravity(self):
        bridge = JaxSimBridge()
        cfg = InverseDynamicsConfig(
            joint_positions=np.array([0.1, 0.2]),
            joint_velocities=np.array([0.0, 0.0]),
            joint_accelerations=np.array([0.5, 0.5]),
            include_gravity=False,
            include_coriolis=False,
        )
        result = bridge._fallback_inverse_dynamics(cfg, n_dof=2)
        assert result["status"] == "success"
        # Without gravity, torques should just be M @ qdd
        assert np.allclose(result["joint_torques"], [0.5, 0.5])


class TestJaxSimBridgePatternAcceleration:
    """Tests for pattern acceleration."""

    def test_classify_pattern_robotics(self):
        bridge = JaxSimBridge()
        assert bridge._classify_pattern("robot_arm") == "robotics"
        assert bridge._classify_pattern("double_pendulum") == "robotics"
        assert bridge._classify_pattern("humanoid") == "robotics"

    def test_classify_pattern_agent(self):
        bridge = JaxSimBridge()
        assert bridge._classify_pattern("swarm") == "agent"
        assert bridge._classify_pattern("multi_agent") == "agent"

    def test_classify_pattern_deformable(self):
        bridge = JaxSimBridge()
        assert bridge._classify_pattern("soft_body") == "deformable"
        assert bridge._classify_pattern("elasticity_3d") == "deformable"

    def test_classify_pattern_unknown(self):
        bridge = JaxSimBridge()
        assert bridge._classify_pattern("classical") == "unknown"
        assert bridge._classify_pattern("") == "unknown"

    def test_accelerate_pattern_not_available(self):
        bridge = JaxSimBridge()
        bridge._available = False
        pattern = MockRoboticsPattern()
        result = bridge.accelerate_pattern(pattern, {})
        assert result["result"] == "fallback"

    def test_accelerate_pattern_robotics(self):
        bridge = JaxSimBridge()
        bridge._available = True
        pattern = MockRoboticsPattern()
        with patch.object(bridge, "run_rigid_body_simulation", return_value={"status": "success"}) as mock_run:
            result = bridge.accelerate_pattern(pattern, {"dt": 0.01})
            assert result["pattern_id"] == "robot_arm"
            assert result["accelerated_by"] == "jaxsim"
            mock_run.assert_called_once()

    def test_accelerate_pattern_agent(self):
        bridge = JaxSimBridge()
        bridge._available = True
        pattern = MockAgentPattern()
        result = bridge.accelerate_pattern(pattern, {})
        assert result["result"] == "fallback"

    def test_accelerate_pattern_deformable(self):
        bridge = JaxSimBridge()
        bridge._available = True
        pattern = MockDeformablePattern()
        result = bridge.accelerate_pattern(pattern, {})
        assert result["result"] == "fallback"

    def test_accelerate_pattern_unknown(self):
        bridge = JaxSimBridge()
        bridge._available = True
        pattern = MockRoboticsPattern()
        pattern.PATTERN_ID = "classical"
        result = bridge.accelerate_pattern(pattern, {})
        assert result["result"] == "fallback"

    def test_accelerate_robotics_with_pattern_config(self):
        bridge = JaxSimBridge()
        bridge._available = True
        pattern = MockRoboticsPattern()
        pattern.config = MagicMock()
        pattern.config.model_path = "robot.urdf"
        pattern.config.dt = 0.01
        pattern.config.t_max = 5.0

        with patch.object(bridge, "run_rigid_body_simulation", return_value={"status": "success"}) as mock_run:
            result = bridge._accelerate_robotics_pattern(pattern, {})
            call_args = mock_run.call_args[0][0]
            assert call_args["model_path"] == "robot.urdf"
            assert call_args["dt"] == 0.01
            assert call_args["duration"] == 5.0


class TestJaxSimBridgeBenchmark:
    """Tests for benchmark method."""

    def test_benchmark_legacy_vs_jaxsim_not_available(self):
        bridge = JaxSimBridge()
        bridge._available = False
        result = bridge.benchmark_legacy_vs_jaxsim("robot_arm", {})
        assert result["jaxsim_available"] is False
        assert result["speedup"] == 1.0
        assert "not installed" in result["message"]

    def test_benchmark_legacy_vs_jaxsim_available(self):
        bridge = JaxSimBridge()
        bridge._available = True
        bridge._device = "cpu"
        with patch.object(bridge, "run_rigid_body_simulation", return_value={"status": "success"}):
            result = bridge.benchmark_legacy_vs_jaxsim("robot_arm", {"dt": 0.001})
            assert result["jaxsim_available"] is True
            assert "legacy_time" in result
            assert "jaxsim_time" in result
            assert "speedup" in result


class TestJaxSimBridgeMetadata:
    """Tests for metadata method."""

    def test_get_metadata(self):
        metadata = JaxSimBridge.get_metadata()
        assert metadata["name"] == "JaxSim Bridge"
        assert metadata["license"] == "BSD-3"
        assert "github" in metadata
        assert "capabilities" in metadata
        assert "limitations" in metadata
        assert "urdf" in metadata["supported_models"]


class TestJaxSimBridgePatternTypes:
    """Tests for pattern type constants."""

    def test_robotics_patterns(self):
        assert "robot_arm" in JaxSimBridge.PATTERN_TYPES_ROBOTICS
        assert "double_pendulum" in JaxSimBridge.PATTERN_TYPES_ROBOTICS
        assert "humanoid" in JaxSimBridge.PATTERN_TYPES_ROBOTICS

    def test_agent_patterns(self):
        assert "swarm" in JaxSimBridge.PATTERN_TYPES_AGENT
        assert "multi_agent" in JaxSimBridge.PATTERN_TYPES_AGENT

    def test_deformable_patterns(self):
        assert "soft_body" in JaxSimBridge.PATTERN_TYPES_DEFORMABLE
        assert "elasticity_3d" in JaxSimBridge.PATTERN_TYPES_DEFORMABLE


class TestJaxSimBridgeErrorHandling:
    """Tests for error handling paths."""

    def test_run_rigid_body_import_error(self):
        bridge = JaxSimBridge()
        with patch.object(bridge, "_parse_rigid_body_config", side_effect=ImportError("no module")):
            result = bridge.run_rigid_body_simulation({})
            assert result["status"] == "error"

    def test_run_inverse_dynamics_import_error(self):
        bridge = JaxSimBridge()
        with patch.object(bridge, "_parse_inverse_dynamics_config", side_effect=ImportError("no module")):
            result = bridge.run_inverse_dynamics({})
            assert result["status"] == "error"

    def test_fallback_inverse_dynamics_with_error_msg(self):
        bridge = JaxSimBridge()
        cfg = InverseDynamicsConfig(joint_positions=np.array([0.1, 0.2]))
        result = bridge._fallback_inverse_dynamics(cfg, 2, error="import failed")
        assert "import failed" in result["note"]
