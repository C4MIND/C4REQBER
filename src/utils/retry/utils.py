"""Retry utilities — monitoring and health check."""
from __future__ import annotations

from typing import Any

from .core import HAS_TENACITY, _circuit_breakers


class RetryMetrics:
    """Track retry statistics for monitoring."""

    def __init__(self) -> None:
        self.total_attempts = 0
        self.successful_first_try = 0
        self.successful_after_retry = 0
        self.failed_after_max_retries = 0
        self.attempts_histogram: dict[str, Any] = {}

    def record_attempt(self, attempts: int, success: bool) -> None:
        """Record an attempt."""
        self.total_attempts += attempts
        self.attempts_histogram[attempts] = self.attempts_histogram.get(attempts, 0) + 1  # type: ignore[call-overload, index]

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

    def report(self) -> dict[str, Any]:
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


def check_retry_system_health() -> dict[str, Any]:
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
