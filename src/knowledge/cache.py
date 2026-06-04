from __future__ import annotations

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
