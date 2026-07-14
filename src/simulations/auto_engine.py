"""Auto-detection of hardware for optimal physics engine selection."""

from __future__ import annotations

import platform
import subprocess


class PhysicsAutoDetector:
    """Auto-detect hardware and recommend physics engine."""

    def __init__(self):
        self._gpu_name: str | None = None
        self._gpu_memory_gb: float | None = None
        self._cuda_available: bool | None = None
        self._initialized: bool = False
        self._platform: str = platform.system()
        self._machine: str = platform.machine()

    @property
    def platform(self) -> str:
        """Get platform name (Darwin, Linux, Windows)."""
        return self._platform

    @property
    def machine(self) -> str:
        """Get machine architecture (arm64, x86_64)."""
        return self._machine

    def _lazy_init(self) -> None:
        if self._initialized:
            return
        self._detect_gpu()
        self._initialized = True

    def _detect_gpu(self) -> None:
        self._cuda_available = False
        self._gpu_name = None
        self._gpu_memory_gb = 0.0

        try:
            import torch
            if torch.cuda.is_available():
                self._cuda_available = True
                self._gpu_name = torch.cuda.get_device_name(0)
                self._gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                return
        except ImportError:
            pass

        try:
            import pynvml
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            if device_count > 0:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                self._cuda_available = True
                self._gpu_name = pynvml.nvmlDeviceGetName(handle)
                if isinstance(self._gpu_name, bytes):
                    self._gpu_name = self._gpu_name.decode("utf-8")
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                self._gpu_memory_gb = mem_info.total / (1024**3)
                pynvml.nvmlShutdown()
                return
        except (ImportError, Exception):
            pass

        if self.has_apple_silicon:
            try:
                result = subprocess.run(
                    ["system_profiler", "SPDisplaysDataType"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    output = result.stdout
                    for line in output.split("\n"):
                        if "Chipset Model:" in line:
                            self._gpu_name = line.split("Chipset Model:")[1].strip()
                        if "VRAM" in line or "Memory:" in line:
                            try:
                                mem_str = line.split(":")[1].strip()
                                if "GB" in mem_str:
                                    self._gpu_memory_gb = float(mem_str.replace("GB", "").strip())
                            except (ValueError, IndexError):
                                pass
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

    @property
    def has_nvidia_gpu(self) -> bool:
        """Check if has nvidia gpu."""
        self._lazy_init()
        return bool(self._cuda_available)

    @property
    def has_apple_silicon(self) -> bool:
        return platform.system() == "Darwin" and platform.machine() == "arm64"

    @property
    def has_gpu(self) -> bool:
        """Check if has gpu."""
        self._lazy_init()
        return bool(self._cuda_available) or self.has_apple_silicon

    @property
    def gpu_name(self) -> str:
        """Gpu name."""
        self._lazy_init()
        return self._gpu_name or "No GPU detected"

    @property
    def gpu_memory_gb(self) -> float:
        """Gpu memory gb."""
        self._lazy_init()
        return self._gpu_memory_gb

    def get_recommended_engine(self, domain: str = "general") -> str:
        """Get recommended engine."""
        self._lazy_init()

        domain_engines = {
            "robotics": "jaxsim",
            "quantum": "schr",
            "atomistic": "torchsim",
        }

        if domain in domain_engines:
            return domain_engines[domain]

        if self.has_nvidia_gpu:
            return "newton"
        elif self.has_apple_silicon:
            return "jaxsim"
        else:
            return "torchsim"

    def get_detection_report(self) -> dict:
        """Get detection report."""
        self._lazy_init()
        return {
            "platform": platform.system(),
            "architecture": platform.machine(),
            "has_nvidia_gpu": self.has_nvidia_gpu,
            "has_apple_silicon": self.has_apple_silicon,
            "has_gpu": self.has_gpu,
            "gpu_name": self.gpu_name,
            "gpu_memory_gb": round(self.gpu_memory_gb, 2),
            "recommended_engine": self.get_recommended_engine(),
        }


def get_detector() -> PhysicsAutoDetector:
    """Get singleton physics auto detector (backed by DI container)."""
    from src.di.container import get_container
    return get_container().get_or_register("physics_detector", PhysicsAutoDetector)
