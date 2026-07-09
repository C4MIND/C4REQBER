"""Provider configuration for multi-provider LLM routing."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum


class LLMProvider(Enum):
    """All available LLM providers."""

    OPENROUTER = "openrouter"
    XAI = "xai"
    MLX = "mlx"
    MISTRAL = "mistral"
    MOONSHOT = "moonshot"
    DEEPSEEK = "deepseek"
    LIQUID = "liquid"
    NVIDIA = "nvidia"
    YANDEX = "yandex"
    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio"
    AUTO = "auto"


class ProviderPreset(Enum):
    """Built-in provider routing presets."""

    QUALITY = "quality"
    COST_OPTIMIZED = "cost"
    LOCAL_ONLY = "local_only"
    HYBRID_FAST = "hybrid_fast"
    HYBRID_DEEP = "hybrid_deep"
    BALANCED = "balanced"
    C4REQBER = "c4reqber"
    LEGACY_BALANCED = "legacy_balanced"


# Provider base URLs from environment or defaults
_PROVIDER_BASE_URLS = {
    LLMProvider.OPENROUTER: os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    LLMProvider.XAI: os.getenv("XAI_BASE_URL", "https://api.x.ai/v1"),
    LLMProvider.MISTRAL: os.getenv("MISTRAL_BASE_URL", "https://api.mistral.ai/v1"),
    LLMProvider.MOONSHOT: os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1"),
    LLMProvider.DEEPSEEK: os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
    LLMProvider.LIQUID: os.getenv("LIQUID_URL", "https://labs.liquid.ai/api/v1"),
    LLMProvider.NVIDIA: os.getenv("NVIDIA_API_URL", "https://integrate.api.nvidia.com/v1"),
    LLMProvider.YANDEX: os.getenv("YANDEX_API_URL", "https://llm.api.cloud.yandex.net/foundationModels/v1"),
    LLMProvider.LM_STUDIO: os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1"),
}  # Note: base URLs kept on getenv for flexibility; keys are centralized via get_key()

# API key env var names
_PROVIDER_API_KEY_ENV = {
    LLMProvider.OPENROUTER: "OPENROUTER_API_KEY",
    LLMProvider.XAI: "XAI_API_KEY",
    LLMProvider.MISTRAL: "MISTRAL_API_KEY",
    LLMProvider.MOONSHOT: "MOONSHOT_API_KEY",
    LLMProvider.DEEPSEEK: "DEEPSEEK_API_KEY",
    LLMProvider.LIQUID: "LIQUID_API_KEY",
    LLMProvider.NVIDIA: "NVIDIA_API_KEY",
    LLMProvider.YANDEX: "YANDEX_API_KEY",
}

# Default models per provider
_PROVIDER_DEFAULT_MODELS = {
    LLMProvider.OPENROUTER: "qwen/qwen-2.5-72b-instruct",
    LLMProvider.XAI: "grok-4.3",
    LLMProvider.MISTRAL: "mistral-large-latest",
    LLMProvider.MOONSHOT: "moonshot-v1-8k",
    LLMProvider.DEEPSEEK: "deepseek-chat",
    LLMProvider.LIQUID: "lfm-40b",
    LLMProvider.NVIDIA: "meta/llama-3.1-8b-instruct",
    LLMProvider.YANDEX: "yandexgpt-lite",
    LLMProvider.MLX: "mlx-community/Qwen2.5-7B-Instruct-4bit",
    LLMProvider.OLLAMA: "qwen2.5:14b",
    LLMProvider.LM_STUDIO: "local-model",
}


def get_base_url(provider: LLMProvider) -> str:
    """Get base URL for a provider."""
    return _PROVIDER_BASE_URLS.get(provider, "")


def get_api_key_env(provider: LLMProvider) -> str | None:
    """Get environment variable name for API key."""
    return _PROVIDER_API_KEY_ENV.get(provider)


def get_default_model(provider: LLMProvider) -> str:
    """Get default model for a provider."""
    return _PROVIDER_DEFAULT_MODELS.get(provider, "unknown")


@dataclass
class ProviderConfig:
    """Configuration for a single provider."""

    provider: LLMProvider
    model: str | None = None
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: float = 60.0

    def get_model(self) -> str:
        """Get effective model (configured or provider default)."""
        return self.model or get_default_model(self.provider)


@dataclass
class StageProviderMapping:
    """Maps pipeline stages to providers."""

    stages: dict[str, ProviderConfig] = field(default_factory=dict)
    default: ProviderConfig = field(default_factory=lambda: ProviderConfig(LLMProvider.AUTO))
    preset: str | None = None
