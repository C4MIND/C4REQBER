"""Characterization tests for the LLM entrypoints (P2-A safety net).

These lock the CURRENT, observed wire behavior of the three live LLM
entrypoints — what model / params / URL each one actually sends for a given
input. They are the equivalence gate for the upcoming LLMGateway consolidation
(REWORK_PLAN.md → P2-A): the gateway facade must keep every one of these green,
proving the refactor changed plumbing, not behavior.

They assert *what is*, not *what should be* — including quirks (the default
ProviderRouter preset resolves "synthesis" to deepseek, not Claude). If a value
here looks wrong, that is a finding for A2 (deliberate behavior change), not a
test to "fix".

Seams mocked (no network):
  * BaseLLMClient path (ProviderRouter direct, AsyncLLMClient) → httpx.AsyncClient.post
  * LLMProviderRouter.chat → LLMProviderRouter._call_openai_sync (sync-in-executor)
"""
from __future__ import annotations

from unittest.mock import patch

import pytest


# ── shared fakes ──────────────────────────────────────────────────────────
class _FakeHTTPResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"choices": [{"message": {"content": "ok"}}], "model": "echo", "usage": {}}


@pytest.fixture
def capture_httpx():
    """Capture every httpx.AsyncClient.post (the BaseLLMClient seam)."""
    calls: list[dict] = []

    async def fake_post(self, url, **kw):  # noqa: ANN001
        calls.append({"url": url, "json": kw.get("json")})
        return _FakeHTTPResponse()

    with patch("httpx.AsyncClient.post", new=fake_post):
        yield calls


