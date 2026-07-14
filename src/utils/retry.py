"""C4REQBER: Retry Utilities v4.0
Production-grade retry logic using Tenacity

DEPRECATED: This module has been split into submodules.
Import from utils.retry instead.
"""
from __future__ import annotations

# Thin wrapper — re-export from new submodules for backward compatibility
from src.utils.retry.core import (
    HAS_TENACITY,
    RETRY_CONFIGS,
    RETRYABLE_EXCEPTIONS,
    CircuitBreaker,
    CircuitBreakerOpen,
    RetryStrategy,
    get_circuit_breaker,
)
from src.utils.retry.policies import (
    custom_retry,
    retry_aggressive,
    retry_db,
    retry_if_status_code,
    retry_llm,
    retry_network,
    with_retry,
)
from src.utils.retry.utils import (
    RetryMetrics,
    check_retry_system_health,
    get_retry_metrics,
)


__all__ = [
    "HAS_TENACITY",
    "RETRY_CONFIGS",
    "RETRYABLE_EXCEPTIONS",
    "CircuitBreaker",
    "CircuitBreakerOpen",
    "RetryStrategy",
    "get_circuit_breaker",
    "custom_retry",
    "retry_aggressive",
    "retry_db",
    "retry_if_status_code",
    "retry_llm",
    "retry_network",
    "with_retry",
    "RetryMetrics",
    "check_retry_system_health",
    "get_retry_metrics",
]
