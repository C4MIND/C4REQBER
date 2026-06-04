# SPDX-License-Identifier: AGPL-3.0
"""JAX MD bridge — differentiable molecular dynamics.

Install: pip install jax-md
"""
from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult

logger = logging.getLogger(__name__)


class JaxMDBridge(BaseSimulationAdapter):
    """Bridge to JAX MD for differentiable MD."""

    _engine_name = "jax_md"
    _package_checks = ["jax_md"]
    _install_hint = "pip install jax-md"

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)
        # Expected: n_particles, temperature, steps

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            import jax.numpy as jnp
            from jax import random
            from jax_md import energy, space, simulate

            key = random.PRNGKey(0)
            n = self._params.get("n_particles", 128)
            box_size = self._params.get("box_size", 5.0)
            R = random.uniform(key, (n, 2)) * box_size

            displacement, shift = space.free()
            morse_energy = energy.morse_pair(displacement, sigma=1.0, epsilon=1.0, alpha=3.0)

            init_fn, apply_fn = simulate.nvt_nose_hoover(
                morse_energy, shift, dt=1e-3, kT=0.5, chain_length=3
            )
            state = init_fn(key, R)

            steps = self._params.get("steps", 100)
            for _ in range(steps):
                state = apply_fn(state)

            return {
                "n_particles": n,
                "final_energy": float(morse_energy(state.position)),
                "mean_position": state.position.mean().item(),
                "steps": steps,
                "note": "JAX MD NVT simulation completed",
            }

        return self._run_wrapped(_run, input_data)
