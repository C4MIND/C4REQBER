"""
C4REQBER API: Authentication v2
JWT-based auth with bcrypt + httpOnly cookies support

Phase 5: Production-ready auth with cookie-based tokens.
Dev mode: falls back to localStorage for testing.
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import bcrypt
import jwt

from src.compat import UTC


if TYPE_CHECKING:
    import redis

from src.api.models import User


logger = logging.getLogger("c4_cdi_turbo.auth")

_revoked_tokens: set[str] = set()
_user_revocation_markers: dict[str, float] = {}


async def _get_redis() -> redis.asyncio.Redis | None:
    """Get Redis connection for token revocation."""
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
    try:
        import redis.asyncio as aioredis

        return aioredis.from_url(redis_url, decode_responses=True)  # type: ignore[no-untyped-call,no-any-return]
    except (OSError, ConnectionError, ImportError):
        return None


async def revoke_token(jti: str, ttl: int = 86400) -> None:
    """Revoke a JWT token — persists across restarts via Redis.

    Args:
        jti: Token unique identifier.
        ttl: Time-to-live in seconds (default 24h).
    """
    _revoked_tokens.add(jti)
    redis = await _get_redis()
    if redis:
        try:
            await redis.setex(f"revoked:jti:{jti}", ttl, "1")
        except (OSError, ConnectionError):
            pass


async def revoke_all_user_tokens(user_id: str, ttl: int = 86400) -> None:
    """Revoke all tokens for a user by storing a user-level revocation marker.

    Any token issued before this marker timestamp is considered revoked.
    """
    now = time.time()
    _user_revocation_markers[user_id] = now
    redis = await _get_redis()
    if redis:
        try:
            await redis.setex(f"revoked:user:{user_id}", ttl, str(now))
        except (OSError, ConnectionError):
            pass


async def is_token_revoked(jti: str, user_id: str | None = None, iat: float | None = None) -> bool:
    """Check if a JWT token is revoked.

    Checks both per-token (jti) revocation and user-level revocation.
    If user_id and iat are provided, also checks if the user's tokens
    were revoked after this token was issued.

    Falls back to in-memory _revoked_tokens when Redis is unavailable.
    """
    if jti in _revoked_tokens:
        return True

    # Check in-memory user revocation markers first (fast path, no I/O)
    if user_id and iat is not None:
        marker = _user_revocation_markers.get(user_id)
        if marker and marker > iat:
            return True

    redis = await _get_redis()
    if redis:
        try:
            exists = await redis.exists(f"revoked:jti:{jti}")
            if exists:
                _revoked_tokens.add(jti)
                return True
            if user_id and iat is not None:
                revoked_at = await redis.get(f"revoked:user:{user_id}")
                if revoked_at and float(revoked_at) > iat:
                    return True
        except (OSError, ConnectionError, ValueError):
            pass
    return False


class MissingJWTSecretError(RuntimeError):
    """Raised when JWT_SECRET is not configured."""

    pass


class AuthManager:
    """JWT authentication manager with cookie support.

    Lazy-loads the JWT secret on first use to avoid import-time crashes
    in development mode.
    """

    def __init__(self) -> None:
        self._lazy_secret: str | None = None
        self.algorithm = "HS256"
        self.token_expire_hours = int(os.getenv("JWT_EXPIRE_HOURS", "24"))
        self.issuer = os.getenv("JWT_ISSUER", "c4reqber")

    @property
    def secret(self) -> str:
        if self._lazy_secret is None:
            self._lazy_secret = os.getenv("JWT_SECRET") or os.getenv("C4REQBER_JWT_SECRET")
            if not self._lazy_secret:
                raise MissingJWTSecretError(
                    "JWT_SECRET or C4REQBER_JWT_SECRET environment variable is required. "
                    "Set a dummy value for development (e.g., export JWT_SECRET=dev-secret)."
                )
        return self._lazy_secret

    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode(), hashed.encode())

    def create_token(self, user_id: str) -> str:
        """Create JWT token with jti for revocation support."""
        now = datetime.now(UTC)
        payload = {
            "jti": str(uuid.uuid4()),
            "sub": str(user_id),
            "user_id": str(user_id),
            "iss": self.issuer,
            "exp": now + timedelta(hours=self.token_expire_hours),
            "iat": now,
            "type": "access",
        }
        assert self.secret is not None
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: str) -> str:
        """Create long-lived refresh token."""
        now = datetime.now(UTC)
        payload = {
            "jti": str(uuid.uuid4()),
            "sub": str(user_id),
            "user_id": str(user_id),
            "iss": self.issuer,
            "exp": now + timedelta(days=30),
            "iat": now,
            "type": "refresh",
        }
        assert self.secret is not None
        assert self.secret is not None
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    async def decode_token(self, token: str) -> dict | None:  # type: ignore[type-arg]
        """Decode and validate JWT token."""
        try:
            assert self.secret is not None
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm],
                issuer=self.issuer,
                options={"require": ["exp", "sub", "jti"], "verify_exp": True},
            )
            user_id = payload.get("sub") or payload.get("user_id")
            # iat from PyJWT is a datetime when decoded; convert to timestamp
            iat_raw = payload.get("iat")
            iat = iat_raw.timestamp() if isinstance(iat_raw, datetime) else iat_raw
            if await is_token_revoked(
                payload.get("jti", ""), user_id=user_id, iat=iat
            ):
                return None
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    async def create_user(self, email: str, password: str, name: str | None) -> User:
        """Create new user in SQLite database."""
        from src.api.db_manager import get_db

        db = await get_db()
        user_id = str(uuid.uuid4())
        password_hash = self.hash_password(password)

        # SQLite async wrapper
        import sqlite3
        from pathlib import Path

        db_path = Path(__file__).parent.parent.parent / "data" / "c4_cdi_turbo.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(str(db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                "INSERT INTO users (id, email, password_hash, name, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, email, password_hash, name, datetime.now(UTC)),
            )
            conn.commit()

        return User(
            id=user_id,
            email=email,
            name=name,
            created_at=datetime.now(UTC),
        )

    async def authenticate(self, email: str, password: str) -> str | None:
        """Authenticate user and return token."""
        import sqlite3
        from pathlib import Path

        db_path = Path(__file__).parent.parent.parent / "data" / "c4_cdi_turbo.db"

        with sqlite3.connect(str(db_path)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT id, password_hash FROM users WHERE email = ?", (email,)
            ).fetchone()

        if not row:
            return None

        if not self.verify_password(password, row["password_hash"]):
            return None

        return self.create_token(row["id"])

    async def get_user_from_token(self, token: str) -> User | None:
        """Get user from JWT token."""
        payload = await self.decode_token(token)
        if not payload:
            return None

        import sqlite3
        from pathlib import Path

        db_path = Path(__file__).parent.parent.parent / "data" / "c4_cdi_turbo.db"

        with sqlite3.connect(str(db_path)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT id, email, name, created_at FROM users WHERE id = ?",
                (payload["user_id"],),
            ).fetchone()

        if not row:
            return None
        return User(
            id=row["id"],
            email=row["email"],
            name=row["name"] if "name" in row.keys() else None,
            created_at=row["created_at"] if "created_at" in row.keys() else None,
        )

    async def revoke_token(self, jti: str, ttl: int = 86400) -> None:
        """Revoke a token by its jti."""
        await revoke_token(jti, ttl)

    async def is_revoked(self, jti: str) -> bool:
        """Check if a token is revoked."""
        return await is_token_revoked(jti)

    def get_cookie_settings(self) -> dict[str, str | bool | int]:
        """Get secure cookie settings for JWT."""
        is_production = os.getenv("ENV", "development") == "production"
        return {
            "key": "c4_cdi_turbo_token",
            "httponly": True,
            "secure": is_production,
            "samesite": "lax",
            "max_age": self.token_expire_hours * 3600,
            "path": "/",
        }
