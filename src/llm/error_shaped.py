"""Detect LLM responses that embed failures in content instead of raising."""

from __future__ import annotations


_ERROR_PREFIXES = (
    "[MLX Error]",
    "Batch error:",
    "[Error]",
    "[LLM unavailable",
    "[LLM Error]",
)


def is_error_shaped_llm(text: str | None) -> bool:
    """True when provider returned a failure string as successful content."""
    if not text or not isinstance(text, str):
        return False
    s = text.strip()
    return any(s.startswith(p) for p in _ERROR_PREFIXES)
