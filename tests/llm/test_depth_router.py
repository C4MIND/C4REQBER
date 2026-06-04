from __future__ import annotations

import pytest

from src.llm.depth_router import DepthBasedRouter


class TestDepthBasedRouter:
    def test_route_cheap_zero(self):
        result = DepthBasedRouter.route(0, "cheap")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_route_for_stage_one_balanced(self):
        result = DepthBasedRouter.route_for_stage(1, "balanced")
        expected = DepthBasedRouter.route(1, "balanced")
        assert result == expected
        assert isinstance(result, str)

    def test_route_for_stage_twelve_premium(self):
        result = DepthBasedRouter.route_for_stage(12, "premium")
        expected = DepthBasedRouter.route(3, "premium")
        assert result == expected
        assert isinstance(result, str)

    def test_estimate_cost_valid_inputs(self):
        cost = DepthBasedRouter.estimate_cost([1, 5, 9], "balanced", tokens_per_stage=4000)
        assert isinstance(cost, float)
        assert cost > 0.0

    def test_cost_badge_formatted_strings(self):
        cheap = DepthBasedRouter.cost_badge(0.05)
        assert "[green]" in cheap
        assert "$0.0500" in cheap

        mid = DepthBasedRouter.cost_badge(0.25)
        assert "[yellow]" in mid
        assert "$0.2500" in mid

        high = DepthBasedRouter.cost_badge(1.0)
        assert "[red]" in high
        assert "$1.0000" in high

    def test_unknown_budget_falls_back_to_balanced(self):
        result = DepthBasedRouter.route(2, "ultra_mega")
        expected = DepthBasedRouter.route(2, "balanced")
        assert result == expected

    def test_invalid_stage_falls_back_to_depth_2(self):
        result = DepthBasedRouter.route_for_stage(999, "balanced")
        expected = DepthBasedRouter.route(2, "balanced")
        assert result == expected
