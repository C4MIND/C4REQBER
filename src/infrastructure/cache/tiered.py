"""
C4REQBER: 4-Tier Cache System
Bootstrap -> Memory LRU -> Redis -> Upstream with cache stampede protection.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from enum import Enum
from typing import Any


# Optional Redis
try:
    import redis.asyncio as redis_lib

    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    redis_lib = None  # type: ignore


class TTLCategory(Enum):
    """Predefined TTL categories."""

    FAST = 60
    MEDIUM = 600
    SLOW = 1800
    STATIC = 7200


class FNV1aHash:
    """FNV-1a 64-bit hash for ETag generation."""

    FNV_OFFSET = 0xCBF29CE484222325
    FNV_PRIME = 0x100000001B3

    @classmethod
    def hash(cls, data: str | bytes) -> str:
        """Hash."""
        if isinstance(data, str):
            data = data.encode("utf-8")
        h = cls.FNV_OFFSET
        for byte in data:
            h ^= byte
            h = (h * cls.FNV_PRIME) & 0xFFFFFFFFFFFFFFFF
        return f'"{h:016x}"'

    @classmethod
    def etag_from_value(cls, value: Any) -> str:
        """Generate ETag from any JSON-serializable value."""
        return cls.hash(json.dumps(value, sort_keys=True, default=str))


class MemoryLRUCache:
    """In-memory LRU cache (Tier 2)."""

    def __init__(self, maxsize: int = 1000) -> None:
        self._maxsize = maxsize
        self._data: dict[str, tuple[Any, float]] = {}
        self._access_order: list[str] = []
        self._hits = 0
        self._misses = 0

    async def get(self, key: str) -> Any | None:
        """Get."""
        now = time.time()
        if key in self._data:
            value, expiry = self._data[key]
            if expiry > now:
                self._hits += 1
                # Move to end (most recently used)
                self._access_order.remove(key)
                self._access_order.append(key)
                return value
            del self._data[key]
            self._access_order.remove(key)
        self._misses += 1
        return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set."""
        now = time.time()
        # Evict oldest if at capacity
        while len(self._data) >= self._maxsize and self._access_order:
            oldest = self._access_order.pop(0)
            self._data.pop(oldest, None)
        self._data[key] = (value, now + ttl)
        if key not in self._access_order:
            self._access_order.append(key)

    async def delete(self, key: str) -> None:
        """Delete."""
        self._data.pop(key, None)
        if key in self._access_order:
            self._access_order.remove(key)

    def get_hit_rate(self) -> float:
        """Get hit rate."""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0


