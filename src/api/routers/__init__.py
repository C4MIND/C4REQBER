"""
c4-cdi-turbo API: Router Package
"""
from __future__ import annotations

from src.api.routers import (
    auth,
    bridge,
    discoveries,
    graph,
    health,
    patterns,
    search,
    theorems,
    validation_single,
    validations,
    websocket,
)


__all__ = [
    "auth",
    "bridge",
    "discoveries",
    "graph",
    "health",
    "patterns",
    "search",
    "theorems",
    "validations",
    "validation_single",
    "websocket",
]
