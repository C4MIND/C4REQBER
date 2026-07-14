"""
C4REQBER API: Cache Layer
Redis (optional) with in-memory fallback
"""

from __future__ import annotations

import json
import os
import time
from typing import Any


# Optional Redis support
try:
    import redis.asyncio as redis

    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    redis = None  # type: ignore


class MemoryCache:
    """In-memory cache with TTL support."""

    def __init__(self) -> None:
        self._data: dict[str, tuple[Any, float]] = {}
        self._hits = 0
        self._misses = 0

    async def get(self, key: str) -> Any | None:
        """Get."""
        now = time.time()
        if key in self._data:
            value, expiry = self._data[key]
            if expiry > now:
                self._hits += 1
                return value
            del self._data[key]
        self._misses += 1
        return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        self._data[key] = (value, time.time() + ttl)

    async def delete(self, key: str) -> None:
        self._data.pop(key, None)

    async def ping(self) -> bool:
        return True

    def get_hit_rate(self) -> float:
        """Get hit rate."""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0


class RedisCache:
    """Redis cache manager."""

    def __init__(self) -> None:
        self.client: redis.Redis | None = None
        self._hits = 0
        self._misses = 0

    async def connect(self) -> None:
        """Connect."""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.client = redis.from_url(  # type: ignore[no-untyped-call]
            redis_url, decode_responses=True)

    async def disconnect(self) -> None:
        if self.client:
            await self.client.close()

    async def ping(self) -> bool:
        """Ping."""
        if not self.client:
            return False
        try:
            await self.client.ping()  # type: ignore[misc]
            return True
        except (OSError, ConnectionError, TimeoutError):
            return False

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
            await self.client.setex(key, ttl, json.dumps(value))
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

    async def get_hit_rate(self) -> float:
        """Get hit rate."""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0


class CacheManager:
    """Unified cache: Redis if available, otherwise in-memory."""

    def __init__(self) -> None:
        self._backend: MemoryCache | RedisCache | None = None
        self._use_redis = os.getenv("CACHE_BACKEND", "memory").lower() == "redis"

    async def connect(self) -> None:
        """Connect."""
        if self._use_redis and HAS_REDIS:
            try:
                redis_cache = RedisCache()
                await redis_cache.connect()
                if await redis_cache.ping():
                    self._backend = redis_cache
                    return
            except (OSError, ConnectionError, TimeoutError):
                pass
        # Fallback to memory
        self._backend = MemoryCache()

    async def disconnect(self) -> None:
        if isinstance(self._backend, RedisCache):
            await self._backend.disconnect()

    async def ping(self) -> bool:
        """Ping."""
        if not self._backend:
            return False
        return await self._backend.ping()

    async def get(self, key: str) -> Any | None:
        """Get."""
        if not self._backend:
            return None
        return await self._backend.get(key)

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set."""
        if not self._backend:
            return
        await self._backend.set(key, value, ttl)

    async def delete(self, key: str) -> None:
        """Delete."""
        if not self._backend:
            return
        await self._backend.delete(key)

    async def get_hit_rate(self) -> float:
        """Get hit rate."""
        if not self._backend:
            return 0.0
        return self._backend.get_hit_rate()  # type: ignore[return-value]
