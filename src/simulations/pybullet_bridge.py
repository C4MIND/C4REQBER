# SPDX-License-Identifier: AGPL-3.0
"""PyBullet bridge — open-source robotics/physics simulator.

Install: pip install pybullet
"""
from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult


logger = logging.getLogger(__name__)


class PyBulletBridge(BaseSimulationAdapter):
    """Bridge to PyBullet for robotics simulation."""

    _engine_name = "pybullet"
    _package_checks = ["pybullet"]
    _install_hint = "pip install pybullet"

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)
        # Expected: gravity, time_step, steps

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            import pybullet as p
            import pybullet_data

            client = p.connect(p.DIRECT)
            p.setAdditionalSearchPath(pybullet_data.getDataPath())
            gravity = self._params.get("gravity", -9.81)
            p.setGravity(0, 0, gravity)
            p.loadURDF("plane.urdf")
            box_id = p.loadURDF("cube_small.urdf", basePosition=[0, 0, 1])

            time_step = self._params.get("time_step", 1 / 240)
            p.setTimeStep(time_step)
            steps = self._params.get("steps", 240)
            for _ in range(steps):
                p.stepSimulation()

            pos, _ = p.getBasePositionAndOrientation(box_id)
            p.disconnect(client)

            return {
                "final_position": list(pos),
                "gravity": gravity,
                "steps": steps,
                "note": "PyBullet box-drop simulation completed",
            }

        return self._run_wrapped(_run, input_data)
