"""Tests for src/compute/ — GPU provider definitions and dashboard."""
from __future__ import annotations

from dataclasses import dataclass


def test_gpu_providers_import():
    from src.compute.gpu_providers import GPU_PROVIDERS
    assert isinstance(GPU_PROVIDERS, dict)
    assert "nvidia_cuda" in GPU_PROVIDERS
    assert "apple_metal" in GPU_PROVIDERS
    assert "vast_ai" in GPU_PROVIDERS


def test_gpu_providers_structure():
    from src.compute.gpu_providers import GPU_PROVIDERS
    for name, info in GPU_PROVIDERS.items():
        assert "type" in info, f"{name} missing type"
        assert info["type"] in ("local", "cloud")


def test_gpu_dashboard_instantiation():
    from src.compute.gpu_dashboard import GPUComputeDashboard, GPUStatus
    db = GPUComputeDashboard()
    assert db is not None


def test_gpu_status_dataclass():
    from src.compute.gpu_dashboard import GPUStatus
    status = GPUStatus(
        provider="nvidia_cuda",
        gpu_name="Tesla V100",
        memory_total_mb=16384,
        memory_used_mb=8192,
        utilization_pct=50.0,
        price_per_hr=0.0,
        available=True,
    )
    assert status.provider == "nvidia_cuda"
    assert status.available is True
    assert status.memory_total_mb == 16384
