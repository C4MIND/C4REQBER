"""Tavily Budget Tracker — 1000 credits/month limit enforcement."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


BUDGET_FILE = Path.home() / ".reqber" / "tavily_budget.json"
MONTHLY_LIMIT = 1000


class TavilyBudgetTracker:
    """Tracks Tavily API usage to stay within 1000 credits/month.

    Each search call costs:
      - basic: 1 credit
      - advanced: 2 credits
    """

    CREDIT_COST = {"basic": 1, "advanced": 2}

    def __init__(self, limit: int = MONTHLY_LIMIT) -> None:
        self.limit = limit
        self._data = self._load()

    def _load(self) -> dict[str, Any]:
        if BUDGET_FILE.exists():
            try:
                return json.loads(BUDGET_FILE.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return {"month": self._current_month(), "used": 0, "history": []}

    def _save(self) -> None:
        BUDGET_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            BUDGET_FILE.write_text(json.dumps(self._data, indent=2))
        except OSError:
            pass

    @staticmethod
    def _current_month() -> str:
        return time.strftime("%Y-%m")

    def _reset_if_new_month(self) -> None:
        current = self._current_month()
        if self._data.get("month") != current:
            self._data = {"month": current, "used": 0, "history": []}
            self._save()

    @property
    def remaining(self) -> int:
        """Remaining."""
        self._reset_if_new_month()
        return max(0, self.limit - self._data.get("used", 0))

    @property
    def used(self) -> int:
        """Used."""
        self._reset_if_new_month()
        return self._data.get("used", 0)

    def can_search(self, depth: str = "basic") -> bool:
        """Check if search is within budget."""
        cost = self.CREDIT_COST.get(depth, 1)
        return self.remaining >= cost

    def record_search(self, depth: str = "basic", query: str = "") -> None:
        """Record a search and deduct credits."""
        self._reset_if_new_month()
        cost = self.CREDIT_COST.get(depth, 1)
        self._data["used"] = self._data.get("used", 0) + cost
        self._data.setdefault("history", []).append({
            "time": time.time(),
            "depth": depth,
            "cost": cost,
            "query": query[:100],
        })
        self._save()

    def status(self) -> dict[str, Any]:
        """Return budget status for dashboard."""
        return {
            "name": "Tavily",
            "enabled": bool(os.environ.get("TAVILY_API_KEY")),
            "provider": "tavily",
            "icon": "🔍",
            "credits": f"{self.remaining}/{self.limit} left",
            "used": self.used,
            "remaining": self.remaining,
            "limit": self.limit,
        }
