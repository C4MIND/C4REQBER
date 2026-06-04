"""Provider Router — Core types and configuration."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from src.llm.config import (
    LLMProvider,
    ProviderPreset,
    get_api_key_env,
    get_base_url,
    get_default_model,
)


__all__ = [
    "LLMProvider",
    "ProviderConfig",
    "StageProviderMapping",
    "ProviderPreset",
    "get_base_url",
    "get_api_key_env",
    "get_default_model",
]


@dataclass
class ProviderConfig:
    """Configuration for a single provider."""

    provider: LLMProvider
    model: str | None = None
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: float = 60.0


@dataclass
class StageProviderMapping:
    """Maps pipeline stages to providers."""

    stages: dict[str, ProviderConfig] = field(default_factory=dict)
    default: ProviderConfig = field(
        default_factory=lambda: ProviderConfig(LLMProvider.OPENROUTER)
    )
    preset: str | None = None
