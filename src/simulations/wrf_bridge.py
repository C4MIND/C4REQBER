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
    _install_hint = "conda install -c conda-forge wrf-python  (requires WRF binaries for simulation)"

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            from netCDF4 import Dataset
            import wrf

            wrf_file = data.get("wrfout")
            if wrf_file:
                nc = Dataset(wrf_file)
                t2 = wrf.getvar(nc, "T2")
                return {
                    "wrfpython_version": wrf.__version__,
                    "t2_shape": list(t2.shape),
                    "t2_mean": float(t2.mean()),
                    "note": "WRF output processed",
                }
            return {
                "wrfpython_version": wrf.__version__,
                "note": "Provide wrfout NetCDF file for post-processing",
            }

        return self._run_wrapped(_run, input_data)
