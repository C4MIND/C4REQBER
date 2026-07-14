"""Backward-compat shim — search_knowledge moved to src.discovery.search.

It is domain logic (wraps knowledge.orchestrator), not an API concern, so it lives
in the discovery layer now. Re-exported here so existing imports keep working.
"""
from __future__ import annotations

from src.discovery.search import search_knowledge


__all__ = ["search_knowledge"]
