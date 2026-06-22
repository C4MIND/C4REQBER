"""Tests for BaseLLMClient.guarded_post + AsyncLLMClient cost/metric helpers.

Audit 2026-06-22 H-8 Tier 1 follow-up: the new guarded_post() and
_record_metric/_record_cost helpers added to BaseLLMClient (and similar
on AsyncLLMClient) shipped without test coverage. These tests lock in
the behaviour and protect against the silent-failure bugs found during
the H-8 audit:

  - COST_TABLE alias is exported from src.llm.cost_tracker
  - CostTracker.add(entry) is a classmethod that appends to the global
  - BaseLLMClient._record_cost looks up rates["input"/"output"] (NOT
    tuple-unpack, which was the original bug — tuple-unpacking a dict
    gives the *keys* as strings, so cost math was `float * str` = TypeError)
  - logger is defined in base.py (else the except branch raises NameError
    and the "observability never crashes callers" contract is violated)
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


# ─────────────────────────────────────────────────────────────────────
# cost_tracker public surface (the fixes)
# ─────────────────────────────────────────────────────────────────────


def test_cost_tracker_exposes_cost_table():
    """Regression: COST_TABLE alias must exist (used by guarded_call + base + async_client)."""
    from src.llm import cost_tracker
    assert hasattr(cost_tracker, "COST_TABLE")
    # The alias is the same dict object as the private one.
    assert cost_tracker.COST_TABLE is cost_tracker._PROVIDER_PRICES


def test_cost_tracker_add_is_classmethod_and_appends_to_singleton():
    """Regression: CostTracker.add(entry) is a classmethod that appends to the global."""
    from src.llm.cost_tracker import CostEntry, CostTracker, get_cost_tracker

    # The call site pattern is `CostTracker.add(CostEntry(...))` — no instance.
    # If add were an instance method, this would raise TypeError.
    singleton = get_cost_tracker()
    before = len(singleton._entries)
    CostTracker.add(CostEntry(
        provider="test", model="gpt-4o",
        input_tokens=1, output_tokens=1,
        duration_ms=0.0, cost_usd=0.0,
    ))
    assert len(singleton._entries) == before + 1
    assert singleton._entries[-1].provider == "test"


def test_base_module_defines_logger():
    """Regression: base.py must define `logger` (used in except branches)."""
    from src.llm.providers import base as base_mod
    assert hasattr(base_mod, "logger"), "base.py must define `logger = logging.getLogger(__name__)`"


# ─────────────────────────────────────────────────────────────────────
# BaseLLMClient._record_metric (smoke + Prometheus increment)
# ─────────────────────────────────────────────────────────────────────


def test_base_record_metric_swallows_no_metrics_module():
    """When metrics module is unavailable, _record_metric must not raise."""
    from src.llm.config import LLMProvider
    from src.llm.providers.base import BaseLLMClient

    client = BaseLLMClient.__new__(BaseLLMClient)
    client.provider = LLMProvider.OPENROUTER
    # Should not raise even if labels() / observe() had a problem;
    # the try/except inside _record_metric makes it best-effort.
    client._record_metric("gpt-4o", "success", 0.1)
    client._record_metric("", "success", 0.1)  # empty model → defaults to "unknown"


def test_base_record_metric_increments_prometheus_counter():
    """The success label on LLM_CALLS must be incremented when metrics is importable."""
    from src.api.routers.metrics import LLM_CALLS
    from src.llm.config import LLMProvider
    from src.llm.providers.base import BaseLLMClient

    client = BaseLLMClient.__new__(BaseLLMClient)
    client.provider = LLMProvider.XAI  # use a label not touched by other tests

    counter = LLM_CALLS.labels(provider="xai", model="gpt-4o", status="success")
    before = counter._value.get()
    client._record_metric("gpt-4o", "success", 0.1)
    after = counter._value.get()
    assert after == before + 1, f"counter should increment from {before} to {before + 1}, got {after}"


# ─────────────────────────────────────────────────────────────────────
# BaseLLMClient._record_cost (gpt-4o known model + local $0)
# ─────────────────────────────────────────────────────────────────────


def test_base_record_cost_known_model_records_correct_amount():
    """gpt-4o: 1M input + 0.5M output → $2.50 + $5.00 = $7.50."""
    from src.llm.config import LLMProvider
    from src.llm.cost_tracker import get_cost_tracker
    from src.llm.providers.base import BaseLLMClient

    client = BaseLLMClient.__new__(BaseLLMClient)
    client.provider = LLMProvider.OPENROUTER

    tracker = get_cost_tracker()
    before = len(tracker._entries)

    client._record_cost("gpt-4o", 1_000_000, 500_000)

    assert len(tracker._entries) == before + 1
    entry = tracker._entries[-1]
    assert entry.provider == "openrouter"
    assert entry.model == "gpt-4o"
    assert entry.input_tokens == 1_000_000
    assert entry.output_tokens == 500_000
    assert abs(entry.cost_usd - 7.5) < 0.001, f"expected $7.50, got ${entry.cost_usd}"


def test_base_record_cost_local_provider_records_zero():
    """Local providers (ollama/lm_studio) normalize to "local" = $0.00/MTok."""
    from src.llm.config import LLMProvider
    from src.llm.cost_tracker import get_cost_tracker
    from src.llm.providers.base import BaseLLMClient

    client = BaseLLMClient.__new__(BaseLLMClient)
    client.provider = LLMProvider.LM_STUDIO

    tracker = get_cost_tracker()
    before = len(tracker._entries)

    client._record_cost("ollama-llama3", 1000, 500)

    assert len(tracker._entries) == before + 1
    entry = tracker._entries[-1]
    assert entry.cost_usd == 0.0


# ─────────────────────────────────────────────────────────────────────
# BaseLLMClient.guarded_post (success + error)
# ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_guarded_post_success_records_metric_and_cost():
    """On 2xx with usage block: success metric incremented + cost entry appended."""
    from src.api.routers.metrics import LLM_CALLS
    from src.llm.config import LLMProvider
    from src.llm.cost_tracker import get_cost_tracker
    from src.llm.providers.base import BaseLLMClient

    client = BaseLLMClient.__new__(BaseLLMClient)
    client.provider = LLMProvider.XAI
    client.timeout = 5.0
    client._client = None  # force _init_client to be a no-op via patch
    client._init_client = AsyncMock()  # type: ignore[method-assign]

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "id": "test-id",
        "choices": [{"message": {"content": "hi"}}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50},
    })
    client._client = MagicMock()
    client._client.post = AsyncMock(return_value=mock_response)

    counter = LLM_CALLS.labels(provider="xai", model="gpt-4o", status="success")
    before_counter = counter._value.get()
    tracker = get_cost_tracker()
    before_entries = len(tracker._entries)

    data = await client.guarded_post(
        url="https://api.x.ai/v1/chat/completions",
        json_body={"model": "gpt-4o", "messages": []},
        model_name="gpt-4o",
    )

    assert data["id"] == "test-id"
    assert counter._value.get() == before_counter + 1
    assert len(tracker._entries) == before_entries + 1
    assert tracker._entries[-1].model == "gpt-4o"


@pytest.mark.asyncio
async def test_guarded_post_error_records_error_metric_and_raises():
    """On HTTPStatusError: error metric + re-raise (no cost entry)."""
    from src.api.routers.metrics import LLM_CALLS
    from src.llm.config import LLMProvider
    from src.llm.cost_tracker import get_cost_tracker
    from src.llm.providers.base import BaseLLMClient

    client = BaseLLMClient.__new__(BaseLLMClient)
    client.provider = LLMProvider.XAI
    client.timeout = 5.0
    client._init_client = AsyncMock()  # type: ignore[method-assign]

    req = httpx.Request("POST", "https://api.x.ai/v1/chat/completions")
    resp = httpx.Response(500, request=req)
    err = httpx.HTTPStatusError("500 Server Error", request=req, response=resp)
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status = MagicMock(side_effect=err)
    client._client = MagicMock()
    client._client.post = AsyncMock(return_value=mock_response)

    counter = LLM_CALLS.labels(provider="xai", model="gpt-4o", status="error")
    before_counter = counter._value.get()
    tracker = get_cost_tracker()
    before_entries = len(tracker._entries)

    with pytest.raises(httpx.HTTPStatusError):
        await client.guarded_post(
            url="https://api.x.ai/v1/chat/completions",
            json_body={"model": "gpt-4o", "messages": []},
            model_name="gpt-4o",
        )

    assert counter._value.get() == before_counter + 1, "error metric should increment"
    assert len(tracker._entries) == before_entries, "no cost entry on error path"


# ─────────────────────────────────────────────────────────────────────
# AsyncLLMClient (the other place _record_cost/_record_metric were added)
# ─────────────────────────────────────────────────────────────────────


def test_async_client_record_metric_swallows_exceptions():
    """AsyncLLMClient._record_metric must never raise (best-effort contract)."""
    from src.llm.async_client import AsyncLLMClient

    client = AsyncLLMClient.__new__(AsyncLLMClient)
    client._record_metric("gpt-4o", "success", 0.1)
    client._record_metric("gpt-4o", "error_retry", 0.5)


def test_async_client_record_cost_known_model_records_correct_amount():
    """AsyncLLMClient._record_cost with gpt-4o = $7.50 for 1M in / 0.5M out."""
    from src.llm.async_client import AsyncLLMClient
    from src.llm.cost_tracker import get_cost_tracker

    client = AsyncLLMClient.__new__(AsyncLLMClient)

    tracker = get_cost_tracker()
    before = len(tracker._entries)

    client._record_cost("gpt-4o", 1_000_000, 500_000)

    assert len(tracker._entries) == before + 1
    entry = tracker._entries[-1]
    assert entry.provider == "async_client"
    assert entry.model == "gpt-4o"
    assert abs(entry.cost_usd - 7.5) < 0.001, f"expected $7.50, got ${entry.cost_usd}"
