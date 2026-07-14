"""LLM Cache.

Unified cache interface for LLM calls with Redis/SQLite backends.

Usage:
    from src.llm.cache import LLMCache

    cache = LLMCache()  # Auto-selects Redis -> SQLite
    cache.set("prompt_hash", "response")
    response = cache.get("prompt_hash")
"""
from __future__ import annotations

import hashlib
import os
import sqlite3
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


# ── Config ──────────────────────────────────────────────────────────


def _env_bool(key: str, default: bool = False) -> bool:
    val = os.getenv(key, "")
    if val.lower() in ("1", "true", "yes", "on"):
        return True
    if val.lower() in ("0", "false", "no", "off"):
        return False
    return default


CACHE_ENABLED = _env_bool("CACHE_ENABLED", True)
CACHE_BACKEND = os.getenv("CACHE_BACKEND", "auto")  # auto | redis | sqlite
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL_DEFAULT = int(os.getenv("CACHE_TTL", "3600"))
CACHE_SQLITE_PATH = os.getenv("CACHE_SQLITE_PATH", "data/llm_cache.db")


# ── Hash helper ─────────────────────────────────────────────────────


def _normalize_prompt(prompt: str) -> str:
    """Normalize prompt for consistent hashing."""
    return " ".join(prompt.split())


def hash_prompt(prompt: str) -> str:
    """SHA256 hash of normalized prompt."""
    normalized = _normalize_prompt(prompt)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


# ── Backends ────────────────────────────────────────────────────────


class CacheBackend(ABC):
    """Abstract cache backend."""

    @abstractmethod
    def get(self, prompt_hash: str) -> str | None:
        """Get cached response by hash."""
        ...

    @abstractmethod
    def set(self, prompt_hash: str, response: str, ttl: int = 3600) -> None:
        """Cache response with TTL (seconds)."""
        ...

    @abstractmethod
    def invalidate(self, prompt_hash: str) -> bool:
        """Remove entry by hash. Returns True if existed."""
        ...

    @abstractmethod
    def clear(self) -> int:
        """Clear all entries. Returns count removed."""
        ...


