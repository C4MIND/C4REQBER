"""
Tier 1 Cache: Pre-populated seed data

Data is loaded ahead of time (e.g., via cron or startup hook)
and served with zero latency for hot keys.
"""

from __future__ import annotations

import time
from typing import Any


class SeedCache:
    """SeedCache."""
    def __init__(self) -> None:
        self._data: dict[str, dict[str, Any]] = {}

    def load(self, key: str, data: Any, ttl: int = 3600) -> None:
        self._data[key] = {
            "data": data,
            "loaded_at": time.time(),
            "ttl": ttl,
        }

    def get(self, key: str) -> Any | None:
        """Get."""
        entry = self._data.get(key)
        if entry is None:
            return None
        if time.time() - entry["loaded_at"] < entry["ttl"]:
            return entry["data"]
        del self._data[key]
        return None

    def is_fresh(self, key: str) -> bool:
        return self.get(key) is not None

    def expire(self, key: str) -> None:
        self._data.pop(key, None)

    def clear(self) -> None:
        self._data.clear()

    @property
    def size(self) -> int:
        return len(self._data)

    @property
    def keys(self) -> list[str]:
        return list(self._data.keys())
