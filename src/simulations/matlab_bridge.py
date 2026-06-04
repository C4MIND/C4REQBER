# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""MATLAB integration — 6th simulation backend.

MATLAB Engine API for Python allows running MATLAB scripts from Python.
Used for: numerical computing, control systems, signal processing, optimization.

Requires: MATLAB R2024a+ with Engine API for Python installed.
Install: cd /Applications/MATLAB_R2024a.app/extern/engines/python && python3.11 setup.py install
"""
from __future__ import annotations

import logging
import os
from typing import Any


logger = logging.getLogger(__name__)

MATLAB_AVAILABLE = False
try:
    import matlab.engine  # type: ignore[import-untyped]
    MATLAB_AVAILABLE = True
except ImportError:
    logger.debug("matlab bridge import failed", exc_info=True)
    pass


def is_available() -> bool:
    return MATLAB_AVAILABLE


def run_simulation(script: str, inputs: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run MATLAB script as simulation backend."""
    if not MATLAB_AVAILABLE:
        return {"status": "unavailable", "error": "MATLAB Engine API not installed"}
    if os.getenv("ENABLE_MATLAB", "").lower() not in ("true", "1", "yes"):
        return {"status": "disabled", "error": "MATLAB integration disabled (set ENABLE_MATLAB=true)"}

    FORBIDDEN = ("system(", "!", "eval(", "run(", "fopen(", "fwrite(", "dos(", "unix(", "web(", "urlread(")
    script_lower = script.lower()
    for tok in FORBIDDEN:
        if tok in script_lower:
            return {"status": "rejected", "error": f"MATLAB script contains forbidden token: {tok}"}

    try:
        eng = matlab.engine.start_matlab()
        if inputs:
            for key, val in inputs.items():
                eng.workspace[key] = float(val) if isinstance(val, (int, float)) else val
        eng.eval(script, nargout=0)
        result = eng.workspace.get("result", None)
        eng.quit()
        return {
            "status": "ok",
            "backend": "matlab",
            "result": str(result)[:500] if result else "",
        }
    except Exception as e:
        logger.debug("MATLAB simulation failed: %s", e)
        return {"status": "error", "backend": "matlab", "error": str(e)}
