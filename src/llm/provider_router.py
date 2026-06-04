"""Provider Router — Compatibility wrapper.

All symbols re-exported from llm.routing.core and llm.routing.strategy.
"""
from src.llm.routing.core import (
    LLMProvider,
    ProviderConfig,
    ProviderPreset,
    StageProviderMapping,
)
from src.llm.routing.strategy import ProviderRouter


__all__ = [
    "LLMProvider",
    "ProviderConfig",
    "ProviderPreset",
    "ProviderRouter",
    "StageProviderMapping",
]
