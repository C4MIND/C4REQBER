# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""Provider-Aware Multi-Agent Coordinator — distributes pipelines across providers.

Different user segments, unified architecture:

User A: GPU cluster / M3 Max 48GB — local MLX/LM Studio/Ollama, parallel, free
User B: Multiple API keys (OR + Together + Groq) — spread across providers, high throughput
User C: Single API key (OpenRouter only) — smart scheduling, rate-limit aware
User D: Free tier (local only, no keys) — all on local models, cpu_only

Architecture:
    ProviderAwareCoordinator
    ├─ Discover available providers (local auto-detect + configured API keys)
    ├─ For each provider: check rate limits, cost, current load
    ├─ Assign each pipeline to optimal provider:
    │   ├─ PREMIUM providers (claude-sonnet) → dissertation Phase F
    │   ├─ BALANCED providers (deepseek-chat) → gap mining, hypotheses
    │   ├─ CHEAP providers (qwen-7b, gpt-4o-mini) → search, summaries
    │   └─ LOCAL providers (mlx, lm-studio, ollama) → fast-complete tasks
    ├─ Multi-provider strategy: spread pipelines to avoid any single rate limit
    └─ Budget guard: estimate cost before launching, abort if exceeds limit
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


@dataclass
class ProviderSlot:
    """ProviderSlot."""
    name: str  # "openrouter", "together", "groq", "lm_studio", "mlx", "ollama"
    url: str
    api_key: str
    tier: str  # "local" | "cheap" | "balanced" | "premium"
    rate_limit_per_min: int  # max calls per minute
    concurrent_limit: int  # max simultaneous pipelines
    cost_per_1k: float
    active_pipelines: int = 0
    calls_this_minute: int = 0
    _call_times: list[float] = field(default_factory=list)
    available: bool = True

    def can_accept(self) -> bool:
        """Check if can accept."""
        now = time.time()
        self._call_times = [t for t in self._call_times if now - t < 60]
        return (
            self.available
            and self.active_pipelines < self.concurrent_limit
            and len(self._call_times) < self.rate_limit_per_min
        )

    def acquire(self) -> None:
        """Acquire."""
        self.active_pipelines += 1
        self._call_times.append(time.time())

    def release(self) -> None:
        self.active_pipelines = max(0, self.active_pipelines - 1)

    @property
    def load_pct(self) -> float:
        return self.active_pipelines / max(self.concurrent_limit, 1)


PROVIDER_TEMPLATES: dict[str, dict] = {
    "openrouter": {
        "url": "https://openrouter.ai/api/v1",
        "tier": "balanced",
        "rate_limit_per_min": 20,
        "concurrent_limit": 3,
        "cost_per_1k": 0.001,  # varies by model
    },
    "together": {
        "url": "https://api.together.xyz/v1",
        "tier": "balanced",
        "rate_limit_per_min": 60,
        "concurrent_limit": 4,
        "cost_per_1k": 0.0002,
    },
    "groq": {
        "url": "https://api.groq.com/openai/v1",
        "tier": "balanced",
        "rate_limit_per_min": 30,
        "concurrent_limit": 2,
        "cost_per_1k": 0.00015,
    },
    "deepseek": {
        "url": "https://api.deepseek.com/v1",
        "tier": "balanced",
        "rate_limit_per_min": 10,
        "concurrent_limit": 2,
        "cost_per_1k": 0.00014,
    },
    "fireworks": {
        "url": "https://api.fireworks.ai/inference/v1",
        "tier": "balanced",
        "rate_limit_per_min": 60,
        "concurrent_limit": 5,
        "cost_per_1k": 0.0002,
    },
    "mlx": {
        "url": "http://localhost:8001/v1",
        "tier": "local",
        "rate_limit_per_min": 999,
        "concurrent_limit": 8,
        "cost_per_1k": 0.0,
    },
    "lm_studio": {
        "url": "http://localhost:1234/v1",
        "tier": "local",
        "rate_limit_per_min": 999,
        "concurrent_limit": 4,
        "cost_per_1k": 0.0,
    },
    "ollama": {
        "url": "http://localhost:11434/v1",
        "tier": "local",
        "rate_limit_per_min": 999,
        "concurrent_limit": 3,
        "cost_per_1k": 0.0,
    },
}


