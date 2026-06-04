"""
Tests for src/llm/cache.py
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
import threading
import time
from pathlib import Path

import pytest

from src.llm.cache import (
    AsyncLLMCache,
    LLMCache,
    SQLiteCacheBackend,
    _NullBackend,
    hash_prompt,
)


pytestmark = pytest.mark.anyio(backend="asyncio")


# ── Helpers ─────────────────────────────────────────────────────────


def test_hash_prompt_normalizes_whitespace():
    p1 = "Hello   world\n\t  test"
    p2 = "Hello world test"
    assert hash_prompt(p1) == hash_prompt(p2)


def test_hash_prompt_is_sha256():
    h = hash_prompt("test")
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


# ── SQLite Backend ──────────────────────────────────────────────────


class TestSQLiteCacheBackend:
    @pytest.fixture
    def backend(self, tmp_path: Path):
        db = tmp_path / "test_cache.db"
        return SQLiteCacheBackend(db)

    def test_get_miss(self, backend: SQLiteCacheBackend):
        assert backend.get("nonexistent") is None

    def test_set_and_get(self, backend: SQLiteCacheBackend):
        backend.set("abc", "hello", ttl=3600)
        assert backend.get("abc") == "hello"

    def test_ttl_expiration(self, backend: SQLiteCacheBackend):
        backend.set("exp", "gone", ttl=1)
        assert backend.get("exp") == "gone"
        time.sleep(1.1)
        assert backend.get("exp") is None

    def test_invalidate(self, backend: SQLiteCacheBackend):
        backend.set("x", "y")
        assert backend.invalidate("x") is True
        assert backend.get("x") is None
        assert backend.invalidate("x") is False

    def test_clear(self, backend: SQLiteCacheBackend):
        backend.set("a", "1")
        backend.set("b", "2")
        assert backend.clear() == 2
        assert backend.get("a") is None
        assert backend.get("b") is None

    def test_update_existing(self, backend: SQLiteCacheBackend):
        backend.set("k", "v1")
        backend.set("k", "v2")
        assert backend.get("k") == "v2"

    def test_table_schema(self, backend: SQLiteCacheBackend):
        with sqlite3.connect(str(backend.db_path)) as conn:
            cols = conn.execute(
                "PRAGMA table_info(llm_cache)"
            ).fetchall()
            names = {c[1] for c in cols}
            assert names == {"hash", "prompt", "response", "created_at", "ttl"}


# ── Null Backend ────────────────────────────────────────────────────


class TestNullBackend:
    def test_all_noop(self):
        nb = _NullBackend()
        assert nb.get("x") is None
        nb.set("x", "y")
        assert nb.invalidate("x") is False
        assert nb.clear() == 0


# ── LLMCache (unified) ──────────────────────────────────────────────


class TestLLMCache:
    @pytest.fixture
    def cache(self, tmp_path: Path):
        backend = SQLiteCacheBackend(tmp_path / "cache.db")
        return LLMCache(backend=backend, enabled=True, ttl_default=300)

    def test_disabled_returns_none(self, cache: LLMCache):
        cache.enabled = False
        cache.set("k", "v")
        assert cache.get("k") is None

    def test_get_or_compute_caches(self, cache: LLMCache):
        calls = 0

        def compute():
            nonlocal calls
            calls += 1
            return "computed"

        r1 = cache.get_or_compute("prompt", compute)
        assert r1 == "computed"
        assert calls == 1

        r2 = cache.get_or_compute("prompt", compute)
        assert r2 == "computed"
        assert calls == 1  # cached

    def test_default_ttl(self, cache: LLMCache):
        cache.set("k", "v")
        # TTL should be 300 from fixture
        assert cache.ttl_default == 300


# ── AsyncLLMCache ───────────────────────────────────────────────────


class TestAsyncLLMCache:
    @pytest.fixture
    def async_cache(self, tmp_path: Path):
        backend = SQLiteCacheBackend(tmp_path / "async_cache.db")
        return AsyncLLMCache(backend=backend, enabled=True)

    @pytest.mark.anyio
    async def test_async_get_set(self, async_cache: AsyncLLMCache):
        await async_cache.set("k", "v", ttl=3600)
        assert await async_cache.get("k") == "v"

    @pytest.mark.anyio
    async def test_async_invalidate(self, async_cache: AsyncLLMCache):
        await async_cache.set("k", "v")
        assert await async_cache.invalidate("k") is True
        assert await async_cache.get("k") is None

    @pytest.mark.anyio
    async def test_async_clear(self, async_cache: AsyncLLMCache):
        await async_cache.set("a", "1")
        await async_cache.set("b", "2")
        assert await async_cache.clear() == 2

    @pytest.mark.anyio
    async def test_async_get_or_compute(self, async_cache: AsyncLLMCache):
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

    @pytest.mark.anyio
    async def test_async_get_or_compute_with_coro(self, async_cache: AsyncLLMCache):
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


# ── Thread safety ───────────────────────────────────────────────────


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


# ── Auto-select / env ───────────────────────────────────────────────


class TestAutoSelect:
    def test_forces_sqlite_when_backend_set(self, tmp_path: Path, monkeypatch):
        monkeypatch.setenv("CACHE_BACKEND", "sqlite")
        monkeypatch.setenv("CACHE_SQLITE_PATH", str(tmp_path / "env_cache.db"))
        # Re-import to pick up env
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
