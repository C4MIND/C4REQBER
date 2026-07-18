"""
Tests for Multi-Engine Physics Layer (v8.0).

Tests PhysicsAutoDetector, engine bridges, PatternRunnerV2, and PatternEngineMap.
"""

import platform
from unittest.mock import MagicMock, patch

import pytest

from src.simulations.auto_engine import PhysicsAutoDetector, get_detector
from src.simulations.pattern_engine_map import (
    EngineType,
    PatternEngineMap,
    get_engine,
    get_gpu_accelerated_patterns,
)
from src.simulations.runner_v2 import PatternRunnerV2, get_runner_v2


class TestPhysicsAutoDetector:
    """Tests for PhysicsAutoDetector hardware detection."""

    def test_auto_detector_detects_apple_silicon(self):
        """Test Apple Silicon detection."""
        detector = PhysicsAutoDetector()

        is_apple = platform.system() == "Darwin" and platform.machine() == "arm64"
        assert detector.has_apple_silicon == is_apple

    def test_auto_detector_has_gpu_property(self):
        """Test has_gpu returns boolean."""
        detector = PhysicsAutoDetector()

        assert isinstance(detector.has_gpu, bool)

    def test_auto_detector_gpu_name_returns_string(self):
        """Test gpu_name returns string."""
        detector = PhysicsAutoDetector()

        assert isinstance(detector.gpu_name, str)

    def test_auto_detector_gpu_memory_returns_float(self):
        """Test gpu_memory_gb returns float."""
        detector = PhysicsAutoDetector()

        assert isinstance(detector.gpu_memory_gb, float)

    def test_get_recommended_engine_returns_valid_string(self):
        """Test get_recommended_engine returns valid engine name."""
        detector = PhysicsAutoDetector()

        engine = detector.get_recommended_engine()
        assert engine in ("newton", "jaxsim", "torchsim")

    def test_get_recommended_engine_robotics_returns_jaxsim(self):
        """Test robotics domain returns jaxsim."""
        detector = PhysicsAutoDetector()

        engine = detector.get_recommended_engine("robotics")
        assert engine == "jaxsim"

    def test_get_recommended_engine_quantum_returns_schr(self):
        """Test quantum domain returns schr."""
        detector = PhysicsAutoDetector()

        engine = detector.get_recommended_engine("quantum")
        assert engine == "schr"

    def test_get_recommended_engine_atomistic_returns_torchsim(self):
        """Test atomistic domain returns torchsim."""
        detector = PhysicsAutoDetector()

        engine = detector.get_recommended_engine("atomistic")
        assert engine == "torchsim"

    def test_get_detection_report_returns_dict(self):
        """Test get_detection_report returns valid dict."""
        detector = PhysicsAutoDetector()

        report = detector.get_detection_report()
        assert isinstance(report, dict)
        assert "platform" in report
        assert "architecture" in report
        assert "has_gpu" in report
        assert "recommended_engine" in report

    def test_get_detector_singleton(self):
        """Test get_detector returns singleton."""
        detector1 = get_detector()
        detector2 = get_detector()
        assert detector1 is detector2


