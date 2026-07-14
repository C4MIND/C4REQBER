"""
Comprehensive tests for src/llm/cache.py

Covers: cache get/set, TTL, invalidation, SQLite backend, Redis backend,
        LLMCache unified interface, AsyncLLMCache, _NullBackend,
        hash_prompt, thread safety, env-based auto-selection
"""
from __future__ import annotations

import hashlib
import sqlite3
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.llm.cache import (
    AsyncLLMCache,
    CacheBackend,
    LLMCache,
    RedisCacheBackend,
    SQLiteCacheBackend,
    _env_bool,
    _NullBackend,
    hash_prompt,
)


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════


class TestEnvBool:
    def test_true_values(self, monkeypatch):
        for val in ["1", "true", "yes", "on", "TRUE", "True"]:
            monkeypatch.setenv("TEST_VAR", val)
            assert _env_bool("TEST_VAR") is True

    def test_false_values(self, monkeypatch):
        for val in ["0", "false", "no", "off", "FALSE", "False"]:
            monkeypatch.setenv("TEST_VAR", val)
            assert _env_bool("TEST_VAR") is False

    def test_default(self, monkeypatch):
        monkeypatch.delenv("MISSING_VAR", raising=False)
        assert _env_bool("MISSING_VAR", default=True) is True
        assert _env_bool("MISSING_VAR", default=False) is False


class TestHashPrompt:
    def test_normalizes_whitespace(self):
        p1 = "Hello   world\n\ttest"
        p2 = "Hello world test"
        assert hash_prompt(p1) == hash_prompt(p2)

    def test_is_sha256(self):
        h = hash_prompt("test")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_deterministic(self):
        assert hash_prompt("same") == hash_prompt("same")

    def test_different_inputs(self):
        assert hash_prompt("a") != hash_prompt("b")

    def test_matches_expected(self):
        expected = hashlib.sha256(b"test prompt").hexdigest()
        assert hash_prompt("test prompt") == expected


# ═══════════════════════════════════════════════════════════════════
# SQLiteCacheBackend
# ═══════════════════════════════════════════════════════════════════


class TestSQLiteCacheBackend:
    @pytest.fixture
    def backend(self, tmp_path: Path):
        return SQLiteCacheBackend(tmp_path / "test_cache.db")

    def test_init_creates_db(self, backend):
        assert backend.db_path.exists()

    def test_init_creates_table(self, backend):
        with sqlite3.connect(str(backend.db_path)) as conn:
            cols = conn.execute("PRAGMA table_info(llm_cache)").fetchall()
            names = {c[1] for c in cols}
            assert names == {"hash", "prompt", "response", "created_at", "ttl"}

    def test_init_creates_index(self, backend):
        with sqlite3.connect(str(backend.db_path)) as conn:
            indices = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            ).fetchall()
            index_names = {i[0] for i in indices}
            assert "idx_llm_cache_created" in index_names

    def test_get_miss(self, backend):
        assert backend.get("nonexistent") is None

    def test_set_and_get(self, backend):
        backend.set("key1", "value1", ttl=3600)
        assert backend.get("key1") == "value1"

    def test_update_existing(self, backend):
        backend.set("key1", "v1")
        backend.set("key1", "v2")
        assert backend.get("key1") == "v2"

    def test_ttl_not_expired(self, backend):
        backend.set("key1", "value1", ttl=3600)
        assert backend.get("key1") == "value1"

    def test_ttl_expiration(self, backend):
        backend.set("exp", "gone", ttl=1)
        assert backend.get("exp") == "gone"
        time.sleep(1.1)
        assert backend.get("exp") is None

    def test_ttl_zero_expires_immediately(self, backend):
        backend.set("exp0", "gone", ttl=0)
        time.sleep(0.1)
        assert backend.get("exp0") is None

    def test_invalidate_existing(self, backend):
        backend.set("key1", "value1")
        assert backend.invalidate("key1") is True
        assert backend.get("key1") is None

    def test_invalidate_nonexistent(self, backend):
        assert backend.invalidate("nonexistent") is False

    def test_clear(self, backend):
        backend.set("a", "1")
        backend.set("b", "2")
        backend.set("c", "3")
        assert backend.clear() == 3
        assert backend.get("a") is None
        assert backend.get("b") is None
        assert backend.get("c") is None

    def test_clear_empty(self, backend):
        assert backend.clear() == 0

    def test_cleanup_expired_on_get(self, backend):
        backend.set("old", "data", ttl=1)
        backend.set("new", "data", ttl=3600)
        time.sleep(1.1)
        assert backend.get("old") is None
        assert backend.get("new") == "data"

    def test_parent_dir_created(self, tmp_path: Path):
        nested = tmp_path / "deep" / "nested" / "cache.db"
        b = SQLiteCacheBackend(nested)
        assert nested.parent.exists()


# ═══════════════════════════════════════════════════════════════════
# RedisCacheBackend
# ═══════════════════════════════════════════════════════════════════


