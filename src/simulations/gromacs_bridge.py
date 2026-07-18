# SPDX-License-Identifier: AGPL-3.0
"""GROMACS bridge via gmxapi (preferred) or ``gmx mdrun`` CLI fallback.

Install: conda install -c conda-forge gromacs && pip install gmxapi
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult


logger = logging.getLogger(__name__)


class GromacsBridge(BaseSimulationAdapter):
    """Bridge to GROMACS molecular dynamics via gmxapi or CLI mdrun."""

    _engine_name = "gromacs"
    _package_checks = ["gmxapi"]
    _install_hint = "conda install -c conda-forge gromacs && pip install gmxapi"

    def is_available(self) -> bool:
        if super().is_available():
            return True
        return bool(shutil.which("gmx") or shutil.which("mdrun"))

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            tpr = data.get("tpr") or self._params.get("tpr")
            if not tpr:
                return {
                    "status": "unavailable",
                    "stub": True,
                    "executed": False,
                    "note": "Provide tpr= path to a GROMACS .tpr — MD not run",
                }
            tpr_path = Path(str(tpr)).expanduser().resolve()
            if not tpr_path.is_file():
                return {
                    "status": "unavailable",
                    "stub": True,
                    "executed": False,
                    "tpr": str(tpr_path),
                    "note": f"tpr file not found: {tpr_path}",
                }

            nsteps = data.get("nsteps", self._params.get("nsteps"))
            deffnm = (
                data.get("deffnm") or self._params.get("deffnm") or str(tpr_path.with_suffix(""))
            )

            if self._can_import("gmxapi"):
                return self._run_gmxapi(tpr_path, nsteps=nsteps, deffnm=deffnm)
            return self._run_cli_mdrun(tpr_path, nsteps=nsteps, deffnm=deffnm)

        return self._run_wrapped(_run, input_data)

    def _run_gmxapi(self, tpr_path: Path, *, nsteps: int | None, deffnm: str) -> dict[str, Any]:
        """Documented gmxapi path: read_tpr → mdrun → run()."""
        import gmxapi as gmx

        version = getattr(gmx, "__version__", "unknown")
        simulation_input = gmx.read_tpr(str(tpr_path))
        if nsteps is not None and hasattr(gmx, "modify_input"):
            simulation_input = gmx.modify_input(
                input=simulation_input, parameters={"nsteps": int(nsteps)}
            )
        runtime_args: dict[str, Any] = {"-deffnm": deffnm}
        md = gmx.mdrun(simulation_input, runtime_args=runtime_args)
        md.run()
        trajectory = None
        try:
            trajectory = md.output.trajectory.result()
        except Exception as exc:  # pragma: no cover - output shape varies by gmxapi version
            logger.debug("gmxapi trajectory result unavailable: %s", exc)
        return {
            "executed": True,
            "stub": False,
            "backend": "gmxapi",
            "gmxapi_version": version,
            "tpr": str(tpr_path),
            "deffnm": deffnm,
            "nsteps": nsteps,
            "trajectory": trajectory,
            "note": "gmxapi.mdrun().run() completed",
        }

    def _run_cli_mdrun(self, tpr_path: Path, *, nsteps: int | None, deffnm: str) -> dict[str, Any]:
        """Fallback when gmxapi is missing but ``gmx``/``mdrun`` is on PATH."""
        gmx = shutil.which("gmx")
        mdrun = shutil.which("mdrun")
        if gmx:
            cmd = [gmx, "mdrun", "-s", str(tpr_path), "-deffnm", deffnm]
        elif mdrun:
            cmd = [mdrun, "-s", str(tpr_path), "-deffnm", deffnm]
        else:
            return {
                "status": "unavailable",
                "stub": True,
                "executed": False,
                "note": "Neither gmxapi nor gmx/mdrun CLI available",
            }
        if nsteps is not None:
            cmd.extend(["-nsteps", str(int(nsteps))])
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(
                f"gmx mdrun failed ({proc.returncode}): {(proc.stderr or proc.stdout)[:500]}"
            )
        return {
            "executed": True,
            "stub": False,
            "backend": "cli",
            "tpr": str(tpr_path),
            "deffnm": deffnm,
            "nsteps": nsteps,
            "cmd": cmd,
            "stdout_tail": (proc.stdout or "")[-400:],
            "note": "CLI mdrun completed",
        }
