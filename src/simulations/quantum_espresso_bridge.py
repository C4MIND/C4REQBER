# SPDX-License-Identifier: AGPL-3.0
"""Quantum ESPRESSO + AiiDA bridge — DFT workflow automation.

Install: pip install aiida-quantumespresso  (requires AiiDA profile + PostgreSQL + RabbitMQ)
"""
from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult


logger = logging.getLogger(__name__)


class QuantumEspressoBridge(BaseSimulationAdapter):
    """Bridge to Quantum ESPRESSO via AiiDA workflow engine."""

    _engine_name = "quantum_espresso"
    _package_checks = ["aiida"]
    _install_hint = "pip install aiida-quantumespresso  (needs AiiDA profile + PostgreSQL + RabbitMQ)"

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            import aiida
            from aiida import orm

            profile = aiida.load_profile()
            return {
                "aiida_profile": profile.name if profile else None,
                "note": "AiiDA profile loaded; submit PwBaseWorkChain for actual QE run",
            }

        return self._run_wrapped(_run, input_data)
