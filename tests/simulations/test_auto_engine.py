"""Tests for src/simulations/auto_engine.py."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest

from simulations.auto_engine import PhysicsAutoDetector, get_detector


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def detector():
    """Fresh PhysicsAutoDetector."""
    return PhysicsAutoDetector()


@pytest.fixture
def detector_initialized():
    """PhysicsAutoDetector with GPU detection mocked."""
    d = PhysicsAutoDetector()
    d._initialized = True
    d._cuda_available = True
    d._gpu_name = "NVIDIA RTX 4090"
    d._gpu_memory_gb = 24.0
    return d


# ═══════════════════════════════════════════════════════════════════
# Initialization
# ═══════════════════════════════════════════════════════════════════


class TestPhysicsAutoDetectorInit:
    """Test PhysicsAutoDetector initialization."""

    def test_init(self, detector):
        assert detector._gpu_name is None
        assert detector._gpu_memory_gb is None
        assert detector._cuda_available is None
        assert detector._initialized is False
        assert detector.platform is not None
        assert detector.machine is not None


# ═══════════════════════════════════════════════════════════════════
# GPU Detection
# ═══════════════════════════════════════════════════════════════════


class TestGPUDetection:
    """Test GPU detection logic."""

    def test_detect_gpu_no_torch_no_pynvml(self, detector):
        with patch("platform.system", return_value="Linux"):
            with patch("platform.machine", return_value="x86_64"):
                with patch.dict("sys.modules", {"torch": None, "pynvml": None}):
                    detector._detect_gpu()
                    assert detector._cuda_available is False
                    assert detector._gpu_name is None
                    assert detector._gpu_memory_gb == 0.0

    def test_detect_gpu_with_torch_cuda(self, detector):
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.get_device_name.return_value = "NVIDIA A100"
        mock_device_props = MagicMock()
        mock_device_props.total_memory = 80 * (1024 ** 3)
        mock_torch.cuda.get_device_properties.return_value = mock_device_props

        with patch.dict("sys.modules", {"torch": mock_torch}):
            detector._detect_gpu()
            assert detector._cuda_available is True
            assert detector._gpu_name == "NVIDIA A100"
            assert detector._gpu_memory_gb == 80.0

    def test_detect_gpu_with_pynvml(self, detector):
        mock_pynvml = MagicMock()
        mock_pynvml.nvmlInit = MagicMock()
        mock_pynvml.nvmlDeviceGetCount.return_value = 1
        mock_handle = MagicMock()
        mock_pynvml.nvmlDeviceGetHandleByIndex.return_value = mock_handle
        mock_pynvml.nvmlDeviceGetName.return_value = b"NVIDIA V100"
        mock_mem = MagicMock()
        mock_mem.total = 32 * (1024 ** 3)
        mock_pynvml.nvmlDeviceGetMemoryInfo.return_value = mock_mem
        mock_pynvml.nvmlShutdown = MagicMock()

        with patch.dict("sys.modules", {"torch": None, "pynvml": mock_pynvml}):
            detector._detect_gpu()
            assert detector._cuda_available is True
            assert detector._gpu_name == "NVIDIA V100"
            assert detector._gpu_memory_gb == 32.0

    def test_detect_gpu_pynvml_bytes_name(self, detector):
        mock_pynvml = MagicMock()
        mock_pynvml.nvmlInit = MagicMock()
        mock_pynvml.nvmlDeviceGetCount.return_value = 1
        mock_handle = MagicMock()
        mock_pynvml.nvmlDeviceGetHandleByIndex.return_value = mock_handle
        mock_pynvml.nvmlDeviceGetName.return_value = b"NVIDIA T4"
        mock_mem = MagicMock()
        mock_mem.total = 16 * (1024 ** 3)
        mock_pynvml.nvmlDeviceGetMemoryInfo.return_value = mock_mem
        mock_pynvml.nvmlShutdown = MagicMock()

        with patch.dict("sys.modules", {"torch": None, "pynvml": mock_pynvml}):
            detector._detect_gpu()
            assert detector._gpu_name == "NVIDIA T4"

    def test_detect_gpu_apple_silicon(self, detector):
        with patch("platform.system", return_value="Darwin"):
            with patch("platform.machine", return_value="arm64"):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(
                        returncode=0,
                        stdout="Chipset Model: Apple M1 Pro\n  Memory: 16 GB\n",
                    )
                    detector._detect_gpu()
                    assert detector._gpu_name == "Apple M1 Pro"
                    assert detector._gpu_memory_gb == 16.0

    def test_detect_gpu_apple_silicon_no_profiler(self, detector):
        with patch("platform.system", return_value="Darwin"):
            with patch("platform.machine", return_value="arm64"):
                with patch("subprocess.run", side_effect=FileNotFoundError):
                    detector._detect_gpu()
                    assert detector._gpu_name is None

    def test_detect_gpu_apple_silicon_parse_error(self, detector):
        with patch("platform.system", return_value="Darwin"):
            with patch("platform.machine", return_value="arm64"):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(
                        returncode=0,
                        stdout="Chipset Model: Apple M1\n  Memory: unknown\n",
                    )
                    detector._detect_gpu()
                    assert detector._gpu_name == "Apple M1"
                    assert detector._gpu_memory_gb == 0.0


# ═══════════════════════════════════════════════════════════════════
# Properties
# ═══════════════════════════════════════════════════════════════════


class TestProperties:
    """Test detector properties."""

    def test_has_nvidia_gpu_true(self, detector_initialized):
        assert detector_initialized.has_nvidia_gpu is True

    def test_has_nvidia_gpu_false(self, detector):
        detector._initialized = True
        detector._cuda_available = False
        assert detector.has_nvidia_gpu is False

    def test_has_apple_silicon(self, detector):
        with patch("platform.system", return_value="Darwin"):
            with patch("platform.machine", return_value="arm64"):
                assert detector.has_apple_silicon is True

    def test_has_apple_silicon_false(self, detector):
        with patch("platform.system", return_value="Linux"):
            with patch("platform.machine", return_value="x86_64"):
                assert detector.has_apple_silicon is False

    def test_has_gpu_nvidia(self, detector_initialized):
        assert detector_initialized.has_gpu is True

    def test_has_gpu_apple(self, detector):
        with patch("platform.system", return_value="Darwin"):
            with patch("platform.machine", return_value="arm64"):
                assert detector.has_gpu is True

    def test_has_gpu_none(self, detector):
        detector._initialized = True
        detector._cuda_available = False
        with patch("platform.system", return_value="Linux"):
            with patch("platform.machine", return_value="x86_64"):
                assert detector.has_gpu is False

    def test_gpu_name(self, detector_initialized):
        assert detector_initialized.gpu_name == "NVIDIA RTX 4090"

    def test_gpu_name_none(self, detector):
        detector._initialized = True
        detector._gpu_name = None
        assert detector.gpu_name == "No GPU detected"

    def test_gpu_memory_gb(self, detector_initialized):
        assert detector_initialized.gpu_memory_gb == 24.0

    def test_gpu_memory_gb_none(self, detector):
        detector._initialized = True
        detector._gpu_memory_gb = None
        assert detector.gpu_memory_gb is None


# ═══════════════════════════════════════════════════════════════════
# Recommended Engine
# ═══════════════════════════════════════════════════════════════════


class TestRecommendedEngine:
    """Test get_recommended_engine method."""

    def test_robotics_domain(self, detector_initialized):
        assert detector_initialized.get_recommended_engine("robotics") == "jaxsim"

    def test_quantum_domain(self, detector_initialized):
        assert detector_initialized.get_recommended_engine("quantum") == "schr"

    def test_atomistic_domain(self, detector_initialized):
        assert detector_initialized.get_recommended_engine("atomistic") == "torchsim"

    def test_nvidia_gpu(self, detector_initialized):
        assert detector_initialized.get_recommended_engine("general") == "newton"

    def test_apple_silicon(self, detector):
        with patch("platform.system", return_value="Darwin"):
            with patch("platform.machine", return_value="arm64"):
                assert detector.get_recommended_engine("general") == "jaxsim"

    def test_no_gpu(self, detector):
        detector._initialized = True
        detector._cuda_available = False
        with patch("platform.system", return_value="Linux"):
            with patch("platform.machine", return_value="x86_64"):
                assert detector.get_recommended_engine("general") == "torchsim"


# ═══════════════════════════════════════════════════════════════════
# Detection Report
# ═══════════════════════════════════════════════════════════════════


class TestDetectionReport:
    """Test get_detection_report method."""

    def test_report_structure(self, detector_initialized):
        report = detector_initialized.get_detection_report()
        assert "platform" in report
        assert "architecture" in report
        assert "has_nvidia_gpu" in report
        assert "has_apple_silicon" in report
        assert "has_gpu" in report
        assert "gpu_name" in report
        assert "gpu_memory_gb" in report
        assert "recommended_engine" in report
        assert report["has_nvidia_gpu"] is True
        assert report["gpu_name"] == "NVIDIA RTX 4090"

    def test_report_no_gpu(self, detector):
        detector._initialized = True
        detector._cuda_available = False
        detector._gpu_name = None
        detector._gpu_memory_gb = 0.0
        with patch("platform.system", return_value="Linux"):
            with patch("platform.machine", return_value="x86_64"):
                report = detector.get_detection_report()
                assert report["has_gpu"] is False
                assert report["gpu_name"] == "No GPU detected"
                assert report["gpu_memory_gb"] == 0.0


# ═══════════════════════════════════════════════════════════════════
# Lazy Init
# ═══════════════════════════════════════════════════════════════════


class TestLazyInit:
    """Test lazy initialization."""

    def test_lazy_init_called_once(self, detector):
        with patch.object(detector, "_detect_gpu") as mock_detect:
            detector._lazy_init()
            detector._lazy_init()
            mock_detect.assert_called_once()

    def test_lazy_init_sets_flag(self, detector):
        with patch.object(detector, "_detect_gpu"):
            detector._lazy_init()
            assert detector._initialized is True


# ═══════════════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════════════


class TestSingleton:
    """Test get_detector singleton."""

    def test_singleton(self):
        d1 = get_detector()
        d2 = get_detector()
        assert d1 is d2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
