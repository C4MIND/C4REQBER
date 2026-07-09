"""Tavily Search Integration — AI-powered search with budget tracking."""
from __future__ import annotations

import os
from typing import Any

import httpx

from src.config import get_key
from src.integrations.tavily_budget import TavilyBudgetTracker


TAVILY_API_URL = "https://api.tavily.com"


class TavilyClient:
    """Tavily search client — 1000 credits/month with budget enforcement."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or get_key("tavily") or os.environ.get("TAVILY_API_KEY")
        self.enabled = bool(self.api_key)
        self.budget = TavilyBudgetTracker()

    async def search(
        self,
        query: str,
        search_depth: str = "basic",  # basic | advanced
        max_results: int = 5,
        include_answer: bool = True,
    ) -> dict[str, Any]:
        """Search Tavily with budget check and tracking."""
        if not self.enabled:
            raise RuntimeError("TAVILY_API_KEY not set")
        if not self.budget.can_search(search_depth):
            remaining = self.budget.remaining
            raise RuntimeError(
                f"Tavily monthly budget exhausted ({remaining} credits left, "
                f"need {self.budget.CREDIT_COST.get(search_depth, 1)})"
            )

        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{TAVILY_API_URL}/search",
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "search_depth": search_depth,
                    "max_results": max_results,
                    "include_answer": include_answer,
                },
                timeout=30,
            )
            r.raise_for_status()
            self.budget.record_search(search_depth, query)
            return r.json()

    def status(self) -> dict[str, Any]:
        """Return client status with remaining credits."""
        return {
            "name": "Tavily",
            "enabled": self.enabled,
            "provider": "tavily",
            "icon": "🔍",
            "credits": f"{self.budget.remaining}/1000 left",
            "remaining": self.budget.remaining,
        }
