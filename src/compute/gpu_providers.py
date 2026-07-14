from __future__ import annotations


"""Pre-integrated GPU providers for local and cloud simulation."""
import os
import shutil
from typing import Any


GPU_PROVIDERS: dict[str, dict[str, Any]] = {
    "nvidia_cuda": {
        "type": "local",
        "check": "nvidia-smi",
        "setup": "pip install numba[cuda]",
        "free": True,
    },
    "apple_metal": {
        "type": "local",
        "check": "system_profiler SPDisplaysDataType",
        "setup": "pip install torch torchvision",
        "free": True,
    },
    "amd_rocm": {
        "type": "local",
        "check": "rocm-smi",
        "setup": "pip install torch --index-url https://download.pytorch.org/whl/rocm",
        "free": True,
    },
    "vast_ai": {
        "type": "cloud",
        "api": "https://console.vast.ai/api/v0/",
        "min_price": "$0.02/hr Tesla V100",
        "setup": "Add VASTAI_API_KEY to .env",
    },
    "lambda_labs": {
        "type": "cloud",
        "api": "https://cloud.lambdalabs.com/api/v1/",
        "min_price": "$0.50/hr A10",
        "setup": "Add LAMBDA_API_KEY to .env",
    },
    "runpod": {
        "type": "cloud",
        "api": "https://api.runpod.io/v2/",
        "min_price": "$0.34/hr RTX 3090",
        "setup": "Add RUNPOD_API_KEY to .env",
    },
    "jarvislabs": {
        "type": "cloud",
        "api": "https://jarvislabs.ai/api/",
        "min_price": "$0.33/hr A4000",
        "setup": "Add JARVISLABS_API_KEY to .env",
    },
    "colab_pro": {
        "type": "cloud",
        "api": None,
        "min_price": "$10/mo V100/T4",
        "setup": "Google Colab Pro subscription",
    },
}


def detect_local_gpu() -> str:
    """Auto-detect local GPU availability.

    Returns the provider name key from GPU_PROVIDERS,
    or 'cpu_only' if no GPU is detected.
    """
    if shutil.which("nvidia-smi"):
        return "nvidia_cuda"
    if shutil.which("system_profiler"):
        return "apple_metal"
    if shutil.which("rocm-smi"):
        return "amd_rocm"
    return "cpu_only"


def list_available_providers() -> list[dict[str, Any]]:
    """List all configured and available GPU providers.

    Includes the auto-detected local GPU (if any) plus
    any cloud providers whose API keys are set in the environment.
    """
    providers: list[dict[str, Any]] = []
    local = detect_local_gpu()
    if local != "cpu_only":
        providers.append(GPU_PROVIDERS[local])
    for name in ["vast_ai", "lambda_labs", "runpod", "jarvislabs"]:
        env_key = f"{name.upper()}_API_KEY"
        if os.getenv(env_key):
            providers.append(GPU_PROVIDERS[name])
    return providers
