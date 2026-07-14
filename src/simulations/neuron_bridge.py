# SPDX-License-Identifier: AGPL-3.0
"""NEURON bridge — biophysical neuron simulations.

Install: pip install neuron
"""
from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult


logger = logging.getLogger(__name__)


class NeuronBridge(BaseSimulationAdapter):
    """Bridge to NEURON for single-cell and network simulations."""

    _engine_name = "neuron"
    _package_checks = ["neuron"]
    _install_hint = "pip install neuron"

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)
        # Expected: tstop, dt, mechanism_files

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            from neuron import h
            from neuron.units import ms

            soma = h.Section(name="soma")
            soma.L = soma.diam = 20
            soma.insert("hh")

            ic = h.IClamp(soma(0.5))
            ic.delay = 2 * ms
            ic.dur = 0.1 * ms
            ic.amp = 0.9

            v = h.Vector().record(soma(0.5)._ref_v)
            t = h.Vector().record(h._ref_t)

            h.tstop = self._params.get("tstop", 40)
            h.dt = self._params.get("dt", 0.025)
            h.run()

            return {
                "t_ms": t.to_python(),
                "v_mV": v.to_python(),
                "section_length_um": float(soma.L),
                "note": "NEURON Hodgkin-Huxley single-compartment simulation completed",
            }

        return self._run_wrapped(_run, input_data)
