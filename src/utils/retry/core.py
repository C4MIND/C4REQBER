"""C4REQBER: Retry Utilities v4.0 — Core
Production-grade retry logic using Tenacity
"""
from __future__ import annotations

import functools
import time
from collections.abc import Callable
from enum import Enum
from typing import Any


# Try to import tenacity, fallback to custom implementation
try:
    from tenacity import (
        RetryCallState,
        before_sleep_log,
        retry_if_exception_type,
        retry_if_result,
        stop_after_attempt,
        stop_after_delay,
        wait_exponential,
        wait_random,
    )
    from tenacity import (
        retry as tenacity_retry,
    )

    HAS_TENACITY = True
except ImportError:
    HAS_TENACITY = False
    print("⚠️  Tenacity not installed. Using custom retry implementation.")


class RetryStrategy(Enum):
    """Predefined retry strategies."""

    LLM_API = "llm_api"  # For OpenRouter/LLM calls
    NETWORK = "network"  # For network requests
    DATABASE = "database"  # For DB operations
    AGGRESSIVE = "aggressive"  # For critical operations
    GENTLE = "gentle"  # For non-critical operations


# Strategy configurations
RETRY_CONFIGS = {
    RetryStrategy.LLM_API: {
        "max_attempts": 5,
        "max_delay": 60,
        "base_delay": 1,
        "max_jitter": 1,
        "exponential_base": 2,
    },
    RetryStrategy.NETWORK: {
        "max_attempts": 3,
        "max_delay": 30,
        "base_delay": 1,
        "max_jitter": 0.5,
        "exponential_base": 2,
    },
    RetryStrategy.DATABASE: {
        "max_attempts": 3,
        "max_delay": 10,
        "base_delay": 0.5,
        "max_jitter": 0.2,
        "exponential_base": 1.5,
    },
    RetryStrategy.AGGRESSIVE: {
        "max_attempts": 10,
        "max_delay": 300,
        "base_delay": 1,
        "max_jitter": 2,
        "exponential_base": 2,
    },
    RetryStrategy.GENTLE: {
        "max_attempts": 2,
        "max_delay": 5,
        "base_delay": 0.5,
        "max_jitter": 0.5,
        "exponential_base": 1.5,
    },
}


# Custom exceptions that should trigger retry
RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    OSError,
)

try:
    import requests  # type: ignore[import-untyped]

    RETRYABLE_EXCEPTIONS += (requests.RequestException,)  # type: ignore[assignment]
except ImportError:
    pass

try:
    import httpx

    RETRYABLE_EXCEPTIONS += (httpx.HTTPError,)  # type: ignore[assignment]
except ImportError:
    pass


class CircuitBreaker:
    """
    Circuit breaker pattern for failing services.

    States:
    - CLOSED: Normal operation
    - OPEN: Failing fast, no calls allowed
    - HALF_OPEN: Testing if service recovered
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exception: type = Exception,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self._failure_count = 0
        self._last_failure_time: float | None = None
        self._state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self._lock = None

    @property
    def state(self) -> str:
        """Get current circuit state."""
        if self._state == "OPEN":
            # Check if we should try half-open
            if (
                self._last_failure_time
                and (time.time() - self._last_failure_time) > self.recovery_timeout
            ):
                self._state = "HALF_OPEN"
                return "HALF_OPEN"
        return self._state

    def can_execute(self) -> bool:
        """Check if execution is allowed."""
        state = self.state
        return state in ("CLOSED", "HALF_OPEN")

    def record_success(self) -> None:
        """Record successful execution."""
        self._failure_count = 0
        self._state = "CLOSED"

    def record_failure(self) -> None:
        """Record failed execution."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._failure_count >= self.failure_threshold:
            self._state = "OPEN"

    def __call__(self, func: Callable) -> Callable:  # type: ignore[type-arg]
        """Decorator to wrap function with circuit breaker."""

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> None:
            """Wrapper."""
            if not self.can_execute():
                raise CircuitBreakerOpen(
                    f"Circuit breaker is OPEN for {func.__name__}. "
                    f"Service temporarily unavailable."
                )

            try:
                result = func(*args, **kwargs)
                self.record_success()
                return result  # type: ignore[no-any-return]
            except self.expected_exception as e:  # type: ignore[misc]
                self.record_failure()
                raise e

        return wrapper


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open."""

    pass


# Global circuit breakers for different services
_circuit_breakers: dict[str, Any] = {}


def get_circuit_breaker(name: str, **kwargs: Any) -> CircuitBreaker:
    """Get or create circuit breaker for a service."""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(**kwargs)
    return _circuit_breakers[name]  # type: ignore[no-any-return]
