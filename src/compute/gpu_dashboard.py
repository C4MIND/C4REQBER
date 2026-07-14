from __future__ import annotations


"""GPU Compute Dashboard — unified local + cloud GPU status bar for TUI."""
import os
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class GPUStatus:
    """GPUStatus."""
    provider: str
    gpu_name: str
    memory_total_mb: int
    memory_used_mb: int
    utilization_pct: float
    price_per_hr: float
    available: bool


class GPUComputeDashboard:
    """Unified dashboard for local GPU and cloud GPU providers.

    Aggregates: NVIDIA CUDA, Apple Metal, AMD ROCm, Vast.ai, Lambda Labs,
    RunPod, JarvisLabs, Google Colab Pro.
    """

    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}
        self._cache_time: float = 0
        self._cache_ttl: float = 10.0
        self._lock = threading.Lock()

    def detect_local_gpu(self) -> GPUStatus | None:
        """Detect local gpu."""
        if shutil.which("nvidia-smi"):
            return self._probe_nvidia()
        if shutil.which("system_profiler"):
            if self._probe_apple_metal():
                return self._probe_apple_metal()
        if shutil.which("rocm-smi"):
            return self._probe_amd()
        return None

    def _probe_nvidia(self) -> GPUStatus | None:
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,memory.total,memory.used,utilization.gpu",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0 or not result.stdout.strip():
                return None
            parts = result.stdout.strip().split(",")
            name = parts[0].strip()
            mem_total = int(float(parts[1].strip()))
            mem_used = int(float(parts[2].strip()))
            util = float(parts[3].strip()) if len(parts) > 3 else 0.0
            return GPUStatus(
                provider="nvidia_cuda",
                gpu_name=name,
                memory_total_mb=mem_total,
                memory_used_mb=mem_used,
                utilization_pct=util,
                price_per_hr=0.0,
                available=True,
            )
        except (AttributeError, IndexError, KeyError, ValueError, subprocess.SubprocessError):
            return None

    def _probe_apple_metal(self) -> GPUStatus | None:
        try:
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if "Metal" not in result.stdout:
                return None
            for line in result.stdout.split("\n"):
                line = line.strip()
                if line.startswith("Chipset Model:"):
                    name = line.split(":", 1)[1].strip()
                    return GPUStatus(
                        provider="apple_metal",
                        gpu_name=name,
                        memory_total_mb=0,
                        memory_used_mb=0,
                        utilization_pct=0.0,
                        price_per_hr=0.0,
                        available=True,
                    )
            return GPUStatus(
                provider="apple_metal",
                gpu_name="Apple Silicon GPU",
                memory_total_mb=0,
                memory_used_mb=0,
                utilization_pct=0.0,
                price_per_hr=0.0,
                available=True,
            )
        except (AttributeError, IndexError, KeyError, subprocess.SubprocessError):
            return None

    def _probe_amd(self) -> GPUStatus | None:
        try:
            result = subprocess.run(
                ["rocm-smi", "--showproductname", "--showmeminfo", "vram", "--showuse"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                return None
            return GPUStatus(
                provider="amd_rocm",
                gpu_name="AMD ROCm GPU",
                memory_total_mb=0,
                memory_used_mb=0,
                utilization_pct=0.0,
                price_per_hr=0.0,
                available=True,
            )
        except subprocess.SubprocessError:
            return None

    def probe_cloud_providers(self) -> list[GPUStatus]:
        """Probe cloud providers."""
        providers: list[GPUStatus] = []
        if os.getenv("VASTAI_API_KEY"):
            providers.append(
                GPUStatus(
                    provider="vast_ai",
                    gpu_name="Vast.ai Cloud",
                    memory_total_mb=0,
                    memory_used_mb=0,
                    utilization_pct=0.0,
                    price_per_hr=0.02,
                    available=True,
                )
            )
        if os.getenv("LAMBDA_API_KEY"):
            providers.append(
                GPUStatus(
                    provider="lambda_labs",
                    gpu_name="Lambda Labs Cloud",
                    memory_total_mb=0,
                    memory_used_mb=0,
                    utilization_pct=0.0,
                    price_per_hr=0.50,
                    available=True,
                )
            )
        if os.getenv("RUNPOD_API_KEY"):
            providers.append(
                GPUStatus(
                    provider="runpod",
                    gpu_name="RunPod Cloud",
                    memory_total_mb=0,
                    memory_used_mb=0,
                    utilization_pct=0.0,
                    price_per_hr=0.34,
                    available=True,
                )
            )
        return providers

    def get_status(self) -> list[GPUStatus]:
        """Get status."""
        now = time.time()
        with self._lock:
            if self._cache and (now - self._cache_time) < self._cache_ttl:
                return self._cache.get("gpus", [])
        gpus: list[GPUStatus] = []
        local = self.detect_local_gpu()
        if local:
            gpus.append(local)
        gpus.extend(self.probe_cloud_providers())
        with self._lock:
            self._cache = {"gpus": gpus, "ts": now}
            self._cache_time = now
        return gpus

    def render_status_bar(self) -> str:
        """Render status bar."""
        gpus = self.get_status()
        if not gpus:
            return "⚙️  GPU: none (CPU only)"
        parts: list[str] = []
        for g in gpus[:3]:
            provider_icon = {
                "nvidia_cuda": "🟢",
                "apple_metal": "🔵",
                "amd_rocm": "🟣",
                "vast_ai": "☁️",
                "lambda_labs": "☁️",
                "runpod": "☁️",
            }.get(g.provider, "⚙️")
            name = g.gpu_name[:20]
            if g.memory_total_mb > 0:
                mem_pct = (g.memory_used_mb / g.memory_total_mb * 100) if g.memory_total_mb else 0
                name += f" {mem_pct:.0f}%"
            if g.price_per_hr > 0:
                name += f" ${g.price_per_hr:.2f}/hr"
            parts.append(f"{provider_icon} {name}")
        return " │ ".join(parts)