class SQLiteCacheBackend(CacheBackend):
    """Thread-safe SQLite cache backend for local/dev."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path or CACHE_SQLITE_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_db()

    def _init_db(self) -> None:
        with self._lock, sqlite3.connect(str(self.db_path), check_same_thread=False) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS llm_cache (
                    hash TEXT PRIMARY KEY,
                    prompt TEXT NOT NULL,
                    response TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    ttl INTEGER NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_llm_cache_created ON llm_cache(created_at)"
            )
            conn.commit()

    def _is_expired(self, created_at: float, ttl: int) -> bool:
        return time.time() > created_at + ttl

    def _cleanup_expired(self, conn: sqlite3.Connection) -> None:
        now = time.time()
        conn.execute("DELETE FROM llm_cache WHERE (? - created_at) > ttl", (now,))

    def get(self, prompt_hash: str) -> str | None:
        with self._lock, sqlite3.connect(str(self.db_path), check_same_thread=False) as conn:
            self._cleanup_expired(conn)
            row = conn.execute(
                "SELECT response, created_at, ttl FROM llm_cache WHERE hash = ?",
                (prompt_hash,),
            ).fetchone()
            if row is None:
                return None
            response, created_at, ttl = row
            if self._is_expired(created_at, ttl):
                conn.execute("DELETE FROM llm_cache WHERE hash = ?", (prompt_hash,))
                conn.commit()
                return None
            return response  # type: ignore[no-any-return]

    def set(self, prompt_hash: str, response: str, ttl: int = 3600) -> None:
        with self._lock, sqlite3.connect(str(self.db_path), check_same_thread=False) as conn:
            conn.execute(
                """
                INSERT INTO llm_cache (hash, prompt, response, created_at, ttl)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(hash) DO UPDATE SET
                    response=excluded.response,
                    created_at=excluded.created_at,
                    ttl=excluded.ttl
                """,
                (prompt_hash, "", response, time.time(), ttl),
            )
            conn.commit()

    def invalidate(self, prompt_hash: str) -> bool:
        with self._lock, sqlite3.connect(str(self.db_path), check_same_thread=False) as conn:
            cur = conn.execute("DELETE FROM llm_cache WHERE hash = ?", (prompt_hash,))
            conn.commit()
            return cur.rowcount > 0

    def clear(self) -> int:
        with self._lock, sqlite3.connect(str(self.db_path), check_same_thread=False) as conn:
            cur = conn.execute("DELETE FROM llm_cache")
            conn.commit()
            return cur.rowcount


class RedisCacheBackend(CacheBackend):
    """Redis cache backend for production."""

    def __init__(self, redis_url: str | None = None) -> None:
        import redis as _redis

        self._redis = _redis.Redis.from_url(redis_url or REDIS_URL, decode_responses=True)
        self._lock = threading.RLock()

    def get(self, prompt_hash: str) -> str | None:
        with self._lock:
            value = self._redis.get(f"llm:cache:{prompt_hash}")
            return value if value is not None else None  # type: ignore[return-value]

    def set(self, prompt_hash: str, response: str, ttl: int = 3600) -> None:
        with self._lock:
            self._redis.setex(f"llm:cache:{prompt_hash}", ttl, response)

    def invalidate(self, prompt_hash: str) -> bool:
        with self._lock:
            return bool(self._redis.delete(f"llm:cache:{prompt_hash}"))

    def clear(self) -> int:
        with self._lock:
            keys = list(self._redis.scan_iter(match="llm:cache:*"))
            if not keys:
                return 0
            return self._redis.delete(*keys)  # type: ignore[return-value]


# ── Unified Cache ───────────────────────────────────────────────────


class LLMCache:
    """
    Unified LLM cache with backend selection.

    Backends (in priority order):
        1. Redis (if available and CACHE_BACKEND != 'sqlite')
        2. SQLite (always available)

    Disabled when CACHE_ENABLED=false.
    """

    def __init__(
        self,
        backend: CacheBackend | None = None,
        enabled: bool | None = None,
        ttl_default: int | None = None,
    ) -> None:
        self.enabled = CACHE_ENABLED if enabled is None else enabled
        self.ttl_default = CACHE_TTL_DEFAULT if ttl_default is None else ttl_default

        if backend is not None:
            self._backend = backend
        elif not self.enabled:
            self._backend = _NullBackend()
        else:
            self._backend = self._auto_select_backend()

    def _auto_select_backend(self) -> CacheBackend:
        backend_choice = CACHE_BACKEND.lower()

        if backend_choice == "redis":
            return self._try_redis()

        if backend_choice == "sqlite":
            return SQLiteCacheBackend()

        # auto: try Redis, else SQLite
        try:
            return self._try_redis()
        except Exception:
            return SQLiteCacheBackend()

    def _try_redis(self) -> CacheBackend:
        import redis as _redis

        r = _redis.Redis.from_url(REDIS_URL, decode_responses=True)
        r.ping()
        return RedisCacheBackend(REDIS_URL)

    # ── Public API ──────────────────────────────────────────────────

    def get(self, prompt_hash: str) -> str | None:
        """Get."""
        if not self.enabled:
            return None
        return self._backend.get(prompt_hash)

    def set(self, prompt_hash: str, response: str, ttl: int | None = None) -> None:
        """Set."""
        if not self.enabled:
            return
        self._backend.set(prompt_hash, response, ttl or self.ttl_default)

    def invalidate(self, prompt_hash: str) -> bool:
        """Invalidate."""
        if not self.enabled:
            return False
        return self._backend.invalidate(prompt_hash)

    def clear(self) -> int:
        """Clear."""
        if not self.enabled:
            return 0
        return self._backend.clear()

    def get_or_compute(
        self,
        prompt: str,
        compute_fn: Any,
        ttl: int | None = None,
    ) -> str:
        """
        High-level helper: check cache, otherwise call compute_fn and cache result.
        compute_fn must be a callable returning a string (or coroutine for async).
        """
        h = hash_prompt(prompt)
        cached = self.get(h)
        if cached is not None:
            return cached
        result = compute_fn()
        self.set(h, result, ttl)
        return result  # type: ignore[no-any-return]


class _NullBackend(CacheBackend):
    """No-op backend when cache is disabled."""

    def get(self, prompt_hash: str) -> str | None:
        return None

    def set(self, prompt_hash: str, response: str, ttl: int = 3600) -> None:
        pass

    def invalidate(self, prompt_hash: str) -> bool:
        return False

    def clear(self) -> int:
        return 0


# ── Async wrappers ──────────────────────────────────────────────────


class AsyncLLMCache:
    """Async-safe wrapper around LLMCache."""

    def __init__(
        self,
        backend: CacheBackend | None = None,
        enabled: bool | None = None,
        ttl_default: int | None = None,
    ) -> None:
        self._cache = LLMCache(backend=backend, enabled=enabled, ttl_default=ttl_default)

    async def get(self, prompt_hash: str) -> str | None:
        return self._cache.get(prompt_hash)

    async def set(self, prompt_hash: str, response: str, ttl: int | None = None) -> None:
        self._cache.set(prompt_hash, response, ttl)

    async def invalidate(self, prompt_hash: str) -> bool:
        return self._cache.invalidate(prompt_hash)

    async def clear(self) -> int:
        return self._cache.clear()

    async def get_or_compute(
        self,
        prompt: str,
        compute_fn: Any,
        ttl: int | None = None,
    ) -> str:
        """Get or compute."""
        h = hash_prompt(prompt)
        cached = await self.get(h)
        if cached is not None:
            return cached
        import inspect

        if inspect.iscoroutinefunction(compute_fn):
            result = await compute_fn()
        else:
            result = compute_fn()
        await self.set(h, result, ttl)
        return result  # type: ignore[no-any-return]
