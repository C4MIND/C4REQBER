"""Local LLM Client — Compatibility wrapper.

All symbols re-exported from llm.local.core, llm.local.client, and llm.local.client_unified.
"""
from src.llm.local.client import LocalLLMClient
from src.llm.local.client_unified import UnifiedLLMClient, UnifiedResponse
from src.llm.local.core import HAS_HTTPX, LocalLLMResponse, LocalProvider


__all__ = [
    "HAS_HTTPX",
    "LocalLLMClient",
    "LocalLLMResponse",
    "LocalProvider",
    "UnifiedLLMClient",
    "UnifiedResponse",
]
