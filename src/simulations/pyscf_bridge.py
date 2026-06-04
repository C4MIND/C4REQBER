# SPDX-License-Identifier: AGPL-3.0
"""PySCF bridge — Python-native quantum chemistry (HF, DFT, MP2, CCSD).

Install: pip install pyscf  (optionally gpu4pyscf for GPU)
"""
from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult

logger = logging.getLogger(__name__)


class PySCFBridge(BaseSimulationAdapter):
    """Bridge to PySCF for electronic structure calculations."""

    _engine_name = "pyscf"
    _package_checks = ["pyscf"]
    _install_hint = "pip install pyscf  (pip install gpu4pyscf for GPU)"

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)
        # Expected: basis, xc (functional), molecule geometry

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            from pyscf import gto, scf, dft

            atom = data.get("atom", "H 0 0 0; H 0 0 0.74")
            basis = self._params.get("basis", "sto-3g")
            xc = self._params.get("xc", "b3lyp")

            mol = gto.M(atom=atom, basis=basis, unit="Angstrom")
            mf = dft.RKS(mol)
            mf.xc = xc
            energy = mf.kernel()

            return {
                "total_energy_hartree": float(energy),
                "converged": bool(mf.converged),
                "basis": basis,
                "xc": xc,
                "note": "PySCF DFT calculation completed",
            }

        return self._run_wrapped(_run, input_data)
