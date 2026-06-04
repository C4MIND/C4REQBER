# SPDX-License-Identifier: AGPL-3.0
"""xarray + iris + cartopy bridge — climate data backbone.

Install: conda install xarray iris cartopy dask  (or pip install xarray cartopy)
"""
from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult

logger = logging.getLogger(__name__)


class XarrayBridge(BaseSimulationAdapter):
    """Bridge to xarray for labelled multi-dimensional climate arrays."""

    _engine_name = "xarray"
    _package_checks = ["xarray"]
    _install_hint = "pip install xarray dask netCDF4  (conda install iris cartopy for full stack)"

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            import xarray as xr
            import numpy as np

            # Create a synthetic climate-like dataset if no file provided
            if "dataset" in data:
                ds = data["dataset"]
            else:
                lat = np.linspace(-90, 90, 18)
                lon = np.linspace(0, 360, 36)
                time = np.arange(1, 13)
                temp = np.random.randn(len(time), len(lat), len(lon)) * 5 + 15
                ds = xr.Dataset(
                    {"temperature": (["time", "lat", "lon"], temp)},
                    coords={"time": time, "lat": lat, "lon": lon},
                )

            mean_temp = float(ds["temperature"].mean())
            return {
                "xarray_version": xr.__version__,
                "mean_temperature": mean_temp,
                "dims": dict(ds.sizes),
                "note": "xarray dataset processed",
            }

        return self._run_wrapped(_run, input_data)
