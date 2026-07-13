from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from src.api.middleware.security import RateLimitMiddleware, setup_security_middleware
from src.llm.async_client import AsyncLLMClient


def test_security_setup_mounts_cors_and_handles_preflight(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://client.example")
    app = FastAPI()
    setup_security_middleware(app)

    assert sum(middleware.cls is CORSMiddleware for middleware in app.user_middleware) == 1

    response = TestClient(app).options(
        "/v8/discover/one-click",
        headers={
            "Origin": "https://client.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://client.example"


@pytest.mark.parametrize("name", ["JWT_SECRET", "CSRF_SECRET"])
def test_production_rejects_missing_or_weak_secrets(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "a" * 40)
    monkeypatch.setenv("CSRF_SECRET", "b" * 40)
    monkeypatch.setenv(name, "dev-secret-change-me")

    with pytest.raises(RuntimeError, match=name):
        setup_security_middleware(FastAPI())


def test_production_multi_worker_requires_shared_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "a" * 40)
    monkeypatch.setenv("CSRF_SECRET", "b" * 40)
    monkeypatch.setenv("WEB_CONCURRENCY", "2")
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setenv("RATE_LIMIT_BACKEND", "memory")

    with pytest.raises(RuntimeError, match="Multi-worker production"):
        setup_security_middleware(FastAPI())

    monkeypatch.setenv("REDIS_URL", "redis://redis:6379")
    monkeypatch.setenv("RATE_LIMIT_BACKEND", "redis")
    setup_security_middleware(FastAPI())


def test_rate_limit_does_not_trust_spoofed_forwarded_for_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RATE_LIMIT_BACKEND", "memory")
    monkeypatch.delenv("TRUST_PROXY_HEADERS", raising=False)
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, requests_per_minute=1)

    @app.get("/limited")
    async def limited() -> dict[str, bool]:
        return {"ok": True}

    client = TestClient(app)
    first = client.get("/limited", headers={"X-Forwarded-For": "198.51.100.1"})
    second = client.get("/limited", headers={"X-Forwarded-For": "203.0.113.2"})

    assert first.status_code == 200
    assert second.status_code == 429


@pytest.mark.asyncio
async def test_llm_guardian_fails_closed_on_scanner_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.security.guardian import Guardian

    def fail_scan(*args: object, **kwargs: object) -> object:
        raise OSError("scanner unavailable")

    monkeypatch.setattr(Guardian, "full_scan", fail_scan)
    client = AsyncLLMClient(api_key="not-a-real-key")

    with pytest.raises(RuntimeError, match="safety scan failed"):
        await client.generate("safe prompt")