class TestPatternEngineMap:
    """Tests for PatternEngineMap pattern-to-engine mapping."""

    def test_get_engine_returns_valid_engine(self):
        """Test get_engine returns valid engine for known patterns."""
        mapper = PatternEngineMap()

        engine = mapper.get_engine("cfd")
        assert engine in ("newton", "jaxsim", "torchsim", "schr", "legacy")

    def test_get_engine_cfd_returns_newton(self):
        """Test CFD pattern maps to Newton."""
        mapper = PatternEngineMap()

        engine = mapper.get_engine("cfd")
        assert engine == "newton"

    def test_get_engine_molecular_dynamics_returns_torchsim(self):
        """Test molecular_dynamics maps to TorchSim."""
        mapper = PatternEngineMap()

        engine = mapper.get_engine("molecular_dynamics")
        assert engine == "torchsim"

    def test_get_engine_double_pendulum_returns_jaxsim(self):
        """Test double_pendulum maps to JaxSim."""
        mapper = PatternEngineMap()

        engine = mapper.get_engine("double_pendulum")
        assert engine == "jaxsim"

    def test_get_engine_quantum_returns_schr(self):
        """Test quantum patterns map to Schr."""
        mapper = PatternEngineMap()

        engine = mapper.get_engine("quantum_harmonic")
        assert engine == "schr"

    def test_get_engine_unknown_returns_legacy(self):
        """Test unknown patterns return legacy."""
        mapper = PatternEngineMap()

        engine = mapper.get_engine("unknown_pattern_xyz")
        assert engine == "legacy"

    def test_get_engine_with_metadata_category(self):
        """Test get_engine uses category from metadata."""
        mapper = PatternEngineMap()

        engine = mapper.get_engine("custom_pattern", metadata={"category": "cfd"})
        assert engine == "newton"

    def test_get_engine_with_metadata_custom_engine(self):
        """Test get_engine uses custom_engine from metadata."""
        mapper = PatternEngineMap()

        engine = mapper.get_engine("custom_pattern", metadata={"custom_engine": "jaxsim"})
        assert engine == "jaxsim"

    def test_get_engine_with_metadata_prefer_gpu(self):
        """Test get_engine respects prefer_gpu flag."""
        mapper = PatternEngineMap()

        engine = mapper.get_engine("custom_pattern", metadata={"prefer_gpu": True})
        assert engine == "newton"

    def test_get_gpu_accelerated_patterns_returns_list(self):
        """Test get_gpu_accelerated_patterns returns list."""
        mapper = PatternEngineMap()

        patterns = mapper.get_gpu_accelerated_patterns()
        assert isinstance(patterns, list)
        assert len(patterns) > 0
        assert "cfd" in patterns

    def test_get_acceleration_factor_returns_float(self):
        """Test get_acceleration_factor returns float."""
        mapper = PatternEngineMap()

        factor = mapper.get_acceleration_factor("cfd")
        assert isinstance(factor, float)
        assert factor >= 1.0

    def test_get_acceleration_factor_cfd_high_speedup(self):
        """Test CFD has high speedup factor."""
        mapper = PatternEngineMap()

        factor = mapper.get_acceleration_factor("cfd")
        assert factor >= 10.0

    def test_register_custom_mapping(self):
        """Test custom mapping registration."""
        mapper = PatternEngineMap()

        mapper.register_custom_mapping("my_custom_pattern", "jaxsim")
        engine = mapper.get_engine("my_custom_pattern")
        assert engine == "jaxsim"

    def test_get_patterns_by_engine(self):
        """Test get_patterns_by_engine returns patterns."""
        mapper = PatternEngineMap()

        patterns = mapper.get_patterns_by_engine("newton")
        assert isinstance(patterns, list)
        assert "cfd" in patterns

    def test_get_engine_stats(self):
        """Test get_engine_stats returns stats dict."""
        mapper = PatternEngineMap()

        stats = mapper.get_engine_stats()
        assert isinstance(stats, dict)
        assert "newton" in stats
        assert "jaxsim" in stats

    def test_is_gpu_pattern_true(self):
        """Test is_gpu_pattern returns True for GPU patterns."""
        mapper = PatternEngineMap()

        assert mapper.is_gpu_pattern("cfd") is True

    def test_is_gpu_pattern_false(self):
        """Test is_gpu_pattern returns False for non-GPU patterns."""
        mapper = PatternEngineMap()

        assert mapper.is_gpu_pattern("unknown_pattern") is False

    def test_recommend_engine_with_gradients(self):
        """Test recommend_engine prefers jaxsim for gradients."""
        mapper = PatternEngineMap()

        engine = mapper.recommend_engine("cfd", requires_gradients=True)
        assert engine == "jaxsim"

    def test_convenience_get_engine_function(self):
        """Test convenience get_engine function."""
        engine = get_engine("cfd")
        assert engine == "newton"

    def test_convenience_get_gpu_accelerated_patterns_function(self):
        """Test convenience get_gpu_accelerated_patterns function."""
        patterns = get_gpu_accelerated_patterns()
        assert isinstance(patterns, list)


class TestTorchSimBridge:
    """Tests for TorchSim bridge."""

    def test_torchsim_bridge_fallback_without_package(self):
        """Test TorchSim bridge works without package."""
        from src.simulations.torchsim_bridge import TorchSimBridge

        bridge = TorchSimBridge()
        available = bridge.is_available()
        assert isinstance(available, bool)

    def test_torchsim_bridge_device_property(self):
        """Test device property returns string."""
        from src.simulations.torchsim_bridge import TorchSimBridge

        bridge = TorchSimBridge()
        device = bridge.device
        assert isinstance(device, str)

    def test_torchsim_list_supported_models(self):
        """Test list_supported_models returns list."""
        from src.simulations.torchsim_bridge import TorchSimBridge

        bridge = TorchSimBridge()
        models = bridge.list_supported_models()
        assert isinstance(models, list)
        assert "lennard_jones" in models

    def test_torchsim_list_supported_integrators(self):
        """Test list_supported_integrators returns list."""
        from src.simulations.torchsim_bridge import TorchSimBridge

        bridge = TorchSimBridge()
        integrators = bridge.list_supported_integrators()
        assert isinstance(integrators, list)
        assert "nvt_langevin" in integrators

    def test_torchsim_list_supported_relaxation_methods(self):
        """Test list_supported_relaxation_methods returns list."""
        from src.simulations.torchsim_bridge import TorchSimBridge

        bridge = TorchSimBridge()
        methods = bridge.list_supported_relaxation_methods()
        assert isinstance(methods, list)
        assert "fire" in methods


