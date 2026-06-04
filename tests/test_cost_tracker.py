"""
TURBO-CDI LLM: Cost Tracker Tests
"""
from __future__ import annotations

import pytest

from src.llm.cost_tracker import CostTracker, _normalize_model, get_cost_tracker


class TestNormalizeModel:
    def test_gpt4o(self):
        assert _normalize_model("openai/gpt-4o") == "gpt-4o"
        assert _normalize_model("GPT-4o-mini") == "gpt-4o"

    def test_claude(self):
        assert _normalize_model("anthropic/claude-3.5-sonnet") == "claude-3.5"
        assert _normalize_model("claude-3-5-haiku") == "claude-3.5"

    def test_gemini(self):
        assert _normalize_model("google/gemini-1.5-pro") == "gemini-1.5"

    def test_local(self):
        assert _normalize_model("ollama/qwen2.5:14b") == "local"
        assert _normalize_model("lm_studio/local-model") == "local"

    def test_fallback(self):
        assert _normalize_model("unknown-model") == "gpt-4o"


class TestCostTracker:
    def test_track_request_returns_cost(self):
        tracker = CostTracker()
        cost = tracker.track_request("openrouter", "gpt-4o", 1_000_000, 500_000, 1000)
        assert cost > 0
        # 1M input @ $2.50 + 0.5M output @ $10.00 = $2.50 + $5.00 = $7.50
        assert round(cost, 2) == 7.50

    def test_local_is_free(self):
        tracker = CostTracker()
        cost = tracker.track_request("ollama", "qwen2.5:14b", 1_000_000, 1_000_000, 500)
        assert cost == 0.0

    def test_get_stats(self):
        tracker = CostTracker()
        tracker.track_request("openrouter", "gpt-4o", 1000, 500, 100)
        tracker.track_request("ollama", "qwen2.5:14b", 2000, 1000, 200)

        stats = tracker.get_stats()
        assert stats["total_requests"] == 2
        assert stats["total_input_tokens"] == 3000
        assert stats["total_output_tokens"] == 1500
        assert stats["total_cost_usd"] > 0
        assert "provider_breakdown" in stats
        assert "openrouter" in stats["provider_breakdown"]
        assert "ollama" in stats["provider_breakdown"]

    def test_get_session_cost(self):
        tracker = CostTracker()
        tracker.track_request("openrouter", "gpt-4o", 2_000_000, 1_000_000, 2000)
        session_cost = tracker.get_session_cost()
        assert session_cost > 0
        assert round(session_cost, 2) == 15.00

    def test_reset(self):
        tracker = CostTracker()
        tracker.track_request("openrouter", "gpt-4o", 1000, 500, 100)
        tracker.reset()
        assert tracker.get_session_cost() == 0.0
        assert tracker.get_stats()["total_requests"] == 0

    def test_thread_safety(self):
        import threading

        tracker = CostTracker()

        def worker():
            for _ in range(100):
                tracker.track_request("openrouter", "gpt-4o", 1000, 500, 10)

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        stats = tracker.get_stats()
        assert stats["total_requests"] == 500


class TestGlobalTracker:
    def test_singleton(self):
        t1 = get_cost_tracker()
        t2 = get_cost_tracker()
        assert t1 is t2
