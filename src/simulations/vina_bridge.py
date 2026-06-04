# SPDX-License-Identifier: AGPL-3.0
"""AutoDock Vina bridge — protein-ligand docking.

Install: conda install -c conda-forge vina  (or)  apt-get install autodock-vina
"""
from __future__ import annotations

import logging
import subprocess
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult

logger = logging.getLogger(__name__)


class VinaBridge(BaseSimulationAdapter):
    """Bridge to AutoDock Vina for molecular docking."""

    _engine_name = "vina"
    _package_checks = ["vina"]
    _install_hint = (
        "conda install -c conda-forge vina  (or)  "
        "apt-get install autodock-vina  (or)  "
        "pip install vina"
    )

    def is_available(self) -> bool:
        try:
            subprocess.run(["vina", "--help"], capture_output=True, check=True, timeout=5)
            return True
        except Exception:
            return False

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            receptor = data.get("receptor_pdbqt", "receptor.pdbqt")
            ligand = data.get("ligand_pdbqt", "ligand.pdbqt")
            center = data.get("center", [0.0, 0.0, 0.0])
            size = data.get("size", [20.0, 20.0, 20.0])
            exhaustiveness = data.get("exhaustiveness", 8)

            cmd = [
                "vina",
                "--receptor", receptor,
                "--ligand", ligand,
                "--center_x", str(center[0]),
                "--center_y", str(center[1]),
                "--center_z", str(center[2]),
                "--size_x", str(size[0]),
                "--size_y", str(size[1]),
                "--size_z", str(size[2]),
                "--exhaustiveness", str(exhaustiveness),
                "--out", "docked.pdbqt",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                raise RuntimeError(f"Vina failed: {result.stderr}")

            binding_affinity = self._parse_affinity(result.stdout)
            return {
                "binding_affinity_kcal_mol": binding_affinity,
                "receptor": receptor,
                "ligand": ligand,
                "exhaustiveness": exhaustiveness,
                "output_file": "docked.pdbqt",
                "stdout": result.stdout[:2000],
            }

        return self._run_wrapped(_run, input_data)

    @staticmethod
    def _parse_affinity(stdout: str) -> float | None:
        for line in stdout.splitlines():
            if "kcal/mol" in line.lower() and "-----" not in line:
                parts = line.split()
                for p in parts:
                    try:
                        return float(p)
                    except ValueError:
                        continue
        return None
