"""
C4REQBER API: Security Middleware (Hardened)
CSP without unsafe-inline, CORS allowlist, rate limiting, API key headers.

CORS is configured separately in `setup_cors()` (src/api/middleware/cors.py).
Do NOT add CORSMiddleware here — audit 2026-06-22 found CORS being mounted
twice (here + in cors.py), causing duplicate Access-Control-* headers that
browsers reject. CORS registration is the sole responsibility of setup_cors().
"""

from __future__ import annotations

import os
import time
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.api.middleware.auth import JWTAuthMiddleware
from src.api.middleware.csrf import CSRFProtectionMiddleware
from src.api.routers.metrics import API_REQUESTS, RATE_LIMIT_HITS


class SecurityHeadersMiddleware:
    """Add hardened security headers to all responses."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Any) -> None:
            """Send with headers."""
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(
                    [
                        (b"X-Content-Type-Options", b"nosniff"),
                        (b"X-Frame-Options", b"DENY"),
                        (b"X-XSS-Protection", b"1; mode=block"),
                        (b"Referrer-Policy", b"strict-origin-when-cross-origin"),
                        (
                            b"Permissions-Policy",
                            b"accelerometer=(), camera=(), geolocation=(), "
                            b"gyroscope=(), magnetometer=(), microphone=(), "
                            b"payment=(), usb=()",
                        ),
                        # CSP without unsafe-inline
                        (
                            b"Content-Security-Policy",
                            b"default-src 'self'; script-src 'self'; "
                            b"style-src 'self' https://fonts.googleapis.com; "
                            b"font-src 'self' https://fonts.gstatic.com; "
                            b"connect-src 'self' /api /ws; "
                            b"img-src 'self' data: blob:; "
                            b"frame-ancestors 'none'; base-uri 'self'; "
                            b"form-action 'self'",
                        ),
                    ]
                )
                if os.getenv("ENV") == "production":
                    headers.append(
                        (
                            b"Strict-Transport-Security",
                            b"max-age=31536000; includeSubDomains; preload",
                        )
                    )
                message["headers"] = headers
                # Audit 2026-06-22: increment API_REQUESTS Prometheus counter
                # here so every HTTP request contributes. Endpoint label uses
                # the route template (scope["path"]) which the
                # SecurityHeadersMiddleware captures before path params expand.
                try:
                    method = scope.get("method", "UNKNOWN")
                    path = scope.get("path", "unknown")
                    status_code = message.get("status", 0)
                    API_REQUESTS.labels(
                        method=method, endpoint=path, status_code=str(status_code)
                    ).inc()
                except Exception:
                    pass  # observability must never crash the response
            await send(message)

        await self.app(scope, receive, send_with_headers)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-endpoint sliding window rate limiting with Redis backing."""

    def __init__(
        self,
        app: Any,
        requests_per_minute: int = 60,
        endpoint_limits: dict[str, int] | None = None,
        redis_url: str | None = None,
    ) -> None:
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.endpoint_limits = endpoint_limits or {}
        self._requests: dict[str, list[float]] = {}
        self._redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self._redis: Any = None
        self._use_redis = os.getenv("RATE_LIMIT_BACKEND", "memory").lower() == "redis"

    async def _get_redis(self) -> Any:
        if self._redis is not None:
            return self._redis
        if not self._use_redis:
            return None
        try:
            import redis.asyncio as aioredis

            redis_url = self._redis_url or "redis://localhost:6379"
            self._redis = aioredis.from_url(  # type: ignore[no-untyped-call]
                redis_url, decode_responses=True
            )
            await self._redis.ping()
            return self._redis
        except (ValueError, TypeError, ConnectionError):
            self._redis = None
            return None

    def _get_client_id(self, request: Request) -> str:
        api_key = request.headers.get("X-API-Key", "")
        if api_key:
            return f"api:{api_key[:16]}"
        if os.getenv("TRUST_PROXY_HEADERS", "false").lower() in {"1", "true", "yes"}:
            forwarded = request.headers.get("X-Forwarded-For", "")
            if forwarded:
                return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        """Dispatch."""
        client_id = self._get_client_id(request)
        path = request.url.path
        key = f"{client_id}:{path}"

        limit = self.endpoint_limits.get(path, self.requests_per_minute)
        now = time.time()
        window = 60  # 1 minute

        r = await self._get_redis()
        if r:
            redis_key = f"rl:{key}"
            pipe = r.pipeline()
            pipe.zremrangebyscore(redis_key, 0, now - window)
            pipe.zcard(redis_key)
            pipe.zadd(redis_key, {str(now): now})
            pipe.expire(redis_key, window)
            _, count, _, _ = await pipe.execute()
            if count >= limit:
                retry_after = int(window)
                RATE_LIMIT_HITS.labels(endpoint=path).inc()
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Try again later."},
                    headers={"Retry-After": str(retry_after)},
                )
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, limit - count - 1))
            return response

        # In-memory rate limiter
        timestamps = self._requests.get(key, [])
        valid = [t for t in timestamps if now - t < window]

        if len(valid) >= limit:
            RATE_LIMIT_HITS.labels(endpoint=path).inc()
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers={"Retry-After": str(int(window - (now - valid[0])))},
            )

        valid.append(now)
        self._requests[key] = valid

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        remaining = max(0, limit - len(valid))
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Validate API keys from header (not query string)."""

    def __init__(self, app: Any, required_paths: list[str] | None = None) -> None:
        super().__init__(app)
        self.required_paths = required_paths or ["/api/"]
        self._valid_keys: set[str] = set()
        # Load keys from env (comma-separated)
        keys_env = os.getenv("API_KEYS", "")
        if keys_env:
            self._valid_keys = {k.strip() for k in keys_env.split(",") if k.strip()}

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        """Dispatch."""
        path = request.url.path

        # Skip health and public endpoints
        if path in ("/health", "/health/live", "/health/ready", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        # Check if path requires API key
        requires_key = any(path.startswith(p) for p in self.required_paths)
        if not requires_key and not self._valid_keys:
            return await call_next(request)

        api_key = request.headers.get("X-API-Key", "")
        if not api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "API key required in X-API-Key header"},
            )

        if self._valid_keys and api_key not in self._valid_keys:
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid API key"},
            )

        return await call_next(request)


def setup_security_middleware(app: FastAPI) -> None:
    """Register all security middleware on the FastAPI app."""
    if os.getenv("ENV", "development").lower() == "production":
        for name in ("JWT_SECRET", "CSRF_SECRET"):
            secret = os.getenv(name, "")
            weak_patterns = ("changeme", "password", "dev-secret", "test-secret")
            if len(secret) < 32 or any(pattern in secret.lower() for pattern in weak_patterns):
                raise RuntimeError(
                    f"{name} must be at least 32 characters and non-default in production"
                )
        worker_value = os.getenv("WEB_CONCURRENCY", os.getenv("UVICORN_WORKERS", "1"))
        try:
            worker_count = int(worker_value)
        except ValueError as exc:
            raise RuntimeError("API worker count must be an integer") from exc
        if worker_count > 1 and (
            not os.getenv("REDIS_URL")
            or os.getenv("RATE_LIMIT_BACKEND", "memory").lower() != "redis"
        ):
            raise RuntimeError(
                "Multi-worker production requires REDIS_URL and RATE_LIMIT_BACKEND=redis"
            )

    # Security headers (ASGI middleware — add first so it runs last)
    app.add_middleware(SecurityHeadersMiddleware)

    # JWT auth (applies to all non-public endpoints)
    app.add_middleware(JWTAuthMiddleware)

    # CSRF protection for state-changing requests
    app.add_middleware(CSRFProtectionMiddleware)

    # Rate limiting with configurable per-endpoint limits
    rpm = int(os.getenv("RATE_LIMIT_RPM", "60"))
    endpoint_limits = {}
    limits_env = os.getenv("RATE_LIMIT_ENDPOINTS", "")
    if limits_env:
        # Format: /api/v1/auth/login:10,/api/v1/discoveries:120
        for part in limits_env.split(","):
            if ":" in part:
                ep, lim = part.split(":", 1)
                try:
                    endpoint_limits[ep.strip()] = int(lim.strip())
                except ValueError:
                    pass
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=rpm,
        endpoint_limits=endpoint_limits,
    )

    # API key validation (only if API_KEYS env is set)
    if os.getenv("API_KEYS"):
        app.add_middleware(APIKeyMiddleware)

    # Add CORS once and last so preflight requests are handled by the outermost
    # middleware before authentication and CSRF checks.
    from src.api.middleware.cors import setup_cors

    setup_cors(app)
