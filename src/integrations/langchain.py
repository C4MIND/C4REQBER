"""LangChain integration bridge — honesty: capability listing only."""

from __future__ import annotations

from typing import Any


class LangChainBridge:
    """Lists tool names for LangChain wiring — not a live runnable chain."""

    available = False

    def as_tool(self) -> list[str]:
        return ["solve_problem", "run_simulation", "verify_proof", "search_knowledge"]

    def as_chain(self) -> dict[str, Any]:
        return {
            "type": "cognitive_exoskeleton",
            "steps": 12,
            "status": "unavailable",
            "note": "Static capability manifest — use blast MCP / gateway for real calls",
        }
