"""
Full end-to-end integration tests for the 4-tier cache system.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.cache.orchestrator import CacheOrchestrator


pytestmark = pytest.mark.anyio(backend="asyncio")


class TestCacheIntegration:
    async def test_full_flow_tier1_to_tier4(self):
        """Walk through all tiers: miss 1,2,3 → compute via 4 → cache in all tiers."""
        orchestrator = CacheOrchestrator()
        factory = AsyncMock(return_value="gold")

        key = "integration_key"
        result = await orchestrator.get_or_compute(key, factory)
        assert result == "gold"
        factory.assert_called_once()

        result_tier1 = orchestrator.tier1.get(key)
        assert result_tier1 is None

        result_tier2 = orchestrator.tier2.get(key)
        assert result_tier2 == "gold"

        result_tier3 = await orchestrator.tier3.get(key)
        assert result_tier3 == "gold"

    async def test_tier1_blocks_deeper_lookups(self):
        orchestrator = CacheOrchestrator()
        orchestrator.seed_tier1("pk", "primary")
        orchestrator.tier2.set("pk", "stale")
        await orchestrator.tier3.set("pk", "also_stale")

        result = await orchestrator.get("pk")
        assert result == "primary"

    async def test_stampede_protection_end_to_end(self):
        """Sequential stampede: first call computes, second call hits cache."""
        orchestrator = CacheOrchestrator()

        compute_count = [0]

        async def factory():
            compute_count[0] += 1
            return "computed"

        r1 = await orchestrator.get_or_compute("stampede", factory)
        r2 = await orchestrator.get_or_compute("stampede", factory)
        assert r1 == "computed"
        assert r2 == "computed"
        assert compute_count[0] == 1

    async def test_invalidate_then_recompute(self):
        orchestrator = CacheOrchestrator()
        orchestrator.seed_tier1("a", 1)
        orchestrator.invalidate("a")
        assert await orchestrator.get("a") is None

        factory = AsyncMock(return_value=99)
        result = await orchestrator.get_or_compute("a", factory)
        assert result == 99
        factory.assert_called_once()

    async def test_clear_all_then_recompute(self):
        orchestrator = CacheOrchestrator()
        orchestrator.seed_tier1("a", 1)
        orchestrator.tier2.set("b", 2)
        await orchestrator.tier3.set("c", 3)
        await orchestrator.clear_all()
        assert await orchestrator.get("a") is None
        assert await orchestrator.get("b") is None
        assert await orchestrator.get("c") is None
