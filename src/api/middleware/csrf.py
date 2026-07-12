from __future__ import annotations


"""
CSRF Protection Middleware for Reqber API.

Implements double-submit cookie pattern for CSRF protection.
Generates CSRF tokens and validates them on state-changing requests.
"""
import hashlib
import hmac
import logging
import os
import secrets
import time
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


logger = logging.getLogger(__name__)

# CSRF cookie name
CSRF_COOKIE = "csrf_token"
CSRF_HEADER = "X-CSRF-Token"

# CSRF token expiry (1 hour)
CSRF_TOKEN_EXPIRY = 3600


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """CSRF protection using double-submit cookie pattern.

    On state-changing requests (POST, PUT, DELETE, PATCH):
    - Validates that the X-CSRF-Token header matches the CSRF cookie
    - Ensures the token is not expired
    """

    def __init__(self, app: Any) -> None:
        super().__init__(app)
        env_secret = os.getenv("CSRF_SECRET", "")
        if env_secret and len(env_secret) >= 32:
            self._secret = env_secret
            self._generated = False
        else:
            # Dev / first-boot fallback: generate a runtime secret so the app
            # can start. CSRF tokens remain valid for the lifetime of this
            # process, so set CSRF_SECRET explicitly in any multi-instance or
            # restart-sensitive deployment.
            self._secret = secrets.token_urlsafe(32)
            self._generated = True
            logger.warning(
                "CSRF_SECRET not set or <32 chars; generated a runtime secret "
                "(valid for this process only). Set CSRF_SECRET in production "
                "deployments to keep tokens stable across restarts."
            )

    def _generate_token(self, request: Request) -> str:
        """Generate a CSRF token for the request.

        Args:
            request: The incoming request.

        Returns:
            CSRF token string.
        """
        random_part = secrets.token_hex(16)
        timestamp = str(int(time.time()))
        signature = hmac.new(
            self._secret.encode() if self._secret else b"",
            f"{random_part}:{timestamp}".encode(),
            hashlib.sha256,
        ).hexdigest()
        return f"{random_part}:{timestamp}:{signature}"

    def _validate_token(self, token: str) -> bool:
        """Validate a CSRF token.

        Args:
            token: The token to validate.

        Returns:
            True if valid, False otherwise.
        """
        try:
            parts = token.split(":")
            if len(parts) != 3:
                return False

            random_part, timestamp_str, signature = parts

            # Check expiry
            timestamp = int(timestamp_str)
            if time.time() - timestamp > CSRF_TOKEN_EXPIRY:
                return False

            # Verify signature
            expected_sig = hmac.new(
                self._secret.encode() if self._secret else b"",
                f"{random_part}:{timestamp_str}".encode(),
                hashlib.sha256,
            ).hexdigest()

            return hmac.compare_digest(signature, expected_sig)
        except (ValueError, IndexError):
            return False

    def _csrf_error(self, status_code: int, detail: str) -> Response:
        """Return a JSON error without raising through BaseHTTPMiddleware."""
        from starlette.responses import JSONResponse

        return JSONResponse(status_code=status_code, content={"detail": detail})

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request, validating CSRF tokens as needed."""
        # Machine clients (TUI after login, MCP, curl with JWT) use Bearer auth —
        # double-submit CSRF is a browser-cookie concern only.
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer ") and len(auth) > len("Bearer "):
            return await call_next(request)

        # Skip CSRF for safe methods
        if request.method in ("GET", "HEAD", "OPTIONS"):
            response = await call_next(request)

            # Set CSRF cookie on GET requests (for forms that need it)
            if request.url.path not in ("/health", "/docs", "/redoc", "/openapi.json"):
                csrf_token = self._generate_token(request)
                secure_cookies = os.getenv("SECURE_COOKIES", "true").lower() == "true"
                response.set_cookie(
                    key=CSRF_COOKIE,
                    value=csrf_token,
                    httponly=False,
                    secure=secure_cookies,
                    samesite="strict",
                    max_age=CSRF_TOKEN_EXPIRY,
                )

            return response

        # For state-changing requests, validate CSRF token
        csrf_cookie = request.cookies.get(CSRF_COOKIE)
        csrf_header = request.headers.get(CSRF_HEADER)

        if not csrf_cookie or not csrf_header:
            logger.warning("Missing CSRF token (cookie=%s, header=%s)", csrf_cookie, csrf_header)
            return self._csrf_error(403, "CSRF token missing")

        if csrf_cookie != csrf_header:
            logger.warning("CSRF token mismatch")
            return self._csrf_error(403, "CSRF token mismatch")

        if not self._validate_token(csrf_cookie):
            logger.warning("Invalid or expired CSRF token")
            return self._csrf_error(403, "Invalid CSRF token")

        return await call_next(request)