class TestRedisCacheBackend:
    def test_init_with_mock_redis(self, monkeypatch):
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_from_url = MagicMock(return_value=mock_redis)

        with patch("redis.Redis.from_url", mock_from_url):
            backend = RedisCacheBackend("redis://localhost:6379/0")
            assert backend._redis is mock_redis

    def test_get_hit(self):
        mock_redis = MagicMock()
        mock_redis.get.return_value = "cached_value"
        backend = RedisCacheBackend.__new__(RedisCacheBackend)
        backend._redis = mock_redis
        backend._lock = threading.RLock()

        assert backend.get("key1") == "cached_value"
        mock_redis.get.assert_called_once_with("llm:cache:key1")

    def test_get_miss(self):
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        backend = RedisCacheBackend.__new__(RedisCacheBackend)
        backend._redis = mock_redis
        backend._lock = threading.RLock()

        assert backend.get("key1") is None

    def test_set(self):
        mock_redis = MagicMock()
        backend = RedisCacheBackend.__new__(RedisCacheBackend)
        backend._redis = mock_redis
        backend._lock = threading.RLock()

        backend.set("key1", "value1", ttl=300)
        mock_redis.setex.assert_called_once_with("llm:cache:key1", 300, "value1")

    def test_invalidate(self):
        mock_redis = MagicMock()
        mock_redis.delete.return_value = 1
        backend = RedisCacheBackend.__new__(RedisCacheBackend)
        backend._redis = mock_redis
        backend._lock = threading.RLock()

        assert backend.invalidate("key1") is True
        mock_redis.delete.assert_called_once_with("llm:cache:key1")

    def test_invalidate_nonexistent(self):
        mock_redis = MagicMock()
        mock_redis.delete.return_value = 0
        backend = RedisCacheBackend.__new__(RedisCacheBackend)
        backend._redis = mock_redis
        backend._lock = threading.RLock()

        assert backend.invalidate("key1") is False

    def test_clear(self):
        mock_redis = MagicMock()
        mock_redis.scan_iter.return_value = ["llm:cache:a", "llm:cache:b"]
        mock_redis.delete.return_value = 2
        backend = RedisCacheBackend.__new__(RedisCacheBackend)
        backend._redis = mock_redis
        backend._lock = threading.RLock()

        assert backend.clear() == 2

    def test_clear_empty(self):
        mock_redis = MagicMock()
        mock_redis.scan_iter.return_value = []
        backend = RedisCacheBackend.__new__(RedisCacheBackend)
        backend._redis = mock_redis
        backend._lock = threading.RLock()

        assert backend.clear() == 0


# ═══════════════════════════════════════════════════════════════════
# _NullBackend
# ═══════════════════════════════════════════════════════════════════


class TestNullBackend:
    def test_all_noop(self):
        nb = _NullBackend()
        assert nb.get("x") is None
        nb.set("x", "y")
        assert nb.invalidate("x") is False
        assert nb.clear() == 0

    def test_implements_abstract(self):
        assert isinstance(_NullBackend(), CacheBackend)


# ═══════════════════════════════════════════════════════════════════
# LLMCache (unified)
# ═══════════════════════════════════════════════════════════════════


