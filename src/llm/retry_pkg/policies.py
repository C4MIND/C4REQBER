"""Retry Policies.

Provider retry manager with provider sequencing and batch generation.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from src.llm.config import get_api_key_env, get_default_model
from src.llm.multi_provider import LLMProvider, LLMResponse, ProviderConfig, ProviderRouter

from .core import (
    RETRY_BACKOFF_BASE,
    RETRY_ENABLED,
    RETRY_MAX_ATTEMPTS,
    AllProvidersExhaustedError,
    ProviderRetryError,
    ProviderStats,
    RetryResult,
)


class ProviderRetryManager:
    """
    Manages auto-retry with provider sequencing.

    Retry strategy:
    1. Try primary provider with exponential backoff retries
    2. If exhausted, try next provider in ordered list
    3. Track per-provider statistics
    4. Return error if all providers fail
    """

    # Default provider order when AUTO or explicit ordering needed
    PROVIDER_ORDER: list[LLMProvider] = [
        LLMProvider.OPENROUTER,
        LLMProvider.XAI,
        LLMProvider.MISTRAL,
        LLMProvider.DEEPSEEK,
        LLMProvider.MOONSHOT,
        LLMProvider.LIQUID,
        LLMProvider.NVIDIA,
        LLMProvider.YANDEX,
        LLMProvider.MLX,
        LLMProvider.OLLAMA,
        LLMProvider.LM_STUDIO,
    ]

    def __init__(
        self,
        router: ProviderRouter,
        max_retries: int = RETRY_MAX_ATTEMPTS,
        backoff_base: float = RETRY_BACKOFF_BASE,
        enabled: bool = RETRY_ENABLED,
        provider_order: list[LLMProvider] | None = None,
    ) -> None:
        self.router = router
        self.max_retries = max(1, max_retries)
        self.backoff_base = max(0.01, backoff_base)
        self.enabled = enabled
        self.provider_order = provider_order or list(self.PROVIDER_ORDER)
        self._stats: dict[str, ProviderStats] = {}
        self._lock: asyncio.Lock | None = None

    def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    # ─────────────────────────────────────────────────────────────
    # Statistics
    # ─────────────────────────────────────────────────────────────

    def _get_stats(self, provider: str) -> ProviderStats:
        if provider not in self._stats:
            self._stats[provider] = ProviderStats(provider=provider)
        return self._stats[provider]

    def _record_success(self, provider: str, latency_ms: float) -> None:
        stats = self._get_stats(provider)
        stats.attempts += 1
        stats.successes += 1
        stats.total_latency_ms += latency_ms
        stats.last_error = None

    def _record_failure(self, provider: str, error: str, is_retry: bool = False) -> None:
        stats = self._get_stats(provider)
        stats.attempts += 1
        stats.failures += 1
        # Count retry on every failure (each failure triggers a retry attempt)
        stats.retries += 1
        stats.last_error = error[:500]  # cap error length

    def get_stats(self) -> dict[str, dict[str, Any]]:
        return {name: s.to_dict() for name, s in self._stats.items()}

    def get_provider_ranking(self) -> list[tuple[str, float]]:
        """Return providers sorted by success rate (descending)."""
        ranked = [(s.provider, s.success_rate) for s in self._stats.values()]
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked

    @staticmethod
    def _provider_has_credentials(provider: LLMProvider) -> bool:
        """Skip cloud providers that have no API key configured."""
        import os

        if provider in (
            LLMProvider.OLLAMA,
            LLMProvider.LM_STUDIO,
            LLMProvider.MLX,
            LLMProvider.AUTO,
        ):
            return True
        env_name = get_api_key_env(provider)
        if not env_name:
            return True
        val = os.environ.get(env_name, "")
        if val and not val.startswith("YOUR_") and not val.startswith("sk-YOUR"):
            return True
        # OpenRouter often uses KILO_OPENROUTER_API_KEY
        if provider == LLMProvider.OPENROUTER:
            alt = os.environ.get("KILO_OPENROUTER_API_KEY", "")
            return bool(alt and not alt.startswith("YOUR_"))
        return False

    @staticmethod
    def _model_for_provider(
        provider: LLMProvider,
        primary: LLMProvider,
        primary_model: str | None,
    ) -> str:
        """Use stage model only on the primary provider; else provider defaults."""
        if provider == primary and primary_model:
            return primary_model
        if provider == LLMProvider.OPENROUTER and primary_model and "/" in primary_model:
            return primary_model
        return get_default_model(provider)

    # ─────────────────────────────────────────────────────────────
    # Core retry logic
    # ─────────────────────────────────────────────────────────────

    async def _sleep_backoff(self, attempt: int) -> None:
        """Exponential backoff: base * 2^attempt (attempt 1 -> base*2, attempt 2 -> base*4)."""
        delay = self.backoff_base * (2**attempt)
        await asyncio.sleep(delay)

    async def _try_provider(
        self,
        provider: LLMProvider,
        config: ProviderConfig,
        stage_name: str,
        prompt: str,
        system_prompt: str | None,
    ) -> LLMResponse:
        """Try a single provider with retries and backoff."""
        last_error = ""
        provider_name = provider.value

        for attempt in range(1, self.max_retries + 1):
            start = time.time()
            try:
                client = await self.router._get_client(provider)
                response = await client.generate(
                    prompt=prompt,
                    model=config.model,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    system_prompt=system_prompt,
                )
                latency_ms = (time.time() - start) * 1000
                self._record_success(provider_name, latency_ms)
                return response

            except Exception as e:
                latency_ms = (time.time() - start) * 1000
                error_msg = f"{type(e).__name__}: {str(e)[:200]}"
                last_error = error_msg
                self._record_failure(provider_name, error_msg)

                if attempt < self.max_retries:
                    await self._sleep_backoff(attempt)

        raise ProviderRetryError(
            f"Provider {provider_name} failed after {self.max_retries} attempts. Last: {last_error}"
        )

    def _get_provider_sequence(self, primary: LLMProvider, stage_name: str) -> list[LLMProvider]:
        """Build ordered list of providers to try (primary first, then alternates)."""
        providers = [primary]

        for p in self.provider_order:
            if p != primary and p not in providers:
                providers.append(p)

        if primary == LLMProvider.AUTO:
            providers = [p for p in self.provider_order if p != LLMProvider.AUTO]

        return providers

    async def execute_with_retry(
        self,
        stage_name: str,
        prompt: str,
        system_prompt: str | None = None,
        max_retries: int | None = None,
    ) -> RetryResult:
        """
        Execute LLM generation with retry and provider sequencing.

        Args:
            stage_name: Pipeline stage name
            prompt: User prompt
            system_prompt: Optional system instructions
            max_retries: Override default max retries (optional)

        Returns:
            RetryResult with response and metadata

        Raises:
            AllProvidersExhaustedError: If all providers fail
        """
        if not self.enabled:
            # Passthrough: no retry logic
            config = self.router.get_config_for_stage(stage_name)
            client = await self.router._get_client(config.provider)
            start = time.time()
            response = await client.generate(
                prompt=prompt,
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                system_prompt=system_prompt,
            )
            latency_ms = (time.time() - start) * 1000
            return RetryResult(
                response=response,
                provider=config.provider.value,
                attempts=1,
                provider_sequence_used=False,
                total_latency_ms=latency_ms,
            )

        retries = max_retries or self.max_retries
        original_retries = self.max_retries
        if max_retries is not None:
            self.max_retries = retries

        config = self.router.get_config_for_stage(stage_name)
        primary = config.provider

        providers = self._get_provider_sequence(primary, stage_name)
        attempt_history: list[tuple[str, str]] = []
        total_start = time.time()
        provider_sequence_used = False

        try:
            for idx, provider in enumerate(providers):
                if idx > 0:
                    provider_sequence_used = True

                if not self._provider_has_credentials(provider):
                    attempt_history.append((provider.value, "missing_api_key"))
                    continue

                try:
                    # Never reuse OpenRouter model IDs on DeepSeek/XAI/etc.
                    model = self._model_for_provider(provider, primary, config.model)
                    provider_config = ProviderConfig(
                        provider=provider,
                        model=model,
                        temperature=config.temperature,
                        max_tokens=config.max_tokens,
                        timeout=config.timeout,
                    )
                    response = await self._try_provider(
                        provider, provider_config, stage_name, prompt, system_prompt
                    )
                    total_latency_ms = (time.time() - total_start) * 1000

                    return RetryResult(
                        response=response,
                        provider=provider.value,
                        attempts=sum(
                            self._get_stats(p.value).attempts for p in providers[: idx + 1]
                        ),
                        provider_sequence_used=provider_sequence_used,
                        total_latency_ms=total_latency_ms,
                    )

                except ProviderRetryError as e:
                    attempt_history.append((provider.value, str(e)))
                    continue

            # All providers exhausted
            raise AllProvidersExhaustedError(stage_name, attempt_history)

        finally:
            if max_retries is not None:
                self.max_retries = original_retries

    # ─────────────────────────────────────────────────────────────
    # Convenience wrappers
    # ─────────────────────────────────────────────────────────────

    async def generate(
        self,
        stage_name: str,
        prompt: str,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """Generate with retry, returning just the response."""
        result = await self.execute_with_retry(stage_name, prompt, system_prompt)
        return result.response

    async def generate_batch(
        self,
        stage_name: str,
        prompts: list[str],
        system_prompt: str | None = None,
        max_concurrent: int = 3,
    ) -> list[LLMResponse]:
        """Batch generate with retry and concurrency limit."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def gen(prompt: str) -> LLMResponse:
            async with semaphore:
                try:
                    return await self.generate(stage_name, prompt, system_prompt)
                except AllProvidersExhaustedError as e:
                    raise RuntimeError(f"Batch generation failed: {e}") from e

        tasks = [gen(p) for p in prompts]
        return await asyncio.gather(*tasks)

    def reset_stats(self) -> None:
        """Clear all provider statistics."""
        self._stats.clear()

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "max_retries": self.max_retries,
            "backoff_base": self.backoff_base,
            "provider_order": [p.value for p in self.provider_order],
            "stats": self.get_stats(),
            "provider_ranking": self.get_provider_ranking(),
        }
