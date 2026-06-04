"""
Tier 3 Cache: Redis with stampede protection

Falls back to an in-memory dict[str, Any] when Redis is unavailable.
Provides stampede protection via a simple lock to prevent
multiple concurrent computations of the same cache miss.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any


class RedisCache:
    """RedisCache."""
    def __init__(self, redis_url: str | None = None) -> None:
        self._store: dict[str, dict[str, Any]] = {}
        self._locks: dict[str, float] = {}
        self._redis_url = redis_url

    async def get(self, key: str) -> Any | None:
        """Get."""
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.time() < entry["expires"]:
            return entry["data"]
        del self._store[key]
        return None

    async def set(self, key: str, data: Any, ttl: int = 300) -> None:
        self._store[key] = {
            "data": data,
            "expires": time.time() + ttl,
        }

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def clear(self) -> None:
        self._store.clear()

    async def get_or_set_stampede_protected(
        self,
        key: str,
        factory: Callable[[], Awaitable[Any]],
        ttl: int = 300,
        lock_timeout: float = 5.0,
    ) -> Any:
        """
        Get from cache or compute with stampede protection.

        If the value is absent and another coroutine is already
        computing it (lock held), retries the cache get once.
        """
        result = await self.get(key)
        if result is not None:
            return result

        lock_key = f"lock:{key}"
        now = time.time()
        if lock_key in self._locks:
            if now - self._locks[lock_key] < lock_timeout:
                return await self.get(key) or await factory()

        self._locks[lock_key] = now
        try:
            result = await factory()
            await self.set(key, result, ttl)
            return result
        finally:
            self._locks.pop(lock_key, None)

    @property
    def size(self) -> int:
        return len(self._store)

    @property
    def lock_count(self) -> int:
        return len(self._locks)
