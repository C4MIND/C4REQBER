# SPDX-License-Identifier: AGPL-3.0
"""COPASI bridge — biochemical network analysis via Basico.

Install: pip install copasi-basico  (or basico)
"""
from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult


logger = logging.getLogger(__name__)


class CopasiBridge(BaseSimulationAdapter):
    """Bridge to COPASI via basico Python bindings."""

    _engine_name = "copasi"
    _package_checks = ["basico"]
    _install_hint = "pip install copasi-basico"

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            import basico

            # Load SBML or create a simple model
            sbml = data.get("sbml")
            if sbml:
                dm = basico.load_model(sbml)
            else:
                dm = basico.new_model(name="c4reqber")
                basico.add_reaction("R1", "A -> B", {"A": 10, "B": 0})

            tc = basico.run_time_course(duration=50, intervals=100)
            return {
                "timecourse_columns": list(tc.columns),
                "timecourse_rows": len(tc),
                "note": "COPASI time-course simulation completed",
            }

        return self._run_wrapped(_run, input_data)
