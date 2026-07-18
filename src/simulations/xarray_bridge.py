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

            path = data.get("path") or data.get("dataset_path") or self._params.get("path")
            if path:
                with xr.open_dataset(path) as ds:
                    var = data.get("variable") or next(iter(ds.data_vars), None)
                    if not var:
                        return {
                            "status": "unavailable",
                            "stub": True,
                            "executed": False,
                            "backend": "xarray",
                            "xarray_version": xr.__version__,
                            "note": f"Opened {path} but no data variable found",
                        }
                    mean_val = float(ds[var].mean())
                    return {
                        "status": "success",
                        "backend": "xarray",
                        "executed": True,
                        "stub": False,
                        "xarray_version": xr.__version__,
                        "path": str(path),
                        "variable": var,
                        "mean": mean_val,
                        "dims": dict(ds.sizes),
                        "note": "Real dataset aggregated",
                    }

            if "dataset" in data and data["dataset"] is not None:
                ds = data["dataset"]
                mean_temp = (
                    float(ds["temperature"].mean())
                    if "temperature" in ds
                    else float(next(iter(ds.data_vars.values())).mean())
                )
                return {
                    "status": "success",
                    "backend": "xarray",
                    "executed": True,
                    "stub": False,
                    "xarray_version": xr.__version__,
                    "mean_temperature": mean_temp,
                    "dims": dict(ds.sizes),
                    "note": "In-memory dataset aggregated",
                }

            return {
                "status": "unavailable",
                "stub": True,
                "executed": False,
                "backend": "xarray",
                "xarray_version": xr.__version__,
                "note": "No path/dataset — refusing synthetic random climate field",
            }

        return self._run_wrapped(_run, input_data)
