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
        """Evaluate a simple Boolean rule safely (no eval, AST-based).

        Supported syntax: variable names, integers 0/1, NOT (!), AND (&), OR (|),
        parentheses. Anything else returns 0. State values come from the local
        state dict only — no attribute access, no function calls, no dunder names.
        """
        import ast

        rule = rule.strip()
        if not rule:
            return 0

        # Normalize Boolean operators to Python syntax.
        rule = rule.replace("!", "not ").replace("&", " and ").replace("|", " or ")

        try:
            tree = ast.parse(rule, mode="eval")
        except SyntaxError:
            return 0

        def _eval(node: ast.AST) -> int:
            if isinstance(node, ast.Expression):
                return _eval(node.body)
            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, bool)):
                    return 1 if node.value else 0
                return 0
            if isinstance(node, ast.Name):
                if node.id.startswith("__"):
                    return 0
                val = state.get(node.id)
                if isinstance(val, (int, bool)):
                    return 1 if val else 0
                return 0
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
                return 0 if _eval(node.operand) else 1
            if isinstance(node, ast.BoolOp):
                values = [_eval(v) for v in node.values]
                if isinstance(node.op, ast.And):
                    return 1 if all(values) else 0
                if isinstance(node.op, ast.Or):
                    return 1 if any(values) else 0
                return 0
            # Reject calls, attributes, comparisons, subscripts, etc.
            return 0

        try:
            return _eval(tree)
        except Exception:
            return 0
