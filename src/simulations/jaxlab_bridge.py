# SPDX-License-Identifier: AGPL-3.0
"""JAX-LaB bridge — differentiable Lattice Boltzmann (multiphase CFD).

Install: pip install jax-lab  (or from source)
"""
from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult

logger = logging.getLogger(__name__)


class JaxLaBBridge(BaseSimulationAdapter):
    """Bridge to JAX-LaB for Lattice Boltzmann multiphase flow."""

    _engine_name = "jax_lab"
    _package_checks = ["jax_lab"]
    _install_hint = "pip install jax-lab  (check PyPI for latest name)"

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)
        # Expected: nx, ny, steps, density_ratio

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            import jax_lab
            import jax.numpy as jnp

            nx = self._params.get("nx", 128)
            ny = self._params.get("ny", 128)
            steps = self._params.get("steps", 100)
            density_ratio = self._params.get("density_ratio", 10.0)

            # JAX-LaB API is evolving; use a safe initialization pattern
            sim = jax_lab.Simulation(shape=(nx, ny), density_ratio=density_ratio)
            sim.initialize()
            for _ in range(steps):
                sim.step()

            rho = sim.density()
            return {
                "nx": nx,
                "ny": ny,
                "steps": steps,
                "density_ratio": density_ratio,
                "mean_density": float(jnp.mean(rho)),
                "note": "JAX-LaB LBM simulation completed",
            }

        return self._run_wrapped(_run, input_data)
