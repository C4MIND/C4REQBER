"""
Tests for src/utils/retry/policies.py

Covers:
- custom_retry decorator (fallback when tenacity unavailable)
- with_retry decorator with all strategies
- retry_if_status_code decorator
- Convenience partials (retry_llm, retry_network, retry_db, retry_aggressive)
- Edge cases: immediate success, all failures, custom exceptions, on_retry callback
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch


_root = Path(__file__).resolve().parent.parent.parent
project_root = _root.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

import pytest
from tenacity import RetryError

from src.utils.retry.core import RETRY_CONFIGS, CircuitBreakerOpen, RetryStrategy
from src.utils.retry.policies import (
    custom_retry,
    retry_aggressive,
    retry_db,
    retry_if_status_code,
    retry_llm,
    retry_network,
    with_retry,
)


# ═══════════════════════════════════════════════════════════════════
# custom_retry (fallback implementation)
# ═══════════════════════════════════════════════════════════════════


class TestCustomRetry:
    """Test the custom retry decorator (used when tenacity is unavailable)."""

    def test_immediate_success(self):
        """Function succeeds on first call — no retries."""
        call_count = 0

        @custom_retry(max_attempts=3, base_delay=0.01, max_jitter=0)
        def success():
            nonlocal call_count
            call_count += 1
            return "ok"

        assert success() == "ok"
        assert call_count == 1

    def test_retry_then_success(self):
        """Function fails twice, then succeeds."""
        call_count = 0

        @custom_retry(max_attempts=5, base_delay=0.01, max_jitter=0)
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("fail")
            return "ok"

        assert flaky() == "ok"
        assert call_count == 3

    def test_all_attempts_exhausted(self):
        """Function always fails — raises last exception."""
        call_count = 0

        @custom_retry(max_attempts=3, base_delay=0.01, max_jitter=0)
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise TimeoutError("timeout")

        with pytest.raises(TimeoutError, match="timeout"):
            always_fail()

        assert call_count == 3

    def test_non_retryable_exception_not_retried(self):
        """Exceptions not in retryable list should fail immediately."""
        call_count = 0

        @custom_retry(
            max_attempts=5, base_delay=0.01, max_jitter=0, retryable_exceptions=(ConnectionError,)
        )
        def raise_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("not retryable")

        with pytest.raises(ValueError):
            raise_value_error()

        assert call_count == 1

    def test_on_retry_callback(self):
        """on_retry callback should be called on each retry."""
        retries_logged = []

        def on_retry(exc, attempt):
            retries_logged.append((type(exc).__name__, attempt))

        call_count = 0

        @custom_retry(max_attempts=3, base_delay=0.01, max_jitter=0, on_retry=on_retry)
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("fail")
            return "ok"

        assert flaky() == "ok"
        assert len(retries_logged) == 2
        assert retries_logged[0] == ("ConnectionError", 1)
        assert retries_logged[1] == ("ConnectionError", 2)

    def test_exponential_backoff_timing(self):
        """Delay should increase exponentially."""
        delays = []

        original_sleep = time.sleep

        def track_sleep(delay):
            delays.append(delay)

        call_count = 0

        @custom_retry(max_attempts=4, base_delay=0.1, exponential_base=2.0, max_jitter=0)
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("fail")

        with patch("time.sleep", track_sleep):
            with pytest.raises(ConnectionError):
                always_fail()

        # Attempt 1: delay = 0.1 * 2^0 = 0.1
        # Attempt 2: delay = 0.1 * 2^1 = 0.2
        # Attempt 3: delay = 0.1 * 2^2 = 0.4
        assert len(delays) == 3
        assert delays[0] == pytest.approx(0.1, abs=0.01)
        assert delays[1] == pytest.approx(0.2, abs=0.01)
        assert delays[2] == pytest.approx(0.4, abs=0.01)

    def test_max_delay_cap(self):
        """Delay should not exceed max_delay."""
        delays = []

        def track_sleep(delay):
            delays.append(delay)

        @custom_retry(
            max_attempts=5, base_delay=1.0, max_delay=1.5, exponential_base=10.0, max_jitter=0
        )
        def always_fail():
            raise ConnectionError("fail")

        with patch("time.sleep", track_sleep):
            with pytest.raises(ConnectionError):
                always_fail()

        for d in delays:
            assert d <= 1.5

    def test_jitter_adds_randomness(self):
        """Jitter should add a random component."""
        delays = []

        def track_sleep(delay):
            delays.append(delay)

        @custom_retry(max_attempts=3, base_delay=0.1, max_jitter=0.5, exponential_base=1.0)
        def always_fail():
            raise ConnectionError("fail")

        with patch("time.sleep", track_sleep):
            with pytest.raises(ConnectionError):
                always_fail()

        # With base=1.0 and jitter, delays should be >= 0.1
        for d in delays:
            assert d >= 0.1

    def test_preserves_function_metadata(self):
        """Decorator should preserve __name__ and __doc__."""

        @custom_retry(max_attempts=2)
        def documented():
            """My docstring."""
            return 42

        assert documented.__name__ == "documented"
        assert documented.__doc__ == "My docstring."


# ═══════════════════════════════════════════════════════════════════
# with_retry
# ═══════════════════════════════════════════════════════════════════


class TestWithRetry:
    """Test the with_retry decorator."""

    def test_llm_api_strategy_success(self):
        """LLM_API strategy with immediate success."""
        call_count = 0

        @with_retry(strategy=RetryStrategy.LLM_API)
        def call_llm():
            nonlocal call_count
            call_count += 1
            return "response"

        assert call_llm() == "response"
        assert call_count == 1

    def test_network_strategy_success(self):
        """NETWORK strategy with immediate success."""

        @with_retry(strategy=RetryStrategy.NETWORK)
        def fetch():
            return "data"

        assert fetch() == "data"

    def test_database_strategy_success(self):
        """DATABASE strategy with immediate success."""

        @with_retry(strategy=RetryStrategy.DATABASE)
        def query():
            return [1, 2, 3]

        assert query() == [1, 2, 3]

    def test_aggressive_strategy_success(self):
        """AGGRESSIVE strategy with immediate success."""

        @with_retry(strategy=RetryStrategy.AGGRESSIVE)
        def critical_op():
            return "done"

        assert critical_op() == "done"

    def test_gentle_strategy_success(self):
        """GENTLE strategy with immediate success."""

        @with_retry(strategy=RetryStrategy.GENTLE)
        def light_op():
            return "ok"

        assert light_op() == "ok"

    def test_custom_retryable_exceptions(self):
        """Custom exception tuple should be respected."""
        call_count = 0

        @with_retry(strategy=RetryStrategy.GENTLE, retryable_exceptions=(ValueError,))
        def raise_value_error():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("retry me")
            return "ok"

        assert raise_value_error() == "ok"
        assert call_count == 2

    def test_circuit_breaker_integration(self):
        """with_retry should integrate with circuit breaker."""
        call_count = 0

        @with_retry(strategy=RetryStrategy.GENTLE, circuit_breaker="test-cb-policy")
        def failing():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("fail")

        # First call: tenacity retries config["max_attempts"]=2 times.
        # CB wraps the inner function, so each tenacity retry calls CB wrapper.
        # CB records failure each time. After 2 failures, CB threshold=5 is not reached,
        # so CB stays CLOSED. Tenacity reraises after exhausting retries.
        with pytest.raises(ConnectionError):
            failing()

        # CB is still CLOSED (only 2 failures, threshold=5).
        # Next call will also retry and fail.
        with pytest.raises(ConnectionError):
            failing()

    def test_on_retry_callback_integration(self):
        """on_retry should be called via with_retry (only when HAS_TENACITY is False)."""
        from src.utils.retry.core import HAS_TENACITY

        retries = []

        def on_retry(exc, attempt):
            retries.append(attempt)

        call_count = 0

        @with_retry(strategy=RetryStrategy.GENTLE, on_retry=on_retry)
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("fail")
            return "ok"

        result = flaky()
        assert result == "ok"
        if HAS_TENACITY:
            # on_retry is only passed to custom_retry (fallback), not tenacity
            assert retries == []
        else:
            assert retries == [1]


# ═══════════════════════════════════════════════════════════════════
# Convenience partials
# ═══════════════════════════════════════════════════════════════════


class TestConveniencePartials:
    """Test retry_llm, retry_network, retry_db, retry_aggressive."""

    def test_retry_llm_applies_correct_strategy(self):
        call_count = 0

        @retry_llm()
        def call():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("fail")
            return "ok"

        assert call() == "ok"
        assert call_count == 2

    def test_retry_network_applies_correct_strategy(self):
        @retry_network()
        def call():
            return "data"

        assert call() == "data"

    def test_retry_db_applies_correct_strategy(self):
        @retry_db()
        def call():
            return "rows"

        assert call() == "rows"

    def test_retry_aggressive_applies_correct_strategy(self):
        call_count = 0

        @retry_aggressive()
        def call():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("fail")
            return "ok"

        assert call() == "ok"
        assert call_count == 2


# ═══════════════════════════════════════════════════════════════════
# retry_if_status_code
# ═══════════════════════════════════════════════════════════════════


class MockResponse:
    """Mock HTTP response for status code testing."""

    def __init__(self, status_code):
        self.status_code = status_code


class TestRetryIfStatusCode:
    """Test retry based on HTTP status codes."""

    def test_success_status_no_retry(self):
        """200 should not trigger retry."""
        call_count = 0

        @retry_if_status_code((429, 500))
        def api_call():
            nonlocal call_count
            call_count += 1
            return MockResponse(200)

        result = api_call()
        assert result.status_code == 200
        assert call_count == 1

    def test_retry_on_429(self):
        """429 should trigger retry, then success."""
        call_count = 0

        @retry_if_status_code((429, 500))
        def api_call():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return MockResponse(429)
            return MockResponse(200)

        result = api_call()
        assert result.status_code == 200
        assert call_count == 3

    def test_retry_on_500(self):
        """500 should trigger retry."""
        call_count = 0

        @retry_if_status_code((500,))
        def api_call():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                return MockResponse(500)
            return MockResponse(200)

        result = api_call()
        assert result.status_code == 200
        assert call_count == 2

    def test_all_attempts_exhausted_raises(self):
        """When all retries exhausted, tenacity raises RetryError."""
        call_count = 0

        @retry_if_status_code((429,))
        def api_call():
            nonlocal call_count
            call_count += 1
            return MockResponse(429)

        with pytest.raises(RetryError):
            api_call()
        assert call_count == 5  # stop_after_attempt(5)

    def test_custom_status_codes(self):
        """Custom status code tuple should be respected."""
        call_count = 0

        @retry_if_status_code((503, 504))
        def api_call():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                return MockResponse(503)
            return MockResponse(200)

        result = api_call()
        assert result.status_code == 200
        assert call_count == 2

    def test_no_status_code_attribute(self):
        """Objects without status_code should not trigger retry."""
        call_count = 0

        @retry_if_status_code((429,))
        def api_call():
            nonlocal call_count
            call_count += 1
            return {"data": "ok"}

        result = api_call()
        assert result == {"data": "ok"}
        assert call_count == 1

    def test_preserves_function_metadata(self):
        @retry_if_status_code((429,))
        def documented():
            """Docstring."""
            return MockResponse(200)

        assert documented.__name__ == "documented"
        assert documented.__doc__ == "Docstring."


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_with_retry_unknown_strategy_not_possible(self):
        """Enum prevents truly unknown strategies, but test behavior."""
        # This validates that all enum values have configs
        for strategy in RetryStrategy:
            assert strategy in RETRY_CONFIGS

    def test_custom_retry_zero_max_attempts(self):
        """max_attempts=1 means no retries."""
        call_count = 0

        @custom_retry(max_attempts=1)
        def fail():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("fail")

        with pytest.raises(ConnectionError):
            fail()

        assert call_count == 1

    def test_custom_retry_very_large_max_attempts(self):
        """Large max_attempts should still work."""
        call_count = 0

        @custom_retry(max_attempts=20, base_delay=0.001, max_jitter=0)
        def succeed_quickly():
            nonlocal call_count
            call_count += 1
            if call_count < 10:
                raise ConnectionError("fail")
            return "ok"

        assert succeed_quickly() == "ok"
        assert call_count == 10

    def test_retry_with_kwargs_passed_to_function(self):
        """Decorated functions should receive kwargs correctly."""

        @with_retry(strategy=RetryStrategy.GENTLE)
        def func_with_kwargs(a, b=None):
            return a + (b or 0)

        assert func_with_kwargs(1, b=2) == 3

    def test_retry_returns_non_primitive(self):
        """Decorated functions can return any type."""

        @with_retry(strategy=RetryStrategy.GENTLE)
        def return_dict():
            return {"key": [1, 2, 3]}

        assert return_dict() == {"key": [1, 2, 3]}

    def test_retry_if_status_code_with_exception(self):
        """If the decorated function raises an exception, it should propagate."""

        @retry_if_status_code((429,))
        def raise_exc():
            raise RuntimeError("unexpected")

        with pytest.raises(RuntimeError, match="unexpected"):
            raise_exc()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