@pytest.fixture
def stable_env(monkeypatch):
    """Deterministic env: dummy keys, no per-phase model overrides."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("XAI_API_KEY", "test-key")
    for k in list(__import__("os").environ):
        if k.startswith("PHASE_"):
            monkeypatch.delenv(k, raising=False)


# ── 1. ProviderRouter (stage-aware, PRESETS) ──────────────────────────────
class TestProviderRouterCharacterization:
    @pytest.mark.asyncio
    async def test_default_preset_synthesis(self, capture_httpx, stable_env):
        from src.llm.router import ProviderRouter

        r = ProviderRouter()
        await r.generate("synthesis", "PROMPT", use_retry=False)
        req = capture_httpx[-1]
        assert req["url"].endswith("/chat/completions")
        assert req["json"]["model"] == "deepseek-chat"
        assert req["json"]["temperature"] == 0.6
        assert req["json"]["max_tokens"] == 3000
        # message shape: user prompt last
        assert req["json"]["messages"][-1] == {"role": "user", "content": "PROMPT"}

    @pytest.mark.asyncio
    async def test_default_preset_includes_system_prompt(self, capture_httpx, stable_env):
        from src.llm.router import ProviderRouter

        r = ProviderRouter()
        await r.generate("synthesis", "PROMPT", system_prompt="SYS", use_retry=False)
        msgs = capture_httpx[-1]["json"]["messages"]
        assert msgs[0] == {"role": "system", "content": "SYS"}
        assert msgs[-1] == {"role": "user", "content": "PROMPT"}

    @pytest.mark.asyncio
    async def test_c4reqber_preset_per_stage(self, capture_httpx, stable_env):
        from src.llm.config import ProviderPreset
        from src.llm.router import ProviderRouter

        r = ProviderRouter.from_preset(ProviderPreset.C4REQBER)
        await r.generate("synthesis", "P", use_retry=False)
        assert capture_httpx[-1]["json"]["model"] == "deepseek-chat"
        await r.generate("mp_rotation", "P", use_retry=False)
        assert capture_httpx[-1]["json"]["model"] == "grok-4.3"
        assert capture_httpx[-1]["json"]["temperature"] == 0.7
        assert capture_httpx[-1]["json"]["max_tokens"] == 800


# ── 2. AsyncLLMClient (DEFAULT_MODEL + response cache) ─────────────────────
class _NullCache:
    """Always-miss cache — forces a wire call regardless of disk cache state."""

    async def get(self, key):  # noqa: ANN001
        return None

    async def set(self, key, value):  # noqa: ANN001
        return None


class _MemCache:
    """Deterministic in-memory cache for the cache-hit characterization."""

    def __init__(self):
        self.d: dict = {}

    async def get(self, key):  # noqa: ANN001
        return self.d.get(key)

    async def set(self, key, value):  # noqa: ANN001
        self.d[key] = value


class TestAsyncLLMClientCharacterization:
    @pytest.mark.asyncio
    async def test_default_model_and_params(self, capture_httpx, stable_env):
        from src.llm.async_client import AsyncLLMClient

        c = AsyncLLMClient(cache=_NullCache())  # bypass disk cache → always hits the wire
        await c.generate("PROMPT", max_tokens=800, temperature=0.3)
        req = capture_httpx[-1]
        assert "openrouter.ai" in req["url"]
        assert req["json"]["model"] == "qwen/qwen-2.5-72b-instruct"
        assert req["json"]["temperature"] == 0.3
        assert req["json"]["max_tokens"] == 800

    @pytest.mark.asyncio
    async def test_response_is_cached(self, capture_httpx, stable_env):
        from src.llm.async_client import AsyncLLMClient

        c = AsyncLLMClient(cache=_MemCache())  # fresh empty cache for a deterministic miss→hit
        await c.generate("CACHE_ME", max_tokens=50, temperature=0.0)
        n_after_first = len(capture_httpx)
        assert n_after_first >= 1  # first call missed the (empty) cache → hit the wire
        await c.generate("CACHE_ME", max_tokens=50, temperature=0.0)
        # second identical call served from cache → no new HTTP request
        assert len(capture_httpx) == n_after_first


# ── 3. LLMProviderRouter.chat (guardian + deepseek→openrouter→lmstudio) ────
class TestLLMProviderRouterCharacterization:
    @pytest.fixture
    def capture_sync_call(self):
        calls: list[dict] = []

        def fake_call(url, key, model, messages, temperature, max_tokens, extra, timeout):  # noqa: ANN001
            calls.append({
                "url": url, "model": model, "messages": messages,
                "temperature": temperature, "max_tokens": max_tokens, "extra": extra,
            })
            return "RESULT"

        with patch(
            "src.llm.providers.unified.LLMProviderRouter._call_openai_sync",
            staticmethod(fake_call),
        ):
            yield calls

    @pytest.mark.asyncio
    async def test_chat_tries_deepseek_first(self, capture_sync_call, stable_env):
        from src.llm.providers.unified import LLMProviderRouter

        out = await LLMProviderRouter.chat(
            [{"role": "user", "content": "PROMPT"}],
            system_prompt="SYS", temperature=0.3, max_tokens=800,
        )
        assert out == "RESULT"
        first = capture_sync_call[0]
        assert "deepseek.com" in first["url"]
        assert first["model"] == "deepseek-v4-flash"
        assert first["temperature"] == 0.3
        assert first["max_tokens"] == 800
        # system prompt is prepended to the message list
        assert first["messages"][0] == {"role": "system", "content": "SYS"}
        assert first["extra"] == {}  # no json_mode

    @pytest.mark.asyncio
    async def test_chat_json_mode_sets_response_format(self, capture_sync_call, stable_env):
        from src.llm.providers.unified import LLMProviderRouter

        await LLMProviderRouter.chat(
            [{"role": "user", "content": "P"}], temperature=0.3, max_tokens=800, json_mode=True,
        )
        assert capture_sync_call[0]["extra"] == {"response_format": {"type": "json_object"}}


# ── 4. DefaultGateway equivalence: routing through the facade must produce the
#       exact same wire request as calling the underlying strategy directly. ──
class TestGatewayEquivalence:
    def test_default_gateway_satisfies_protocol(self):
        from src.llm.gateway import DefaultGateway, LLMGateway, get_gateway

        assert isinstance(DefaultGateway(), LLMGateway)
        assert get_gateway() is get_gateway()  # singleton

    @pytest.mark.asyncio
    async def test_generate_for_stage_matches_provider_router(self, capture_httpx, stable_env):
        from src.llm.gateway import DefaultGateway

        await DefaultGateway().generate_for_stage("synthesis", "PROMPT", use_retry=False)
        req = capture_httpx[-1]["json"]
        assert req["model"] == "deepseek-chat"
        assert req["temperature"] == 0.6
        assert req["max_tokens"] == 3000
        assert req["messages"][-1] == {"role": "user", "content": "PROMPT"}

    @pytest.mark.asyncio
    async def test_generate_matches_async_client(self, capture_httpx, stable_env):
        from src.llm.async_client import AsyncLLMClient
        from src.llm.gateway import DefaultGateway

        gw = DefaultGateway(async_client=AsyncLLMClient(cache=_NullCache()))
        await gw.generate("PROMPT", max_tokens=800, temperature=0.3)
        req = capture_httpx[-1]
        assert "openrouter.ai" in req["url"]
        assert req["json"]["model"] == "qwen/qwen-2.5-72b-instruct"
        assert req["json"]["temperature"] == 0.3
        assert req["json"]["max_tokens"] == 800

    @pytest.mark.asyncio
    async def test_chat_matches_provider_router(self, stable_env):
        from src.llm.gateway import DefaultGateway

        calls: list[dict] = []

        def fake_call(url, key, model, messages, temperature, max_tokens, extra, timeout):  # noqa: ANN001
            calls.append({"url": url, "model": model})
            return "RESULT"

        with patch(
            "src.llm.providers.unified.LLMProviderRouter._call_openai_sync",
            staticmethod(fake_call),
        ):
            out = await DefaultGateway().chat([{"role": "user", "content": "P"}], system_prompt="S")
        assert out == "RESULT"
        assert "deepseek.com" in calls[0]["url"]
        assert calls[0]["model"] == "deepseek-v4-flash"
