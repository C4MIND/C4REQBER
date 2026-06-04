"""
Cache configuration
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default

def _env_float(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        return default

@dataclass
class CacheConfig:
    """CacheConfig."""
    tier1_ttl: int = field(default_factory=lambda: _env_int("CACHE_TIER1_TTL", 3600))
    tier2_max_size: int = field(default_factory=lambda: _env_int("CACHE_TIER2_MAX_SIZE", 1000))
    tier2_default_ttl: int = field(default_factory=lambda: _env_int("CACHE_TIER2_TTL", 60))
    tier3_ttl: int = field(default_factory=lambda: _env_int("CACHE_TIER3_TTL", 300))
    tier3_lock_timeout: float = field(default_factory=lambda: _env_float("CACHE_TIER3_LOCK_TIMEOUT", 5.0))
    tier4_timeout: float = field(default_factory=lambda: _env_float("CACHE_TIER4_TIMEOUT", 30.0))
    tier4_retries: int = field(default_factory=lambda: _env_int("CACHE_TIER4_RETRIES", 3))
    tier4_retry_delay: float = field(default_factory=lambda: _env_float("CACHE_TIER4_RETRY_DELAY", 0.5))
    promotion_ttl_seconds: int = field(default_factory=lambda: _env_int("CACHE_PROMOTION_TTL", 30))
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
