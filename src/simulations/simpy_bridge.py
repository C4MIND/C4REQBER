# SPDX-License-Identifier: AGPL-3.0
"""SimPy bridge — discrete-event simulation.

Install: pip install simpy
"""
from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult

logger = logging.getLogger(__name__)


class SimPyBridge(BaseSimulationAdapter):
    """Bridge to SimPy for process-based DES."""

    _engine_name = "simpy"
    _package_checks = ["simpy"]
    _install_hint = "pip install simpy"

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)
        # Expected: sim_time, num_customers, service_time

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            import simpy

            sim_time = self._params.get("sim_time", 100)
            num_customers = self._params.get("num_customers", 50)
            service_time = self._params.get("service_time", 5)

            wait_times = []

            def customer(env, name, counter):
                arrive = env.now
                with counter.request() as req:
                    yield req
                    wait = env.now - arrive
                    wait_times.append(wait)
                    yield env.timeout(service_time)

            def source(env, n, counter):
                for i in range(n):
                    c = customer(env, f"Customer {i}", counter)
                    env.process(c)
                    yield env.timeout(2)

            env = simpy.Environment()
            counter = simpy.Resource(env, capacity=1)
            env.process(source(env, num_customers, counter))
            env.run(until=sim_time)

            return {
                "avg_wait_time": round(sum(wait_times) / len(wait_times), 3) if wait_times else 0,
                "max_wait_time": max(wait_times) if wait_times else 0,
                "num_customers": num_customers,
                "sim_time": sim_time,
                "note": "SimPy discrete-event simulation completed",
            }

        return self._run_wrapped(_run, input_data)
