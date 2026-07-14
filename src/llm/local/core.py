"""Local LLM Client — Core types and provider definitions."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


@dataclass
class LocalLLMResponse:
    """LocalLLMResponse."""
    content: str
    model: str
    usage: dict[str, int]
    latency_ms: float = 0.0
    provider: str = "unknown"


class LocalProvider(Enum):
    """LocalProvider."""
    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio"
