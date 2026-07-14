# SPDX-License-Identifier: AGPL-3.0
"""AMUSE bridge — astrophysical multi-physics framework.

Install: pip install amuse-framework
"""
from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult


logger = logging.getLogger(__name__)


class AmuseBridge(BaseSimulationAdapter):
    """Bridge to AMUSE for coupled astrophysical codes."""

    _engine_name = "amuse"
    _package_checks = ["amuse"]
    _install_hint = "pip install amuse-framework  (build from source recommended)"

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            from amuse.datamodel import Particles
            from amuse.units import units

            particles = Particles(2)
            particles.mass = [1.0, 1.0] | units.MSun
            particles.position = [[0, 0, 0], [1.0, 0, 0]] | units.AU
            particles.velocity = [[0, 0, 0], [0, 29.8, 0]] | units.kms

            return {
                "n_particles": len(particles),
                "total_mass": float(particles.mass.sum().value_in(units.MSun)),
                "note": "AMUSE particle set created; attach gravity solver for evolution",
            }

        return self._run_wrapped(_run, input_data)
