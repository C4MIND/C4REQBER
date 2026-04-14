"""
TURBO-CDI API: Redis Cache
LLM response caching
"""

import os
import json
from typing import Optional, Any
import redis.asyncio as redis


class CacheManager:
    """Redis cache manager."""

    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self._hits = 0
        self._misses = 0

    async def connect(self):
        """Connect to Redis."""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.client = redis.from_url(redis_url, decode_responses=True)

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.client:
            await self.client.close()

    async def ping(self) -> bool:
        """Check Redis connectivity."""
        try:
            await self.client.ping()
            return True
        except (redis.RedisError, ConnectionError, OSError) as e:
            return False

    async def get(self, key: str) -> Optional[Any]:
        """Get cached value."""
        try:
            value = await self.client.get(key)
            if value:
                self._hits += 1
                return json.loads(value)
            self._misses += 1
            return None
        except (redis.RedisError, json.JSONDecodeError, ConnectionError) as e:
            self._misses += 1
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set cached value with TTL."""
        try:
            await self.client.setex(key, ttl, json.dumps(value))
        except (redis.RedisError, ConnectionError, TypeError) as e:
            # Silently fail - cache is best-effort
            pass

    async def delete(self, key: str):
        """Delete cached value."""
        try:
            await self.client.delete(key)
        except (redis.RedisError, ConnectionError) as e:
            # Silently fail - cache is best-effort
            pass

    async def get_hit_rate(self) -> float:
        """Get cache hit rate."""
        total = self._hits + self._misses
        if total == 0:
            return 0.0
        return self._hits / total
