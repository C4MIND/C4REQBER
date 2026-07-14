"""Tests for BaseP6Client caching."""
from __future__ import annotations

import pytest

from src.knowledge.sources.base_p6 import _SimpleTTLCache


class TestSimpleTTLCache:
    def test_get_missing_returns_none(self) -> None:
        cache = _SimpleTTLCache()
        assert cache.get("missing") is None

    def test_set_and_get(self) -> None:
        cache = _SimpleTTLCache()
        cache.set("key", {"data": 42})
        assert cache.get("key") == {"data": 42}

    def test_ttl_expires(self) -> None:
        cache = _SimpleTTLCache(default_ttl=0.01)
        cache.set("key", "value")
        import time
        time.sleep(0.02)
        assert cache.get("key") is None

    def test_clear(self) -> None:
        cache = _SimpleTTLCache()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_custom_ttl(self) -> None:
        cache = _SimpleTTLCache(default_ttl=300.0)
        cache.set("key", "value", ttl=0.01)
        import time
        time.sleep(0.02)
        assert cache.get("key") is None
