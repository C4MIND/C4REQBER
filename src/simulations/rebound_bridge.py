# SPDX-License-Identifier: AGPL-3.0
"""Rebound + REBOUNDx bridge — N-body astrophysical simulator.

Install: pip install rebound
"""
from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult


logger = logging.getLogger(__name__)


class ReboundBridge(BaseSimulationAdapter):
    """Bridge to Rebound for planetary dynamics."""

    _engine_name = "rebound"
    _package_checks = ["rebound"]
    _install_hint = "pip install rebound"

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)
        # Expected: integrator, dt, t_max

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            import rebound

            sim = rebound.Simulation()
            sim.add(m=1.0)
            sim.add(m=1e-3, a=1.0, e=0.01)
            sim.add(m=1e-3, a=1.5, e=0.02)

            integrator = self._params.get("integrator", "ias15")
            sim.integrator = integrator
            dt = self._params.get("dt", 0.01)
            sim.dt = dt
            t_max = self._params.get("t_max", 100.0)

            sim.integrate(t_max)

            ps = sim.particles
            return {
                "integrator": integrator,
                "n_particles": sim.N,
                "energy_error": sim.calculate_energy(),
                "final_positions": [
                    {"x": float(p.x), "y": float(p.y), "z": float(p.z)} for p in ps[1:]
                ],
                "note": "Rebound N-body simulation completed",
            }

        return self._run_wrapped(_run, input_data)
