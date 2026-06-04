"""
Multi-tier cache orchestrator

Implements read-through with promotion:
  Tier 1 → Tier 2 → Tier 3 → Tier 4 (compute)

On a Tier-N hit, the value is promoted into the faster tiers
above it for future reads.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from src.cache.config import CacheConfig
from src.cache.tier1_seed import SeedCache
from src.cache.tier2_memory import MemoryCache
from src.cache.tier3_redis import RedisCache
from src.cache.tier4_upstream import UpstreamCache


class CacheOrchestrator:
    """CacheOrchestrator."""
    def __init__(self, config: CacheConfig | None = None) -> None:
        cfg = config or CacheConfig()
        self.tier1 = SeedCache()
        self.tier2 = MemoryCache(
            max_size=cfg.tier2_max_size,
            default_ttl=cfg.tier2_default_ttl,
        )
        self.tier3 = RedisCache(redis_url=cfg.redis_url)
        self.tier4 = UpstreamCache(
            timeout=cfg.tier4_timeout,
            retries=cfg.tier4_retries,
            retry_delay=cfg.tier4_retry_delay,
        )
        self._cfg = cfg

    async def get(self, key: str) -> Any | None:
        """Get."""
        result = self.tier1.get(key)
        if result is not None:
            return result

        result = self.tier2.get(key)
        if result is not None:
            return result

        result = await self.tier3.get(key)
        if result is not None:
            self.tier2.set(key, result, ttl=self._cfg.promotion_ttl_seconds)
            return result

        return None

    async def get_or_compute(
        self,
        key: str,
        factory: Callable[[], Awaitable[Any]],
        ttl: int = 300,
    ) -> Any:
        """Get or compute."""
        result = await self.get(key)
        if result is not None:
            return result

        result = await self.tier3.get_or_set_stampede_protected(
            key,
            factory,
            ttl=ttl,
            lock_timeout=self._cfg.tier3_lock_timeout,
        )
        self.tier2.set(key, result, ttl=self._cfg.promotion_ttl_seconds)
        return result

    async def compute_and_seed(
        self,
        key: str,
        factory: Callable[[], Awaitable[Any]],
        seed_ttl: int = 3600,
        tier3_ttl: int = 300,
    ) -> Any:
        """Compute via tier4, then populate tiers 3→1."""
        result = await self.tier4.fetch(factory)
        await self.tier3.set(key, result, ttl=tier3_ttl)
        self.tier2.set(key, result, ttl=self._cfg.promotion_ttl_seconds)
        self.tier1.load(key, result, ttl=seed_ttl)
        return result

    def seed_tier1(self, key: str, data: Any, ttl: int = 3600) -> None:
        self.tier1.load(key, data, ttl=ttl)

    def invalidate(self, key: str) -> None:
        """Invalidate."""
        self.tier1.expire(key)
        self.tier2.delete(key)

    async def clear_all(self) -> None:
        """Clear all."""
        self.tier1.clear()
        self.tier2.clear()
        await self.tier3.clear()

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "tier1_size": self.tier1.size,
            "tier2": self.tier2.stats,
            "tier3_size": self.tier3.size,
            "tier3_locks": self.tier3.lock_count,
            "tier4": self.tier4.stats,
        }
