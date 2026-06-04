# SPDX-License-Identifier: AGPL-3.0
"""BoolNet bridge — Boolean network analysis for gene regulatory networks.

Install: BiocManager::install("BoolNet") in R, then reticulate in Python.
Alternative: pip install booleanNetwork (if available).
"""
from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult


logger = logging.getLogger(__name__)


class BoolNetBridge(BaseSimulationAdapter):
    """Bridge to BoolNet for Boolean gene regulatory network analysis."""

    _engine_name = "boolnet"
    _package_checks = ["rpy2"]
    _install_hint = (
        "Install R + BoolNet:  BiocManager::install('BoolNet')  "
        "Then in Python:  pip install rpy2  "
        "Alternative: use Python boolean-network libraries (e.g. pystablemotifs)"
    )

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            network_file = data.get("network_file")
            if not network_file:
                # Generate a simple toggle-switch network inline
                network = data.get("network", {
                    "A": "!B",
                    "B": "!A",
                })
                attractors = self._compute_attractors(network)
                return {
                    "attractors": attractors,
                    "network_nodes": list(network.keys()),
                    "note": "Computed attractors for Boolean network",
                }

            import rpy2.robjects as ro
            from rpy2.robjects.packages import importr
            boolnet = importr("BoolNet")
            net = boolnet.loadNetwork(network_file)
            attrs = boolnet.getAttractors(net)
            return {
                "attractors": str(attrs),
                "network_file": network_file,
                "note": "BoolNet attractor analysis completed",
            }

        return self._run_wrapped(_run, input_data)

    @staticmethod
    def _compute_attractors(network: dict[str, str]) -> list[dict[str, int]]:
        """Simple brute-force attractor computation for small networks."""
        nodes = list(network.keys())
        attractors = []
        for state_bits in range(2 ** len(nodes)):
            state = {n: (state_bits >> i) & 1 for i, n in enumerate(nodes)}
            seen = []
            current = state.copy()
            while current not in seen:
                seen.append(current.copy())
                next_state = {}
                for node, rule in network.items():
                    next_state[node] = BoolNetBridge._eval_rule(rule, current)
                current = next_state
                if len(seen) > 100:
                    break
            if current in seen:
                cycle_start = seen.index(current)
                cycle = seen[cycle_start:]
                if cycle not in [a["states"] for a in attractors]:
                    attractors.append({"states": cycle, "period": len(cycle)})
        return attractors

    @staticmethod
    def _eval_rule(rule: str, state: dict[str, int]) -> int:
        """Evaluate a simple Boolean rule."""
        rule = rule.strip().replace("!", "not ").replace("&", " and ").replace("|", " or ")
        try:
            return int(eval(rule, {"__builtins__": {}}, state))
        except Exception:
            return 0
