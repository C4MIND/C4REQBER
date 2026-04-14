"""
TURBO-CDI: Retry Utilities v4.0
Production-grade retry logic using Tenacity

Provides:
- Exponential backoff for LLM API calls
- Circuit breaker pattern for failing services
- Custom retry conditions for specific errors
"""

import functools
import random
import time
from typing import Callable, Optional, TypeVar, Any
from enum import Enum

# Try to import tenacity, fallback to custom implementation
try:
    from tenacity import (
        retry as tenacity_retry,
        stop_after_attempt,
        stop_after_delay,
        wait_exponential,
        wait_random,
        retry_if_exception_type,
        retry_if_result,
        before_sleep_log,
        RetryCallState,
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
    import requests

    RETRYABLE_EXCEPTIONS += (requests.RequestException,)
except ImportError:
    pass

try:
    import httpx

    RETRYABLE_EXCEPTIONS += (httpx.HTTPError,)
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
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
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

    def record_success(self):
        """Record successful execution."""
        self._failure_count = 0
        self._state = "CLOSED"

    def record_failure(self):
        """Record failed execution."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._failure_count >= self.failure_threshold:
            self._state = "OPEN"

    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap function with circuit breaker."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not self.can_execute():
                raise CircuitBreakerOpen(
                    f"Circuit breaker is OPEN for {func.__name__}. "
                    f"Service temporarily unavailable."
                )

            try:
                result = func(*args, **kwargs)
                self.record_success()
                return result
            except self.expected_exception as e:
                self.record_failure()
                raise e

        return wrapper


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open."""

    pass


# Global circuit breakers for different services
_circuit_breakers: dict = {}


def get_circuit_breaker(name: str, **kwargs) -> CircuitBreaker:
    """Get or create circuit breaker for a service."""
    global _circuit_breakers
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(**kwargs)
    return _circuit_breakers[name]


# ═══════════════════════════════════════════════════════════════════
# CUSTOM RETRY IMPLEMENTATION (Fallback if tenacity not available)
# ═══════════════════════════════════════════════════════════════════

T = TypeVar("T")


def custom_retry(
    max_attempts: int = 3,
    max_delay: float = 60.0,
    base_delay: float = 1.0,
    max_jitter: float = 0.5,
    exponential_base: float = 2.0,
    retryable_exceptions: tuple = RETRYABLE_EXCEPTIONS,
    on_retry: Optional[Callable[[Exception, int], None]] = None,
):
    """
    Custom retry decorator (fallback when tenacity unavailable).
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        break

                    # Calculate delay
                    delay = min(
                        base_delay * (exponential_base ** (attempt - 1)), max_delay
                    )
                    delay += random.uniform(0, max_jitter)

                    if on_retry:
                        on_retry(e, attempt)

                    time.sleep(delay)

            raise last_exception

        return wrapper

    return decorator


# ═══════════════════════════════════════════════════════════════════
# PRODUCTION DECORATORS
# ═══════════════════════════════════════════════════════════════════


def with_retry(
    strategy: RetryStrategy = RetryStrategy.LLM_API,
    retryable_exceptions: Optional[tuple] = None,
    on_retry: Optional[Callable[[Exception, int], None]] = None,
    circuit_breaker: Optional[str] = None,
):
    """
    Production-grade retry decorator.

    Usage:
        @with_retry(strategy=RetryStrategy.LLM_API)
        def call_openrouter(prompt):
            ...

        @with_retry(strategy=RetryStrategy.NETWORK, circuit_breaker="arxiv")
        def fetch_arxiv(query):
            ...
    """
    config = RETRY_CONFIGS[strategy]
    exceptions = retryable_exceptions or RETRYABLE_EXCEPTIONS

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Apply circuit breaker if specified
        if circuit_breaker:
            cb = get_circuit_breaker(circuit_breaker)
            func = cb(func)

        # Apply retry logic
        if HAS_TENACITY:
            # Use tenacity
            @tenacity_retry(
                stop=stop_after_attempt(config["max_attempts"]),
                wait=wait_exponential(
                    multiplier=config["base_delay"],
                    exp_base=config["exponential_base"],
                    max=config["max_delay"],
                )
                + wait_random(0, config["max_jitter"]),
                retry=retry_if_exception_type(exceptions),
                reraise=True,
            )
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> T:
                return func(*args, **kwargs)
        else:
            # Use custom implementation
            wrapper = custom_retry(
                max_attempts=config["max_attempts"],
                max_delay=config["max_delay"],
                base_delay=config["base_delay"],
                max_jitter=config["max_jitter"],
                exponential_base=config["exponential_base"],
                retryable_exceptions=exceptions,
                on_retry=on_retry,
            )(func)

        return wrapper

    return decorator


# Convenience decorators
retry_llm = functools.partial(with_retry, strategy=RetryStrategy.LLM_API)
retry_network = functools.partial(with_retry, strategy=RetryStrategy.NETWORK)
retry_db = functools.partial(with_retry, strategy=RetryStrategy.DATABASE)
retry_aggressive = functools.partial(with_retry, strategy=RetryStrategy.AGGRESSIVE)


# ═══════════════════════════════════════════════════════════════════
# RESULT-BASED RETRY (for HTTP status codes, etc.)
# ═══════════════════════════════════════════════════════════════════


def retry_if_status_code(status_codes: tuple = (429, 500, 502, 503, 504)):
    """
    Retry based on result (e.g., HTTP response status code).

    Usage:
        @retry_if_status_code((429, 500))
        def api_call() -> Response:
            return requests.get(url)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        if HAS_TENACITY:

            @tenacity_retry(
                stop=stop_after_attempt(5),
                wait=wait_exponential(multiplier=1, max=60),
                retry=retry_if_result(
                    lambda r: hasattr(r, "status_code")
                    and r.status_code in status_codes
                ),
                reraise=True,
            )
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> T:
                return func(*args, **kwargs)
        else:

            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> T:
                last_result = None
                for attempt in range(5):
                    result = func(*args, **kwargs)
                    last_result = result

                    if (
                        hasattr(result, "status_code")
                        and result.status_code in status_codes
                    ):
                        if attempt < 4:
                            delay = min(2**attempt, 60)
                            time.sleep(delay)
                            continue

                    return result

                return last_result

        return wrapper

    return decorator


# ═══════════════════════════════════════════════════════════════════
# MONITORING & METRICS
# ═══════════════════════════════════════════════════════════════════


class RetryMetrics:
    """Track retry statistics for monitoring."""

    def __init__(self):
        self.total_attempts = 0
        self.successful_first_try = 0
        self.successful_after_retry = 0
        self.failed_after_max_retries = 0
        self.attempts_histogram: dict = {}

    def record_attempt(self, attempts: int, success: bool):
        """Record an attempt."""
        self.total_attempts += attempts
        self.attempts_histogram[attempts] = self.attempts_histogram.get(attempts, 0) + 1

        if success:
            if attempts == 1:
                self.successful_first_try += 1
            else:
                self.successful_after_retry += 1
        else:
            self.failed_after_max_retries += 1

    @property
    def retry_rate(self) -> float:
        """Percentage of calls that needed retry."""
        total = (
            self.successful_first_try
            + self.successful_after_retry
            + self.failed_after_max_retries
        )
        if total == 0:
            return 0.0
        return (self.successful_after_retry + self.failed_after_max_retries) / total

    @property
    def success_rate(self) -> float:
        """Percentage of calls that eventually succeeded."""
        total = (
            self.successful_first_try
            + self.successful_after_retry
            + self.failed_after_max_retries
        )
        if total == 0:
            return 0.0
        return (self.successful_first_try + self.successful_after_retry) / total

    def report(self) -> dict:
        """Generate report."""
        return {
            "total_attempts": self.total_attempts,
            "successful_first_try": self.successful_first_try,
            "successful_after_retry": self.successful_after_retry,
            "failed_after_max_retries": self.failed_after_max_retries,
            "retry_rate": round(self.retry_rate, 4),
            "success_rate": round(self.success_rate, 4),
            "attempts_histogram": self.attempts_histogram,
        }


# Global metrics instance
_retry_metrics = RetryMetrics()


def get_retry_metrics() -> RetryMetrics:
    """Get global retry metrics."""
    return _retry_metrics


# ═══════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════


def check_retry_system_health() -> dict:
    """Check health of retry system."""
    return {
        "tenacity_available": HAS_TENACITY,
        "circuit_breakers": {
            name: {
                "state": cb.state,
                "failure_count": cb._failure_count,
            }
            for name, cb in _circuit_breakers.items()
        },
        "metrics": _retry_metrics.report(),
    }
