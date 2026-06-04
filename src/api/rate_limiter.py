"""
C4REQBER API: Rate Limiter
API protection with Redis-backed sliding window + WebSocket rate limiter.
"""
from __future__ import annotations

import asyncio
import os
import threading
import time
from collections import defaultdict
from typing import Any


try:
    import redis.asyncio as redis
    _REDIS_AVAILABLE = True
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    _REDIS_AVAILABLE = False


class RateLimiter:
    """Redis-backed sliding window rate limiter with in-memory fallback."""

    def __init__(self, redis_url: str | None = None) -> None:
        # requests per hour
        self.limits = {"free": 100, "basic": 1000, "pro": 10000, "enterprise": 100000}

        # In-memory fallback storage
        self.requests: dict[str, list] = defaultdict(list)  # type: ignore[type-arg]
        self.hourly_counts: dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()

        # Redis backend
        self._redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self._redis: Any = None
        self._use_redis = os.getenv("RATE_LIMIT_BACKEND", "memory").lower() == "redis"

    async def _get_redis(self) -> Any:
        """Lazy-connect to Redis."""
        if self._redis is not None:
            return self._redis
        if not self._use_redis or not _REDIS_AVAILABLE:
            return None
        try:
            url = self._redis_url or "redis://localhost:6379"
            self._redis = redis.from_url(  # type: ignore[no-untyped-call]
                url, decode_responses=True
            )
            await self._redis.ping()
            return self._redis
        except (ValueError, TypeError):
            self._redis = None
            return None

    async def check_limit(
        self,
        user_id: str,
        tier: str = "free",
        window_seconds: int = 3600,
    ) -> bool:
        """Check if user is within rate limit using Redis-backed sliding window."""
        r = await self._get_redis()
        if r:
            return await self._check_limit_redis(user_id, tier, window_seconds)
        return await self._check_limit_memory(user_id, tier, window_seconds)

    async def _check_limit_redis(
        self, user_id: str, tier: str, window_seconds: int
    ) -> bool:
        now = time.time()
        key = f"rate_limit:{user_id}"
        limit = self.limits.get(tier, 100)
        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(key, 0, now - window_seconds)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window_seconds)
        results = await pipe.execute()
        count = results[1]
        return count < limit  # type: ignore[no-any-return]

    async def _check_limit_memory(
        self, user_id: str, tier: str, window_seconds: int
    ) -> bool:
        now = time.time()
        with self._lock:
            # Clean old requests and drop empty lists to prevent unbounded growth
            filtered = [
                req_time
                for req_time in self.requests[user_id]
                if now - req_time < window_seconds
            ]
            if filtered:
                self.requests[user_id] = filtered
            else:
                self.requests.pop(user_id, None)
                self.hourly_counts.pop(user_id, None)

            # Check limit
            limit = self.limits.get(tier, 100)
            if len(self.requests.get(user_id, [])) >= limit:
                return False

            # Record request
            self.requests[user_id].append(now)
            self.hourly_counts[user_id] = self.hourly_counts.get(user_id, 0) + 1

            return True

    async def get_remaining(
        self, user_id: str, tier: str = "free", window_seconds: int = 3600
    ) -> int:
        """Get remaining requests in current window."""
        r = await self._get_redis()
        limit = self.limits.get(tier, 100)
        if r:
            now = time.time()
            key = f"rate_limit:{user_id}"
            await r.zremrangebyscore(key, 0, now - window_seconds)
            count = await r.zcard(key)
            return max(0, limit - count)  # type: ignore[no-any-return]
        with self._lock:
            now = time.time()
            filtered = [
                req_time
                for req_time in self.requests.get(user_id, [])
                if now - req_time < window_seconds
            ]
            return max(0, limit - len(filtered))

    async def get_request_count(self, hours: int = 24) -> int:
        """Get total request count."""
        with self._lock:
            return sum(self.hourly_counts.values())

    def cleanup(self) -> None:
        """Remove stale entries to prevent unbounded memory growth."""
        now = time.time()
        window = 3600 * 24  # 24 hours
        with self._lock:
            stale_users = [
                uid
                for uid, timestamps in self.requests.items()
                if not timestamps or now - timestamps[-1] > window
            ]
            for uid in stale_users:
                self.requests.pop(uid, None)
                self.hourly_counts.pop(uid, None)


class WebSocketRateLimiter:
    """Sliding-window rate limiter for WebSocket messages.

    Supports in-memory (dict) and optional Redis backends.
    """

    def __init__(self, redis_url: str | None = None) -> None:
        self._redis_url = redis_url
        self._redis: Any = None
        self._memory: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._cleanup_counter = 0
        self._cleanup_interval = 100

        if redis_url and _REDIS_AVAILABLE:
            try:
                self._redis = redis.from_url(  # type: ignore[no-untyped-call]
            redis_url, decode_responses=True)
            except (ValueError, TypeError):
                self._redis = None

    async def check_limit(
        self,
        client_id: str,
        max_requests: int = 10,
        window_seconds: int = 60,
    ) -> bool:
        """Return True if the client is within the rate limit."""
        now = time.time()

        if self._redis:
            return await self._check_limit_redis(client_id, max_requests, window_seconds, now)

        return await self._check_limit_memory(client_id, max_requests, window_seconds, now)

    async def _check_limit_memory(
        self,
        client_id: str,
        max_requests: int,
        window_seconds: int,
        now: float,
    ) -> bool:
        async with self._lock:
            # Periodic cleanup of stale entries
            self._cleanup_counter += 1
            if self._cleanup_counter >= self._cleanup_interval:
                self._cleanup_counter = 0
                stale = [
                    cid
                    for cid, timestamps in self._memory.items()
                    if not timestamps or now - timestamps[-1] > window_seconds * 2
                ]
                for cid in stale:
                    self._memory.pop(cid, None)

            timestamps = self._memory.get(client_id, [])
            # Sliding window: keep only timestamps within the window
            valid = [t for t in timestamps if now - t < window_seconds]
            if len(valid) >= max_requests:
                self._memory[client_id] = valid
                return False

            valid.append(now)
            self._memory[client_id] = valid
            return True

    async def _check_limit_redis(
        self,
        client_id: str,
        max_requests: int,
        window_seconds: int,
        now: float,
    ) -> bool:
        key = f"ws_rate:{client_id}"
        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(key, 0, now - window_seconds)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window_seconds)
        _, count, _, _ = await pipe.execute()
        return count < max_requests  # type: ignore[no-any-return]

    async def get_remaining(
        self,
        client_id: str,
        max_requests: int = 10,
        window_seconds: int = 60,
    ) -> int:
        """Return remaining allowed requests in the current window."""
        now = time.time()

        if self._redis:
            key = f"ws_rate:{client_id}"
            await self._redis.zremrangebyscore(key, 0, now - window_seconds)
            count = await self._redis.zcard(key)
            return max(0, max_requests - count)  # type: ignore[no-any-return]

        async with self._lock:
            timestamps = self._memory.get(client_id, [])
            valid = [t for t in timestamps if now - t < window_seconds]
            return max(0, max_requests - len(valid))

    def cleanup(self) -> None:
        """Remove all stale in-memory entries (synchronous, for shutdown)."""
        now = time.time()
        stale = [
            cid
            for cid, timestamps in self._memory.items()
            if not timestamps or now - timestamps[-1] > 3600
        ]
        for cid in stale:
            self._memory.pop(cid, None)
