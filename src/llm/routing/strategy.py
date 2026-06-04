"""Provider Router — Routing strategy and execution.

Multi-provider LLM routing for pipeline stages.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any

from src.llm.cache import AsyncLLMCache, hash_prompt
from src.llm.local_client import LocalLLMClient, LocalProvider
from src.llm.routing.core import (
    LLMProvider,
    ProviderConfig,
    ProviderPreset,
    StageProviderMapping,
)


class ProviderRouter:
    """
    Routes LLM requests to appropriate providers based on pipeline stage.

    Usage:
        router = ProviderRouter.from_preset(ProviderPreset.HYBRID_DEEP)
        client = router.get_client_for_stage("synthesis")
        response = await client.generate("prompt...")
    """

    PRESETS: dict[ProviderPreset, StageProviderMapping] = {
        ProviderPreset.QUALITY: StageProviderMapping(
            preset="quality",
            default=ProviderConfig(
                LLMProvider.OPENROUTER, model="anthropic/claude-3.5-sonnet"
            ),
            stages={
                "synthesis": ProviderConfig(
                    LLMProvider.OPENROUTER,
                    model="anthropic/claude-3.5-sonnet",
                    temperature=0.6,
                    max_tokens=2000,
                ),
                "mp_rotation": ProviderConfig(
                    LLMProvider.OPENROUTER,
                    model="anthropic/claude-3.5-sonnet",
                    temperature=0.7,
                    max_tokens=500,
                ),
                "validation": ProviderConfig(
                    LLMProvider.OPENROUTER,
                    model="openai/gpt-4o-mini",
                    temperature=0.3,
                    max_tokens=500,
                ),
            },
        ),
        ProviderPreset.COST_OPTIMIZED: StageProviderMapping(
            preset="cost_optimized",
            default=ProviderConfig(LLMProvider.OLLAMA, model="qwen2.5:14b"),
            stages={
                "synthesis": ProviderConfig(
                    LLMProvider.OPENROUTER,
                    model="openai/gpt-4o-mini",
                    temperature=0.6,
                    max_tokens=2000,
                ),
                "mp_rotation": ProviderConfig(
                    LLMProvider.OLLAMA,
                    model="qwen2.5:14b",
                    temperature=0.7,
                    max_tokens=500,
                ),
                "validation": ProviderConfig(
                    LLMProvider.OLLAMA,
                    model="qwen2.5:14b",
                    temperature=0.3,
                    max_tokens=500,
                ),
            },
        ),
        ProviderPreset.LOCAL_ONLY: StageProviderMapping(
            preset="local_only",
            default=ProviderConfig(LLMProvider.OLLAMA, model="qwen2.5:14b"),
            stages={
                "synthesis": ProviderConfig(
                    LLMProvider.LM_STUDIO, temperature=0.6, max_tokens=2000
                ),
                "mp_rotation": ProviderConfig(
                    LLMProvider.OLLAMA,
                    model="qwen2.5:7b",
                    temperature=0.7,
                    max_tokens=500,
                ),
            },
        ),
        ProviderPreset.HYBRID_FAST: StageProviderMapping(
            preset="hybrid_fast",
            default=ProviderConfig(LLMProvider.OLLAMA, model="qwen2.5:14b"),
            stages={
                "synthesis": ProviderConfig(
                    LLMProvider.OPENROUTER,
                    model="openai/gpt-4o-mini",
                    temperature=0.6,
                    max_tokens=2000,
                ),
            },
        ),
        ProviderPreset.HYBRID_DEEP: StageProviderMapping(
            preset="hybrid_deep",
            default=ProviderConfig(LLMProvider.OLLAMA, model="qwen2.5:7b"),
            stages={
                "synthesis": ProviderConfig(
                    LLMProvider.OPENROUTER,
                    model="anthropic/claude-3.5-sonnet",
                    temperature=0.6,
                    max_tokens=2000,
                ),
                "mp_rotation": ProviderConfig(
                    LLMProvider.OPENROUTER,
                    model="openai/gpt-4o-mini",
                    temperature=0.7,
                    max_tokens=500,
                ),
                "validation": ProviderConfig(
                    LLMProvider.OLLAMA,
                    model="qwen2.5:7b",
                    temperature=0.3,
                    max_tokens=500,
                ),
            },
        ),
        ProviderPreset.BALANCED: StageProviderMapping(
            preset="balanced",
            default=ProviderConfig(LLMProvider.OLLAMA, model="qwen2.5:14b"),
            stages={
                "synthesis": ProviderConfig(
                    LLMProvider.OPENROUTER,
                    model="openai/gpt-4o",
                    temperature=0.6,
                    max_tokens=2000,
                ),
                "mp_rotation": ProviderConfig(
                    LLMProvider.OLLAMA,
                    model="qwen2.5:14b",
                    temperature=0.7,
                    max_tokens=500,
                ),
                "validation": ProviderConfig(
                    LLMProvider.OLLAMA,
                    model="qwen2.5:7b",
                    temperature=0.3,
                    max_tokens=300,
                ),
            },
        ),
    }

    def __init__(
        self,
        mapping: StageProviderMapping | None = None,
        cache: AsyncLLMCache | None = None,
    ) -> None:
        self.mapping = mapping or StageProviderMapping()
        self._clients: dict[str, Any] = {}
        self._local_client: LocalLLMClient | None = None
        self._remote_client: Any | None = None
        self._stats: dict[str, dict[str, Any]] = {}
        self._client_lock = asyncio.Lock()
        self._auto_client: Any | None = None
        self._cache = cache or AsyncLLMCache()

    @classmethod
    def from_preset(cls, preset: ProviderPreset) -> ProviderRouter:
        """Create router from built-in preset."""
        mapping = cls.PRESETS.get(preset, StageProviderMapping())
        return cls(mapping)

    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> ProviderRouter:
        """Create router from dict config."""
        if "preset" in config:
            try:
                preset = ProviderPreset(config["preset"])
                return cls.from_preset(preset)
            except ValueError:
                pass

        # Custom mapping
        stages = {}
        for stage_name, stage_config in config.get("stages", {}).items():
            stages[stage_name] = ProviderConfig(
                provider=LLMProvider(stage_config["provider"]),
                model=stage_config.get("model"),
                temperature=stage_config.get("temperature", 0.7),
                max_tokens=stage_config.get("max_tokens", 2000),
            )

        default_config = config.get("default", {})
        default = ProviderConfig(
            provider=LLMProvider(default_config.get("provider", "auto")),
            model=default_config.get("model"),
            temperature=default_config.get("temperature", 0.7),
            max_tokens=default_config.get("max_tokens", 2000),
        )

        return cls(StageProviderMapping(stages=stages, default=default))

    def get_config_for_stage(self, stage_name: str) -> ProviderConfig:
        """Get provider config for a pipeline stage."""
        return self.mapping.stages.get(stage_name, self.mapping.default)

    async def get_client_for_stage(self, stage_name: str) -> Any:
        """Get appropriate client for a stage (thread-safe lazy init)."""
        config = self.get_config_for_stage(stage_name)


        if config.provider == LLMProvider.OPENROUTER:
            from src.llm.async_client import AsyncLLMClient

            async with self._client_lock:
                if self._remote_client is None:
                    self._remote_client = AsyncLLMClient(timeout=config.timeout)
                return self._remote_client

        if config.provider in (LLMProvider.OLLAMA, LLMProvider.LM_STUDIO):
            async with self._client_lock:
                if self._local_client is None:
                    self._local_client = LocalLLMClient(timeout=config.timeout)
                return self._local_client

        if config.provider == LLMProvider.LIQUID:
            from src.integrations.liquid_ai import LiquidAIClient
            return LiquidAIClient(timeout=config.timeout)

        if config.provider == LLMProvider.NVIDIA:
            from src.integrations.nvidia import NvidiaNimClient
            return NvidiaNimClient(timeout=config.timeout)

        if config.provider == LLMProvider.YANDEX:
            from src.integrations.yandex import YandexGPTClient
            return YandexGPTClient(timeout=config.timeout)

        if config.provider == LLMProvider.MLX:
            from src.llm.providers.mlx_provider import MLXProvider
            return MLXProvider(model=config.model, timeout=config.timeout)

        if config.provider == LLMProvider.XAI:
            from src.integrations.xai_client import XAIClient
            return XAIClient(timeout=config.timeout)

        if config.provider == LLMProvider.MISTRAL:
            from src.integrations.mistral_client import MistralClient
            return MistralClient(timeout=config.timeout)

        if config.provider == LLMProvider.MOONSHOT:
            from src.integrations.moonshot_client import MoonshotClient
            return MoonshotClient(timeout=config.timeout)

        if config.provider == LLMProvider.DEEPSEEK:
            from src.integrations.deepseek_client import DeepSeekClient
            return DeepSeekClient(timeout=config.timeout)

        if config.provider == LLMProvider.AUTO:
            raise ValueError("AUTO provider is not supported. Choose explicit provider.")

        raise ValueError(f"Unknown provider: {config.provider}")

    async def generate(
        self,
        stage_name: str,
        prompt: str,
        system_prompt: str | None = None,
    ) -> Any:
        """Generate text for a specific pipeline stage."""
        config = self.get_config_for_stage(stage_name)

        # ── Cache check ───────────────────────────────────────────
        prompt_hash = hash_prompt(
            f"{config.provider.value}:{prompt}:{(system_prompt or '')}:"
            f"{(config.model or '')}:{stage_name}"
        )
        cached = await self._cache.get(prompt_hash)
        if cached is not None:
            from src.llm.async_client import LLMResponse

            return LLMResponse(
                content=cached,
                model=config.model or "cached",
                usage={"prompt_tokens": 0, "completion_tokens": 0, "cached": True},
                latency_ms=0.0,
            )

        client = await self.get_client_for_stage(stage_name)  # type: ignore[func-returns-value]

        start = time.time()

        try:
            if hasattr(client, "generate"):
                response = await client.generate(  # type: ignore[attr-defined]
                    prompt=prompt,
                    model=config.model,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    system_prompt=system_prompt,
                )
            else:
                # LocalLLMClient has different signature
                from src.llm.local_client import LocalLLMClient

                if isinstance(client, LocalLLMClient):
                    response = await client.generate(  # type: ignore[unreachable]
                        prompt=prompt,
                        model=config.model,
                        temperature=config.temperature,
                        max_tokens=config.max_tokens,
                        system_prompt=system_prompt,
                        provider=LocalProvider(config.provider.value)
                        if config.provider != LLMProvider.AUTO
                        else None,
                    )
                else:
                    response = await client.generate(  # type: ignore[attr-defined]
                        prompt=prompt,
                        model=config.model,
                        temperature=config.temperature,
                        max_tokens=config.max_tokens,
                        system_prompt=system_prompt,
                    )

            # ── Cache save ──────────────────────────────────────
            if hasattr(response, "content"):
                await self._cache.set(prompt_hash, response.content)

            # Track cost via global CostTracker
            try:
                from src.llm.cost_tracker import get_cost_tracker
                tracker = get_cost_tracker()
                usage = getattr(response, "usage", {}) or {}
                tracker.track_request(
                    provider=config.provider.value,
                    model=config.model or "unknown",
                    input_tokens=usage.get("prompt_tokens", 0) or len(prompt.split()),
                    output_tokens=usage.get("completion_tokens", 0) or (len(getattr(response, "content", "").split()) if hasattr(response, "content") else 0),
                    duration_ms=(time.time() - start) * 1000,
                )
            except (ConnectionError, TimeoutError, RuntimeError, ValueError):
                pass

            # Track stats
            latency = (time.time() - start) * 1000
            if stage_name not in self._stats:
                self._stats[stage_name] = {
                    "calls": 0,
                    "total_latency_ms": 0,
                    "errors": 0,
                }
            self._stats[stage_name]["calls"] += 1
            self._stats[stage_name]["total_latency_ms"] += latency

            return response

        except (ConnectionError, TimeoutError, RuntimeError, ValueError):
            if stage_name not in self._stats:
                self._stats[stage_name] = {
                    "calls": 0,
                    "total_latency_ms": 0,
                    "errors": 0,
                }
            self._stats[stage_name]["errors"] += 1
            raise

    async def generate_batch(
        self,
        stage_name: str,
        prompts: list[str],
        system_prompt: str | None = None,
    ) -> list[Any]:
        """Batch generate for a stage."""
        config = self.get_config_for_stage(stage_name)
        client = await self.get_client_for_stage(stage_name)  # type: ignore[func-returns-value]

        if hasattr(client, "generate_batch"):
            return await client.generate_batch(  # type: ignore[attr-defined, no-any-return]
                prompts=prompts,
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )

        # Fallback to sequential
        results = []
        for prompt in prompts:
            results.append(await self.generate(stage_name, prompt, system_prompt))
        return results

    async def close_all(self) -> None:
        """Close all cached clients."""
        if self._remote_client:
            await self._remote_client.close()
            self._remote_client = None
        if self._local_client:
            await self._local_client.close()
            self._local_client = None
        if self._auto_client:
            await self._auto_client.close()
            self._auto_client = None

    def get_stats(self) -> dict[str, Any]:
        """Get routing statistics."""
        stats = {}
        for stage, data in self._stats.items():
            stats[stage] = {
                **data,
                "avg_latency_ms": data["total_latency_ms"] / max(data["calls"], 1),
            }
        return {
            "preset": self.mapping.preset,
            "mapping": {
                stage: {
                    "provider": cfg.provider.value,
                    "model": cfg.model,
                }
                for stage, cfg in self.mapping.stages.items()
            },
            "default_provider": self.mapping.default.provider.value,
            "default_model": self.mapping.default.model,
            "stage_stats": stats,
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize router config."""
        return {
            "preset": self.mapping.preset,
            "default": {
                "provider": self.mapping.default.provider.value,
                "model": self.mapping.default.model,
                "temperature": self.mapping.default.temperature,
                "max_tokens": self.mapping.default.max_tokens,
            },
            "stages": {
                stage: {
                    "provider": cfg.provider.value,
                    "model": cfg.model,
                    "temperature": cfg.temperature,
                    "max_tokens": cfg.max_tokens,
                }
                for stage, cfg in self.mapping.stages.items()
            },
        }
