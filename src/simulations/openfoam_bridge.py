# SPDX-License-Identifier: AGPL-3.0
"""OpenFOAM bridge via foamlib — modern typed Python API for CFD.

Install: pip install foamlib
Requires: OpenFOAM installed (apt install openfoam)
"""
from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult

logger = logging.getLogger(__name__)


class OpenFOAMBridge(BaseSimulationAdapter):
    """Bridge to OpenFOAM using foamlib for case manipulation."""

    _engine_name = "openfoam"
    _package_checks = ["foamlib"]
    _install_hint = "pip install foamlib  (requires OpenFOAM installed)"

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)
        # Expected: solver, end_time, nx/ny/nz

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            from foamlib import FoamCase

            # Create a minimal cavity case in a temp dir
            with tempfile.TemporaryDirectory(prefix="c4reqber_of_") as td:
                case_path = Path(td)
                case = FoamCase(case_path)
                # foamlib can load existing tutorials; here we return a stub
                # indicating the engine is reachable.
                return {
                    "foamlib_version": getattr(FoamCase, "__version__", "unknown"),
                    "case_path": str(case_path),
                    "note": "foamlib is available; full CFD workflow requires OpenFOAM case files",
                }

        return self._run_wrapped(_run, input_data)
