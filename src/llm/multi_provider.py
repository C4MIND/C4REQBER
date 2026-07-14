"""
Multi-Provider LLM Router
Unified interface for all LLM providers.

Supported providers:
- OpenRouter (openrouter)
- XAI / Grok (xai)
- Mistral AI (mistral)
- Moonshot AI (moonshot)
- DeepSeek (deepseek)
- Ollama (ollama) — local
- LM Studio (lm_studio) — local
"""

from __future__ import annotations

from typing import Any

from src.llm.config import (
    LLMProvider,
    ProviderConfig,
    ProviderPreset,
    StageProviderMapping,
)
from src.llm.providers import (
    BaseLLMClient,
    DeepSeekClient,
    LLMResponse,
    MistralClient,
    MoonshotClient,
    OpenRouterClient,
    XAIClient,
)
from src.llm.router import ProviderRouter


# Backward compatibility
AsyncLLMClient = OpenRouterClient


async def async_generate(
    prompt: str,
    model: str | None = None,
    api_key: str | None = None,
    provider: LLMProvider = LLMProvider.OPENROUTER,
    **kwargs: Any,
) -> LLMResponse:
    """One-shot async generation with any provider."""
    if provider == LLMProvider.OPENROUTER:
        client = OpenRouterClient(api_key=api_key)
    elif provider == LLMProvider.XAI:
        client = XAIClient(api_key=api_key)  # type: ignore[assignment]
    elif provider == LLMProvider.MISTRAL:
        client = MistralClient(api_key=api_key)  # type: ignore[assignment]
    elif provider == LLMProvider.MOONSHOT:
        client = MoonshotClient(api_key=api_key)  # type: ignore[assignment]
    elif provider == LLMProvider.DEEPSEEK:
        client = DeepSeekClient(api_key=api_key)  # type: ignore[assignment]
    else:
        client = OpenRouterClient(api_key=api_key)

    try:
        return await client.generate(prompt, model=model, **kwargs)  # type: ignore[no-any-return]
    finally:
        await client.close()


__all__ = [
    "LLMProvider",
    "ProviderPreset",
    "ProviderConfig",
    "StageProviderMapping",
    "LLMResponse",
    "BaseLLMClient",
    "OpenRouterClient",
    "XAIClient",
    "MistralClient",
    "MoonshotClient",
    "DeepSeekClient",
    "ProviderRouter",
    "AsyncLLMClient",
    "async_generate",
]
