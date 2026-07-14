"""
Complexity Cache: Caches engine results for reuse across complexity levels
When a user solves a problem in Lite then switches to Advanced, we don't re-run the engine
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


class ComplexityCache:
    """
    Redis-based cache for C4 engine results

    Key design: "level_cache:{problem_hash}:{level}" for filtered results
    But store raw engine result once, then filter on retrieval
    """

    @staticmethod
    def _generate_problem_hash(problem: str) -> str:
        """
        Create a stable hash for a problem query
        Normalizes whitespace and lowercase before hashing
        """
        normalized = problem.strip().lower().replace(r"\s+", " ")
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _make_raw_key(problem_hash: str) -> str:
        """Cache key for raw engine result"""
        return f"level_cache:raw:{problem_hash}"

    @staticmethod
    def _make_filtered_key(problem_hash: str, level: str) -> str:
        """Cache key for filtered result (rarely used - we filter on the fly)"""
        return f"level_cache:filtered:{problem_hash}:{level}"

    @staticmethod
    async def get_or_compute(
        engine_func: Any, problem: str, level: str, ttl: int = 3600
    ) -> dict[str, Any]:
        """
        Get cached result or compute and cache it

        Flow:
        1. Check if raw result exists in cache
        2. If yes: Filter it for the requested level and return
        3. If no: Run engine_func, cache raw result, then filter and return

        Args:
            engine_func: Async function that runs the pipeline
            problem: The research problem/query
            level: Complexity level (lite/advanced/expert)
            ttl: Cache TTL in seconds (default 1 hour)

        Returns:
            Filtered result for the requested level
        """
        import redis.asyncio as redis

        problem_hash = ComplexityCache._generate_problem_hash(problem)
        raw_key = ComplexityCache._make_raw_key(problem_hash)

        # Try to get raw result from cache
        redis_client = await redis.from_url(  # type: ignore[no-untyped-call]
            "redis://localhost:6379")

        try:
            cached_raw = await redis_client.get(raw_key)

            if cached_raw:
                # Cache hit! Use raw result
                raw_result = json.loads(cached_raw)

                # Filter for the requested level
                from src.core.complexity_adapter import get_config, validate_level
                from src.core.disclosure_filter import filter_solve_result

                level_enum = validate_level(level)
                config = get_config(level_enum)

                return filter_solve_result(raw_result, config)

            # Cache miss - compute fresh
            raw_result = await engine_func(problem)

            # Store raw result in cache
            await redis_client.setex(raw_key, ttl, json.dumps(raw_result))

            # Filter and return
            level_enum = validate_level(level)
            config = get_config(level_enum)
            return filter_solve_result(raw_result, config)

        finally:
            await redis_client.close()

    @staticmethod
    async def invalidate(problem: str) -> bool:
        """
        Invalidate cache for a specific problem
        Useful when user manually updates data or when we want to force refresh

        Args:
            problem: The problem query to invalidate

        Returns:
            True if cache was invalidated, False if not found
        """
        import redis.asyncio as redis

        redis_client = await redis.from_url(  # type: ignore[no-untyped-call]
            "redis://localhost:6379")

        try:
            problem_hash = ComplexityCache._generate_problem_hash(problem)
            raw_key = ComplexityCache._make_raw_key(problem_hash)

            # Also invalidate any filtered variants
            pattern = f"level_cache:*{problem_hash}*"

            deleted = await redis_client.delete(raw_key)

            # Clean up filtered variants if any exist
            keys_to_delete = []
            async for key in redis_client.scan_iter(match=pattern):
                keys_to_delete.append(key)

            if keys_to_delete:
                await redis_client.delete(*keys_to_delete)

            return deleted > 0 or len(keys_to_delete) > 0

        finally:
            await redis_client.close()

    @staticmethod
    async def invalidate_all() -> int:
        """
        Clear entire level cache (use with caution)

        Returns:
            Number of keys deleted
        """
        import redis.asyncio as redis

        redis_client = await redis.from_url(  # type: ignore[no-untyped-call]
            "redis://localhost:6379")

        try:
            pattern = "level_cache:*"
            keys_to_delete = []

            async for key in redis_client.scan_iter(match=pattern):
                keys_to_delete.append(key)

            if keys_to_delete:
                await redis_client.delete(*keys_to_delete)

            return len(keys_to_delete)

        finally:
            await redis_client.close()

    @staticmethod
    async def get_stats() -> dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dict with hit_rate, miss_rate, total_keys, etc.
        """
        import redis.asyncio as redis

        redis_client = await redis.from_url(  # type: ignore[no-untyped-call]
            "redis://localhost:6379")

        try:
            # Count keys by pattern
            total_keys = 0
            raw_keys = 0
            filtered_keys = 0

            async for key in redis_client.scan_iter(match="level_cache:*"):
                total_keys += 1
                if key.startswith(b"level_cache:raw:"):
                    raw_keys += 1
                elif key.startswith(b"level_cache:filtered:"):
                    filtered_keys += 1

            # Get Redis info
            info = await redis_client.info("stats")

            return {
                "total_keys": total_keys,
                "raw_keys": raw_keys,
                "filtered_keys": filtered_keys,
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": info.get("keyspace_hits", 0)
                / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1),
            }

        finally:
            await redis_client.close()


# Alternative: In-memory cache for development (no Redis)
class InMemoryComplexityCache:
    """Development-only cache that doesn't require Redis"""

    _cache: dict[str, tuple[dict[str, Any], float]] = {}  # key -> (data, expiry)

    @staticmethod
    async def get_or_compute(
        engine_func: Any, problem: str, level: str, ttl: int = 3600
    ) -> dict[str, Any]:
        """Get or compute."""
        from time import time

        problem_hash = ComplexityCache._generate_problem_hash(problem)
        raw_key = ComplexityCache._make_raw_key(problem_hash)

        now = time()

        # Check cache
        if raw_key in InMemoryComplexityCache._cache:
            data, expiry = InMemoryComplexityCache._cache[raw_key]
            if now < expiry:
                # Cache hit
                from src.core.complexity_adapter import get_config, validate_level
                from src.core.disclosure_filter import filter_solve_result

                level_enum = validate_level(level)
                config = get_config(level_enum)
                return filter_solve_result(data, config)
            else:
                # Expired - remove
                del InMemoryComplexityCache._cache[raw_key]

        # Cache miss - compute
        raw_result = await engine_func(problem)

        # Store in cache
        InMemoryComplexityCache._cache[raw_key] = (raw_result, now + ttl)

        # Filter and return
        from src.core.complexity_adapter import get_config, validate_level
        from src.core.disclosure_filter import filter_solve_result

        level_enum = validate_level(level)
        config = get_config(level_enum)
        return filter_solve_result(raw_result, config)


# Factory function to get appropriate cache
def get_complexity_cache() -> None:
    """
    Returns appropriate cache implementation based on environment
    Use Redis in production, in-memory in development
    """
    import os

    if os.getenv("ENVIRONMENT") == "production":
        return ComplexityCache  # type: ignore[return-value]
    else:
        return InMemoryComplexityCache  # type: ignore[return-value]
