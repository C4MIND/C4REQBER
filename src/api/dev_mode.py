"""
C4REQBER: Dev Mode Authentication
Simplifies auth in development mode by optionally bypassing authentication
or returning a test user.
"""
from __future__ import annotations

import hmac
import os

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.api.models import User


security = HTTPBearer(auto_error=False)


def is_dev_mode(request: Request | None = None) -> bool:
    """Check if DEV_MODE is enabled with cryptographic bypass token."""
    if os.getenv("DEV_MODE", "").lower() not in ("true", "1", "yes", "on"):
        return False
    if request is None:
        return False
    expected = os.getenv("DEV_MODE_BYPASS_TOKEN", "")
    if not expected:
        return False
    token = request.headers.get("X-C4-DEV-BYPASS", "")
    return hmac.compare_digest(token, expected)


def get_dev_user() -> User:
    """Return a test user for development mode."""
    return User(
        id=os.getenv("DEV_USER_ID", "dev-user-001"),
        email="dev@c4reqber.local",
        name=os.getenv("DEV_USER_NAME", "Developer"),
    )


async def dev_mode_dependency(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User | None:
    """
    FastAPI dependency that optionally bypasses auth in dev mode.

    In dev mode (DEV_MODE=true):
      - Returns the dev user regardless of credentials.
    In production:
      - Validates the JWT token and returns the authenticated user.
      - Raises 401 if no valid token is provided.
    """
    if is_dev_mode(request):
        return get_dev_user()

    # Production: require valid JWT
    token = None
    if credentials:
        token = credentials.credentials
    else:
        # Fallback to query param or cookie
        token = request.query_params.get("token") or request.cookies.get("c4_cdi_turbo_token")

    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    from src.api.auth import AuthManager

    auth = AuthManager()
    user = await auth.get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


class DevModeAuth:
    """Convenience class exposing dev-mode auth helpers."""

    @staticmethod
    def is_dev_mode() -> bool:
        return is_dev_mode()

    @staticmethod
    def get_dev_user() -> User:
        return get_dev_user()

    @staticmethod
    async def dependency(
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = Depends(security),
    ) -> User | None:
        return await dev_mode_dependency(request, credentials)
