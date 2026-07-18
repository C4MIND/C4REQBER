# SPDX-License-Identifier: AGPL-3.0
"""Quantum ESPRESSO bridge — real ``pw.x`` CLI (preferred) or AiiDA submit.

Install QE binaries: ``pw.x`` on PATH, pass ``input_file=``.
Optional: pip install aiida-quantumespresso for AiiDA workchain path.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult


logger = logging.getLogger(__name__)


class QuantumEspressoBridge(BaseSimulationAdapter):
    """Bridge to Quantum ESPRESSO via pw.x subprocess or AiiDA."""

    _engine_name = "quantum_espresso"
    # Prefer pw.x path; aiida is optional enhancement
    _package_checks: list[str] = []
    _install_hint = (
        "Install Quantum ESPRESSO so pw.x is on PATH; pass input_file=. "
        "Optional: pip install aiida-quantumespresso for AiiDA workchains"
    )

    def is_available(self) -> bool:
        # Importable aiida alone is not enough — need pw.x or explicit AiiDA builder path.
        return bool(shutil.which("pw.x") or shutil.which("pw.x.exe"))

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            input_file = data.get("input_file") or self._params.get("input_file")
            if input_file:
                return self._run_pw_x(Path(str(input_file)).expanduser().resolve())

            # AiiDA path only when explicitly requested with builder kwargs
            if data.get("use_aiida") or self._params.get("use_aiida"):
                return self._run_aiida(data)

            return {
                "status": "unavailable",
                "stub": True,
                "executed": False,
                "note": (
                    "Provide input_file= for pw.x, or use_aiida=True with AiiDA "
                    "structure/pseudo setup — refusing profile-only success"
                ),
            }

        return self._run_wrapped(_run, input_data)

    def _run_pw_x(self, input_path: Path) -> dict[str, Any]:
        if not input_path.is_file():
            return {
                "status": "unavailable",
                "stub": True,
                "executed": False,
                "input_file": str(input_path),
                "note": f"input_file not found: {input_path}",
            }
        pw = shutil.which("pw.x") or shutil.which("pw.x.exe")
        if not pw:
            return {
                "status": "unavailable",
                "stub": True,
                "executed": False,
                "note": "pw.x not on PATH",
            }
        out_path = input_path.with_suffix(".out")
        with out_path.open("w", encoding="utf-8") as stdout_f:
            proc = subprocess.run(
                [pw, "-in", str(input_path)],
                stdout=stdout_f,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
        if proc.returncode != 0:
            raise RuntimeError(f"pw.x failed ({proc.returncode}): {(proc.stderr or '')[:500]}")
        total_energy = self._parse_total_energy(out_path)
        return {
            "executed": True,
            "stub": False,
            "backend": "pw.x",
            "input_file": str(input_path),
            "output_file": str(out_path),
            "total_energy_ry": total_energy,
            "note": "pw.x completed",
        }

    def _run_aiida(self, data: dict[str, Any]) -> dict[str, Any]:
        """Submit a real AiiDA process when builder is provided — no fake 'routed'."""
        try:
            import aiida
            from aiida.engine import run_get_node
        except ImportError as exc:
            return {
                "status": "unavailable",
                "stub": True,
                "executed": False,
                "note": f"aiida not importable: {exc}",
            }

        profile = aiida.load_profile()
        builder = data.get("builder") or self._params.get("builder")
        if builder is None:
            return {
                "status": "unavailable",
                "stub": True,
                "executed": False,
                "aiida_profile": profile.name if profile else None,
                "note": "use_aiida=True requires a ProcessBuilder in builder=",
            }

        result, node = run_get_node(builder)
        return {
            "executed": True,
            "stub": False,
            "backend": "aiida",
            "aiida_profile": profile.name if profile else None,
            "node_pk": getattr(node, "pk", None),
            "result_keys": list(result.keys()) if isinstance(result, dict) else [],
            "note": "aiida.engine.run_get_node completed",
        }

    @staticmethod
    def _parse_total_energy(out_path: Path) -> float | None:
        try:
            text = out_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
        # Typical QE line: "!    total energy              =     -xx.yyyy Ry"
        for line in reversed(text.splitlines()):
            if "total energy" in line.lower() and "=" in line:
                try:
                    return float(line.split("=")[-1].replace("Ry", "").strip())
                except ValueError:
                    continue
        return None
