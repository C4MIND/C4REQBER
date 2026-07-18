from __future__ import annotations

import logging


logger = logging.getLogger(__name__)

import time
from collections import OrderedDict
from typing import Any


class SearchCache:
    """Simple dict-based TTL cache for search results with max size and LRU eviction."""

    def __init__(self, enabled: bool = True, ttl: float = 300.0, max_size: int = 1000) -> None:
        self.enabled = enabled
        self.ttl = ttl
        self.max_size = max_size
        self._store: OrderedDict[str, tuple[Any, float]] = OrderedDict()

    def get(self, key: str) -> Any | None:
        """Get."""
        if not self.enabled:
            return None
        entry = self._store.get(key)
        if entry is None:
            return None
        value, timestamp = entry
        if time.monotonic() - timestamp > self.ttl:
            self._store.pop(key, None)
            return None
        # Promote to MRU
        self._store.move_to_end(key)
        # Audit 2026-06-22: best-effort Prometheus hit counter. CACHE_MISSES
        # is intentionally NOT incremented here — misses are too noisy (every
        # fresh search is a miss). Operators wanting miss rate can compute
        # (queries - hits) from logs.
        try:
            from src.api.routers.metrics import CACHE_HITS

            CACHE_HITS.labels(cache_type="search").inc()
        except Exception as _exc:
            logger.debug("swallowed exception: %s", _exc, exc_info=True)
        return value

    def set(self, key: str, value: Any) -> None:
        """Set."""
        if not self.enabled:
            return
        # Evict oldest if at capacity
        if len(self._store) >= self.max_size and key not in self._store:
            oldest = next(iter(self._store))
            self._store.pop(oldest, None)
        self._store[key] = (value, time.monotonic())
        self._store.move_to_end(key)

    def clear(self) -> None:
        self._store.clear()

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)
