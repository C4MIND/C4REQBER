"""GPU compute providers — local and cloud GPU delegation."""

from __future__ import annotations

from .gpu_providers import (
    GPU_PROVIDERS,
    detect_local_gpu,
    list_available_providers,
)
from .vastai_runner import VastAIRunner


__all__ = [
    "GPU_PROVIDERS",
    "detect_local_gpu",
    "list_available_providers",
    "VastAIRunner",
]
