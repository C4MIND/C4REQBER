"""Deprecated shell — use ``src.llm.get_gateway().generate_sync`` or ``src.llm.generate_with_fallback``."""

from __future__ import annotations

from src.llm.gateway import generate_with_fallback


class NoProviderAvailableError(RuntimeError):
    """Raised when no LLM provider can be reached."""


__all__ = ["NoProviderAvailableError", "generate_with_fallback"]
