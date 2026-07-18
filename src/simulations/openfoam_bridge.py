# SPDX-License-Identifier: AGPL-3.0
"""OpenFOAM bridge via foamlib — runs the case solver (not load-only).

Install: pip install foamlib
Requires: OpenFOAM on PATH (blockMesh / simpleFoam / foamVersion)
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult


logger = logging.getLogger(__name__)


class OpenFOAMBridge(BaseSimulationAdapter):
    """Bridge to OpenFOAM using foamlib.FoamCase.run()."""

    _engine_name = "openfoam"
    _package_checks = ["foamlib"]
    _install_hint = (
        "pip install foamlib  (requires OpenFOAM installed: blockMesh/simpleFoam on PATH)"
    )

    def is_available(self) -> bool:
        if not super().is_available():
            return False
        return bool(
            shutil.which("blockMesh")
            or shutil.which("simpleFoam")
            or shutil.which("foamVersion")
            or shutil.which("foamExec")
        )

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            case_dir = (data or {}).get("case_dir") or self._params.get("case_dir")
            if not case_dir:
                return {
                    "status": "unavailable",
                    "stub": True,
                    "executed": False,
                    "note": "OpenFOAM case_dir required",
                }
            case_path = Path(str(case_dir)).expanduser().resolve()
            if not case_path.is_dir():
                return {
                    "status": "unavailable",
                    "stub": True,
                    "executed": False,
                    "case_path": str(case_path),
                    "note": f"case_dir is not a directory: {case_path}",
                }

            from foamlib import FoamCase

            case = FoamCase(case_path)
            # foamlib: FoamCase.run() executes Allrun / application sequence
            if not hasattr(case, "run"):
                raise RuntimeError("foamlib.FoamCase has no run() — upgrade foamlib")
            case.run()
            return {
                "executed": True,
                "stub": False,
                "case_path": str(case_path),
                "backend": "foamlib.FoamCase.run",
                "note": "OpenFOAM case.run() completed",
            }

        return self._run_wrapped(_run, input_data)
