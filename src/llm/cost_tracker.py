"""LLM Cost Tracker.

Tracks token usage and estimated cost per request / session.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any

from src.di.container import get_container


# USD per 1M tokens (input / output) — updated for current models in balanced/premium
_PROVIDER_PRICES: dict[str, dict[str, tuple[float, float]]] = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "claude-3.5": {"input": 3.00, "output": 15.00},
    "claude-sonnet-4.6": {"input": 3.00, "output": 15.00},  # approx, via OpenRouter
    "claude-opus-4.6": {"input": 15.00, "output": 75.00},
    "gemini-1.5": {"input": 0.50, "output": 1.50},
    "local": {"input": 0.0, "output": 0.0},
}


def _normalize_model(model: str) -> str:
    """Map a raw model string to a known pricing key."""
    model_lower = model.lower()
    if "gpt-4o" in model_lower:
        return "gpt-4o"
    if "claude-sonnet-4.6" in model_lower or "claude-4.6" in model_lower:
        return "claude-sonnet-4.6"
    if "claude-opus-4.6" in model_lower or "claude-opus" in model_lower:
        return "claude-opus-4.6"
    if "claude-3.5" in model_lower or "claude-3-5" in model_lower:
        return "claude-3.5"
    if "gemini-1.5" in model_lower or "gemini-1.5" in model_lower:
        return "gemini-1.5"
    if any(local in model_lower for local in ("ollama", "lm_studio", "local", "qwen2.5")):
        return "local"
    return "gpt-4o"  # Default pricing


@dataclass
class CostEntry:
    """Single tracked request."""

    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    duration_ms: float
    cost_usd: float
    timestamp: float = field(default_factory=time.time)


class CostTracker:
    """
    Thread-safe cost tracker for LLM requests.

    Usage:
        tracker = CostTracker()
        cost = tracker.track_request("openrouter", "gpt-4o", 1000, 500, 1200)
        stats = tracker.get_stats()
    """

    def __init__(self) -> None:
        self._entries: list[CostEntry] = []
        self._lock = threading.Lock()
        self._session_start = time.time()

    def track_request(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        duration_ms: float,
    ) -> float:
        """
        Track a single LLM request and return its estimated cost in USD.
        """
        price_key = _normalize_model(model)
        prices = _PROVIDER_PRICES.get(price_key, _PROVIDER_PRICES["gpt-4o"])
        input_cost = (input_tokens / 1_000_000) * prices["input"]  # type: ignore[operator]
        output_cost = (output_tokens / 1_000_000) * prices["output"]  # type: ignore[operator]
        cost_usd = input_cost + output_cost

        entry = CostEntry(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=duration_ms,
            cost_usd=cost_usd,
        )

        with self._lock:
            self._entries.append(entry)

        return cost_usd  # type: ignore[no-any-return]

    def get_stats(self) -> dict[str, Any]:
        """Return aggregate statistics for all tracked requests."""
        with self._lock:
            total_requests = len(self._entries)
            total_input = sum(e.input_tokens for e in self._entries)
            total_output = sum(e.output_tokens for e in self._entries)
            total_cost = sum(e.cost_usd for e in self._entries)
            total_duration = sum(e.duration_ms for e in self._entries)

            provider_breakdown: dict[str, dict[str, Any]] = {}
            for e in self._entries:
                if e.provider not in provider_breakdown:
                    provider_breakdown[e.provider] = {
                        "requests": 0,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "cost_usd": 0.0,
                    }
                p = provider_breakdown[e.provider]
                p["requests"] += 1
                p["input_tokens"] += e.input_tokens
                p["output_tokens"] += e.output_tokens
                p["cost_usd"] += e.cost_usd

        return {
            "total_requests": total_requests,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_cost_usd": round(total_cost, 6),
            "total_duration_ms": round(total_duration, 2),
            "avg_cost_per_request": round(total_cost / max(total_requests, 1), 6),
            "provider_breakdown": provider_breakdown,
        }

    def get_session_cost(self) -> float:
        """Return total cost for the current session."""
        with self._lock:
            return round(sum(e.cost_usd for e in self._entries), 6)

    def reset(self) -> None:
        """Clear all tracked entries and reset session start."""
        with self._lock:
            self._entries.clear()
            self._session_start = time.time()


def get_cost_tracker() -> CostTracker:
    """Get the global CostTracker singleton (backed by DI container)."""
    container = get_container()
    if not container.has("cost_tracker"):
        tracker = CostTracker()
        container.register("cost_tracker", tracker)
    return container.resolve("cost_tracker")
