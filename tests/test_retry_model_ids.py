"""F11: retry cascade must not cross-wire foreign org/model IDs."""

from __future__ import annotations

from src.llm.multi_provider import LLMProvider
from src.llm.retry_pkg.policies import ProviderRetryManager


def test_non_openrouter_gets_provider_default_not_foreign_id() -> None:
    foreign = "anthropic/claude-sonnet-4.6"
    primary = LLMProvider.OPENROUTER
    for provider in (
        LLMProvider.DEEPSEEK,
        LLMProvider.MISTRAL,
        LLMProvider.XAI,
        LLMProvider.MOONSHOT,
    ):
        model = ProviderRetryManager._model_for_provider(provider, primary, foreign)
        assert not str(model).startswith("anthropic/"), (
            f"{provider} must not reuse foreign anthropic/ id, got {model}"
        )
