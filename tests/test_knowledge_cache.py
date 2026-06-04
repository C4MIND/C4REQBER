"""Tests for src/knowledge/cache.py"""
import time
from unittest.mock import patch

import pytest

from src.knowledge.cache import SearchCache


class TestSearchCache:
    def test_init_defaults(self):
        cache = SearchCache()
        assert cache.enabled is True
        assert cache.ttl == 300.0

    def test_init_disabled(self):
        cache = SearchCache(enabled=False)
        assert cache.enabled is False

    def test_get_miss(self):
        cache = SearchCache()
        assert cache.get("missing") is None

    def test_get_disabled(self):
        cache = SearchCache(enabled=False)
        cache.set("key", "value")
        assert cache.get("key") is None

    def test_set_and_get(self):
        cache = SearchCache()
        cache.set("key", "value")
        assert cache.get("key") == "value"

    def test_ttl_expiry(self):
        cache = SearchCache(ttl=0.01)
        cache.set("key", "value")
        time.sleep(0.02)
        assert cache.get("key") is None

    def test_clear(self):
        cache = SearchCache()
        cache.set("key", "value")
        cache.clear()
        assert cache.get("key") is None

    def test_invalidate(self):
        cache = SearchCache()
        cache.set("key", "value")
        cache.invalidate("key")
        assert cache.get("key") is None

    def test_invalidate_missing(self):
        cache = SearchCache()
        cache.invalidate("missing")
        assert cache.get("missing") is None

    def test_set_disabled(self):
        cache = SearchCache(enabled=False)
        cache.set("key", "value")
        assert cache.get("key") is None
