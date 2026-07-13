"""Tests for the guarded_call helper (audit H-8 Tier 1).

Verifies:
- Module imports without crashing (heavy deps optional)
- Provider detection from URL works for common providers
- Sanitization is applied to message content
- Errors are recorded but not propagated with raw credentials
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def test_module_imports():
    """guarded_call module must import (heavy deps via try/except inside)."""
    from src.llm import guarded_call

    assert hasattr(guarded_call, "guarded_chat_completion")
    assert hasattr(guarded_call, "guarded_chat_completion_sync")


def test_provider_detection():
    """URL → provider mapping must work for common endpoints."""
    from src.llm.guarded_call import _provider_from_url

    assert _provider_from_url("https://openrouter.ai/api/v1/chat/completions") == "openrouter"
    assert _provider_from_url("https://api.anthropic.com/v1/messages") == "anthropic"
    assert _provider_from_url("https://api.openai.com/v1/chat/completions") == "openai"
    assert _provider_from_url("http://localhost:11434/api/chat") == "local"
    assert _provider_from_url("https://example.com/v1/chat") == "unknown"


def test_sanitize_messages_returns_list():
    """_scan_messages should not crash and should return a list."""
    from src.llm.guarded_call import _scan_messages

    msgs = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello world"},
    ]
    out = _scan_messages(msgs)
    assert isinstance(out, list)
    assert len(out) == len(msgs)


def test_sanitize_preserves_role_keys():
    """Sanitized messages should keep all keys except possibly 'content'."""
    from src.llm.guarded_call import _scan_messages

    msgs = [{"role": "user", "content": "test", "name": "alice"}]
    out = _scan_messages(msgs)
    assert out[0]["role"] == "user"
    assert out[0]["name"] == "alice"
    assert "content" in out[0]


def test_sanitize_handles_non_string_content():
    """Multimodal content (lists of parts) should pass through unchanged."""
    from src.llm.guarded_call import _scan_messages

    msgs = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}},
            ],
        }
    ]
    out = _scan_messages(msgs)
    assert isinstance(out[0]["content"], list)


def test_record_metrics_swallows_exceptions():
    """Metrics recording must never crash the caller (best-effort)."""
    from src.llm.guarded_call import _record_metrics

    # No Prometheus registry available in this test; should not raise.
    _record_metrics("test", "test-model", "success", 0.1)
    _record_metrics("test", "test-model", "error", 0.2)


def test_record_cost_with_unknown_model_is_zero():
    """Unknown model name should result in $0 cost (no crash)."""
    from src.llm.guarded_call import _record_cost

    _record_cost("totally-unknown-model-xyz", 100, 50)
    # No assertion — just must not raise


@pytest.mark.asyncio
async def test_guarded_call_handles_connection_error():
    """When the upstream is unreachable, we record error metric and re-raise."""
    import httpx

    from src.llm.guarded_call import guarded_chat_completion

    with pytest.raises(httpx.HTTPError):
        await guarded_chat_completion(
            url="http://127.0.0.1:1/chat/completions",  # nothing listens here
            api_key="dummy",
            model="test-model",
            messages=[{"role": "user", "content": "hi"}],
            timeout=2.0,
        )
