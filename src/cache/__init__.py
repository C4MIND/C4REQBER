"""
c4-cdi-turbo: 4-Tier Cache System

Tier 1: SeedCache — Pre-populated seed data, refreshed via cron
Tier 2: MemoryCache — In-memory LRU with configurable TTL
Tier 3: RedisCache — Redis with stampede protection
Tier 4: UpstreamCache — Fallback to upstream API/compute

Orchestration: CacheOrchestrator — Multi-tier read-through with promotion
"""

from __future__ import annotations

from src.cache.config import CacheConfig
from src.cache.orchestrator import CacheOrchestrator
from src.cache.tier1_seed import SeedCache
from src.cache.tier2_memory import MemoryCache
from src.cache.tier3_redis import RedisCache
from src.cache.tier4_upstream import UpstreamCache


__all__ = [
    "CacheConfig",
    "SeedCache",
    "MemoryCache",
    "RedisCache",
    "UpstreamCache",
    "CacheOrchestrator",
]
