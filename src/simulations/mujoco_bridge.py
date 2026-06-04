# SPDX-License-Identifier: AGPL-3.0
"""MuJoCo bridge — contact-rich robotics simulation.

Install: pip install mujoco
"""
from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult


logger = logging.getLogger(__name__)


class MuJoCoBridge(BaseSimulationAdapter):
    """Bridge to MuJoCo for rigid-body/contact dynamics."""

    _engine_name = "mujoco"
    _package_checks = ["mujoco"]
    _install_hint = "pip install mujoco"

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)
        # Expected: xml_model, duration, timestep

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            import mujoco
            import numpy as np

            xml = data.get(
                "xml_model",
                """
                <mujoco>
                  <worldbody>
                    <light diffuse=".5 .5 .5" pos="0 0 3" dir="0 0 -1"/>
                    <geom type="plane" size="1 1 0.1" rgba=".9 0 0 1"/>
                    <body pos="0 0 1">
                      <joint type="free"/>
                      <geom type="box" size=".1 .1 .1" rgba="0 .9 0 1" mass="1"/>
                    </body>
                  </worldbody>
                </mujoco>
                """,
            )
            model = mujoco.MjModel.from_xml_string(xml)
            data_sim = mujoco.MjData(model)
            duration = self._params.get("duration", 1.0)
            timestep = model.opt.timestep

            positions = []
            n_steps = int(duration / timestep)
            for _ in range(n_steps):
                mujoco.mj_step(model, data_sim)
                positions.append(float(data_sim.qpos[2]))  # z-height

            return {
                "mujoco_version": mujoco.__version__,
                "duration": duration,
                "n_steps": n_steps,
                "final_z": positions[-1] if positions else None,
                "min_z": min(positions) if positions else None,
                "note": "MuJoCo free-fall simulation completed",
            }

        return self._run_wrapped(_run, input_data)
