"""Retry policies and decorators."""
from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any, TypeVar

from .core import (
    HAS_TENACITY,
    RETRY_CONFIGS,
    RETRYABLE_EXCEPTIONS,
    RetryStrategy,
    get_circuit_breaker,
)


if HAS_TENACITY:
    from tenacity import (
        retry as tenacity_retry,
    )
    from tenacity import (
        retry_if_exception_type,
        retry_if_result,
        stop_after_attempt,
        wait_exponential,
        wait_random,
    )

T = TypeVar("T")


def custom_retry(
    max_attempts: int = 3,
    max_delay: float = 60.0,
    base_delay: float = 1.0,
    max_jitter: float = 0.5,
    exponential_base: float = 2.0,
    retryable_exceptions: tuple[Any, ...] = RETRYABLE_EXCEPTIONS,
    on_retry: Callable[[Exception, int], None] | None = None,
) -> Any:
    """
    Custom retry decorator (fallback when tenacity unavailable).
    """
    import random
    import time

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        """Decorator."""
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            """Wrapper."""
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

            raise last_exception  # type: ignore[misc]

        return wrapper

    return decorator


def with_retry(
    strategy: RetryStrategy = RetryStrategy.LLM_API,
    retryable_exceptions: tuple | None = None,  # type: ignore[type-arg]
    on_retry: Callable[[Exception, int], None] | None = None,
    circuit_breaker: str | None = None,
) -> Any:
    """
    Production-grade retry decorator.

    Usage:
        @with_retry(strategy=RetryStrategy.LLM_API)
        def call_openrouter(prompt) -> str:
            ...

        @with_retry(strategy=RetryStrategy.NETWORK, circuit_breaker="arxiv")
        def fetch_arxiv(query) -> dict[str, Any]:
            ...
    """
    config = RETRY_CONFIGS[strategy]
    exceptions = retryable_exceptions or RETRYABLE_EXCEPTIONS

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Apply circuit breaker if specified
        """Decorator."""
        if circuit_breaker:
            cb = get_circuit_breaker(circuit_breaker)
            func = cb(func)

        # Apply retry logic
        if HAS_TENACITY:
            # Use tenacity
            @tenacity_retry(
                stop=stop_after_attempt(config["max_attempts"]),  # type: ignore[index]
                wait=wait_exponential(
                    multiplier=config["base_delay"],  # type: ignore[index]
                    exp_base=config["exponential_base"],  # type: ignore[index]
                    max=config["max_delay"],  # type: ignore[index]
                )
                + wait_random(0, config["max_jitter"]),  # type: ignore[index]
                retry=retry_if_exception_type(exceptions),
                reraise=True,
            )
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> T:
                return func(*args, **kwargs)
        else:
            # Use custom implementation
            wrapper = custom_retry(
                max_attempts=config["max_attempts"],  # type: ignore[index]
                max_delay=config["max_delay"],  # type: ignore[index]
                base_delay=config["base_delay"],  # type: ignore[index]
                max_jitter=config["max_jitter"],  # type: ignore[index]
                exponential_base=config["exponential_base"],  # type: ignore[index]
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


def retry_if_status_code(status_codes: tuple[Any, ...] = (429, 500, 502, 503, 504)) -> Any:
    """
    Retry based on result (e.g., HTTP response status code).

    Usage:
        @retry_if_status_code((429, 500))
        def api_call() -> Response:
            return requests.get(url)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        """Decorator."""
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
            def wrapper(*args: Any, **kwargs: Any) -> T:
                return func(*args, **kwargs)
        else:
            import time

            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> T:
                """Wrapper."""
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

                return last_result  # type: ignore[return-value]

        return wrapper

    return decorator
