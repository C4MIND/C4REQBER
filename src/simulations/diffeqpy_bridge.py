# SPDX-License-Identifier: AGPL-3.0
"""diffeqpy bridge — Julia DifferentialEquations.jl via Python.

Install: pip install diffeqpy  (requires Julia installed)
"""
from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult


logger = logging.getLogger(__name__)


class DiffEqPyBridge(BaseSimulationAdapter):
    """Bridge to DifferentialEquations.jl via diffeqpy."""

    _engine_name = "diffeqpy"
    _package_checks = ["diffeqpy"]
    _install_hint = "pip install diffeqpy  (requires Julia >= 1.6 installed)"

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)
        # Expected: tspan, u0, algorithm

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            from diffeqpy import de

            def f(u, p, t):
                return [-0.5 * u[0], 0.5 * u[0] - 0.3 * u[1]]

            u0 = self._params.get("u0", [1.0, 0.0])
            tspan = self._params.get("tspan", (0.0, 10.0))
            prob = de.ODEProblem(f, u0, tspan)
            sol = de.solve(prob, de.Tsit5(), saveat=0.1)

            t = list(sol.t)
            u = [list(row) for row in sol.u]
            return {
                "t": t,
                "u": u,
                "n_steps": len(t),
                "note": "diffeqpy ODE solve completed",
            }

        return self._run_wrapped(_run, input_data)
