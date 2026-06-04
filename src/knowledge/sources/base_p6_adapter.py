"""
Bridge between BaseSourceAdapter interface and BaseP6Client infrastructure.

Provides: source_id, search(), _normalize() pattern of BaseSourceAdapter
PLUS: TTL cache, connection pooling, client registry, graceful shutdown from BaseP6Client.
"""
from __future__ import annotations

import abc
import asyncio
import logging
from typing import Any

from .base_p6 import BaseP6Client

logger = logging.getLogger("c4reqber.knowledge.base_p6_adapter")


class BaseP6SourceAdapter(BaseP6Client, abc.ABC):
    """Async source adapter with P6 infrastructure (cache, pool, registry).

    Subclasses must define ``BASE_URL`` and implement ``source_id`` + ``search``.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        cache_ttl: float | None = None,
    ) -> None:
        self.api_key = api_key
        merged_headers: dict[str, str] = dict(headers or {})
        if api_key and "Authorization" not in merged_headers:
            # Most APIs accept this; override in subclass if needed.
            merged_headers["Authorization"] = f"Bearer {api_key}"
        super().__init__(headers=merged_headers, timeout=timeout, cache_ttl=cache_ttl)

    @property
    @abc.abstractmethod
    def source_id(self) -> str:
        """Return the source identifier (e.g. 'openalex')."""

    @abc.abstractmethod
    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Search the source and return normalized paper records."""

    @abc.abstractmethod
    def _normalize(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize raw API response into unified paper record format."""

    async def _get_with_retry(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        use_cache: bool = True,
        max_retries: int = 3,
        base_delay: float = 1.0,
    ) -> dict[str, Any]:
        """GET with exponential-backoff retry on 429/5xx."""
        last_exc: Exception | None = None
        for attempt in range(max_retries):
            try:
                return await self._get(path, params=params, use_cache=use_cache)
            except Exception as exc:
                last_exc = exc
                status = getattr(exc, "response", None)
                status_code = status.status_code if status else 0
                if status_code == 429 or (500 <= status_code < 600):
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        "%s: retry %d/%d after %ds (HTTP %s)",
                        self.source_id,
                        attempt + 1,
                        max_retries,
                        delay,
                        status_code,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise
        if last_exc:
            raise last_exc
        return {}
