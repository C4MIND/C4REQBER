from __future__ import annotations

import time

import pytest

from src.pipeline.provider_coordinator import (
    PROVIDER_TEMPLATES,
    ProviderAwareCoordinator,
    ProviderSlot,
)


class TestProviderSlot:
    def test_can_accept_when_available_and_under_limits(self) -> None:
        slot = ProviderSlot(
            name="test", url="http://localhost", api_key="k", tier="local",
            rate_limit_per_min=100, concurrent_limit=10, cost_per_1k=0.0,
        )
        assert slot.can_accept() is True

    def test_can_accept_false_when_not_available(self) -> None:
        slot = ProviderSlot(
            name="test", url="http://localhost", api_key="k", tier="local",
            rate_limit_per_min=100, concurrent_limit=10, cost_per_1k=0.0,
            available=False,
        )
        assert slot.can_accept() is False

    def test_can_accept_false_when_at_concurrent_limit(self) -> None:
        slot = ProviderSlot(
            name="test", url="http://localhost", api_key="k", tier="local",
            rate_limit_per_min=100, concurrent_limit=3, cost_per_1k=0.0,
            active_pipelines=3,
        )
        assert slot.can_accept() is False

    def test_can_accept_false_when_at_rate_limit(self) -> None:
        slot = ProviderSlot(
            name="test", url="http://localhost", api_key="k", tier="local",
            rate_limit_per_min=3, concurrent_limit=10, cost_per_1k=0.0,
            _call_times=[time.time()] * 3,
        )
        assert slot.can_accept() is False

    def test_can_accept_prunes_old_call_times(self) -> None:
        slot = ProviderSlot(
            name="test", url="http://localhost", api_key="k", tier="local",
            rate_limit_per_min=3, concurrent_limit=10, cost_per_1k=0.0,
            _call_times=[time.time() - 61, time.time() - 62],  # both older than 60s
        )
        assert slot.can_accept() is True

    def test_acquire_increments_active_pipelines(self) -> None:
        slot = ProviderSlot(
            name="test", url="http://localhost", api_key="k", tier="local",
            rate_limit_per_min=100, concurrent_limit=10, cost_per_1k=0.0,
        )
        assert slot.active_pipelines == 0
        slot.acquire()
        assert slot.active_pipelines == 1
        slot.acquire()
        assert slot.active_pipelines == 2

    def test_acquire_appends_call_time(self) -> None:
        slot = ProviderSlot(
            name="test", url="http://localhost", api_key="k", tier="local",
            rate_limit_per_min=100, concurrent_limit=10, cost_per_1k=0.0,
        )
        before = len(slot._call_times)
        slot.acquire()
        assert len(slot._call_times) == before + 1

    def test_release_decrements_active_pipelines(self) -> None:
        slot = ProviderSlot(
            name="test", url="http://localhost", api_key="k", tier="local",
            rate_limit_per_min=100, concurrent_limit=10, cost_per_1k=0.0,
            active_pipelines=5,
        )
        slot.release()
        assert slot.active_pipelines == 4
        slot.release()
        assert slot.active_pipelines == 3

    def test_release_does_not_go_below_zero(self) -> None:
        slot = ProviderSlot(
            name="test", url="http://localhost", api_key="k", tier="local",
            rate_limit_per_min=100, concurrent_limit=10, cost_per_1k=0.0,
            active_pipelines=0,
        )
        slot.release()
        assert slot.active_pipelines == 0

    def test_load_pct_calculation(self) -> None:
        slot = ProviderSlot(
            name="test", url="http://localhost", api_key="k", tier="local",
            rate_limit_per_min=100, concurrent_limit=4, cost_per_1k=0.0,
            active_pipelines=2,
        )
        assert slot.load_pct == 0.5

    def test_load_pct_zero_when_no_active(self) -> None:
        slot = ProviderSlot(
            name="test", url="http://localhost", api_key="k", tier="local",
            rate_limit_per_min=100, concurrent_limit=4, cost_per_1k=0.0,
            active_pipelines=0,
        )
        assert slot.load_pct == 0.0

    def test_load_pct_one_when_full(self) -> None:
        slot = ProviderSlot(
            name="test", url="http://localhost", api_key="k", tier="local",
            rate_limit_per_min=100, concurrent_limit=5, cost_per_1k=0.0,
            active_pipelines=5,
        )
        assert slot.load_pct == 1.0


class TestProviderTemplates:
    def test_has_expected_providers(self) -> None:
        assert "openrouter" in PROVIDER_TEMPLATES
        assert "together" in PROVIDER_TEMPLATES
        assert "groq" in PROVIDER_TEMPLATES
        assert "mlx" in PROVIDER_TEMPLATES

    def test_local_tier_has_zero_cost(self) -> None:
        for name in ("mlx", "lm_studio", "ollama"):
            assert PROVIDER_TEMPLATES[name]["cost_per_1k"] == 0.0
            assert PROVIDER_TEMPLATES[name]["tier"] == "local"

    def test_mlx_has_high_rate_limit(self) -> None:
        assert PROVIDER_TEMPLATES["mlx"]["rate_limit_per_min"] == 999

    def test_deepseek_has_balanced_tier(self) -> None:
        assert PROVIDER_TEMPLATES["deepseek"]["tier"] == "balanced"


class TestProviderAwareCoordinator:
    def test_constructor_initializes_slots(self) -> None:
        coordinator = ProviderAwareCoordinator(budget_limit=0.0, mode="auto")
        assert hasattr(coordinator, "_slots")
        assert isinstance(coordinator._slots, dict)

    def test_available_tiers_returns_list(self) -> None:
        coordinator = ProviderAwareCoordinator(budget_limit=0.0, mode="auto")
        tiers = coordinator.available_tiers()
        assert isinstance(tiers, list)

    def test_total_concurrent_capacity_returns_int(self) -> None:
        coordinator = ProviderAwareCoordinator(budget_limit=0.0, mode="auto")
        capacity = coordinator.total_concurrent_capacity()
        assert isinstance(capacity, int)
        assert capacity >= 0

    def test_best_provider_for_tier_returns_none_when_empty(self) -> None:
        coordinator = ProviderAwareCoordinator(budget_limit=0.0, mode="auto")
        coordinator._slots.clear()
        result = coordinator.best_provider_for_tier("premium")
        assert result is None

    def test_dashboard_returns_string(self) -> None:
        coordinator = ProviderAwareCoordinator(budget_limit=0.0, mode="auto")
        dashboard = coordinator.dashboard()
        assert isinstance(dashboard, str)
        assert "Provider Dashboard" in dashboard
