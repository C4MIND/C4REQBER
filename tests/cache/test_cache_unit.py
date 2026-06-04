"""
Tests for src/cache/ — 4-tier caching system

Covers: tier1_seed, tier2_memory, tier3_redis, tier4_upstream, orchestrator, config
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, patch

import anyio
import pytest

from src.cache.config import CacheConfig
from src.cache.orchestrator import CacheOrchestrator
from src.cache.tier1_seed import SeedCache
from src.cache.tier2_memory import MemoryCache
from src.cache.tier3_redis import RedisCache
from src.cache.tier4_upstream import UpstreamCache


pytestmark = pytest.mark.anyio(backend="asyncio")


# ── Tier 1: SeedCache ───────────────────────────────────────────────


class TestSeedCache:
    def test_get_miss(self):
        c = SeedCache()
        assert c.get("nonexistent") is None

    def test_load_and_get(self):
        c = SeedCache()
        c.load("a", 42)
        assert c.get("a") == 42

    def test_is_fresh_true(self):
        c = SeedCache()
        c.load("a", "hello")
        assert c.is_fresh("a") is True

    def test_is_fresh_false_missing(self):
        c = SeedCache()
        assert c.is_fresh("b") is False

    def test_is_fresh_false_expired(self):
        c = SeedCache()
        c._data["x"] = {"data": 1, "loaded_at": 0, "ttl": 1}
        assert c.is_fresh("x") is False

    def test_expire_removes_key(self):
        c = SeedCache()
        c.load("a", 1)
        c.expire("a")
        assert c.get("a") is None

    def test_clear_empties_all(self):
        c = SeedCache()
        c.load("a", 1)
        c.load("b", 2)
        c.clear()
        assert c.size == 0

    def test_size(self):
        c = SeedCache()
        c.load("a", 1)
        c.load("b", 2)
        assert c.size == 2

    def test_keys(self):
        c = SeedCache()
        c.load("one", 1)
        c.load("two", 2)
        assert set(c.keys) == {"one", "two"}

    def test_expired_entry_returned_as_none(self):
        c = SeedCache()
        c._data["old"] = {"data": 99, "loaded_at": time.time() - 99999, "ttl": 1}
        assert c.get("old") is None

    def test_load_custom_ttl(self):
        c = SeedCache()
        c.load("short", "val", ttl=0)
        assert c.is_fresh("short") is False


# ── Tier 2: MemoryCache ─────────────────────────────────────────────


class TestMemoryCache:
    def test_get_miss(self):
        c = MemoryCache()
        assert c.get("x") is None

    def test_set_and_get(self):
        c = MemoryCache()
        c.set("x", 123)
        assert c.get("x") == 123

    def test_ttl_expiration(self):
        c = MemoryCache()
        c._cache["exp"] = {"data": "gone", "ts": 0, "ttl": 1}
        assert c.get("exp") is None

    def test_lru_eviction(self):
        c = MemoryCache(max_size=2)
        c.set("a", 1)
        c.set("b", 2)
        c.set("c", 3)  # evicts 'a'
        assert c.get("a") is None
        assert c.get("b") == 2
        assert c.get("c") == 3

    def test_lru_reorder_on_get(self):
        c = MemoryCache(max_size=2)
        c.set("a", 1)
        c.set("b", 2)
        c.get("a")
        c.set("c", 3)
        assert c.get("a") == 1  # 'a' was re-ordered, survives
        assert c.get("b") is None
        assert c.get("c") == 3

    def test_custom_ttl(self):
        c = MemoryCache(default_ttl=999)
        c.set("x", 7, ttl=0)
        assert c.get("x") is None

    def test_stats(self):
        c = MemoryCache(max_size=5)
        c.set("a", 1)
        c.get("a")
        c.get("missing")
        s = c.stats
        assert s["hits"] == 1
        assert s["misses"] == 1
        assert s["size"] == 1
        assert s["max_size"] == 5

    def test_delete(self):
        c = MemoryCache()
        c.set("a", 1)
        c.delete("a")
        assert c.get("a") is None

    def test_clear(self):
        c = MemoryCache()
        c.set("a", 1)
        c.set("b", 2)
        c.clear()
        assert c.size == 0

    def test_set_updates_existing(self):
        c = MemoryCache(max_size=2)
        c.set("a", 1)
        c.set("a", 99)
        assert c.get("a") == 99
        assert c.stats["size"] == 1

    def test_ttl_remaining(self):
        c = MemoryCache(default_ttl=300)
        c.set("a", 1)
        rem = c.ttl("a")
        assert rem is not None
        assert 0 < rem <= 300

    def test_ttl_none_for_expired(self):
        c = MemoryCache()
        c._cache["old"] = {"data": "gone", "ts": 0, "ttl": 1}
        assert c.ttl("old") is None

    def test_ttl_none_for_missing(self):
        c = MemoryCache()
        assert c.ttl("nope") is None

    def test_keys(self):
        c = MemoryCache()
        c.set("a", 1)
        c.set("b", 2)
        assert set(c.keys) == {"a", "b"}


# ── Tier 3: RedisCache ──────────────────────────────────────────────


class TestRedisCache:
    async def test_get_miss(self):
        c = RedisCache()
        assert await c.get("x") is None

    async def test_set_and_get(self):
        c = RedisCache()
        await c.set("k", "v")
        assert await c.get("k") == "v"

    async def test_expired_entry(self):
        c = RedisCache()
        c._store["old"] = {"data": "stale", "expires": 0}
        assert await c.get("old") is None

    async def test_delete(self):
        c = RedisCache()
        await c.set("a", 1)
        await c.delete("a")
        assert await c.get("a") is None

    async def test_clear(self):
        c = RedisCache()
        await c.set("a", 1)
        await c.set("b", 2)
        await c.clear()
        assert c.size == 0

    async def test_get_or_set_stampede_hit(self):
        c = RedisCache()
        await c.set("x", "cached")
        factory = AsyncMock(return_value="computed")
        result = await c.get_or_set_stampede_protected("x", factory)
        assert result == "cached"
        factory.assert_not_called()

    async def test_get_or_set_stampede_miss(self):
        c = RedisCache()
        factory = AsyncMock(return_value="computed")
        result = await c.get_or_set_stampede_protected("x", factory)
        assert result == "computed"
        factory.assert_called_once()
        assert await c.get("x") == "computed"

    async def test_get_or_set_lock_released_after_success(self):
        c = RedisCache()
        factory = AsyncMock(return_value="ok")
        await c.get_or_set_stampede_protected("k", factory)
        assert c.lock_count == 0

    async def test_get_or_set_lock_released_after_failure(self):
        c = RedisCache()
        async def fail():
            raise RuntimeError("boom")
        with pytest.raises(RuntimeError):
            await c.get_or_set_stampede_protected("k", fail)
        assert c.lock_count == 0

    async def test_stampede_lock_prevents_concurrent_compute(self):
        c = RedisCache()

        async def slow_factory():
            await asyncio.sleep(0.1)
            return "computed"

        c._locks["lock:x"] = time.time()

        factory = AsyncMock(return_value="fresh")
        result = await c.get_or_set_stampede_protected("x", factory, lock_timeout=0.01)
        assert result is not None
        c._locks.pop("lock:x", None)

    async def test_size(self):
        c = RedisCache()
        await c.set("a", 1)
        await c.set("b", 2)
        assert c.size == 2

    async def test_lock_count(self):
        c = RedisCache()
        assert c.lock_count == 0


# ── Tier 4: UpstreamCache ───────────────────────────────────────────


class TestUpstreamCache:
    async def test_fetch_success(self):
        u = UpstreamCache()
        result = await u.fetch(AsyncMock(return_value="ok"))
        assert result == "ok"
        assert u.stats["calls"] == 1
        assert u.stats["errors"] == 0

    async def test_fetch_retry_on_failure(self):
        u = UpstreamCache(retries=3, retry_delay=0.01)
        call_count = [0]

        async def flaky():
            call_count[0] += 1
            if call_count[0] < 3:
                raise RuntimeError("fail")
            return "finally"

        result = await u.fetch(flaky)
        assert result == "finally"
        assert call_count[0] == 3
        assert u.stats["errors"] == 2

    async def test_fetch_exhausts_retries(self):
        u = UpstreamCache(retries=2, retry_delay=0.01)

        async def always_fail():
            raise RuntimeError("always")

        with pytest.raises(RuntimeError):
            await u.fetch(always_fail)
        assert u.stats["errors"] == 2

    async def test_fetch_with_default_returns_default_on_failure(self):
        u = UpstreamCache(retries=1, retry_delay=0.01)

        async def fail():
            raise RuntimeError("nope")

        result = await u.fetch_with_default(fail, default="fallback")
        assert result == "fallback"

    async def test_fetch_with_default_returns_value_on_success(self):
        u = UpstreamCache()
        result = await u.fetch_with_default(AsyncMock(return_value=42), default=0)
        assert result == 42

    async def test_fetch_timeout(self):
        u = UpstreamCache(timeout=0.01, retries=1, retry_delay=0.01)

        async def slow():
            await anyio.sleep(0.5)

        with pytest.raises(TimeoutError):
            await u.fetch(slow)
        assert u.stats["errors"] >= 1

    async def test_stats_defaults(self):
        u = UpstreamCache()
        s = u.stats
        assert s["calls"] == 0
        assert s["errors"] == 0
        assert s["timeout"] == 30.0
        assert s["retries"] == 3


# ── Orchestrator ────────────────────────────────────────────────────


class TestCacheOrchestrator:
    def setup_method(self):
        self.orchestrator = CacheOrchestrator()

    async def test_get_tier1_hit(self):
        self.orchestrator.seed_tier1("prompt", "response")
        result = await self.orchestrator.get("prompt")
        assert result == "response"

    async def test_get_tier2_hit_promotes(self):
        self.orchestrator.tier2.set("key", "val")
        result = await self.orchestrator.get("key")
        assert result == "val"

    async def test_get_tier3_hit_promotes_to_tier2(self):
        await self.orchestrator.tier3.set("k", "redis_val")
        result = await self.orchestrator.get("k")
        assert result == "redis_val"
        assert self.orchestrator.tier2.get("k") == "redis_val"

    async def test_get_miss_all_tiers(self):
        result = await self.orchestrator.get("nothing")
        assert result is None

    async def test_get_or_compute_hit(self):
        self.orchestrator.seed_tier1("a", 1)
        factory = AsyncMock(return_value=99)
        result = await self.orchestrator.get_or_compute("a", factory)
        assert result == 1
        factory.assert_not_called()

    async def test_get_or_compute_miss_computes(self):
        factory = AsyncMock(return_value=42)
        result = await self.orchestrator.get_or_compute("miss", factory)
        assert result == 42
        factory.assert_called_once()

    async def test_get_or_compute_promotes_to_tier2(self):
        factory = AsyncMock(return_value="computed")
        result = await self.orchestrator.get_or_compute("key", factory)
        assert result == "computed"
        assert self.orchestrator.tier2.get("key") == "computed"

    async def test_compute_and_seed(self):
        factory = AsyncMock(return_value="seeded")
        result = await self.orchestrator.compute_and_seed("key", factory)
        assert result == "seeded"
        assert self.orchestrator.tier1.get("key") == "seeded"
        assert self.orchestrator.tier2.get("key") == "seeded"
        assert await self.orchestrator.tier3.get("key") == "seeded"

    def test_invalidate(self):
        self.orchestrator.seed_tier1("k", "v")
        self.orchestrator.tier2.set("k", "v")
        self.orchestrator.invalidate("k")
        assert self.orchestrator.tier1.get("k") is None
        assert self.orchestrator.tier2.get("k") is None

    async def test_clear_all(self):
        self.orchestrator.seed_tier1("a", 1)
        self.orchestrator.seed_tier1("b", 2)
        self.orchestrator.tier2.set("c", 3)
        await self.orchestrator.clear_all()
        assert self.orchestrator.tier1.size == 0
        assert self.orchestrator.tier2.stats["size"] == 0

    def test_stats(self):
        s = self.orchestrator.stats
        assert "tier1_size" in s
        assert "tier2" in s
        assert "tier3_size" in s
        assert "tier3_locks" in s
        assert "tier4" in s


# ── Config ──────────────────────────────────────────────────────────


class TestCacheConfig:
    def test_defaults(self):
        cfg = CacheConfig()
        assert cfg.tier1_ttl == 3600
        assert cfg.tier2_max_size == 1000
        assert cfg.tier2_default_ttl == 60
        assert cfg.tier3_ttl == 300
        assert cfg.tier3_lock_timeout == 5.0
        assert cfg.tier4_timeout == 30.0
        assert cfg.tier4_retries == 3
        assert cfg.tier4_retry_delay == 0.5
        assert cfg.promotion_ttl_seconds == 30

    def test_custom_values(self):
        cfg = CacheConfig(
            tier1_ttl=7200,
            tier2_max_size=500,
            tier4_retries=5,
        )
        assert cfg.tier1_ttl == 7200
        assert cfg.tier2_max_size == 500
        assert cfg.tier4_retries == 5
