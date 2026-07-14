# SPDX-License-Identifier: AGPL-3.0
"""COBRApy bridge — constraint-based metabolic modeling (FBA, FVA, pFBA).

Install: pip install cobra
"""
from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult


logger = logging.getLogger(__name__)


class CobraBridge(BaseSimulationAdapter):
    """Bridge to COBRApy for flux balance analysis and metabolic modeling."""

    _engine_name = "cobra"
    _package_checks = ["cobra"]
    _install_hint = "pip install cobra  (requires libglpk-dev or similar LP solver)"

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            import cobra
            from cobra.io import load_model

            model_source = data.get("model", "textbook")
            if model_source == "textbook":
                model = load_model("textbook")
            else:
                model = cobra.io.read_sbml_model(model_source)

            objective = data.get("objective", model.objective)
            model.objective = objective

            solution = model.optimize()
            fva_fraction = data.get("fva_fraction")
            result = {
                "objective_value": solution.objective_value,
                "status": solution.status,
                "model_id": model.id,
                "reactions_count": len(model.reactions),
                "metabolites_count": len(model.metabolites),
            }
            if fva_fraction is not None:
                from cobra.flux_analysis import flux_variability_analysis
                fva = flux_variability_analysis(model, fraction_of_optimum=fva_fraction)
                result["fva"] = fva.to_dict()

            return result

        return self._run_wrapped(_run, input_data)
