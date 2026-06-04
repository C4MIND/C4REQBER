# SPDX-License-Identifier: AGPL-3.0
"""LAMMPS bridge via official Python module.

Install: pip install lammps
"""
from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult

logger = logging.getLogger(__name__)


class LammpsBridge(BaseSimulationAdapter):
    """Bridge to LAMMPS MD engine."""

    _engine_name = "lammps"
    _package_checks = ["lammps"]
    _install_hint = "pip install lammps"

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            from lammps import lammps

            lmp = lammps()
            version = lmp.version()
            # Run a minimal Lennard-Jones melt if no input provided
            if not data.get("input_script"):
                cmds = [
                    "units lj",
                    "atom_style atomic",
                    "region box block 0 10 0 10 0 10",
                    "create_box 1 box",
                    "create_atoms 1 random 100 42 box",
                    "mass 1 1.0",
                    "pair_style lj/cut 2.5",
                    "pair_coeff 1 1 1.0 1.0",
                    "velocity all create 1.0 42",
                    "fix 1 all nve",
                    "run 10",
                ]
                for cmd in cmds:
                    lmp.command(cmd)
                natoms = lmp.get_natoms()
                pe = lmp.extract_compute("thermo_pe", 0, 0)
                return {
                    "lammps_version": version,
                    "natoms": natoms,
                    "potential_energy": pe,
                    "note": "LJ melt demo completed 10 steps",
                }
            return {"lammps_version": version, "note": "custom input_script mode"}

        return self._run_wrapped(_run, input_data)
