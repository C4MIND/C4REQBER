"""Tests for src/simulations/nvidia_bridge.py."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import numpy as np
import pytest

from simulations.nvidia_bridge import (
    CloudComputeStub,
    CuBLASWrapper,
    CudaCostTracker,
    CudaMode,
    CuDNNWrapper,
    CuQuantumWrapper,
    NCCLWrapper,
    NvidiaBridge,
    NvidiaBridgeConfig,
    NvidiaBridgeResult,
    get_nvidia_bridge,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def bridge_unavailable():
    """NvidiaBridge forced unavailable."""
    with patch.object(NvidiaBridge, "_detect_mode", return_value=CudaMode.UNAVAILABLE):
        with patch.object(NvidiaBridge, "_initialize", return_value=False):
            bridge = NvidiaBridge()
            bridge._mode = CudaMode.UNAVAILABLE
            bridge._initialized = False
            yield bridge


@pytest.fixture
def bridge_cpu():
    """NvidiaBridge in CPU mode."""
    bridge = NvidiaBridge()
    bridge._mode = CudaMode.CPU
    bridge._initialized = True
    bridge._cost_tracker = CudaCostTracker()
    return bridge


@pytest.fixture
def bridge_gpu():
    """NvidiaBridge in GPU mode."""
    bridge = NvidiaBridge()
    bridge._mode = CudaMode.GPU
    bridge._initialized = True
    bridge._device_name = "NVIDIA A100"
    bridge._device_memory_gb = 80.0
    bridge._cost_tracker = CudaCostTracker()
    return bridge


@pytest.fixture
def mock_pattern():
    """Mock pattern with PATTERN_ID and run method."""
    pattern = MagicMock()
    pattern.PATTERN_ID = "quantum_circuit"
    pattern.run = MagicMock(return_value={"status": "ok", "source": "pattern"})
    return pattern


# ═══════════════════════════════════════════════════════════════════
# Initialization & Availability
# ═══════════════════════════════════════════════════════════════════


class TestNvidiaBridgeInit:
    """Test NvidiaBridge initialization."""

    def test_init_default_config(self):
        with patch.object(NvidiaBridge, "_detect_mode", return_value=CudaMode.UNAVAILABLE):
            with patch.object(NvidiaBridge, "_initialize", return_value=False):
                bridge = NvidiaBridge()
                assert isinstance(bridge.config, NvidiaBridgeConfig)

    def test_init_custom_config(self):
        cfg = NvidiaBridgeConfig(device_id=1, track_cost=False)
        with patch.object(NvidiaBridge, "_detect_mode", return_value=CudaMode.UNAVAILABLE):
            with patch.object(NvidiaBridge, "_initialize", return_value=False):
                bridge = NvidiaBridge(config=cfg)
                assert bridge.config.device_id == 1
                assert bridge.config.track_cost is False

    def test_unavailable_mode(self, bridge_unavailable):
        assert bridge_unavailable.get_mode() == CudaMode.UNAVAILABLE
        assert bridge_unavailable.is_available() is False
        assert bridge_unavailable.available is False

    def test_cpu_mode(self, bridge_cpu):
        assert bridge_cpu.get_mode() == CudaMode.CPU
        assert bridge_cpu.is_available() is True
        assert bridge_cpu.is_gpu_mode() is False

    def test_gpu_mode(self, bridge_gpu):
        assert bridge_gpu.get_mode() == CudaMode.GPU
        assert bridge_gpu.is_available() is True
        assert bridge_gpu.is_gpu_mode() is True

    def test_detect_mode_darwin_cpu_fallback(self):
        with patch("platform.system", return_value="Darwin"):
            bridge = NvidiaBridge.__new__(NvidiaBridge)
            bridge.config = NvidiaBridgeConfig(allow_cpu_fallback=True)
            assert bridge._detect_mode() == CudaMode.CPU

    def test_detect_mode_darwin_no_fallback(self):
        with patch("platform.system", return_value="Darwin"):
            bridge = NvidiaBridge.__new__(NvidiaBridge)
            bridge.config = NvidiaBridgeConfig(allow_cpu_fallback=False)
            assert bridge._detect_mode() == CudaMode.UNAVAILABLE

    def test_detect_mode_torch_cuda(self):
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.get_device_name.return_value = "RTX 4090"
        mock_device_props = MagicMock()
        mock_device_props.total_memory = 24 * 1024**3
        mock_torch.cuda.get_device_properties.return_value = mock_device_props

        with patch("platform.system", return_value="Linux"):
            with patch.dict("sys.modules", {"torch": mock_torch}):
                bridge = NvidiaBridge.__new__(NvidiaBridge)
                bridge.config = NvidiaBridgeConfig()
                mode = bridge._detect_mode()
                assert mode == CudaMode.GPU
                assert bridge._device_name == "RTX 4090"

    def test_detect_mode_nvidia_smi(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "NVIDIA A100, 81920 MiB\n"

        with patch("platform.system", return_value="Linux"):
            with patch("subprocess.run", return_value=mock_result):
                bridge = NvidiaBridge.__new__(NvidiaBridge)
                bridge.config = NvidiaBridgeConfig()
                mode = bridge._detect_mode()
                assert mode == CudaMode.GPU
                assert "A100" in (bridge._device_name or "")

    def test_detect_mode_no_cuda(self):
        with patch("platform.system", return_value="Linux"):
            with patch("subprocess.run", side_effect=FileNotFoundError):
                bridge = NvidiaBridge.__new__(NvidiaBridge)
                bridge.config = NvidiaBridgeConfig(allow_cpu_fallback=True)
                mode = bridge._detect_mode()
                assert mode == CudaMode.CPU

    def test_get_device_name(self, bridge_gpu):
        assert bridge_gpu.get_device_name() == "NVIDIA A100"

    def test_get_device_memory_gb(self, bridge_gpu):
        assert bridge_gpu.get_device_memory_gb() == 80.0


# ═══════════════════════════════════════════════════════════════════
# CUDA Wrappers
# ═══════════════════════════════════════════════════════════════════


class TestCuBLASWrapper:
    """Test cuBLAS wrapper."""

    def test_matmul_cpu_fallback(self, bridge_cpu):
        a = np.array([[1.0, 2.0], [3.0, 4.0]])
        b = np.array([[5.0, 6.0], [7.0, 8.0]])
        result = bridge_cpu.cublas.matmul(a, b)
        expected = np.matmul(a, b)
        np.testing.assert_array_almost_equal(result, expected)

    def test_vector_dot_cpu_fallback(self, bridge_cpu):
        a = np.array([1.0, 2.0, 3.0])
        b = np.array([4.0, 5.0, 6.0])
        result = bridge_cpu.cublas.vector_dot(a, b)
        expected = np.dot(a, b)
        assert result == pytest.approx(expected)

    def test_batch_matmul_cpu_fallback(self, bridge_cpu):
        a = np.array([[1.0, 0.0], [0.0, 1.0]])
        b = np.array([[2.0, 0.0], [0.0, 2.0]])
        result = bridge_cpu.cublas.batch_matmul([a, b])
        expected = np.matmul(a, b)
        np.testing.assert_array_almost_equal(result, expected)

    def test_batch_matmul_empty(self, bridge_cpu):
        result = bridge_cpu.cublas.batch_matmul([])
        assert result.size == 0

    def test_batch_matmul_single(self, bridge_cpu):
        a = np.array([[1.0, 2.0], [3.0, 4.0]])
        result = bridge_cpu.cublas.batch_matmul([a])
        np.testing.assert_array_almost_equal(result, a)


class TestCuDNNWrapper:
    """Test cuDNN wrapper."""

    def test_relu_cpu_fallback(self, bridge_cpu):
        x = np.array([-1.0, 0.0, 1.0, 2.0])
        result = bridge_cpu.cudnn.relu(x)
        expected = np.array([0.0, 0.0, 1.0, 2.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_batch_norm_cpu_fallback(self, bridge_cpu):
        x = np.array([1.0, 2.0, 3.0])
        gamma = np.array([1.0, 1.0, 1.0])
        beta = np.array([0.0, 0.0, 0.0])
        mean = np.array([0.0, 0.0, 0.0])
        var = np.array([1.0, 1.0, 1.0])
        result = bridge_cpu.cudnn.batch_norm(x, gamma, beta, mean, var)
        expected = x  # (x - 0) / sqrt(1 + 1e-5) * 1 + 0 ≈ x
        np.testing.assert_array_almost_equal(result, expected, decimal=5)


class TestCuQuantumWrapper:
    """Test cuQuantum wrapper."""

    def test_simulate_circuit_hadamard(self, bridge_cpu):
        result = bridge_cpu.cuquantum.simulate_circuit(
            n_qubits=1,
            gates=[{"gate": "h", "targets": [0]}],
            initial_state="zero",
        )
        assert result["n_qubits"] == 1
        assert result["n_gates"] == 1
        probs = result["probabilities"]
        assert pytest.approx(probs[0], abs=1e-10) == 0.5
        assert pytest.approx(probs[1], abs=1e-10) == 0.5

    def test_simulate_circuit_bell_state(self, bridge_cpu):
        result = bridge_cpu.cuquantum.simulate_circuit(
            n_qubits=2,
            gates=[
                {"gate": "h", "targets": [0]},
                {"gate": "cnot", "targets": [0, 1]},
            ],
            initial_state="zero",
        )
        probs = result["probabilities"]
        assert pytest.approx(probs[0], abs=1e-10) == 0.5
        assert pytest.approx(probs[3], abs=1e-10) == 0.5

    def test_expectation_value_cpu_fallback(self, bridge_cpu):
        sv = np.array([1.0, 0.0], dtype=complex)
        obs = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
        result = bridge_cpu.cuquantum.expectation_value(sv, obs)
        assert pytest.approx(result, abs=1e-10) == 1.0

    def test_get_gate_matrix_standard_gates(self, bridge_cpu):
        for gate_name in ["x", "y", "z", "h", "s", "t"]:
            mat = bridge_cpu.cuquantum._get_gate_matrix(gate_name, {})
            assert mat.shape == (2, 2)
            assert mat.dtype == complex

    def test_get_gate_matrix_rx(self, bridge_cpu):
        mat = bridge_cpu.cuquantum._get_gate_matrix("rx", {"theta": np.pi})
        assert mat.shape == (2, 2)


class TestNCCLWrapper:
    """Test NCCL wrapper."""

    def test_all_reduce_single_gpu(self, bridge_cpu):
        bridge_cpu.nccl._world_size = 1
        data = np.array([1.0, 2.0, 3.0])
        result = bridge_cpu.nccl.all_reduce(data)
        np.testing.assert_array_equal(result, data)

    def test_broadcast_fallback(self, bridge_cpu):
        data = np.array([1.0, 2.0, 3.0])
        result = bridge_cpu.nccl.broadcast(data)
        np.testing.assert_array_equal(result, data)

    def test_all_gather_single(self, bridge_cpu):
        bridge_cpu.nccl._world_size = 1
        data = np.array([1.0, 2.0])
        result = bridge_cpu.nccl.all_gather(data)
        assert len(result) == 1
        np.testing.assert_array_equal(result[0], data)

    def test_initialize_single_gpu(self, bridge_cpu):
        result = bridge_cpu.nccl.initialize(1, 0)
        assert result is False  # Cupy not available in tests


# ═══════════════════════════════════════════════════════════════════
# Cost Tracking
# ═══════════════════════════════════════════════════════════════════


class TestCudaCostTracker:
    """Test cost tracking."""

    def test_start_end_session(self):
        tracker = CudaCostTracker()
        tracker.start_session()
        assert tracker._session_active is True
        tracker.end_session()
        assert tracker._session_active is False
        assert tracker.cuda_hours >= 0.0

    def test_record_kernel(self):
        tracker = CudaCostTracker()
        tracker.record_kernel(memory_mb=1024.0)
        assert tracker.total_kernel_calls == 1
        assert tracker.peak_memory_mb == 1024.0
        tracker.record_kernel(memory_mb=512.0)
        assert tracker.peak_memory_mb == 1024.0

    def test_get_report(self):
        tracker = CudaCostTracker()
        tracker.start_session()
        tracker.end_session()
        report = tracker.get_report()
        assert "cuda_hours" in report
        assert "peak_memory_mb" in report
        assert "total_kernel_calls" in report


# ═══════════════════════════════════════════════════════════════════
# Simulation Methods
# ═══════════════════════════════════════════════════════════════════


class TestRunSimulation:
    """Test run_simulation method."""

    def test_run_unavailable(self, bridge_unavailable):
        result = bridge_unavailable.run_simulation({"type": "linear_algebra"})
        assert result.status == "error"
        assert "not available" in result.error_message.lower()

    def test_run_linear_algebra(self, bridge_cpu):
        result = bridge_cpu.run_simulation(
            {
                "type": "linear_algebra",
                "a": [[1.0, 2.0], [3.0, 4.0]],
                "b": [[5.0, 6.0], [7.0, 8.0]],
                "op": "matmul",
            }
        )
        assert result.status == "partial"  # CPU kernel — not CUDA success
        assert "result" in result.data
        assert result.data.get("backend") == "numpy_cpu"

    def test_run_neural_network_relu(self, bridge_cpu):
        result = bridge_cpu.run_simulation(
            {
                "type": "neural_network",
                "input": [[-1.0, 2.0], [-3.0, 4.0]],
                "op": "relu",
            }
        )
        assert result.status == "partial"

    def test_run_quantum_circuit(self, bridge_cpu):
        result = bridge_cpu.run_simulation(
            {
                "type": "quantum_circuit",
                "n_qubits": 2,
                "gates": [{"gate": "h", "targets": [0]}],
            }
        )
        assert result.status == "partial"
        assert result.data["n_qubits"] == 2

    def test_run_multi_gpu(self, bridge_cpu):
        result = bridge_cpu.run_simulation(
            {
                "type": "multi_gpu_collective",
                "data": [1.0, 2.0, 3.0],
                "collective_op": "all_reduce",
            }
        )
        assert result.status == "partial"

    def test_run_generic(self, bridge_cpu):
        result = bridge_cpu.run_simulation({"type": "unknown"})
        assert result.status == "unavailable"
        assert result.data.get("stub") is True

    def test_run_error(self, bridge_cpu):
        with patch.object(bridge_cpu, "_run_linear_algebra", side_effect=ValueError("test error")):
            result = bridge_cpu.run_simulation({"type": "linear_algebra"})
            assert result.status == "error"
            assert "test error" in result.error_message


# ═══════════════════════════════════════════════════════════════════
# Pattern Acceleration
# ═══════════════════════════════════════════════════════════════════


class TestAcceleratePattern:
    """Test accelerate_pattern method."""

    def test_accelerate_not_in_list(self, bridge_gpu, mock_pattern):
        mock_pattern.PATTERN_ID = "unknown_pattern"
        result = bridge_gpu.accelerate_pattern(mock_pattern)
        assert result["accelerated"] is False
        assert result["engine"] == "legacy"

    def test_accelerate_unavailable(self, bridge_unavailable, mock_pattern):
        result = bridge_unavailable.accelerate_pattern(mock_pattern)
        assert result["accelerated"] is False
        assert result["engine"] == "legacy"

    def test_accelerate_cpu_mode(self, bridge_cpu, mock_pattern):
        result = bridge_cpu.accelerate_pattern(mock_pattern)
        assert result["accelerated"] is False
        assert result["engine"] == "legacy"

    def test_accelerate_gpu_success(self, bridge_gpu, mock_pattern):
        mock_result = NvidiaBridgeResult(
            status="success",
            mode=CudaMode.GPU,
            execution_time=0.1,
            data={"test": True, "backend": "cupy_local"},
            metrics={},
        )
        with patch.object(bridge_gpu, "run_simulation", return_value=mock_result):
            result = bridge_gpu.accelerate_pattern(mock_pattern, {"type": "linear_algebra"})
            assert result["accelerated"] is True
            assert result["engine"] == "nvidia"
            assert result["mode"] == "gpu"

    def test_accelerate_gpu_failure(self, bridge_gpu, mock_pattern):
        mock_result = NvidiaBridgeResult(
            status="error",
            mode=CudaMode.GPU,
            error_message="GPU fail",
        )
        with patch.object(bridge_gpu, "run_simulation", return_value=mock_result):
            result = bridge_gpu.accelerate_pattern(mock_pattern, {"type": "linear_algebra"})
            assert result["accelerated"] is False
            assert result["engine"] == "legacy"

    def test_fallback_run(self, bridge_unavailable, mock_pattern):
        result = bridge_unavailable._fallback_run(mock_pattern, {"test": True})
        assert result["accelerated"] is False
        assert result["engine"] == "legacy"
        mock_pattern.run.assert_called_once_with({"test": True})

    def test_extract_pattern_config(self, bridge_gpu, mock_pattern):
        result = bridge_gpu._extract_pattern_config(mock_pattern, {"type": "quantum_circuit"})
        assert result["type"] == "quantum_circuit"
        assert result["pattern_id"] == "quantum_circuit"

    def test_extract_pattern_config_no_invented_cfd_matmul(self, bridge_gpu, mock_pattern):
        mock_pattern.PATTERN_ID = "cfd"
        result = bridge_gpu._extract_pattern_config(mock_pattern, {})
        assert result["type"] == "unsupported_pattern"
        assert result["pattern_id"] == "cfd"


# ═══════════════════════════════════════════════════════════════════
# Cloud Stubs
# ═══════════════════════════════════════════════════════════════════


class TestCloudComputeStub:
    """Test cloud compute routing stubs."""

    def test_route_brev_dev_no_api_key(self, bridge_cpu):
        with patch.dict("os.environ", {}, clear=True):
            result = bridge_cpu.cloud.route_brev_dev("quantum_circuit", {})
            assert result["provider"] == "brev.dev"
            assert result["status"] == "unavailable"
            assert result.get("stub") is True
            assert "BREV_API_KEY" in result["message"]

    def test_route_dgx_cloud_no_api_key(self, bridge_cpu):
        with patch.dict("os.environ", {}, clear=True):
            result = bridge_cpu.cloud.route_dgx_cloud("quantum_circuit", {})
            assert result["provider"] == "dgx_cloud"
            assert result["status"] == "unavailable"
            assert result.get("stub") is True
            assert "NGC_API_KEY" in result["message"]

    def test_route_brev_dev_with_api_key(self, bridge_cpu):
        with patch.dict("os.environ", {"BREV_API_KEY": "test_key"}):
            result = bridge_cpu.cloud.route_brev_dev("quantum_circuit", {}, gpu_type="H100")
            assert result["status"] == "unavailable"
            assert result.get("stub") is True
            assert result["executed"] is False
            assert result["gpu_type"] == "H100"
            assert result["api_key_configured"] is True

    def test_route_dgx_cloud_with_api_key(self, bridge_cpu):
        with patch.dict("os.environ", {"NGC_API_KEY": "test_key"}):
            result = bridge_cpu.cloud.route_dgx_cloud("quantum_circuit", {}, gpu_type="H100")
            assert result["status"] == "unavailable"
            assert result.get("stub") is True
            assert result["executed"] is False
            assert result["gpu_type"] == "H100"
            assert result["api_key_configured"] is True

    def test_no_hardcoded_api_keys(self, bridge_cpu):
        # Ensure no API keys are hardcoded in the stub
        import inspect

        source = inspect.getsource(CloudComputeStub)
        assert "sk-" not in source
        assert "api_key = " not in source or "api_key = os" in source

    def test_estimate_brev_cost(self, bridge_cpu):
        cost = bridge_cpu.cloud._estimate_brev_cost("A100", 2.0)
        assert cost == pytest.approx(4.0)

    def test_estimate_dgx_cost(self, bridge_cpu):
        cost = bridge_cpu.cloud._estimate_dgx_cost("H100", 1.0)
        assert cost == pytest.approx(6.0)

    def test_hash_config(self, bridge_cpu):
        h1 = bridge_cpu.cloud._hash_config({"a": 1, "b": 2})
        h2 = bridge_cpu.cloud._hash_config({"b": 2, "a": 1})
        assert h1 == h2
        assert len(h1) == 16


# ═══════════════════════════════════════════════════════════════════
# Bridge Router
# ═══════════════════════════════════════════════════════════════════


class TestRouteToCloud:
    """Test route_to_cloud method."""

    def test_route_to_cloud_brev(self, bridge_cpu):
        with patch.dict("os.environ", {}, clear=True):
            result = bridge_cpu.route_to_cloud("brev", "quantum_circuit", {})
            assert result["provider"] == "brev.dev"

    def test_route_to_cloud_dgx(self, bridge_cpu):
        with patch.dict("os.environ", {}, clear=True):
            result = bridge_cpu.route_to_cloud("dgx", "quantum_circuit", {})
            assert result["provider"] == "dgx_cloud"

    def test_route_to_cloud_unknown(self, bridge_cpu):
        result = bridge_cpu.route_to_cloud("unknown", "quantum_circuit", {})
        assert result["status"] == "error"
        assert "Unknown cloud provider" in result["message"]


# ═══════════════════════════════════════════════════════════════════
# Benchmark
# ═══════════════════════════════════════════════════════════════════


class TestBenchmark:
    """Test benchmark method."""

    def test_benchmark(self, bridge_cpu):
        mock_result = NvidiaBridgeResult(status="success", mode=CudaMode.CPU, execution_time=0.01)
        with patch.object(bridge_cpu, "run_simulation", return_value=mock_result):
            result = bridge_cpu.benchmark({"grid_size": 10}, num_runs=2)
            assert "nvidia_avg_time" in result
            assert "speedup" in result
            assert result["mode"] == "cpu"

    def test_estimate_legacy_time(self, bridge_cpu):
        t = bridge_cpu._estimate_legacy_time({"num_particles": 100, "num_steps": 10})
        assert t > 0


# ═══════════════════════════════════════════════════════════════════
# Metadata
# ═══════════════════════════════════════════════════════════════════


class TestMetadata:
    """Test metadata."""

    def test_get_metadata(self):
        meta = NvidiaBridge.get_metadata()
        assert meta["name"] == "NvidiaBridge"
        assert "cublas_linear_algebra" in meta["capabilities"]
        assert "cuquantum_quantum_circuits" in meta["capabilities"]


# ═══════════════════════════════════════════════════════════════════
# Representation
# ═══════════════════════════════════════════════════════════════════


class TestRepresentation:
    """Test __repr__."""

    def test_repr(self, bridge_cpu):
        r = repr(bridge_cpu)
        assert "NvidiaBridge" in r
        assert "cpu" in r


# ═══════════════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════════════


class TestSingleton:
    """Test get_nvidia_bridge singleton."""

    def test_singleton(self):
        with patch.object(NvidiaBridge, "_detect_mode", return_value=CudaMode.UNAVAILABLE):
            with patch.object(NvidiaBridge, "_initialize", return_value=False):
                b1 = get_nvidia_bridge()
                b2 = get_nvidia_bridge()
                assert b1 is b2


# ═══════════════════════════════════════════════════════════════════
# Cost Report Integration
# ═══════════════════════════════════════════════════════════════════


class TestCostReportIntegration:
    """Test cost tracking integration."""

    def test_cost_report_after_simulation(self, bridge_cpu):
        bridge_cpu.reset_cost_tracker()
        result = bridge_cpu.run_simulation(
            {
                "type": "linear_algebra",
                "a": [[1.0, 0.0], [0.0, 1.0]],
                "b": [[1.0, 0.0], [0.0, 1.0]],
            }
        )
        assert result.status == "partial"
        report = bridge_cpu.get_cost_report()
        assert "cuda_hours" in report
        assert report["total_kernel_calls"] >= 0

    def test_reset_cost_tracker(self, bridge_cpu):
        bridge_cpu._cost_tracker.record_kernel(memory_mb=100.0)
        bridge_cpu.reset_cost_tracker()
        report = bridge_cpu.get_cost_report()
        assert report["peak_memory_mb"] == 0.0
        assert report["total_kernel_calls"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