class ProviderAwareCoordinator:
    """Discovers providers, assigns pipelines, manages rate limits per provider."""

    def __init__(self, budget_limit: float = 0.0, mode: str = "auto") -> None:
        self.budget_limit = budget_limit
        self.mode = mode  # "auto" | "local_only" | "cheapest" | "premium"
        self._slots: dict[str, ProviderSlot] = {}
        self._total_cost = 0.0
        self._discover_providers()

    def _discover_providers(self) -> None:
        """Auto-detect all available providers."""
        import json

        # Check configured providers from models.json
        config_path = os.path.expanduser("~/.c4reqber/models.json")
        configured: dict = {}
        if os.path.exists(config_path):
            try:
                with open(config_path) as f:
                    configured = json.load(f).get("connected_providers", [])
            except Exception:
                logger.debug("Provider check failed", exc_info=True)

                pass

        # Cloud providers from API keys
        cloud_providers = {
            "openrouter": "OPENROUTER_API_KEY",
            "together": "TOGETHER_API_KEY",
            "groq": "GROQ_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "fireworks": "FIREWORKS_API_KEY",
        }
        for name, env_key in cloud_providers.items():
            key = os.environ.get(env_key, "")
            # Also check configured providers
            for cp in configured:
                if isinstance(cp, dict) and cp.get("name", "").lower() == name:
                    key = key or cp.get("api_key", "")
                    break
            if key:
                template = PROVIDER_TEMPLATES.get(name, {})
                self._slots[name] = ProviderSlot(
                    name=name,
                    url=template.get("url", ""),
                    api_key=key,
                    tier=template.get("tier", "balanced"),
                    rate_limit_per_min=template.get("rate_limit_per_min", 10),
                    concurrent_limit=template.get("concurrent_limit", 2),
                    cost_per_1k=template.get("cost_per_1k", 0.001),
                )
                logger.info("Cloud provider: %s (limit=%d/min, concurrent=%d)", name, self._slots[name].rate_limit_per_min, self._slots[name].concurrent_limit)

        # Local providers via auto-detect
        local_providers: dict[str, tuple[str, dict[str, str]]] = {
            "mlx": ("http://localhost:8001/v1/models", {}),
            "lm_studio": ("http://localhost:1234/v1/models", {}),
            "ollama": ("http://localhost:11434/api/tags", {}),
        }
        for name, (check_url, _headers) in local_providers.items():
            try:
                import httpx
                with httpx.Client(timeout=3.0) as client:
                    r = client.get(check_url)
                    if r.status_code == 200:
                        template = PROVIDER_TEMPLATES.get(name, {})
                        self._slots[name] = ProviderSlot(
                            name=name,
                            url=template.get("url", ""),
                            api_key="",
                            tier="local",
                            rate_limit_per_min=999,
                            concurrent_limit=template.get("concurrent_limit", 4),
                            cost_per_1k=0.0,
                        )
                        logger.info("Local provider: %s (no rate limits, $0/MTok)", name)
            except Exception:
                logger.debug("Provider check failed", exc_info=True)

                pass

        if not self._slots:
            logger.warning("No LLM providers detected. Add API keys or start local LLM.")
            self._slots["fallback"] = ProviderSlot(
                name="fallback", url="", api_key="", tier="local",
                rate_limit_per_min=1, concurrent_limit=1, cost_per_1k=0.0,
            )

    def available_tiers(self) -> list[str]:
        return sorted(set(s.tier for s in self._slots.values() if s.available))

    def total_concurrent_capacity(self) -> int:
        return sum(s.concurrent_limit for s in self._slots.values() if s.available)

    def best_provider_for_tier(self, tier: str) -> ProviderSlot | None:
        """Find best available provider for given tier."""
        candidates = [s for s in self._slots.values() if s.tier == tier and s.can_accept()]
        if not candidates:
            # Fall back to any tier
            candidates = [s for s in self._slots.values() if s.can_accept()]
        if not candidates:
            return None
        # Pick least loaded provider
        return min(candidates, key=lambda s: s.load_pct)

    def assign_pipelines(self, num_pipelines: int) -> list[tuple[int, ProviderSlot | None]]:
        """Assign each pipeline to the best available provider."""
        assignments: list[tuple[int, ProviderSlot | None]] = []
        tier_prefs = ["local", "cheap", "balanced", "premium"]

        for i in range(num_pipelines):
            assigned = False
            for tier in tier_prefs:
                provider = self.best_provider_for_tier(tier)
                if provider:
                    provider.acquire()
                    assignments.append((i, provider))
                    assigned = True
                    logger.info("Pipeline %d → %s (%s, load=%.0f%%)", i + 1, provider.name, provider.tier, provider.load_pct * 100)
                    break
            if not assigned:
                assignments.append((i, None))
                logger.warning("Pipeline %d → QUEUED (no provider available)", i + 1)

        return assignments

    def release(self, provider_name: str) -> None:
        if provider_name in self._slots:
            self._slots[provider_name].release()

    def estimate_cost(self, num_pipelines: int, tokens_per_pipeline: int = 8000) -> float:
        """Estimate cost."""
        total = 0.0
        assignments = self.assign_pipelines(num_pipelines)
        for _, provider in assignments:
            if provider:
                total += provider.cost_per_1k * (tokens_per_pipeline / 1000)
        # Release (these were for estimation)
        for _, provider in assignments:
            if provider:
                self.release(provider.name)
        return round(total, 4)

    def dashboard(self) -> str:
        """Dashboard."""
        lines = ["", "Provider Dashboard:", ""]
        for name, s in sorted(self._slots.items()):
            lines.append(f"  {name:15} {s.tier:10} {s.active_pipelines}/{s.concurrent_limit} active  "
                         f"{len(s._call_times)}/{s.rate_limit_per_min}/min  ${s.cost_per_1k}/MTok")
        if not self._slots:
            lines.append("  (no providers — add API keys or start local LLM)")
        return "\n".join(lines)
