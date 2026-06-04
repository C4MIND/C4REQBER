# SPDX-License-Identifier: AGPL-3.0
"""ModelingToolkit.jl bridge — symbolic-numeric modeling via PyJulia.

Install: pip install julia  (then run julia.install())
"""
from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult

logger = logging.getLogger(__name__)


class ModelingToolkitBridge(BaseSimulationAdapter):
    """Bridge to ModelingToolkit.jl via PyJulia."""

    _engine_name = "modelingtoolkit"
    _package_checks = ["julia"]
    _install_hint = "pip install julia  (requires Julia >= 1.9 + ModelingToolkit.jl)"

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)
        # Expected: model_script (Julia string)

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            from julia import Main

            script = data.get(
                "model_script",
                """
                using ModelingToolkit, DifferentialEquations
                @variables t x(t)
                @parameters p=1.0
                D = Differential(t)
                eqs = [D(x) ~ -p*x]
                @named sys = ODESystem(eqs)
                prob = ODEProblem(sys, [x => 1.0], (0.0, 10.0))
                sol = solve(prob, Tsit5())
                sol.u[end][1]
                """,
            )
            result = Main.eval(script)
            return {
                "julia_result": float(result) if hasattr(result, "__float__") else str(result),
                "note": "ModelingToolkit.jl model executed via PyJulia",
            }

        return self._run_wrapped(_run, input_data)
