"""
TURBO-CDI API: Authentication
JWT-based auth with bcrypt
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict
import bcrypt
import jwt


class AuthManager:
    """JWT authentication manager."""

    def __init__(self):
        self.secret = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.token_expire_hours = 24

    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode(), hashed.encode())

    def create_token(self, user_id: str) -> str:
        """Create JWT token."""
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(hours=self.token_expire_hours),
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def decode_token(self, token: str) -> Optional[Dict]:
        """Decode and validate JWT token."""
        try:
            return jwt.decode(token, self.secret, algorithms=[self.algorithm])
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    async def create_user(self, email: str, password: str, name: Optional[str]) -> Dict:
        """Create new user."""
        from src.api.database import get_db

        db = await get_db()
        user_id = str(uuid.uuid4())
        password_hash = self.hash_password(password)

        async with db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO users (id, email, password_hash, name, created_at)
                VALUES ($1, $2, $3, $4, $5)
                """,
                user_id,
                email,
                password_hash,
                name,
                datetime.utcnow(),
            )

        return {
            "id": user_id,
            "email": email,
            "name": name,
            "created_at": datetime.utcnow(),
        }

    async def authenticate(self, email: str, password: str) -> Optional[str]:
        """Authenticate user and return token."""
        from src.api.database import get_db

        db = await get_db()

        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, password_hash FROM users WHERE email = $1", email
            )

        if not row:
            return None

        if not self.verify_password(password, row["password_hash"]):
            return None

        return self.create_token(row["id"])

    async def get_user_from_token(self, token: str) -> Optional[Dict]:
        """Get user from JWT token."""
        payload = self.decode_token(token)
        if not payload:
            return None

        from src.api.database import get_db

        db = await get_db()

        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, email, name FROM users WHERE id = $1", payload["user_id"]
            )

        return dict(row) if row else None
