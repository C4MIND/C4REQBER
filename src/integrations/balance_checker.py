"""Balance Checker — unified balance retrieval for all providers."""
from __future__ import annotations

import os
from typing import Any

import httpx


class BalanceChecker:
    """Check real balances across all integrated providers."""

    @staticmethod
    async def check_openrouter(key: str | None = None) -> dict[str, Any]:
        """Check OpenRouter credits balance."""
        api_key = key or os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            return {"provider": "openrouter", "balance": None, "error": "no key"}
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    "https://openrouter.ai/api/v1/credits",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10,
                )
                if r.status_code == 200:
                    data = r.json()
                    return {
                        "provider": "openrouter",
                        "balance": data.get("data", {}).get("total_credits", 0),
                        "usage": data.get("data", {}).get("total_usage", 0),
                        "currency": "USD",
                    }
                return {"provider": "openrouter", "balance": None, "error": f"HTTP {r.status_code}"}
        except Exception as e:
            return {"provider": "openrouter", "balance": None, "error": str(e)}

    @staticmethod
    async def check_exa(key: str | None = None) -> dict[str, Any]:
        """Check Exa.ai account info."""
        api_key = key or os.environ.get("EXA_API_KEY")
        if not api_key:
            return {"provider": "exa", "balance": None, "error": "no key"}
        # Exa не имеет прямого endpoint баланса, но можно получить usage
        return {"provider": "exa", "balance": "unknown", "note": "$9.91 (manual)", "currency": "USD"}

    @staticmethod
    async def check_tavily(key: str | None = None) -> dict[str, Any]:
        """Check Tavily remaining credits."""
        from integrations.tavily_budget import TavilyBudgetTracker
        tracker = TavilyBudgetTracker()
        return {
            "provider": "tavily",
            "balance": tracker.remaining,
            "limit": tracker.limit,
            "used": tracker.used,
            "currency": "credits",
        }

    @staticmethod
    async def check_deepseek(key: str | None = None) -> dict[str, Any]:
        """Check DeepSeek balance."""
        api_key = key or os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            return {"provider": "deepseek", "balance": None, "error": "no key"}
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    "https://api.deepseek.com/user/balance",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10,
                )
                if r.status_code == 200:
                    data = r.json()
                    return {
                        "provider": "deepseek",
                        "balance": data.get("balance_info", [{}])[0].get("total_balance", 0),
                        "currency": "USD",
                    }
                return {"provider": "deepseek", "balance": None, "error": f"HTTP {r.status_code}"}
        except Exception as e:
            return {"provider": "deepseek", "balance": None, "error": str(e)}

    @staticmethod
    async def check_all() -> list[dict[str, Any]]:
        """Check all provider balances in parallel."""
        results = await asyncio.gather(
            BalanceChecker.check_openrouter(),
            BalanceChecker.check_exa(),
            BalanceChecker.check_tavily(),
            BalanceChecker.check_deepseek(),
        )
        return list(results)


import asyncio