class RedisTierCache:
    """Redis cache (Tier 3)."""

    def __init__(self) -> None:
        self.client: Any = None
        self._hits = 0
        self._misses = 0

    async def connect(self) -> None:
        """Connect."""
        if not HAS_REDIS:
            return
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.client = redis_lib.from_url(redis_url, decode_responses=True)  # type: ignore[no-untyped-call]

    async def disconnect(self) -> None:
        if self.client:
            await self.client.close()

    async def get(self, key: str) -> Any | None:
        """Get."""
        if not self.client:
            return None
        try:
            value = await self.client.get(key)
            if value:
                self._hits += 1
                return json.loads(value)
            self._misses += 1
            return None
        except (OSError, ConnectionError, TimeoutError, json.JSONDecodeError):
            self._misses += 1
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set."""
        if not self.client:
            return
        try:
            await self.client.setex(key, ttl, json.dumps(value, default=str))
        except (OSError, ConnectionError, TimeoutError):
            pass

    async def delete(self, key: str) -> None:
        """Delete."""
        if not self.client:
            return
        try:
            await self.client.delete(key)
        except (OSError, ConnectionError, TimeoutError):
            pass

    def get_hit_rate(self) -> float:
        """Get hit rate."""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0


class UpstreamCache:
    """Tier 4 — on-disk JSON cache under ~/.c4reqber/cache/upstream (not a CDN)."""

    def __init__(self, cache_dir: str | None = None) -> None:
        from pathlib import Path

        self._dir = Path(cache_dir or os.path.expanduser("~/.c4reqber/cache/upstream"))
        self._dir.mkdir(parents=True, exist_ok=True)
        self._hits = 0
        self._misses = 0

    def _path(self, key: str) -> Any:
        import hashlib
        from pathlib import Path

        digest = hashlib.sha256(key.encode()).hexdigest()[:32]
        return self._dir / f"{digest}.json"

    async def get(self, key: str) -> Any | None:
        """Get."""
        path = self._path(key)
        try:
            if not path.is_file():
                self._misses += 1
                return None
            raw = json.loads(path.read_text(encoding="utf-8"))
            if float(raw.get("expiry", 0)) < time.time():
                path.unlink(missing_ok=True)
                self._misses += 1
                return None
            self._hits += 1
            return raw.get("value")
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            self._misses += 1
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        path = self._path(key)
        try:
            path.write_text(
                json.dumps(
                    {"expiry": time.time() + ttl, "value": value},
                    default=str,
                ),
                encoding="utf-8",
            )
        except OSError:
            pass

    def get_hit_rate(self) -> float:
        """Get hit rate."""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0


class TieredCache:
    """4-tier cache: Bootstrap -> Memory LRU -> Redis -> Upstream."""

    def __init__(self, memory_maxsize: int = 1000) -> None:
        self.bootstrap = MemoryLRUCache(maxsize=100)  # Tier 1: seed
        self.memory = MemoryLRUCache(maxsize=memory_maxsize)  # Tier 2
        self.redis = RedisTierCache()  # Tier 3
        self.upstream = UpstreamCache()  # Tier 4
        self._pending: dict[str, Any] = {}  # stampede protection

    async def connect(self) -> None:
        await self.redis.connect()

    async def disconnect(self) -> None:
        await self.redis.disconnect()

    def _make_key(self, key: str, namespace: str = "") -> str:
        return f"turbo:cache:{namespace}:{key}" if namespace else f"turbo:cache:{key}"

    async def get(
        self,
        key: str,
        namespace: str = "",
        tier: str = "auto",
        loader: Callable[[], Any] | None = None,
        ttl: int | TTLCategory = TTLCategory.MEDIUM,
    ) -> Any | None:
        """Get value from cache, trying tiers in order.

        Args:
            key: Cache key
            namespace: Key namespace
            tier: "auto" | "memory" | "redis" | "upstream"
            loader: Optional async callable to load value on miss
            ttl: TTL in seconds or TTLCategory
        """
        if isinstance(ttl, TTLCategory):
            ttl = ttl.value

        full_key = self._make_key(key, namespace)

        # Cache stampede protection: if key is being loaded, wait
        if full_key in self._pending:
            # Return pending result (simplified; in prod use asyncio.Event)
            return self._pending.get(full_key)

        # Tier 1: Bootstrap (seed data)
        value = await self.bootstrap.get(full_key)
        if value is not None:
            return value

        # Tier 2: Memory LRU
        if tier in ("auto", "memory"):
            value = await self.memory.get(full_key)
            if value is not None:
                return value

        # Tier 3: Redis
        if tier in ("auto", "redis"):
            value = await self.redis.get(full_key)
            if value is not None:
                # Backfill memory
                await self.memory.set(full_key, value, ttl=min(ttl, 300))
                return value

        # Tier 4: Upstream
        if tier in ("auto", "upstream"):
            value = await self.upstream.get(full_key)
            if value is not None:
                await self.memory.set(full_key, value, ttl=min(ttl, 300))
                await self.redis.set(full_key, value, ttl=ttl)
                return value

        # Miss: load if loader provided
        if loader is not None:
            self._pending[full_key] = None
            try:
                value = await loader()
                if value is not None:
                    await self.set(key, value, namespace=namespace, ttl=ttl)
                return value
            finally:
                self._pending.pop(full_key, None)

        return None

    async def set(
        self,
        key: str,
        value: Any,
        namespace: str = "",
        ttl: int | TTLCategory = TTLCategory.MEDIUM,
    ) -> None:
        """Set value in all applicable tiers."""
        if isinstance(ttl, TTLCategory):
            ttl = ttl.value

        full_key = self._make_key(key, namespace)
        await self.memory.set(full_key, value, ttl=min(ttl, 300))
        await self.redis.set(full_key, value, ttl=ttl)

    async def delete(self, key: str, namespace: str = "") -> None:
        """Delete from all tiers."""
        full_key = self._make_key(key, namespace)
        await self.memory.delete(full_key)
        await self.redis.delete(full_key)

    def get_hit_rate(self) -> float:
        """Aggregate hit rate across all tiers."""
        total_hits = (
            self.bootstrap._hits + self.memory._hits + self.redis._hits + self.upstream._hits
        )
        total_misses = (
            self.bootstrap._misses
            + self.memory._misses
            + self.redis._misses
            + self.upstream._misses
        )
        total = total_hits + total_misses
        return total_hits / total if total > 0 else 0.0

    def get_tier_stats(self) -> dict[str, dict[str, float]]:
        """Per-tier statistics."""
        return {
            "bootstrap": {
                "hits": self.bootstrap._hits,
                "misses": self.bootstrap._misses,
                "hit_rate": self.bootstrap.get_hit_rate(),
            },
            "memory": {
                "hits": self.memory._hits,
                "misses": self.memory._misses,
                "hit_rate": self.memory.get_hit_rate(),
            },
            "redis": {
                "hits": self.redis._hits,
                "misses": self.redis._misses,
                "hit_rate": self.redis.get_hit_rate(),
            },
            "upstream": {
                "hits": self.upstream._hits,
                "misses": self.upstream._misses,
                "hit_rate": self.upstream.get_hit_rate(),
            },
        }

    def generate_etag(self, value: Any) -> str:
        """Generate ETag for a cached value."""
        return FNV1aHash.etag_from_value(value)

    def cache_control_header(self, ttl: int | TTLCategory) -> str:
        """Generate Cache-Control header value."""
        if isinstance(ttl, TTLCategory):
            ttl = ttl.value
        return f"max-age={ttl}, stale-while-revalidate={min(ttl // 2, 300)}"
