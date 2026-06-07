"""
C4REQBER API: Shared Dependencies
Auth, rate limiting, cache, helpers.
"""
from __future__ import annotations

import math
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.api.auth import AuthManager
from src.api.cache import CacheManager
from src.api.models import User
from src.api.rate_limiter import RateLimiter


security = HTTPBearer(auto_error=False)
cache = CacheManager()
rate_limiter = RateLimiter()
auth_manager = AuthManager()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_manager: Any = None,
) -> User:
    """Validate JWT token and return user. In dev mode, returns test user."""
    from src.api.dev_mode import get_dev_user, is_dev_mode

    if is_dev_mode(request):
        return get_dev_user()

    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme. Use Bearer.",
        )
    am = auth_manager or AuthManager()
    user = await am.get_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    auth_manager: Any = None,
) -> User | None:
    """Optional JWT validation — returns user if token is valid, else None."""
    if not credentials or credentials.scheme.lower() != "bearer":
        return None
    am = auth_manager or AuthManager()
    return await am.get_user_from_token(credentials.credentials)


async def check_rate_limit_ip(
    request: Request,
    rate_limiter: Any = None,
) -> bool:
    """Check API rate limits by IP for unauthenticated endpoints."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[-1].strip()
    elif request.client:
        client_ip = request.client.host
    else:
        client_ip = "unknown"
    rl = rate_limiter or RateLimiter()
    allowed = await rl.check_limit(f"ip:{client_ip}")
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
        )
    return True


def sanitize_json(obj: Any) -> Any:
    """Recursively replace NaN/Inf float values with None for JSON compliance."""
    if isinstance(obj, dict):
        return {k: sanitize_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_json(item) for item in obj]
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    return obj
