# SPDX-License-Identifier: AGPL-3.0
"""Tellurium bridge — systems/synthetic biology (SBML, Antimony, libRoadRunner).

Install: pip install tellurium
"""
from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult

logger = logging.getLogger(__name__)


class TelluriumBridge(BaseSimulationAdapter):
    """Bridge to Tellurium for SBML-based biochemical simulations."""

    _engine_name = "tellurium"
    _package_checks = ["tellurium"]
    _install_hint = "pip install tellurium"

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)
        # Expected: start_time, end_time, steps

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            import tellurium as te

            ant_str = data.get(
                "antimony",
                "model m; S1 -> S2; k1*S1; k1=0.1; S1=10; S2=0; end",
            )
            r = te.loada(ant_str)
            start = self._params.get("start_time", 0)
            end = self._params.get("end_time", 50)
            steps = self._params.get("steps", 100)
            result = r.simulate(start, end, steps)

            return {
                "time_points": result[:, 0].tolist(),
                "species": {
                    r.selections[i]: result[:, i].tolist()
                    for i in range(1, len(r.selections))
                },
                "antimony": ant_str,
                "note": "Tellurium ODE simulation completed",
            }

        return self._run_wrapped(_run, input_data)
