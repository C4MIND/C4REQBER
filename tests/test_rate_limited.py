"""W7: OpenRouter 429 → RateLimited, rotate cap, flash partial."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.llm.errors import RateLimited
from src.llm.sync_provider_chain import MAX_ROTATION_DEPTH, generate_with_fallback


class _FakeResponse:
    def __init__(self, status_code: int, *, retry_after: str = "") -> None:
        self.status_code = status_code
        self.headers = {"Retry-After": retry_after} if retry_after else {}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            req = httpx.Request("POST", "https://example.test/v1/chat/completions")
            raise httpx.HTTPStatusError(
                f"{self.status_code}",
                request=req,
                response=httpx.Response(self.status_code, request=req),
            )

    def json(self) -> dict:
        return {"choices": [{"message": {"content": "ok"}}]}


def test_sync_chain_raises_rate_limited_on_all_429(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every provider 429 → RateLimited (not silent empty success)."""
    specs = [
        MagicMock(
            name="openrouter",
            url="https://or.test/v1/chat/completions",
            model="m1",
            api_key="k",
            extra_headers={},
        ),
        MagicMock(
            name="lm_studio",
            url="http://127.0.0.1:1234/v1/chat/completions",
            model="local",
            api_key="",
            extra_headers={},
        ),
    ]
    monkeypatch.setattr(
        "src.llm.sync_provider_chain._build_chain",
        lambda: list(specs),
    )
    monkeypatch.setattr("src.llm.sync_provider_chain.MAX_ROTATION_DEPTH", 2)

    class _Client:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def __enter__(self) -> _Client:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def post(self, *args: object, **kwargs: object) -> _FakeResponse:
            return _FakeResponse(429, retry_after="30")

    monkeypatch.setattr("src.llm.sync_provider_chain.httpx.Client", _Client)

    with pytest.raises(RateLimited) as exc_info:
        generate_with_fallback("hello")

    assert exc_info.value.retry_after == 30.0
    assert "429" in str(exc_info.value).lower() or "rate" in str(exc_info.value).lower()


def test_sync_chain_rotation_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    """R9: stop after MAX_ROTATION_DEPTH attempts."""
    long_chain = [
        MagicMock(
            name=f"p{i}",
            url=f"https://p{i}.test/v1/chat/completions",
            model=f"m{i}",
            api_key="k",
            extra_headers={},
        )
        for i in range(20)
    ]
    monkeypatch.setattr(
        "src.llm.sync_provider_chain._build_chain",
        lambda: long_chain,
    )
    calls: list[int] = []

    class _Client:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def __enter__(self) -> _Client:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def post(self, *args: object, **kwargs: object) -> _FakeResponse:
            calls.append(1)
            return _FakeResponse(429)

    monkeypatch.setattr("src.llm.sync_provider_chain.httpx.Client", _Client)

    with pytest.raises(RateLimited):
        generate_with_fallback("cap test")

    assert len(calls) == MAX_ROTATION_DEPTH


@pytest.mark.asyncio
async def test_run_flash_rate_limited_returns_partial() -> None:
    """flash_runner must surface partial + rate_limited warning, not success."""
    from src.knowledge.flash_runner import run_flash

    mock_gateway = MagicMock()
    mock_gateway.chat = AsyncMock(
        side_effect=RateLimited("all providers rate-limited", retry_after=60.0)
    )
    mock_gateway.generate = AsyncMock(
        side_effect=RateLimited("all providers rate-limited", retry_after=60.0)
    )

    with (
        patch("src.llm.gateway.get_gateway", return_value=mock_gateway),
        patch(
            "src.knowledge.flash_sources.gather_flash_sources",
            new=AsyncMock(return_value=([], "", {"found": 0, "verified": 0})),
        ),
    ):
        result = await run_flash("test question", with_sources=False)

    assert result["status"] == "partial"
    assert any("rate_limited" in w for w in result.get("warnings", []))
    assert result.get("answer", "") == ""


def test_rate_limited_carries_retry_after() -> None:
    exc = RateLimited("slow down", retry_after=12.5, provider="openrouter")
    assert exc.retry_after == 12.5
    assert exc.provider == "openrouter"
    assert "12.5" in str(exc)
