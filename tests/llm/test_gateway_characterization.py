"""Characterization tests for the LLM entrypoints (P2-A safety net).

These lock the CURRENT, observed wire behavior of the live LLM entrypoints.
Model IDs are asserted against live SSOT (ProviderRouter config /
AsyncLLMClient._resolve_model / preferred_model), not frozen 2025 cloud names.

Seams mocked (no network):
  * BaseLLMClient path (ProviderRouter, AsyncLLMClient) → httpx.AsyncClient.post
  * LLMProviderRouter.chat → src.llm.sync_provider_chain.generate_with_fallback
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
    """Deterministic env: dummy keys, no per-phase model overrides via PHASE_*."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("XAI_API_KEY", "test-key")
    for k in list(__import__("os").environ):
        if k.startswith("PHASE_"):
            monkeypatch.delenv(k, raising=False)


# ── 1. ProviderRouter (stage-aware, PRESETS + ModelAssignment) ────────────
class TestProviderRouterCharacterization:
    @pytest.mark.asyncio
    async def test_default_preset_synthesis(self, capture_httpx, stable_env):
        from src.llm.router import ProviderRouter

        r = ProviderRouter()
        expected_model = r.get_config_for_stage("synthesis").model
        await r.generate("synthesis", "PROMPT", use_retry=False)
        req = capture_httpx[-1]
        assert req["url"].endswith("/chat/completions")
        assert req["json"]["model"] == expected_model
        assert req["json"]["temperature"] == r.get_config_for_stage("synthesis").temperature
        assert req["json"]["max_tokens"] == r.get_config_for_stage("synthesis").max_tokens
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
        synth_cfg = r.get_config_for_stage("synthesis")
        await r.generate("synthesis", "P", use_retry=False)
        assert capture_httpx[-1]["json"]["model"] == synth_cfg.model
        mp_cfg = r.get_config_for_stage("mp_rotation")
        await r.generate("mp_rotation", "P", use_retry=False)
        assert capture_httpx[-1]["json"]["model"] == mp_cfg.model
        assert capture_httpx[-1]["json"]["temperature"] == mp_cfg.temperature
        assert capture_httpx[-1]["json"]["max_tokens"] == mp_cfg.max_tokens


# ── 2. AsyncLLMClient (ModelAssignment + DEFAULT_MODEL fallback) ───────────
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

        c = AsyncLLMClient(cache=_NullCache())
        expected = c._resolve_model(None)
        await c.generate("PROMPT", max_tokens=800, temperature=0.3)
        req = capture_httpx[-1]
        assert "openrouter.ai" in req["url"]
        assert req["json"]["model"] == expected
        assert req["json"]["temperature"] == 0.3
        assert req["json"]["max_tokens"] == 800

    @pytest.mark.asyncio
    async def test_response_is_cached(self, capture_httpx, stable_env):
        from src.llm.async_client import AsyncLLMClient

        c = AsyncLLMClient(cache=_MemCache())
        await c.generate("CACHE_ME", max_tokens=50, temperature=0.0)
        n_after_first = len(capture_httpx)
        assert n_after_first >= 1
        await c.generate("CACHE_ME", max_tokens=50, temperature=0.0)
        assert len(capture_httpx) == n_after_first


# ── 3. LLMProviderRouter.chat → generate_with_fallback ─────────────────────
class TestLLMProviderRouterCharacterization:
    @pytest.fixture
    def capture_fallback(self):
        calls: list[dict] = []

        def fake_fallback(
            prompt,
            system_prompt=None,
            max_tokens=800,
            temperature=0.3,
            preferred_model=None,
            **kw,
        ):  # noqa: ANN001
            calls.append(
                {
                    "prompt": prompt,
                    "system_prompt": system_prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "preferred_model": preferred_model,
                }
            )
            return "RESULT"

        with patch(
            "src.llm.sync_provider_chain.generate_with_fallback",
            side_effect=fake_fallback,
        ):
            yield calls

    @pytest.mark.asyncio
    async def test_chat_uses_sync_provider_chain(self, capture_fallback, stable_env):
        from src.llm.providers.unified import LLMProviderRouter

        out = await LLMProviderRouter.chat(
            [{"role": "user", "content": "PROMPT"}],
            system_prompt="SYS",
            temperature=0.3,
            max_tokens=800,
        )
        assert out == "RESULT"
        first = capture_fallback[0]
        assert first["prompt"] == "PROMPT"
        assert first["system_prompt"] == "SYS"
        assert first["temperature"] == 0.3
        assert first["max_tokens"] == 800
        assert first["preferred_model"] == LLMProviderRouter._preferred_model()

    @pytest.mark.asyncio
    async def test_chat_json_mode_still_reaches_chain(self, capture_fallback, stable_env):
        """json_mode is accepted; current chat path uses generate_with_fallback."""
        from src.llm.providers.unified import LLMProviderRouter

        await LLMProviderRouter.chat(
            [{"role": "user", "content": "P"}],
            temperature=0.3,
            max_tokens=800,
            json_mode=True,
        )
        assert len(capture_fallback) == 1
        assert capture_fallback[0]["prompt"] == "P"


