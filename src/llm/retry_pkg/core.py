"""Retry Core.

Data structures, exceptions, and statistics for provider retry logic.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from src.llm.multi_provider import LLMResponse


# ═══════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════

RETRY_ENABLED = os.getenv("RETRY_ENABLED", "true").lower() in ("1", "true", "yes")
RETRY_MAX_ATTEMPTS = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
RETRY_BACKOFF_BASE = float(os.getenv("RETRY_BACKOFF_BASE", "1.0"))


# ═══════════════════════════════════════════════════════════════════
# STATISTICS
# ═══════════════════════════════════════════════════════════════════


@dataclass
class ProviderStats:
    """Per-provider retry statistics."""

    provider: str
    attempts: int = 0
    successes: int = 0
    failures: int = 0
    retries: int = 0
    total_latency_ms: float = 0.0
    last_error: str | None = None

    @property
    def success_rate(self) -> float:
        """Success rate."""
        if self.attempts == 0:
            return 0.0
        return self.successes / self.attempts

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "attempts": self.attempts,
            "successes": self.successes,
            "failures": self.failures,
            "retries": self.retries,
            "success_rate": round(self.success_rate, 3),
            "total_latency_ms": round(self.total_latency_ms, 2),
            "last_error": self.last_error,
        }


@dataclass
class RetryResult:
    """Result of a retry operation with metadata."""

    response: LLMResponse
    provider: str
    attempts: int
    provider_sequence_used: bool
    total_latency_ms: float


# ═══════════════════════════════════════════════════════════════════
# EXCEPTIONS
# ═══════════════════════════════════════════════════════════════════


class AllProvidersExhaustedError(Exception):
    """Raised when all providers have been tried and failed."""

    def __init__(self, stage: str, attempts: list[tuple[str, str]]) -> None:
        self.stage = stage
        self.attempts = attempts
        providers_tried = ", ".join(f"{p}: {e}" for p, e in attempts)
        super().__init__(f"All providers exhausted for stage '{stage}'. History: {providers_tried}")


class ProviderRetryError(Exception):
    """Raised when a single provider retry chain fails."""

    pass
