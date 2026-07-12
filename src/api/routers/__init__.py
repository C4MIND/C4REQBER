"""
c4-cdi-turbo API: Router Package

Submodules are imported explicitly by ``src.api.server`` (and callers).
Avoid eager imports here — loading every router at package init pulls in
heavy optional deps (agents, DB) and breaks isolated imports like metrics.
"""
from __future__ import annotations

__all__ = [
    "auth",
    "bridge",
    "discoveries",
    "discovery_list",
    "graph",
    "health",
    "metrics",
    "patterns",
    "search",
    "theorems",
    "validations",
    "validation_single",
    "websocket",
]