# ── 4. DefaultGateway equivalence ─────────────────────────────────────────
class TestGatewayEquivalence:
    def test_default_gateway_satisfies_protocol(self):
        from src.llm.gateway import DefaultGateway, LLMGateway, get_gateway

        assert isinstance(DefaultGateway(), LLMGateway)
        assert get_gateway() is get_gateway()

    @pytest.mark.asyncio
    async def test_generate_for_stage_matches_provider_router(self, capture_httpx, stable_env):
        from src.llm.gateway import DefaultGateway
        from src.llm.router import ProviderRouter

        expected = ProviderRouter().get_config_for_stage("synthesis")
        await DefaultGateway().generate_for_stage("synthesis", "PROMPT", use_retry=False)
        req = capture_httpx[-1]["json"]
        assert req["model"] == expected.model
        assert req["temperature"] == expected.temperature
        assert req["max_tokens"] == expected.max_tokens
        assert req["messages"][-1] == {"role": "user", "content": "PROMPT"}

    @pytest.mark.asyncio
    async def test_generate_matches_async_client(self, capture_httpx, stable_env):
        from src.llm.async_client import AsyncLLMClient
        from src.llm.gateway import DefaultGateway

        client = AsyncLLMClient(cache=_NullCache())
        expected = client._resolve_model(None)
        gw = DefaultGateway(async_client=client)
        await gw.generate("PROMPT", max_tokens=800, temperature=0.3)
        req = capture_httpx[-1]
        assert "openrouter.ai" in req["url"]
        assert req["json"]["model"] == expected
        assert req["json"]["temperature"] == 0.3
        assert req["json"]["max_tokens"] == 800

    @pytest.mark.asyncio
    async def test_chat_matches_provider_router(self, stable_env):
        from src.llm.gateway import DefaultGateway
        from src.llm.providers.unified import LLMProviderRouter

        calls: list[dict] = []

        def fake_fallback(
            prompt, system_prompt=None, max_tokens=800, temperature=0.3, preferred_model=None, **kw
        ):  # noqa: ANN001
            calls.append(
                {
                    "prompt": prompt,
                    "system_prompt": system_prompt,
                    "preferred_model": preferred_model,
                }
            )
            return "RESULT"

        with patch(
            "src.llm.sync_provider_chain.generate_with_fallback",
            side_effect=fake_fallback,
        ):
            out = await DefaultGateway().chat([{"role": "user", "content": "P"}], system_prompt="S")
        assert out == "RESULT"
        assert calls[0]["prompt"] == "P"
        assert calls[0]["system_prompt"] == "S"
        assert calls[0]["preferred_model"] == LLMProviderRouter._preferred_model()

    @pytest.mark.asyncio
    async def test_chat_json_matches_provider_router(self, stable_env):
        from src.llm.gateway import DefaultGateway

        calls: list[dict] = []

        def fake_fallback(
            prompt, system_prompt=None, max_tokens=800, temperature=0.3, preferred_model=None, **kw
        ):  # noqa: ANN001
            calls.append({"prompt": prompt, "preferred_model": preferred_model})
            return '{"ok": true}'

        with patch(
            "src.llm.sync_provider_chain.generate_with_fallback",
            side_effect=fake_fallback,
        ):
            out = await DefaultGateway().chat_json([{"role": "user", "content": "P"}])
        assert out == {"ok": True}
        assert len(calls) == 1
        assert calls[0]["prompt"] == "P"


# ── 5. DefaultGateway lifecycle ───────────────────────────────────────────
class TestGatewayLifecycle:
    @pytest.mark.asyncio
    async def test_generate_lazily_constructs_async_client(self, capture_httpx, stable_env):
        from src.llm.gateway import DefaultGateway

        gw = DefaultGateway()
        assert gw._async_client is None
        await gw.generate("LAZY_PROMPT", max_tokens=10, temperature=0.0)
        assert gw._async_client is not None

    @pytest.mark.asyncio
    async def test_generate_for_stage_lazily_constructs_router(self, capture_httpx, stable_env):
        from src.llm.gateway import DefaultGateway

        gw = DefaultGateway()
        assert gw._provider_router is None
        await gw.generate_for_stage("synthesis", "P", use_retry=False)
        assert gw._provider_router is not None

    @pytest.mark.asyncio
    async def test_close_releases_injected_strategies(self):
        from unittest.mock import AsyncMock

        from src.llm.gateway import DefaultGateway

        router, client = AsyncMock(), AsyncMock()
        gw = DefaultGateway(provider_router=router, async_client=client)
        await gw.close()
        router.close_all.assert_awaited_once()
        client.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_close_is_noop_when_nothing_constructed(self):
        from src.llm.gateway import DefaultGateway

        await DefaultGateway().close()
