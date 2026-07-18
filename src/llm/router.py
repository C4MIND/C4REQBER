"""Provider router for multi-provider LLM routing."""

from __future__ import annotations

import asyncio
import time
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
    LocalLLMClient,
    MistralClient,
    MoonshotClient,
    OpenRouterClient,
    XAIClient,
)


class ProviderRouter:
    """Stage-based multi-provider router (internal strategy).

    Prefer ``src.llm.get_gateway().generate_for_stage`` for new code.
    Supports OpenRouter, XAI, Mistral, Moonshot, DeepSeek, Ollama, LM Studio.
    """

    PRESETS: dict[ProviderPreset, StageProviderMapping] = {
        ProviderPreset.QUALITY: StageProviderMapping(
            preset="quality",
            default=ProviderConfig(LLMProvider.OPENROUTER, model="anthropic/claude-sonnet-4.6"),
            stages={
                "synthesis": ProviderConfig(
                    LLMProvider.OPENROUTER,
                    model="anthropic/claude-sonnet-4.6",
                    temperature=0.6,
                    max_tokens=2000,
                ),
                "mp_rotation": ProviderConfig(
                    LLMProvider.XAI, model="grok-2-latest", temperature=0.7, max_tokens=500
                ),
                "validation": ProviderConfig(
                    LLMProvider.MISTRAL,
                    model="mistral-large-latest",
                    temperature=0.3,
                    max_tokens=500,
                ),
            },
        ),
        ProviderPreset.COST_OPTIMIZED: StageProviderMapping(
            preset="cost_optimized",
            default=ProviderConfig(LLMProvider.LM_STUDIO, model="qwen2.5-14b-instruct"),
            stages={
                "synthesis": ProviderConfig(
                    LLMProvider.LM_STUDIO,
                    model="qwen2.5-14b-instruct",
                    temperature=0.6,
                    max_tokens=2000,
                ),
                "mp_rotation": ProviderConfig(
                    LLMProvider.LM_STUDIO,
                    model="qwen2.5-14b-instruct",
                    temperature=0.7,
                    max_tokens=500,
                ),
                "validation": ProviderConfig(
                    LLMProvider.LM_STUDIO,
                    model="qwen2.5-14b-instruct",
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
                    LLMProvider.OLLAMA, model="qwen2.5:7b", temperature=0.7, max_tokens=500
                ),
            },
        ),
        ProviderPreset.HYBRID_FAST: StageProviderMapping(
            preset="hybrid_fast",
            default=ProviderConfig(LLMProvider.DEEPSEEK, model="deepseek-chat"),
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
            default=ProviderConfig(LLMProvider.DEEPSEEK, model="deepseek-chat"),
            stages={
                "synthesis": ProviderConfig(
                    LLMProvider.OPENROUTER,
                    model="anthropic/claude-sonnet-4.6",
                    temperature=0.6,
                    max_tokens=2000,
                ),
                "mp_rotation": ProviderConfig(
                    LLMProvider.XAI, model="grok-2-latest", temperature=0.7, max_tokens=500
                ),
                "validation": ProviderConfig(
                    LLMProvider.DEEPSEEK, model="deepseek-chat", temperature=0.3, max_tokens=500
                ),
            },
        ),
        ProviderPreset.BALANCED: StageProviderMapping(
            preset="balanced",
            default=ProviderConfig(LLMProvider.DEEPSEEK, model="deepseek-chat"),
            stages={
                "synthesis": ProviderConfig(
                    LLMProvider.OPENROUTER, model="openai/gpt-4o", temperature=0.6, max_tokens=2000
                ),
            },
        ),
        ProviderPreset.C4REQBER: StageProviderMapping(
            preset="c4reqber",
            default=ProviderConfig(LLMProvider.LM_STUDIO, model="qwen2.5-14b-instruct"),
            stages={
                "synthesis": ProviderConfig(
                    LLMProvider.LM_STUDIO,
                    model="qwen2.5-14b-instruct",
                    temperature=0.6,
                    max_tokens=3000,
                ),
                "mp_rotation": ProviderConfig(
                    LLMProvider.LM_STUDIO,
                    model="qwen2.5-14b-instruct",
                    temperature=0.7,
                    max_tokens=800,
                ),
                "validation": ProviderConfig(
                    LLMProvider.LM_STUDIO,
                    model="qwen2.5-14b-instruct",
                    temperature=0.3,
                    max_tokens=500,
                ),
                "c4_fingerprint": ProviderConfig(
                    LLMProvider.LM_STUDIO,
                    model="qwen2.5-14b-instruct",
                    temperature=0.4,
                    max_tokens=200,
                ),
            },
        ),
        ProviderPreset.LEGACY_BALANCED: StageProviderMapping(
            preset="legacy_balanced",
            default=ProviderConfig(LLMProvider.DEEPSEEK, model="deepseek-chat"),
            stages={
                "synthesis": ProviderConfig(
                    LLMProvider.OPENROUTER, model="openai/gpt-4o", temperature=0.6, max_tokens=2000
                ),
                "mp_rotation": ProviderConfig(
                    LLMProvider.MISTRAL,
                    model="mistral-large-latest",
                    temperature=0.7,
                    max_tokens=500,
                ),
                "validation": ProviderConfig(
                    LLMProvider.DEEPSEEK, model="deepseek-chat", temperature=0.3, max_tokens=300
                ),
            },
        ),
    }

    def __init__(self, mapping: StageProviderMapping | None = None) -> None:
        if mapping is None:
            mapping = self.PRESETS.get(ProviderPreset.C4REQBER, StageProviderMapping())
        self.mapping = mapping
        self._clients: dict[LLMProvider, BaseLLMClient] = {}
        self._stats: dict[str, dict[str, Any]] = {}
        self._client_lock = asyncio.Lock()
        self._batch_semaphore = asyncio.Semaphore(5)

    def _get_lock(self) -> asyncio.Lock:
        return self._client_lock

    @classmethod
    def from_preset(cls, preset: ProviderPreset) -> ProviderRouter:
        """From preset."""
        mapping = cls.PRESETS.get(preset, StageProviderMapping())
        return cls(mapping)

    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> ProviderRouter:
        """From dict."""
        if "preset" in config:
            try:
                preset = ProviderPreset(config["preset"])
                return cls.from_preset(preset)
            except ValueError:
                pass

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
        config = self.mapping.stages.get(stage_name, self.mapping.default)
        overridden = self._apply_model_assignment(stage_name, config)
        return overridden

    @staticmethod
    def _apply_model_assignment(stage_name: str, config: ProviderConfig) -> ProviderConfig:
        """Override PRESET model with ~/.c4reqber/models.json when set."""
        try:
            from src.llm.model_assignment import ModelAssignment, get_model_for_phase

            stage_to_phase = {
                "synthesis": "F",
                "dissertation": "F",
                "hypothesis": "D",
                "hypothesis_generation": "D",
                "gap_analysis": "C",
                "knowledge": "B",
                "framing": "A",
                "c4_framing": "A",
                "validation": "G",
                "quality": "G",
                "mp_rotation": "D",
            }
            phase = stage_to_phase.get((stage_name or "").lower(), "")
            if not phase:
                return config
            model = get_model_for_phase(phase)
            if not model:
                return config
            ma = ModelAssignment.load()
            provider_asg = ma.phases.get(phase)
            provider_str = (provider_asg.provider if provider_asg is not None else "") or ""
            if not provider_str:
                from src.llm.model_assignment import _detect_provider

                provider_str = _detect_provider(model)

            if ":" in model or provider_str in ("local", "ollama"):
                provider = LLMProvider.OLLAMA
            elif provider_str in ("lm_studio", "lmstudio"):
                provider = LLMProvider.LM_STUDIO
            elif provider_str == "deepseek":
                provider = LLMProvider.DEEPSEEK
            elif provider_str in ("xai", "mistral", "moonshot", "nvidia", "yandex"):
                try:
                    provider = LLMProvider(provider_str)
                except ValueError:
                    provider = LLMProvider.OPENROUTER
            else:
                # Bare free-tier / OpenRouter-style IDs (incl. nemotron-*-free)
                provider = LLMProvider.OPENROUTER

            return ProviderConfig(
                provider=provider,
                model=model,
                temperature=ma.get_temperature(phase) if phase else config.temperature,
                max_tokens=ma.get_max_tokens(phase) if phase else config.max_tokens,
                timeout=config.timeout,
            )
        except Exception:
            return config

    async def _get_client(self, provider: LLMProvider) -> BaseLLMClient:
        """Get or create client for a provider (thread-safe)."""

        async with self._get_lock():
            if provider not in self._clients:
                if provider == LLMProvider.OPENROUTER:
                    self._clients[provider] = OpenRouterClient()
                elif provider == LLMProvider.XAI:
                    self._clients[provider] = XAIClient()
                elif provider == LLMProvider.MISTRAL:
                    self._clients[provider] = MistralClient()
                elif provider == LLMProvider.MOONSHOT:
                    self._clients[provider] = MoonshotClient()
                elif provider == LLMProvider.DEEPSEEK:
                    self._clients[provider] = DeepSeekClient()
                elif provider == LLMProvider.OLLAMA:
                    self._clients[provider] = LocalLLMClient(LLMProvider.OLLAMA)
                elif provider == LLMProvider.LM_STUDIO:
                    self._clients[provider] = LocalLLMClient(LLMProvider.LM_STUDIO)
                elif provider == LLMProvider.AUTO:
                    raise ValueError("AUTO provider is not supported. Choose explicit provider.")
                else:
                    raise ValueError(f"Unknown provider: {provider}")
            return self._clients[provider]

    async def get_client_for_stage(self, stage_name: str) -> BaseLLMClient:
        """Get client for stage."""
        config = self.get_config_for_stage(stage_name)
        return await self._get_client(config.provider)

    async def generate(
        self,
        stage_name: str,
        prompt: str,
        system_prompt: str | None = None,
        use_retry: bool = True,
    ) -> Any:
        """Generate text for a specific pipeline stage."""
        if use_retry:
            from src.llm.retry_pkg.policies import ProviderRetryManager

            retry_mgr = ProviderRetryManager(self)
            result = await retry_mgr.execute_with_retry(stage_name, prompt, system_prompt)

            if stage_name not in self._stats:
                self._stats[stage_name] = {"calls": 0, "total_latency_ms": 0, "errors": 0}
            self._stats[stage_name]["calls"] += 1
            self._stats[stage_name]["total_latency_ms"] += result.total_latency_ms

            return result.response

        config = self.get_config_for_stage(stage_name)
        client = await self._get_client(config.provider)

        start = time.time()
        try:
            response = await client.generate(
                prompt=prompt,
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                system_prompt=system_prompt,
            )
            latency = (time.time() - start) * 1000

            if stage_name not in self._stats:
                self._stats[stage_name] = {"calls": 0, "total_latency_ms": 0, "errors": 0}
            self._stats[stage_name]["calls"] += 1
            self._stats[stage_name]["total_latency_ms"] += latency

            return response
        except (ConnectionError, TimeoutError, RuntimeError, ValueError):
            if stage_name not in self._stats:
                self._stats[stage_name] = {"calls": 0, "total_latency_ms": 0, "errors": 0}
            self._stats[stage_name]["errors"] += 1
            raise

    async def generate_batch(
        self,
        stage_name: str,
        prompts: list[str],
        system_prompt: str | None = None,
    ) -> list[Any]:
        """Generate batch."""
        config = self.get_config_for_stage(stage_name)
        client = await self._get_client(config.provider)

        async def gen(prompt: str) -> Any:
            async with self._batch_semaphore:
                try:
                    return await client.generate(  # type: ignore[return-value]
                        prompt=prompt,
                        model=config.model,
                        temperature=config.temperature,
                        max_tokens=config.max_tokens,
                        system_prompt=system_prompt,
                    )
                except (ConnectionError, TimeoutError, RuntimeError) as e:
                    raise RuntimeError(f"Batch generation failed: {e}") from e

        tasks = [gen(p) for p in prompts]
        return await asyncio.gather(*tasks)

    async def close_all(self) -> None:
        """Close all."""
        await asyncio.gather(
            *(client.close() for client in self._clients.values()),
            return_exceptions=True,
        )
        self._clients.clear()

    def get_stats(self) -> dict[str, Any]:
        """Get stats."""
        stats = {}
        for stage, data in self._stats.items():
            stats[stage] = {
                **data,
                "avg_latency_ms": data["total_latency_ms"] / max(data["calls"], 1),
            }
        return {
            "preset": self.mapping.preset,
            "mapping": {
                stage: {"provider": cfg.provider.value, "model": cfg.get_model()}
                for stage, cfg in self.mapping.stages.items()
            },
            "default_provider": self.mapping.default.provider.value,
            "default_model": self.mapping.default.get_model(),
            "stage_stats": stats,
        }

    def to_dict(self) -> dict[str, Any]:
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
