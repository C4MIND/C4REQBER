"""
C4REQBER: Sentry Integration
Error tracking and performance monitoring.
"""
from __future__ import annotations

import os
from typing import Any


class SentryManager:
    """Manages Sentry integration for error tracking."""

    def __init__(self, dsn: str | None = None, environment: str = "development") -> None:
        self.dsn = dsn or os.getenv("SENTRY_DSN")
        self.environment = environment
        self._initialized = False

    def init(self) -> bool:
        """Initialize Sentry SDK."""
        if not self.dsn:
            print("⚠️  SENTRY_DSN not set. Sentry disabled.")
            return False

        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.redis import RedisIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

            sentry_sdk.init(
                dsn=self.dsn,
                environment=self.environment,
                traces_sample_rate=0.1,  # 10% of transactions
                profiles_sample_rate=0.01,  # 1% profiling
                integrations=[
                    FastApiIntegration(),
                    RedisIntegration(),
                    SqlalchemyIntegration(),
                ],
                before_send=self._before_send,
            )

            self._initialized = True
            print(f"✅ Sentry initialized ({self.environment})")
            return True

        except ImportError:
            print("⚠️  sentry-sdk not installed. Run: pip install sentry-sdk[fastapi]")
            return False

    def _before_send(self, event: dict[str, Any], hint: dict[str, Any]) -> dict | None:  # type: ignore[type-arg]
        """Filter events before sending to Sentry."""
        # Don't send events in development unless explicitly enabled
        if self.environment == "development" and not os.getenv("SENTRY_DEV"):
            return None

        # Filter out specific errors
        if "exc_info" in hint:
            exc_type, exc_value, _ = hint["exc_info"]
            if exc_type and exc_type.__name__ in ("HTTPException", "ValidationError"):
                # Don't track 4xx errors
                return None

        return event

    def capture_exception(self, exc: Exception, **context: Any) -> str | None:
        """Capture an exception with context."""
        if not self._initialized:
            return None

        try:
            import sentry_sdk
            with sentry_sdk.push_scope() as scope:
                for key, value in context.items():
                    scope.set_extra(key, value)
                return sentry_sdk.capture_exception(exc)  # type: ignore[no-any-return]
        except ImportError:
            return None

    def capture_message(self, message: str, level: str = "info") -> str | None:
        """Capture a message."""
        if not self._initialized:
            return None

        try:
            import sentry_sdk
            return sentry_sdk.capture_message(message, level=level)  # type: ignore[no-any-return]
        except ImportError:
            return None


def get_sentry() -> SentryManager:
    """Get singleton Sentry manager (backed by DI container)."""
    from src.di.container import get_container
    return get_container().get_or_register("sentry", SentryManager)
