"""LLM integration — public API is ``get_gateway()``.

Legacy symbols (``ProviderRouter``, clients, etc.) remain importable for
internal/strategy use but new callers should go through the gateway.
"""

from __future__ import annotations

from .async_client import AsyncLLMClient, async_generate
from .cache import AsyncLLMCache, LLMCache, hash_prompt
from .client import LLMClient
from .config import (
    LLMProvider,
    ProviderConfig,
    ProviderPreset,
    StageProviderMapping,
)
from .falsifiability import FalsifiabilityGenerator
from .gateway import DefaultGateway, generate_with_fallback, get_gateway
from .multi_provider import (
    async_generate as multi_async_generate,
)
from .providers import (
    BaseLLMClient,
    DeepSeekClient,
    LLMResponse,
    MistralClient,
    MoonshotClient,
    OpenRouterClient,
    XAIClient,
)
from .router import ProviderRouter
from .synthesizer import HypothesisSynthesizer


__all__ = [
    # Preferred public API
    "get_gateway",
    "DefaultGateway",
    "generate_with_fallback",
    # Legacy / strategy (prefer get_gateway)
    "LLMClient",
    "AsyncLLMClient",
    "async_generate",
    "HypothesisSynthesizer",
    "FalsifiabilityGenerator",
    "LLMCache",
    "AsyncLLMCache",
    "hash_prompt",
    "ProviderRouter",
    "ProviderPreset",
    "ProviderConfig",
    "StageProviderMapping",
    "LLMProvider",
    "LLMResponse",
    "OpenRouterClient",
    "XAIClient",
    "MistralClient",
    "MoonshotClient",
    "DeepSeekClient",
    "BaseLLMClient",
    "multi_async_generate",
]
