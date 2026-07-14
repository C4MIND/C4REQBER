# SPDX-License-Identifier: AGPL-3.0
"""MDAnalysis bridge — trajectory analysis toolkit.

Install: pip install MDAnalysis
"""
from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult


logger = logging.getLogger(__name__)


class MDAnalysisBridge(BaseSimulationAdapter):
    """Bridge to MDAnalysis for MD trajectory post-processing."""

    _engine_name = "mdanalysis"
    _package_checks = ["MDAnalysis"]
    _install_hint = "pip install MDAnalysis"

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            import MDAnalysis as mda

            version = mda.__version__
            topology = data.get("topology")
            trajectory = data.get("trajectory")

            if topology and trajectory:
                u = mda.Universe(topology, trajectory)
                n_frames = len(u.trajectory)
                n_atoms = len(u.atoms)
                # Compute radius of gyration for first frame
                u.trajectory[0]
                rg = u.atoms.radius_of_gyration()
                return {
                    "mdanalysis_version": version,
                    "n_frames": n_frames,
                    "n_atoms": n_atoms,
                    "radius_of_gyration": float(rg),
                }

            return {
                "mdanalysis_version": version,
                "note": "Provide topology + trajectory files for analysis",
            }

        return self._run_wrapped(_run, input_data)
