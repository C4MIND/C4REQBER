from __future__ import annotations


"""JWT Auth middleware for c44tcdi API."""
import logging
import os
from typing import Any

import jwt
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


logger = logging.getLogger(__name__)


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """JWT Authentication middleware.

    Requires JWT_SECRET to be set in environment.
    Auth is bypassed in development/test mode (DEV_MODE=true or ENVIRONMENT=development).
    """

    async def dispatch(self, request: Request, call_next) -> JSONResponse:
        """Authenticate requests using JWT token."""
        # Bypass auth in dev/test mode with cryptographic token
        from src.api.dev_mode import is_dev_mode
        if is_dev_mode(request):
            return await call_next(request)

        # Public endpoints that don't require authentication
        public_paths = {
            "/health",
            "/api/v1/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/v8/simulations/capabilities",
            "/v8/verification/methods",
        }
        if request.url.path.rstrip("/") in {p.rstrip("/") for p in public_paths}:
            return await call_next(request)

        # Webhook endpoints require HMAC auth and JWT
        body = b""
        if request.url.path.startswith("/v8/webhook") or request.url.path.startswith("/api/v8/webhook"):
            signature = request.headers.get("X-C4-HMAC", "")
            body = await request.body()
            webhook_secret = os.getenv("WEBHOOK_SECRET", "")
            if not webhook_secret or not signature:
                return JSONResponse(status_code=401, content={"detail": "Webhook auth required"})
            import hashlib
            import hmac

            digest = hmac.new(webhook_secret.encode(), body, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(digest, signature):
                return JSONResponse(status_code=401, content={"detail": "Invalid webhook signature"})

        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token required"},
            )

        try:
            secret = os.getenv("JWT_SECRET")
            if not secret:
                logger.critical("JWT_SECRET is not configured!")
                return JSONResponse(
                    status_code=500,
                    content={"detail": "Server configuration error"},
                )
            weak_patterns = ("changeme", "secret", "password", "jwt_secret", "test")
            if len(secret) < 32 or any(p in secret.lower() for p in weak_patterns):
                logger.critical("JWT_SECRET is too weak!")
                return JSONResponse(
                    status_code=500,
                    content={"detail": "Server configuration error"},
                )

            payload = jwt.decode(token, secret, algorithms=["HS256"])
            request.state.user = payload
        except jwt.ExpiredSignatureError:
            logger.warning("Expired token")
            return JSONResponse(
                status_code=401,
                content={"detail": "Token expired"},
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid token"},
            )

        if body:
            async def receive() -> dict[str, Any]:
                return {"type": "http.request", "body": body, "more_body": False}

            request = Request(request.scope, receive)
        return await call_next(request)
