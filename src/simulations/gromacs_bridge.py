# SPDX-License-Identifier: AGPL-3.0
"""GROMACS bridge via gmxapi.

Install: conda install -c conda-forge gromacs && pip install gmxapi
"""
from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult


logger = logging.getLogger(__name__)


class GromacsBridge(BaseSimulationAdapter):
    """Bridge to GROMACS molecular dynamics via gmxapi."""

    _engine_name = "gromacs"
    _package_checks = ["gmxapi"]
    _install_hint = "conda install -c conda-forge gromacs && pip install gmxapi"

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            import gmxapi as gmx

            version = getattr(gmx, "__version__", "unknown")
            # gmxapi requires actual TPR input for a real run.
            # Return availability metadata.
            return {
                "gmxapi_version": version,
                "note": "gmxapi available; provide .tpr file for production run",
            }

        return self._run_wrapped(_run, input_data)