class TestJaxSimBridge:
    """Tests for JaxSim bridge."""

    def test_jaxsim_bridge_available_property(self):
        """Test available property returns boolean."""
        from src.simulations.jaxsim_bridge import JaxSimBridge

        bridge = JaxSimBridge()
        available = bridge.available
        assert isinstance(available, bool)

    def test_jaxsim_bridge_get_device(self):
        """Test get_device returns string."""
        from src.simulations.jaxsim_bridge import JaxSimBridge

        bridge = JaxSimBridge()
        device = bridge.get_device()
        assert isinstance(device, str)

    def test_jaxsim_list_supported_models(self):
        """Test list_supported_models returns list."""
        from src.simulations.jaxsim_bridge import JaxSimBridge

        bridge = JaxSimBridge()
        models = bridge.list_supported_models()
        assert isinstance(models, list)

    def test_jaxsim_run_rigid_body_simulation_returns_dict(self):
        """Test run_rigid_body_simulation returns dict."""
        from src.simulations.jaxsim_bridge import JaxSimBridge

        bridge = JaxSimBridge()
        result = bridge.run_rigid_body_simulation(
            {
                "dt": 0.001,
                "duration": 0.1,
                "integrate": False,
            }
        )
        assert isinstance(result, dict)
        assert "status" in result

    def test_jaxsim_fallback_simulation(self):
        """Without JaxSim/URDF, rigid-body path is unavailable — not fake success."""
        from src.simulations.jaxsim_bridge import JaxSimBridge

        bridge = JaxSimBridge()
        result = bridge.run_rigid_body_simulation(
            {
                "dt": 0.001,
                "duration": 0.1,
                "initial_joint_positions": [0.0, 0.0, 0.0],
            }
        )
        assert result["status"] == "unavailable"
        assert result.get("stub") is True
        assert result.get("executed") is False

    def test_jaxsim_get_metadata(self):
        """Test get_metadata returns dict."""
        from src.simulations.jaxsim_bridge import JaxSimBridge

        metadata = JaxSimBridge.get_metadata()
        assert isinstance(metadata, dict)
        assert "name" in metadata
        assert "license" in metadata


class TestNewtonBridge:
    """Tests for Newton bridge."""

    def test_newton_bridge_is_available_returns_bool(self):
        """Test is_available returns boolean."""
        from src.simulations.newton_bridge import NewtonBridge

        bridge = NewtonBridge()
        available = bridge.is_available()
        assert isinstance(available, bool)

    def test_newton_bridge_is_gpu_mode_returns_bool(self):
        """Test is_gpu_mode returns boolean."""
        from src.simulations.newton_bridge import NewtonBridge

        bridge = NewtonBridge()
        gpu_mode = bridge.is_gpu_mode()
        assert isinstance(gpu_mode, bool)

    def test_newton_bridge_get_supported_simulations(self):
        """Test get_supported_simulations returns list."""
        from src.simulations.newton_bridge import NewtonBridge

        bridge = NewtonBridge()
        sims = bridge.get_supported_simulations()
        assert isinstance(sims, list)
        assert "rigid_body" in sims

    def test_newton_bridge_can_accelerate(self):
        """Test can_accelerate returns boolean."""
        from src.simulations.newton_bridge import NewtonBridge

        bridge = NewtonBridge()
        assert bridge.can_accelerate("cfd") is True
        assert bridge.can_accelerate("unknown_pattern") is False

    def test_newton_bridge_run_simulation_returns_result(self):
        """Test run_simulation returns NewtonResult."""
        from src.simulations.newton_bridge import NewtonBridge

        bridge = NewtonBridge()
        result = bridge.run_simulation(
            {
                "type": "rigid_body",
                "num_bodies": 5,
                "num_steps": 10,
            }
        )
        assert result.status in ("success", "error")

    def test_newton_bridge_benchmark_returns_dict(self):
        """Test benchmark returns dict with speedup."""
        from src.simulations.newton_bridge import NewtonBridge

        bridge = NewtonBridge()
        result = bridge.benchmark({"type": "rigid_body", "num_steps": 10}, num_runs=1)
        assert "speedup" in result


