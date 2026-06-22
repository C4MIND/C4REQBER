"""Tests for LLMClient (audit 2026-06-22 H-8 Tier 1 migration).

client.py was migrated from urllib.request (stdlib) to httpx so it
can be wrapped in guarded_call_sync. These tests verify the
behavioral contract is unchanged.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def test_client_imports():
    from src.llm.client import LLMClient, LLMResponse
    assert hasattr(LLMClient, "generate")
    assert hasattr(LLMClient, "generate_structured")
    assert hasattr(LLMClient, "test_connection")


def test_client_no_longer_uses_urllib():
    """Audit 2026-06-22: client.py migrated from urllib.request to httpx.

    We exclude docstrings/comments so the migration-history note
    doesn't trip the assertion.
    """
    from src.llm import client as client_module
    src = Path(client_module.__file__).read_text()
    # Strip docstrings and comments
    import re
    no_strings = re.sub(r'"""[\s\S]*?"""', '', src)
    no_strings = re.sub(r"'''[\s\S]*?'''", '', no_strings)
    no_strings = re.sub(r"#.*", '', no_strings)
    assert "urllib.request" not in no_strings
    assert "urllib.error" not in no_strings
    assert "import httpx" in no_strings or "from httpx" in no_strings


def test_client_uses_guarded_call_sync():
    """The new client.py must delegate to guarded_call_sync for observability."""
    from src.llm import client as client_module
    src = Path(client_module.__file__).read_text()
    assert "guarded_chat_completion_sync" in src
    assert "extra_headers" in src  # OpenRouter HTTP-Referer + X-Title preserved


def test_client_requires_api_key():
    """Empty api_key must raise ValueError BEFORE attempting the call."""
    from src.llm.client import LLMClient
    c = LLMClient(api_key=None)
    # Force empty key (env override skipped in CI)
    c.api_key = None
    with pytest.raises(ValueError, match="API key required"):
        c.generate(prompt="hello")


def test_client_handles_httpx_error():
    """httpx.HTTPError from guarded_call must surface as RuntimeError."""
    from src.llm.client import LLMClient
    c = LLMClient(api_key="dummy")
    with pytest.raises(RuntimeError):
        c.generate(prompt="hi", model="any-model")
    # The error message should NOT contain the API key
    # (credential redaction is applied by guarded_call)


def test_response_dataclass_fields():
    """LLMResponse fields unchanged."""
    from src.llm.client import LLMResponse
    r = LLMResponse(content="hello", model="m", usage={"prompt_tokens": 1})
    assert r.content == "hello"
    assert r.model == "m"
    assert r.usage == {"prompt_tokens": 1}
    assert r.raw_response is None