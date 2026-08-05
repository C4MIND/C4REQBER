# SPDX-License-Identifier: AGPL-3.0
"""WRF bridge — Weather Research and Forecasting via wrf-python.

Install: conda install -c conda-forge wrf-python
"""

from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult


logger = logging.getLogger(__name__)


class WrfBridge(BaseSimulationAdapter):
    """Bridge to WRF output post-processing via wrf-python."""

    _engine_name = "wrf"
    _package_checks = ["wrf"]
    _install_hint = (
        "conda install -c conda-forge wrf-python  (requires WRF binaries for simulation)"
    )

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            wrf_file = data.get("wrfout") or self._params.get("wrfout")
            if not wrf_file:
                return {
                    "status": "unavailable",
                    "stub": True,
                    "executed": False,
                    "backend": "wrf-python",
                    "note": "Provide wrfout NetCDF — wrf-python alone does not run WRF",
                }
            # Validate before importing heavy deps — path hatch must not require wrf installed
            try:
                from src.utils.security_middleware import validate_sim_path

                wrf_file = str(validate_sim_path(str(wrf_file)))
            except ValueError as exc:
                return {
                    "status": "unavailable",
                    "stub": True,
                    "executed": False,
                    "backend": "wrf-python",
                    "note": str(exc),
                }

            import wrf
            from netCDF4 import Dataset

            with Dataset(wrf_file) as nc:
                t2 = wrf.getvar(nc, "T2")
                return {
                    "status": "success",
                    "backend": "wrf-python",
                    "executed": True,
                    "stub": False,
                    "wrf_file": str(wrf_file),
                    "wrfpython_version": wrf.__version__,
                    "t2_shape": list(t2.shape),
                    "t2_mean": float(t2.mean()),
                    "note": "WRF output post-processed (not a WRF forecast run)",
                    "postprocess_only": True,
                }

        return self._run_wrapped(_run, input_data)
