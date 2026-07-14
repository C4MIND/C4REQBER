from __future__ import annotations


"""LLM integration for c4-cdi-turbo"""

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
    "LLMClient",
    "AsyncLLMClient",
    "async_generate",
    "HypothesisSynthesizer",
    "FalsifiabilityGenerator",
    # Cache
    "LLMCache",
    "AsyncLLMCache",
    "hash_prompt",
    # Multi-provider
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
    "multi_async_generate",
]