class TestSchrBridge:
    """Tests for Schr quantum bridge."""

    def test_schr_bridge_available_property(self):
        """Test available property returns boolean."""
        from src.simulations.schr_bridge import SchrBridge

        bridge = SchrBridge()
        available = bridge.available
        assert isinstance(available, bool)

    def test_schr_bridge_get_device(self):
        """Test get_device returns string."""
        from src.simulations.schr_bridge import SchrBridge

        bridge = SchrBridge()
        device = bridge.get_device()
        assert isinstance(device, str)

    def test_schr_run_schrodinger_returns_dict(self):
        """Test run_schrodinger returns dict."""
        from src.simulations.schr_bridge import SchrBridge

        bridge = SchrBridge()
        result = bridge.run_schrodinger(
            {
                "n_points": 32,
                "domain_size": 5.0,
                "dt": 0.01,
                "duration": 0.1,
                "integrate": False,
            }
        )
        assert isinstance(result, dict)
        assert "status" in result

    def test_schr_fallback_schrodinger(self):
        """Test fallback Schrödinger simulation works."""
        from src.simulations.schr_bridge import SchrBridge

        bridge = SchrBridge()
        result = bridge.run_schrodinger(
            {
                "n_points": 32,
                "domain_size": 5.0,
                "dt": 0.01,
                "duration": 0.1,
            }
        )
        assert result["status"] == "success"

    def test_schr_run_qed_returns_dict(self):
        """Test run_qed returns dict."""
        from src.simulations.schr_bridge import SchrBridge

        bridge = SchrBridge()
        result = bridge.run_qed(
            {
                "n_modes": 2,
                "n_photons_max": 2,
                "dt": 0.1,
                "duration": 1.0,
            }
        )
        assert isinstance(result, dict)
        assert "status" in result

    def test_schr_get_metadata(self):
        """Test get_metadata returns dict."""
        from src.simulations.schr_bridge import SchrBridge

        metadata = SchrBridge.get_metadata()
        assert isinstance(metadata, dict)
        assert "name" in metadata
        assert "license" in metadata


class TestPatternRunnerV2:
    """Tests for PatternRunnerV2 multi-engine runner."""

    def test_runner_v2_instantiation(self):
        """Test PatternRunnerV2 can be instantiated."""
        runner = PatternRunnerV2()
        assert runner is not None

    def test_runner_v2_has_auto_detector(self):
        """Test runner has auto_detector."""
        runner = PatternRunnerV2()
        assert hasattr(runner, "auto_detector")

    def test_runner_v2_has_engine_map(self):
        """Test runner has engine_map."""
        runner = PatternRunnerV2()
        assert hasattr(runner, "engine_map")

    def test_runner_v2_run_returns_dict(self):
        """Test run returns dict."""
        runner = PatternRunnerV2()

        result = runner.run("unknown_pattern_12345")
        assert isinstance(result, dict)
        assert "pattern_id" in result

    def test_runner_v2_run_unknown_pattern_returns_error(self):
        """Test unknown pattern returns error."""
        runner = PatternRunnerV2()

        result = runner.run("nonexistent_pattern")
        assert result["status"] == "failed"

    def test_runner_v2_get_engine_status(self):
        """Test get_engine_status returns dict."""
        runner = PatternRunnerV2()

        status = runner.get_engine_status()
        assert isinstance(status, dict)
        assert "hardware" in status
        assert "engines" in status

    def test_runner_v2_benchmark_returns_dict(self):
        """Test benchmark returns dict."""
        runner = PatternRunnerV2()

        result = runner.benchmark("unknown_pattern_12345")
        assert isinstance(result, dict)

    def test_runner_v2_run_batch_raises_on_mismatched_lengths(self):
        """Test run_batch raises on mismatched lengths."""
        runner = PatternRunnerV2()

        with pytest.raises(ValueError):
            runner.run_batch(["p1", "p2"], [{}])

    def test_runner_v2_run_batch_returns_list(self):
        """Test run_batch returns list."""
        runner = PatternRunnerV2()

        results = runner.run_batch(
            ["unknown_pattern_1", "unknown_pattern_2"],
            [{}, {}],
            parallel=False,
        )
        assert isinstance(results, list)
        assert len(results) == 2

    def test_pattern_runner_v2_backward_compatible_with_v1(self):
        """Test v2 runner is backward compatible with v1."""
        runner = PatternRunnerV2()

        assert hasattr(runner, "run")
        assert hasattr(runner, "_patterns")
        assert hasattr(runner, "auto_detector")
        assert hasattr(runner, "engine_map")

    def test_runner_v2_singleton(self):
        """Test get_runner_v2 returns singleton."""
        runner1 = get_runner_v2()
        runner2 = get_runner_v2()
        assert runner1 is runner2
