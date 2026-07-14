"""
C4REQBER API: Authentication Router
"""

from __future__ import annotations

import logging
import sqlite3
import time
from collections import defaultdict
from datetime import datetime
from typing import Any

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from src.api.auth import (
    AuthManager,
    MissingJWTSecretError,
    revoke_all_user_tokens,
    revoke_token,
)
from src.api.dependencies import get_current_user
from src.api.models import TokenResponse, User, UserCreate, UserResponse
from src.compat import UTC


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
auth_manager = AuthManager()

_runtime_api_keys: dict[str, str] = {}
_runtime_key_expiry: dict[str, float] = {}
_RUNTIME_KEY_TTL = 3600  # 1 hour auto-expiry for in-memory keys


def _mask_key(key: str) -> str:
    """Mask API key for safe display: sk-or-v1-abc...xyz."""
    return key[:12] + "..." + key[-4:] if len(key) > 20 else "***"


def get_runtime_api_key(provider: str) -> str | None:
    """Get API key from runtime store with TTL enforcement. Returns None if expired."""
    import time as _time

    now = _time.time()
    if now - _runtime_key_expiry.get(provider, 0) > _RUNTIME_KEY_TTL:
        _runtime_api_keys.pop(provider, None)
        _runtime_key_expiry.pop(provider, None)
        return None
    return _runtime_api_keys.get(provider)


_login_attempts: dict[str, list[float]] = defaultdict(list)
MAX_ATTEMPTS = 5
LOCKOUT_WINDOW = 300

ALGORITHM = "HS256"


async def check_brute_force(identifier: str) -> bool:
    """Check if login is rate-limited due to too many attempts."""
    now = time.time()
    attempts = [a for a in _login_attempts[identifier] if now - a < LOCKOUT_WINDOW]
    _login_attempts[identifier] = attempts

    if len(attempts) >= MAX_ATTEMPTS:
        oldest = min(attempts)
        wait_time = min(2 ** (len(attempts) - MAX_ATTEMPTS), 3600)
        if now - oldest < wait_time:
            return False
    return True


async def record_failed_attempt(identifier: str) -> None:
    """Record a failed login attempt."""
    _login_attempts[identifier].append(time.time())


def _extract_token(request: Request) -> str | None:
    """Extract JWT from cookie or Authorization header."""
    token = request.cookies.get("access_token")
    if token:
        return token
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


@router.post("/register", response_model=UserResponse, operation_id="authRegister")
async def register(request: Request, user_data: UserCreate) -> UserResponse:
    """Register."""
    ip = request.client.host if request.client else "unknown"
    if not await check_brute_force(f"register:{ip}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many register attempts. Please wait.",
        )
    try:
        user = await auth_manager.create_user(
            email=user_data.email, password=user_data.password, name=user_data.name
        )
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            created_at=user.created_at or datetime.now(UTC),
        )
    except sqlite3.IntegrityError:
        # User already exists — idempotent, return 200 with existing user info
        existing = await auth_manager.get_user_by_email(user_data.email)
        if existing:
            return UserResponse(
                id=existing.id,
                email=existing.email,
                name=existing.name or "",
                created_at=existing.created_at or datetime.now(UTC),
            )
        raise HTTPException(status_code=409, detail="User already exists") from None


@router.post("/login", response_model=TokenResponse, operation_id="authLogin")
async def login(request: Request, credentials: UserCreate) -> TokenResponse:
    """Login."""
    ip = request.client.host if request.client else "unknown"

    if not await check_brute_force(ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please wait.",
        )

    token = await auth_manager.authenticate(credentials.email, credentials.password)
    if not token:
        await record_failed_attempt(ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(access_token=token, token_type="bearer")


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)) -> dict[str, Any]:
    return {"id": user.id, "email": user.email, "name": user.name}


@router.post("/settings/keys")
async def update_api_keys(
    payload: dict[str, Any],
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Update api keys."""
    import time as _time

    now = _time.time()
    # Auto-expire keys older than TTL
    for k in list(_runtime_api_keys):
        if now - _runtime_key_expiry.get(k, 0) > _RUNTIME_KEY_TTL:
            del _runtime_api_keys[k]
            _runtime_key_expiry.pop(k, None)
    openrouter_key = payload.get("openrouter_api_key")
    if openrouter_key is not None:
        _runtime_api_keys["openrouter_api_key"] = str(openrouter_key)
        _runtime_key_expiry["openrouter_api_key"] = now
        try:
            from src.llm.client import LLMClient

            if hasattr(LLMClient, "_global_api_key"):
                LLMClient._global_api_key = str(openrouter_key)
        except Exception as e:
            logging.getLogger("c4_cdi_turbo").warning("Failed to update LLM client API key: %s", e)
    return {
        "status": "ok",
        "keys_updated": ["openrouter_api_key"] if openrouter_key is not None else [],
    }


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """Logout — revoke current token and all user tokens."""
    token = _extract_token(request)
    if token:
        try:
            auth_manager = AuthManager()
            payload = jwt.decode(
                token,
                auth_manager.secret,
                algorithms=[ALGORITHM],
                options={"verify_exp": False},
            )
            jti = payload.get("jti")
            user_id = payload.get("sub") or payload.get("user_id")
            if jti:
                await revoke_token(jti)
            if user_id:
                await revoke_all_user_tokens(user_id)
        except MissingJWTSecretError:
            pass
        except jwt.InvalidTokenError:
            pass

    response = JSONResponse({"message": "Logged out"})
    response.delete_cookie("access_token")
    return response


@router.post("/logout-all")
async def logout_all(
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """Logout all sessions for current user."""
    user_id = current_user.id
    if user_id:
        await revoke_all_user_tokens(user_id)

    response = JSONResponse({"message": "All sessions logged out"})
    response.delete_cookie("access_token")
    return response
