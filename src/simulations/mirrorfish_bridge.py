# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""Mirrorfish integration — ultra-high-performance simulation backend.

Mirrorfish: https://github.com/username/mirrorfish (awaiting URL confirmation)
Described as: super-complex simulations for scientific computing.

Integration pattern: subprocess runner with JSON IPC, like Newton Physics.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
from typing import Any


logger = logging.getLogger(__name__)

MIRRORFISH_PATH = os.environ.get("MIRRORFISH_PATH", "mirrorfish")


def is_available() -> bool:
    try:
        result = subprocess.run([MIRRORFISH_PATH, "--version"], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False


def run_simulation(config: dict[str, Any]) -> dict[str, Any]:
    """Run Mirrorfish simulation with JSON config."""
    if not is_available():
        return {"status": "unavailable", "error": "mirrorfish not found. Set MIRRORFISH_PATH."}

    try:
        config_json = json.dumps(config)
        result = subprocess.run(
            [MIRRORFISH_PATH, "run", "--config", "-"],
            input=config_json, capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            return {"status": "ok", "backend": "mirrorfish", "output": result.stdout[:2000]}
        return {"status": "error", "backend": "mirrorfish", "error": result.stderr[:500]}
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "backend": "mirrorfish", "error": "Simulation timed out (120s)"}
    except Exception as e:
        logger.debug("Mirrorfish failed: %s", e)
        return {"status": "error", "backend": "mirrorfish", "error": str(e)}
