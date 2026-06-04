"""
Tier 4 Cache: Upstream API / compute fallback

Calls an upstream factory function with retries and timeout.
This is the slowest tier — used only when all caches miss.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import anyio


class UpstreamCache:
    """UpstreamCache."""
    def __init__(
        self,
        timeout: float = 30.0,
        retries: int = 3,
        retry_delay: float = 0.5,
    ) -> None:
        self.timeout = timeout
        self.retries = retries
        self.retry_delay = retry_delay
        self._call_count = 0
        self._error_count = 0

    async def fetch(
        self,
        factory: Callable[[], Awaitable[Any]],
    ) -> Any:
        """
        Call the upstream factory with retries and timeout.

        Raises the last exception if all retries are exhausted.
        Raises TimeoutError if all attempts time out.
        """
        last_exc: Exception | None = None
        for attempt in range(self.retries):
            try:
                self._call_count += 1
                with anyio.fail_after(self.timeout):
                    return await factory()
            except TimeoutError:
                last_exc = TimeoutError(
                    f"Upstream timed out after {self.timeout}s "
                    f"(attempt {attempt + 1}/{self.retries})"
                )
                self._error_count += 1
            except Exception as exc:
                last_exc = exc
                self._error_count += 1
            if attempt < self.retries - 1:
                await anyio.sleep(self.retry_delay * (2 ** attempt))
        raise last_exc  # type: ignore[misc]

    async def fetch_with_default(
        self,
        factory: Callable[[], Awaitable[Any]],
        default: Any = None,
    ) -> Any:
        """
        Call the upstream factory. Return *default* on any failure.
        """
        try:
            return await self.fetch(factory)
        except (TimeoutError, RuntimeError):
            return default

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "calls": self._call_count,
            "errors": self._error_count,
            "timeout": self.timeout,
            "retries": self.retries,
        }