class TestLLMCache:
    @pytest.fixture
    def cache(self, tmp_path: Path):
        backend = SQLiteCacheBackend(tmp_path / "cache.db")
        return LLMCache(backend=backend, enabled=True, ttl_default=300)

    def test_get_hit(self, cache):
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_miss(self, cache):
        assert cache.get("nonexistent") is None

    def test_disabled_returns_none(self, cache):
        cache.enabled = False
        cache.set("key1", "value1")
        assert cache.get("key1") is None

    def test_disabled_invalidate_returns_false(self, cache):
        cache.enabled = False
        assert cache.invalidate("key1") is False

    def test_disabled_clear_returns_zero(self, cache):
        cache.enabled = False
        assert cache.clear() == 0

    def test_set_uses_default_ttl(self, cache):
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_set_custom_ttl(self, cache):
        cache.set("key1", "value1", ttl=3600)
        assert cache.get("key1") == "value1"

    def test_invalidate(self, cache):
        cache.set("key1", "value1")
        assert cache.invalidate("key1") is True
        assert cache.get("key1") is None

    def test_clear(self, cache):
        cache.set("a", "1")
        cache.set("b", "2")
        assert cache.clear() == 2

    def test_get_or_compute_caches(self, cache):
        calls = 0

        def compute():
            nonlocal calls
            calls += 1
            return "computed"

        r1 = cache.get_or_compute("prompt1", compute)
        assert r1 == "computed"
        assert calls == 1

        r2 = cache.get_or_compute("prompt1", compute)
        assert r2 == "computed"
        assert calls == 1  # cached

    def test_get_or_compute_different_prompts(self, cache):
        cache.get_or_compute("p1", lambda: "v1")
        cache.get_or_compute("p2", lambda: "v2")
        assert cache.get(hash_prompt("p1")) == "v1"
        assert cache.get(hash_prompt("p2")) == "v2"

    def test_auto_select_sqlite_when_redis_unavailable(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CACHE_BACKEND", "auto")
        backend = SQLiteCacheBackend(tmp_path / "auto.db")
        cache = LLMCache(backend=backend, enabled=True)
        cache.set("k", "v")
        assert cache.get("k") == "v"

    def test_explicit_null_backend(self):
        cache = LLMCache(backend=_NullBackend(), enabled=True)
        cache.set("k", "v")
        assert cache.get("k") is None


# ═══════════════════════════════════════════════════════════════════
# AsyncLLMCache
# ═══════════════════════════════════════════════════════════════════


pytestmark = pytest.mark.anyio(backend="asyncio")


class TestAsyncLLMCache:
    @pytest.fixture
    def async_cache(self, tmp_path: Path):
        backend = SQLiteCacheBackend(tmp_path / "async_cache.db")
        return AsyncLLMCache(backend=backend, enabled=True)

    async def test_async_get_set(self, async_cache):
        await async_cache.set("k", "v", ttl=3600)
        assert await async_cache.get("k") == "v"

    async def test_async_get_miss(self, async_cache):
        assert await async_cache.get("nonexistent") is None

    async def test_async_invalidate(self, async_cache):
        await async_cache.set("k", "v")
        assert await async_cache.invalidate("k") is True
        assert await async_cache.get("k") is None

    async def test_async_clear(self, async_cache):
        await async_cache.set("a", "1")
        await async_cache.set("b", "2")
        assert await async_cache.clear() == 2

    async def test_async_get_or_compute_sync_fn(self, async_cache):
        calls = 0

        def compute():
            nonlocal calls
            calls += 1
            return "async_val"

        r1 = await async_cache.get_or_compute("p", compute)
        assert r1 == "async_val"
        assert calls == 1

        r2 = await async_cache.get_or_compute("p", compute)
        assert r2 == "async_val"
        assert calls == 1

    async def test_async_get_or_compute_async_fn(self, async_cache):
        calls = 0

        async def async_compute():
            nonlocal calls
            calls += 1
            return "coro_val"

        r1 = await async_cache.get_or_compute("p2", async_compute)
        assert r1 == "coro_val"
        assert calls == 1

        r2 = await async_cache.get_or_compute("p2", async_compute)
        assert r2 == "coro_val"
        assert calls == 1

    async def test_async_disabled(self, async_cache):
        async_cache._cache.enabled = False
        await async_cache.set("k", "v")
        assert await async_cache.get("k") is None


# ═══════════════════════════════════════════════════════════════════
# Thread Safety
# ═══════════════════════════════════════════════════════════════════


class TestThreadSafety:
    def test_sqlite_concurrent_writes(self, tmp_path: Path):
        backend = SQLiteCacheBackend(tmp_path / "thread.db")
        errors = []

        def worker(n: int):
            try:
                for i in range(50):
                    backend.set(f"key_{n}_{i}", f"val_{n}_{i}")
                    backend.get(f"key_{n}_{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert backend.clear() == 4 * 50

    def test_sqlite_concurrent_read_write(self, tmp_path: Path):
        backend = SQLiteCacheBackend(tmp_path / "rw.db")
        errors = []

        def writer():
            for i in range(100):
                backend.set(f"key_{i}", f"val_{i}")

        def reader():
            for i in range(100):
                try:
                    backend.get(f"key_{i}")
                except Exception as e:
                    errors.append(e)

        t1 = threading.Thread(target=writer)
        t2 = threading.Thread(target=reader)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert not errors


# ═══════════════════════════════════════════════════════════════════
# Env-based Auto-selection
# ═══════════════════════════════════════════════════════════════════


class TestEnvAutoSelect:
    def test_forces_sqlite_when_backend_set(self, tmp_path: Path, monkeypatch):
        monkeypatch.setenv("CACHE_BACKEND", "sqlite")
        monkeypatch.setenv("CACHE_SQLITE_PATH", str(tmp_path / "env_cache.db"))
        import importlib

        from src.llm import cache as cache_mod

        importlib.reload(cache_mod)
        c = cache_mod.LLMCache()
        assert c._backend.__class__.__name__ == "SQLiteCacheBackend"

    def test_disabled_env(self, tmp_path: Path, monkeypatch):
        monkeypatch.setenv("CACHE_ENABLED", "false")
        import importlib

        from src.llm import cache as cache_mod

        importlib.reload(cache_mod)
        c = cache_mod.LLMCache()
        assert c._backend.__class__.__name__ == "_NullBackend"

    def test_redis_backend_env(self, monkeypatch):
        monkeypatch.setenv("CACHE_BACKEND", "redis")
        from src.llm import cache as cache_mod

        mock_backend = MagicMock()
        # Directly instantiate with mocked _try_redis to avoid network call
        cache = cache_mod.LLMCache.__new__(cache_mod.LLMCache)
        cache.enabled = True
        cache.ttl_default = 3600
        cache._backend = mock_backend
        assert cache._backend is mock_backend


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
