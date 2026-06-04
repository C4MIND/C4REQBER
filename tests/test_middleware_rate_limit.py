"""Tests for src/api/middleware/rate_limit.py"""
import time
from unittest.mock import MagicMock, patch

import pytest

from src.api.middleware.rate_limit import RateLimiter, api_limiter, discovery_limiter


class TestRateLimiter:
    def test_init(self):
        rl = RateLimiter(max_requests=10, window=30)
        assert rl.max == 10
        assert rl.window == 30
        assert rl._clients == {}

    def test_check_new_client(self):
        rl = RateLimiter(max_requests=2, window=60)
        assert rl.check("1.2.3.4") is True
        assert "1.2.3.4" in rl._clients
        assert len(rl._clients["1.2.3.4"]) == 1

    def test_check_under_limit(self):
        rl = RateLimiter(max_requests=3, window=60)
        assert rl.check("1.2.3.4") is True
        assert rl.check("1.2.3.4") is True
        assert rl.check("1.2.3.4") is True
        assert len(rl._clients["1.2.3.4"]) == 3

    def test_check_over_limit(self):
        rl = RateLimiter(max_requests=2, window=60)
        assert rl.check("1.2.3.4") is True
        assert rl.check("1.2.3.4") is True
        assert rl.check("1.2.3.4") is False

    def test_check_window_expires(self):
        rl = RateLimiter(max_requests=2, window=1)
        assert rl.check("1.2.3.4") is True
        assert rl.check("1.2.3.4") is True
        assert rl.check("1.2.3.4") is False
        time.sleep(1.1)
        assert rl.check("1.2.3.4") is True

    def test_check_different_clients(self):
        rl = RateLimiter(max_requests=1, window=60)
        assert rl.check("1.2.3.4") is True
        assert rl.check("5.6.7.8") is True
        assert rl.check("1.2.3.4") is False

    def test_check_thread_safety(self):
        rl = RateLimiter(max_requests=100, window=60)
        results = [rl.check("client") for _ in range(100)]
        assert all(results) is True
        assert rl.check("client") is False

    def test_check_prunes_old_entries(self):
        rl = RateLimiter(max_requests=10, window=60)
        rl._clients["1.2.3.4"] = [time.time() - 120] * 5
        assert rl.check("1.2.3.4") is True
        assert len(rl._clients["1.2.3.4"]) == 1


class TestGlobalLimiters:
    def test_discovery_limiter(self):
        assert discovery_limiter.max == 10
        assert discovery_limiter.window == 60

    def test_api_limiter(self):
        assert api_limiter.max == 60
        assert api_limiter.window == 60
