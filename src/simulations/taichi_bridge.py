# SPDX-License-Identifier: AGPL-3.0
"""Taichi bridge — JIT-compiled differentiable simulation.

Install: pip install taichi
"""
from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult


logger = logging.getLogger(__name__)


class TaichiBridge(BaseSimulationAdapter):
    """Bridge to Taichi for high-performance numerical kernels."""

    _engine_name = "taichi"
    _package_checks = ["taichi"]
    _install_hint = "pip install taichi"

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)
        # Expected: arch (cpu/cuda/vulkan), n_particles, steps

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            import taichi as ti

            arch_map = {
                "cpu": ti.cpu,
                "cuda": ti.cuda,
                "vulkan": ti.vulkan,
                "metal": ti.metal,
            }
            arch = arch_map.get(self._params.get("arch", "cpu"), ti.cpu)
            ti.init(arch=arch)

            n = self._params.get("n_particles", 1024)
            x = ti.field(dtype=ti.f32, shape=n)
            v = ti.field(dtype=ti.f32, shape=n)

            @ti.kernel
            def init():
                for i in range(n):
                    x[i] = ti.random() * 2.0 - 1.0
                    v[i] = 0.0

            @ti.kernel
            def step():
                for i in range(n):
                    v[i] += -0.1 * x[i]
                    x[i] += 0.01 * v[i]

            init()
            steps = self._params.get("steps", 100)
            for _ in range(steps):
                step()

            x_np = x.to_numpy()
            return {
                "arch": str(arch),
                "n_particles": n,
                "steps": steps,
                "mean_x": float(x_np.mean()),
                "std_x": float(x_np.std()),
                "note": "Taichi harmonic oscillator simulation completed",
            }

        return self._run_wrapped(_run, input_data)
