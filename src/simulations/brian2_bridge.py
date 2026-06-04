# SPDX-License-Identifier: AGPL-3.0
"""Brian2 bridge — spiking neural network simulator.

Install: pip install brian2
"""
from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult


logger = logging.getLogger(__name__)


class Brian2Bridge(BaseSimulationAdapter):
    """Bridge to Brian2 for SNN simulations."""

    _engine_name = "brian2"
    _package_checks = ["brian2"]
    _install_hint = "pip install brian2"

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)
        # Expected: duration_ms, dt_ms

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            from brian2 import NeuronGroup, SpikeMonitor, StateMonitor, defaultclock, ms, mV, run

            duration = self._params.get("duration_ms", 100) * ms
            defaultclock.dt = self._params.get("dt_ms", 0.1) * ms

            eqs = """
            dv/dt = (I-v)/tau : volt
            I : volt
            tau : second
            """
            group = NeuronGroup(100, eqs, threshold="v>0.8*mV", reset="v=0*mV", method="exact")
            group.v = "rand()*0.5*mV"
            group.I = "(rand()*0.5 + 0.5)*mV"
            group.tau = "(10 + rand()*10)*ms"

            spike_mon = SpikeMonitor(group)
            state_mon = StateMonitor(group, "v", record=True)
            run(duration)

            return {
                "spike_times_ms": {i: list(spike_mon.t[spike_mon.i == i] / ms) for i in range(5)},
                "n_spikes": int(spike_mon.num_spikes),
                "n_neurons": 100,
                "note": "Brian2 SNN simulation completed",
            }

        return self._run_wrapped(_run, input_data)
