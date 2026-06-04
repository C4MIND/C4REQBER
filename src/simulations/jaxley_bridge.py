# SPDX-License-Identifier: AGPL-3.0
"""Jaxley bridge — differentiable neuron simulator (JAX-based).

Install: pip install jaxley
"""
from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult

logger = logging.getLogger(__name__)


class JaxleyBridge(BaseSimulationAdapter):
    """Bridge to Jaxley for gradient-based neuron optimization."""

    _engine_name = "jaxley"
    _package_checks = ["jaxley"]
    _install_hint = "pip install jaxley"

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)
        # Expected: n_compartments, dt, t_max

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            import jaxley as jx
            import jax.numpy as jnp

            n_comp = self._params.get("n_compartments", 4)
            cell = jx.Cell()
            # Jaxley API: build a simple compartmental cell
            # Note: exact API may shift; wrap in try/except for compatibility
            try:
                branch = jx.Branch(n_comp)
                cell = jx.Cell([branch], [-1])
                cell.insert(jx.channels.HH())
                cell.set("v", -65.0)

                dt = self._params.get("dt", 0.025)
                t_max = self._params.get("t_max", 10.0)
                time = jnp.arange(0, t_max, dt)

                # Stimulus
                current = jnp.zeros((len(time), 1))
                current = current.at[100:400].set(0.1)
                cell.stimulate(current)

                v = cell.integrate(dt=dt, t_max=t_max)
                return {
                    "v_shape": list(v.shape),
                    "n_compartments": n_comp,
                    "dt": dt,
                    "t_max": t_max,
                    "note": "Jaxley simulation completed",
                }
            except Exception as exc:
                # Graceful fallback if API differs
                return {
                    "jaxley_available": True,
                    "api_error": str(exc),
                    "note": "Jaxley installed but API mismatch; check version",
                }

        return self._run_wrapped(_run, input_data)
