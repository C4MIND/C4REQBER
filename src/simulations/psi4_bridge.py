# SPDX-License-Identifier: AGPL-3.0
"""Psi4 bridge — ab initio quantum chemistry with PsiAPI.

Install: conda install -c psi4 psi4
"""
from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult


logger = logging.getLogger(__name__)


class Psi4Bridge(BaseSimulationAdapter):
    """Bridge to Psi4 for HF, DFT, MP2, CCSD calculations."""

    _engine_name = "psi4"
    _package_checks = ["psi4"]
    _install_hint = "conda install -c psi4 psi4"

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)
        # Expected: basis, method, memory

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            import psi4

            psi4.core.set_output_file("/dev/null", False)
            memory = self._params.get("memory", "500 MB")
            psi4.set_memory(memory)

            basis = self._params.get("basis", "sto-3g")
            method = self._params.get("method", "scf")
            mol_str = data.get("molecule", "H 0 0 0\nH 0 0 0.74\nsymmetry c1")

            mol = psi4.geometry(mol_str)
            energy = psi4.energy(f"{method}/{basis}")

            return {
                "total_energy_hartree": float(energy),
                "method": method,
                "basis": basis,
                "memory": memory,
                "note": "Psi4 calculation completed",
            }

        return self._run_wrapped(_run, input_data)
