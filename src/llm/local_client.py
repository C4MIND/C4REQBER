"""Local LLM Client — Compatibility wrapper.

All symbols re-exported from llm.local.core and llm.local.client.
"""
from src.llm.local.client import LocalLLMClient
from src.llm.local.core import HAS_HTTPX, LocalLLMResponse, LocalProvider


__all__ = [
    "HAS_HTTPX",
    "LocalLLMClient",
    "LocalLLMResponse",
    "LocalProvider",
]
