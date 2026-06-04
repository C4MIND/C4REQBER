"""
Tier 2 Cache: In-memory LRU

Fast read-through cache with bounded memory footprint.
Entries expire after default_ttl seconds.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from typing import Any


class MemoryCache:
    """MemoryCache."""
    def __init__(self, max_size: int = 1000, default_ttl: int = 60) -> None:
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Any | None:
        """Get."""
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry["ts"] < entry["ttl"]:
                self._cache.move_to_end(key)
                self._hits += 1
                return entry["data"]
            del self._cache[key]
        self._misses += 1
        return None

    def set(self, key: str, data: Any, ttl: int | None = None) -> None:
        """Set."""
        if key in self._cache:
            self._cache.move_to_end(key)
        elif len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)
        self._cache[key] = {
            "data": data,
            "ts": time.time(),
            "ttl": ttl if ttl is not None else self.default_ttl,
        }

    def delete(self, key: str) -> None:
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def ttl(self, key: str) -> float | None:
        """Return remaining TTL in seconds, or None if absent/expired."""
        entry = self._cache.get(key)
        if entry is None:
            return None
        elapsed = time.time() - entry["ts"]
        remaining = entry["ttl"] - elapsed
        return remaining if remaining > 0 else None

    @property
    def size(self) -> int:
        return len(self._cache)

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
        }

    @property
    def keys(self) -> list[str]:
        return list(self._cache.keys())
