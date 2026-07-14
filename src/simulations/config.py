# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""Simulation Configuration — hardware-aware simulation orchestrator.

Reads ~/.c4reqber/simulations.json. Controls which sim engines run based on:
- User's hardware (Metal/CUDA/CPU)
- User's budget (vast.ai key + cost limit)
- User's mode preference (auto|gpu|cpu_only|off)

Integrated into pipeline Step 7 and Step 11 (output generation).
"""
from __future__ import annotations

import json
import logging
import os
import platform
import subprocess
from dataclasses import dataclass
from pathlib import Path


logger = logging.getLogger(__name__)

CONFIG_PATH = Path.home() / ".c4reqber" / "simulations.json"
DEFAULT_CONFIG = {
    "mode": "auto",
    "cost_limit_per_run": 5.00,
    "fallback_to_protocol": True,
    "providers": {
        "vastai": {"api_key": "", "gpu_type": "RTX_4090"},
        "local": {"cuda": False, "metal": False},
    },
}


@dataclass
class SimulationConfig:
    """SimulationConfig."""
    mode: str = "auto"  # "auto" | "gpu" | "cpu_only" | "off"
    cost_limit_per_run: float = 5.00
    fallback_to_protocol: bool = True
    vastai_key: str = ""
    gpu_type: str = "RTX_4090"
    local_cuda: bool = False
    local_metal: bool = False

    @classmethod
    def load(cls) -> SimulationConfig:
        """Load."""
        os.makedirs(CONFIG_PATH.parent, exist_ok=True)
        if not CONFIG_PATH.exists():
            _save_default()
            return cls._from_dict(DEFAULT_CONFIG)
        try:
            data = json.loads(CONFIG_PATH.read_text())
            return cls._from_dict(data)
        except Exception:
            return cls._from_dict(DEFAULT_CONFIG)

    @classmethod
    def _from_dict(cls, data: dict) -> SimulationConfig:
        providers = data.get("providers", {})
        local = providers.get("local", {})
        vastai = providers.get("vastai", {})
        return cls(
            mode=data.get("mode", "auto"),
            cost_limit_per_run=float(data.get("cost_limit_per_run", 5.00)),
            fallback_to_protocol=data.get("fallback_to_protocol", True),
            vastai_key=vastai.get("api_key", "") or os.environ.get("VASTAI_API_KEY", ""),
            gpu_type=vastai.get("gpu_type", "RTX_4090"),
            local_cuda=local.get("cuda", False),
            local_metal=local.get("metal", False),
        )

    def save(self) -> None:
        """Save."""
        data = {
            "mode": self.mode,
            "cost_limit_per_run": self.cost_limit_per_run,
            "fallback_to_protocol": self.fallback_to_protocol,
            "providers": {
                "vastai": {"api_key": self.vastai_key, "gpu_type": self.gpu_type},
                "local": {"cuda": self.local_cuda, "metal": self.local_metal},
            },
        }
        os.makedirs(CONFIG_PATH.parent, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(data, indent=2))

    @property
    def can_run_gpu(self) -> bool:
        return bool(self.vastai_key) or self.local_cuda or self.local_metal

    @property
    def should_run_simulations(self) -> bool:
        """Determine if should run simulations."""
        if self.mode == "off":
            return False
        if self.mode == "cpu_only":
            return True
        if self.mode == "gpu":
            return self.can_run_gpu
        return True

    @property
    def should_generate_protocol(self) -> bool:
        """Determine if should generate protocol."""
        if self.mode == "off":
            return self.fallback_to_protocol
        if self.mode == "cpu_only" and not self.can_run_gpu:
            return self.fallback_to_protocol
        return True


def _save_default() -> None:
    os.makedirs(CONFIG_PATH.parent, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, indent=2))


def detect_hardware() -> dict[str, bool]:
    """Auto-detect available compute hardware."""
    hw = {"metal": False, "cuda": False, "nvidia_gpu": False, "apple_gpu": False}

    # Apple Silicon (Metal via MPS)
    if platform.system() == "Darwin" and platform.processor() == "arm":
        hw["apple_gpu"] = True
        try:
            import torch
            hw["metal"] = torch.backends.mps.is_available()
        except Exception:
            logger.debug("Provider check failed", exc_info=True)

            pass

    # NVIDIA GPU (CUDA)
    try:
        result = subprocess.run(["nvidia-smi"], capture_output=True, timeout=5)
        hw["nvidia_gpu"] = result.returncode == 0
        try:
            import torch
            hw["cuda"] = torch.cuda.is_available()
        except Exception:
            logger.debug("Provider check failed", exc_info=True)

            pass
    except Exception:
        logger.debug("Hardware detection failed", exc_info=True)
        pass

    return hw


def auto_configure() -> SimulationConfig:
    """Auto configure."""
    cfg = SimulationConfig.load()
    hw = detect_hardware()

    if hw["cuda"] or hw["metal"]:
        cfg.local_cuda = hw["cuda"]
        cfg.local_metal = hw["metal"]
        if cfg.mode == "auto":
            cfg.mode = "gpu"
        logger.info("GPU detected: CUDA=%s Metal=%s → mode=%s", hw["cuda"], hw["metal"], cfg.mode)
    else:
        if cfg.mode == "auto":
            cfg.mode = "cpu_only"
        logger.info("No GPU detected → mode=cpu_only")

    cfg.save()
    return cfg
