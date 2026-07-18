# SPDX-License-Identifier: AGPL-3.0
"""AMUSE / Rebound N-body bridge — hypothesis-parameterized gravity evolve.

Prefers AMUSE gravity communities when installed; otherwise uses Rebound
(real N-body integrator) with backend labeled honestly.
"""

from __future__ import annotations

import importlib
import logging
from typing import Any

import numpy as np

from .base_adapter import BaseSimulationAdapter, SimulationResult


logger = logging.getLogger(__name__)

_GRAVITY_CANDIDATES: list[tuple[str, str]] = [
    ("amuse.community.hermite.interface", "Hermite"),
    ("amuse.community.huayno.interface", "Huayno"),
    ("amuse.community.ph4.interface", "Ph4"),
    ("amuse.community.bhtree.interface", "BHTree"),
]


def _as_float_list(val: Any, n: int, default: list[float]) -> list[float]:
    if val is None:
        return list(default)
    if isinstance(val, (int, float)):
        return [float(val)] * n
    arr = list(val)
    if len(arr) < n:
        arr = arr + default[len(arr) : n]
    return [float(x) for x in arr[:n]]


def _bodies_from_data(data: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Parse masses/positions/velocities from hypothesis-style config."""
    masses = data.get("masses")
    positions = data.get("positions")
    velocities = data.get("velocities")
    n = int(data.get("n_particles") or data.get("n_bodies") or 0)

    if positions is not None:
        pos = np.asarray(positions, dtype=float)
        if pos.ndim == 1:
            pos = pos.reshape(1, -1)
        n = len(pos)
    elif masses is not None:
        n = len(list(masses))
        pos = None
    elif n <= 0:
        # Default Sun–Earth-like only when nothing specified
        n = 2
        pos = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]], dtype=float)
    else:
        pos = None

    if pos is None:
        # Circular-ish ring
        angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
        pos = np.stack([np.cos(angles), np.sin(angles), np.zeros(n)], axis=1)

    if masses is None:
        m = np.ones(n, dtype=float)
        if n >= 2:
            m[0] = 1.0
            m[1:] = 1e-6
    else:
        m = np.asarray(_as_float_list(masses, n, [1.0] * n), dtype=float)

    if velocities is None:
        # Approx circular velocity in AU/yr units-ish for AU positions
        vel = np.zeros_like(pos)
        if n >= 2:
            vel[1] = np.array([0.0, 2 * np.pi, 0.0])  # ~1 yr period at 1 AU
    else:
        vel = np.asarray(velocities, dtype=float)
        if vel.ndim == 1:
            vel = vel.reshape(1, -1)
        if len(vel) < n:
            pad = np.zeros((n - len(vel), 3))
            vel = np.vstack([vel, pad])

    return m, pos, vel[:n]


class AmuseBridge(BaseSimulationAdapter):
    """Hypothesis-parameterized N-body via AMUSE or Rebound."""

    _engine_name = "amuse"
    _package_checks = ["amuse"]  # soft — is_available also accepts rebound
    _install_hint = "pip install amuse-framework amuse-hermite  OR  pip install rebound"

    def is_available(self) -> bool:
        if self._first_gravity_class() is not None:
            return True
        return self._can_import("rebound")

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            evolve_time = float(data.get("evolve_time_yr", self._params.get("evolve_time_yr", 0.1)))
            do_evolve = data.get("evolve", self._params.get("evolve", True))
            if do_evolve is False:
                return {
                    "status": "unavailable",
                    "stub": True,
                    "executed": False,
                    "note": "evolve=False — refusing particle-only scaffold",
                }

            masses, positions, velocities = _bodies_from_data({**self._params, **data})
            hyp_driven = any(
                k in data for k in ("masses", "positions", "velocities", "n_particles", "n_bodies")
            )

            gravity_cls = self._first_gravity_class()
            if gravity_cls is not None:
                return self._run_amuse(
                    gravity_cls, masses, positions, velocities, evolve_time, hyp_driven
                )

            if self._can_import("rebound"):
                return self._run_rebound(masses, positions, velocities, evolve_time, hyp_driven)

            return {
                "status": "unavailable",
                "stub": True,
                "executed": False,
                "note": "Neither AMUSE gravity community nor rebound installed",
            }

        return self._run_wrapped(_run, input_data)

    def _run_amuse(
        self,
        gravity_cls: type,
        masses: np.ndarray,
        positions: np.ndarray,
        velocities: np.ndarray,
        evolve_time: float,
        hyp_driven: bool,
    ) -> dict[str, Any]:
        from amuse.datamodel import Particles
        from amuse.units import units

        n = len(masses)
        particles = Particles(n)
        particles.mass = masses.tolist() | units.MSun
        particles.position = positions.tolist() | units.AU
        # velocities given as AU/yr-ish → convert to km/s roughly: 1 AU/yr ≈ 4.74 km/s
        particles.velocity = (velocities * 4.74).tolist() | units.kms

        gravity = gravity_cls()
        try:
            gravity.particles.add_particles(particles)
            gravity.evolve_model(evolve_time | units.yr)
            channel = gravity.particles.new_channel_to(particles)
            channel.copy()
            final_sep = (
                float(particles[0].position.distance_to(particles[1].position).value_in(units.AU))
                if n >= 2
                else 0.0
            )
            community = type(gravity).__name__
            final_pos = [list(p.position.value_in(units.AU)) for p in particles]
        finally:
            if hasattr(gravity, "stop"):
                gravity.stop()

        return {
            "executed": True,
            "stub": False,
            "backend": "amuse",
            "n_particles": n,
            "evolve_time_yr": evolve_time,
            "final_separation_au": final_sep,
            "final_positions_au": final_pos[:16],
            "gravity_community": community,
            "hypothesis_driven": hyp_driven,
            "note": f"{community}.evolve_model completed",
        }

    def _run_rebound(
        self,
        masses: np.ndarray,
        positions: np.ndarray,
        velocities: np.ndarray,
        evolve_time: float,
        hyp_driven: bool,
    ) -> dict[str, Any]:
        import rebound

        sim = rebound.Simulation()
        sim.units = ("yr", "AU", "Msun")
        sim.integrator = "whfast"
        sim.dt = min(1e-3, max(evolve_time / 1000.0, 1e-6))
        for m, p, v in zip(masses, positions, velocities, strict=True):
            sim.add(
                m=float(m),
                x=float(p[0]),
                y=float(p[1]),
                z=float(p[2]),
                vx=float(v[0]),
                vy=float(v[1]),
                vz=float(v[2]),
            )
        sim.move_to_com()
        sim.integrate(evolve_time)
        final_pos = [[float(p.x), float(p.y), float(p.z)] for p in sim.particles]
        final_sep = (
            float(np.linalg.norm(np.array(final_pos[0]) - np.array(final_pos[1])))
            if len(final_pos) >= 2
            else 0.0
        )
        return {
            "executed": True,
            "stub": False,
            "backend": "rebound",
            "engine_truth": "rebound_not_amuse",
            "n_particles": len(masses),
            "evolve_time_yr": evolve_time,
            "final_separation_au": final_sep,
            "final_positions_au": final_pos[:16],
            "gravity_community": "REBOUND/WHFast",
            "hypothesis_driven": hyp_driven,
            "note": (
                "AMUSE not installed — ran real Rebound WHFast N-body "
                f"({'hypothesis params' if hyp_driven else 'default 2-body'})"
            ),
        }

    @staticmethod
    def _first_gravity_class() -> type | None:
        for module_name, class_name in _GRAVITY_CANDIDATES:
            try:
                mod = importlib.import_module(module_name)
                cls = getattr(mod, class_name, None)
                if cls is not None:
                    return cls
            except Exception:
                continue
        return None
