"""LLM error types — rate limits and provider exhaustion."""

from __future__ import annotations


class RateLimited(Exception):
    """HTTP 429 / provider rate limit — rotate or surface partial, never fake success."""

    def __init__(
        self,
        message: str = "Rate limited by LLM provider",
        *,
        retry_after: float | None = None,
        provider: str = "",
    ) -> None:
        self.retry_after = retry_after
        self.provider = provider
        detail = message
        if provider:
            detail = f"{provider}: {message}"
        if retry_after is not None:
            detail = f"{detail} (retry after {retry_after}s)"
        super().__init__(detail)
