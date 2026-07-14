"""
C44TCDI: Supabase Anonymous Authentication
Zero-PII authentication using Supabase Auth (anonymous sign-in).
"""
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any

import httpx


# Unified with ~/.c4reqber (Python wizard + Go persist). Fallback for migration.
_c4_home = Path.home() / ".c4reqber"
if not _c4_home.exists():
    _c4_home = Path.home() / ".config" / "c4reqber"
SESSION_PATH = _c4_home / "supabase_session.json"

_HAS_SUPABASE = False
try:
    from supabase import create_client

    _HAS_SUPABASE = True
except ImportError:
    pass


def _ensure_session_dir() -> None:
    SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)


def generate_local_uuid() -> str:
    """Generate a local-only UUID for fallback auth."""
    return f"local_{uuid.uuid4().hex}"


def _load_session() -> dict[str, Any] | None:
    if not SESSION_PATH.exists():
        return None
    try:
        return json.loads(SESSION_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _save_session(session: dict[str, Any]) -> None:
    _ensure_session_dir()
    SESSION_PATH.write_text(json.dumps(session, indent=2))


def _clear_session() -> None:
    if SESSION_PATH.exists():
        SESSION_PATH.unlink()


class SupabaseAnonAuth:
    """
    Zero-PII anonymous authentication via Supabase Auth.
    Falls back to local-only UUID when Supabase is not configured.
    """

    def __init__(
        self,
        supabase_url: str | None = None,
        supabase_key: str | None = None,
    ) -> None:
        raw_url = supabase_url or os.getenv("SUPABASE_URL", "")
        self.supabase_url = raw_url.rstrip("/") if raw_url else ""
        self.supabase_key = supabase_key or os.getenv("SUPABASE_ANON_KEY", "") or ""
        self._async_client: httpx.AsyncClient | None = None
        self._sync_client: httpx.Client | None = None
        self._supabase: Any = None
        if _HAS_SUPABASE and self.is_configured():
            self._supabase = create_client(self.supabase_url, self.supabase_key)

    def _api_headers(self, bearer_token: str | None = None) -> dict[str, str]:
        token = bearer_token or self.supabase_key
        return {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def is_configured(self) -> bool:
        """Check if Supabase credentials are available."""
        return bool(self.supabase_url and self.supabase_key)

    # ─── Sync helpers ───

    def _sync_request(
        self,
        method: str,
        path: str,
        json_data: dict[str, Any] | None = None,
        bearer_token: str | None = None,
    ) -> dict[str, Any]:
        if not self._sync_client:
            self._sync_client = httpx.Client(timeout=30.0)
        url = f"{self.supabase_url}{path}"
        kwargs: dict[str, Any] = {"headers": self._api_headers(bearer_token)}
        if json_data is not None:
            kwargs["json"] = json_data
        resp = self._sync_client.request(method, url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    # ─── Async helpers ───

    async def _async_request(
        self,
        method: str,
        path: str,
        json_data: dict[str, Any] | None = None,
        bearer_token: str | None = None,
    ) -> dict[str, Any]:
        if not self._async_client:
            self._async_client = httpx.AsyncClient(timeout=30.0)
        url = f"{self.supabase_url}{path}"
        kwargs: dict[str, Any] = {"headers": self._api_headers(bearer_token)}
        if json_data is not None:
            kwargs["json"] = json_data
        resp = await self._async_client.request(method, url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    # ─── Public sync API ───

    def sign_up_anon(self) -> dict[str, str]:
        """
        Create an anonymous user.
        Returns {user_id, access_token, refresh_token}.
        """
        if not self.is_configured():
            user_id = generate_local_uuid()
            session = {
                "user_id": user_id,
                "access_token": user_id,
                "refresh_token": user_id,
            }
            _save_session(session)
            return session

        # Prefer supabase-py if available
        if self._supabase is not None:
            try:
                resp = self._supabase.auth.sign_in_anonymously()
                user = resp.user
                session = {
                    "user_id": str(user.id) if user and getattr(user, "id", None) else "",
                    "access_token": resp.session.access_token if resp.session else "",
                    "refresh_token": resp.session.refresh_token if resp.session else "",
                }
                _save_session(session)
                return session
            except (httpx.HTTPStatusError, RuntimeError, ValueError):
                pass  # Fall through to raw HTTP

        # Raw HTTP: try native anonymous signup
        try:
            data = self._sync_request("POST", "/auth/v1/signup", {"data": {}})
        except httpx.HTTPStatusError as exc:
            # Fallback: anon email if anonymous sign-in not enabled on plan
            if exc.response.status_code in (400, 403, 422):
                payload = {
                    "email": f"anon_{uuid.uuid4().hex}@c4reqber.local",
                    "password": uuid.uuid4().hex,
                    "data": {},
                }
                data = self._sync_request("POST", "/auth/v1/signup", payload)
            else:
                raise

        user = data.get("user") or {}
        session = {
            "user_id": user.get("id", ""),
            "access_token": data.get("access_token", ""),
            "refresh_token": data.get("refresh_token", ""),
        }
        _save_session(session)
        return session

    def get_user(self, access_token: str) -> str | None:
        """Validate token and return user_id."""
        if not self.is_configured():
            return access_token if access_token.startswith("local_") else None

        if self._supabase is not None:
            try:
                resp = self._supabase.auth.get_user(access_token)
                return str(resp.user.id) if resp.user else None
            except (httpx.HTTPStatusError, RuntimeError, ValueError):
                return None

        try:
            data = self._sync_request("GET", "/auth/v1/user", bearer_token=access_token)
            return data.get("id")
        except httpx.HTTPStatusError:
            return None

    def refresh_session(self, refresh_token: str) -> dict[str, str]:
        """Get new access token from refresh token."""
        if not self.is_configured():
            return {
                "user_id": refresh_token,
                "access_token": refresh_token,
                "refresh_token": refresh_token,
            }

        if self._supabase is not None:
            try:
                resp = self._supabase.auth.refresh_session(refresh_token)
                user = resp.user
                session = {
                    "user_id": str(user.id) if user and getattr(user, "id", None) else "",
                    "access_token": resp.session.access_token if resp.session else "",
                    "refresh_token": resp.session.refresh_token if resp.session else "",
                }
                _save_session(session)
                return session
            except (httpx.HTTPStatusError, RuntimeError, ValueError):
                pass

        data = self._sync_request(
            "POST",
            "/auth/v1/token?grant_type=refresh_token",
            {"refresh_token": refresh_token},
        )
        user = data.get("user") or {}
        session = {
            "user_id": user.get("id", ""),
            "access_token": data.get("access_token", ""),
            "refresh_token": data.get("refresh_token", ""),
        }
        _save_session(session)
        return session

    def sign_out(self, access_token: str) -> bool:
        """Invalidate session."""
        if not self.is_configured():
            _clear_session()
            return True

        if self._supabase is not None:
            try:
                self._supabase.auth.sign_out()
                _clear_session()
                return True
            except (httpx.HTTPStatusError, RuntimeError, ValueError):
                return False

        try:
            self._sync_request("POST", "/auth/v1/logout", {}, bearer_token=access_token)
            _clear_session()
            return True
        except httpx.HTTPStatusError:
            return False

    # ─── Public async API ───

    async def async_sign_up_anon(self) -> dict[str, str]:
        """Async sign up anon."""
        if not self.is_configured():
            user_id = generate_local_uuid()
            session = {
                "user_id": user_id,
                "access_token": user_id,
                "refresh_token": user_id,
            }
            _save_session(session)
            return session

        # supabase-py is sync-only; use raw HTTP for async
        try:
            data = await self._async_request("POST", "/auth/v1/signup", {"data": {}})
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (400, 403, 422):
                payload = {
                    "email": f"anon_{uuid.uuid4().hex}@c4reqber.local",
                    "password": uuid.uuid4().hex,
                    "data": {},
                }
                data = await self._async_request("POST", "/auth/v1/signup", payload)
            else:
                raise

        user = data.get("user") or {}
        session = {
            "user_id": user.get("id", ""),
            "access_token": data.get("access_token", ""),
            "refresh_token": data.get("refresh_token", ""),
        }
        _save_session(session)
        return session

    async def async_get_user(self, access_token: str) -> str | None:
        """Async get user."""
        if not self.is_configured():
            return access_token if access_token.startswith("local_") else None

        try:
            data = await self._async_request(
                "GET", "/auth/v1/user", bearer_token=access_token
            )
            return data.get("id")
        except httpx.HTTPStatusError:
            return None

    async def async_refresh_session(self, refresh_token: str) -> dict[str, str]:
        """Async refresh session."""
        if not self.is_configured():
            return {
                "user_id": refresh_token,
                "access_token": refresh_token,
                "refresh_token": refresh_token,
            }

        data = await self._async_request(
            "POST",
            "/auth/v1/token?grant_type=refresh_token",
            {"refresh_token": refresh_token},
        )
        user = data.get("user") or {}
        session = {
            "user_id": user.get("id", ""),
            "access_token": data.get("access_token", ""),
            "refresh_token": data.get("refresh_token", ""),
        }
        _save_session(session)
        return session

    async def async_sign_out(self, access_token: str) -> bool:
        """Async sign out."""
        if not self.is_configured():
            _clear_session()
            return True

        try:
            await self._async_request(
                "POST", "/auth/v1/logout", {}, bearer_token=access_token
            )
            _clear_session()
            return True
        except httpx.HTTPStatusError:
            return False


# ─── Database schema helper ───

async def ensure_tables(supabase_client: Any) -> None:
    """
    Create users, credits, usage_log tables if not exist.
    Accepts a raw httpx client or supabase-py client.
    """
    if hasattr(supabase_client, "table"):
        try:
            await supabase_client.table("users").select(
                "id", count="exact"
            ).limit(1).execute()
        except (httpx.HTTPStatusError, RuntimeError, ValueError):
            pass
        return

    if hasattr(supabase_client, "post"):
        ddl = (
            "CREATE TABLE IF NOT EXISTS users ("
            "  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),"
            "  created_at TIMESTAMPTZ DEFAULT now(),"
            "  last_seen TIMESTAMPTZ DEFAULT now()"
            ");"
            "CREATE TABLE IF NOT EXISTS credits ("
            "  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,"
            "  balance INTEGER DEFAULT 0,"
            "  updated_at TIMESTAMPTZ DEFAULT now()"
            ");"
            "CREATE TABLE IF NOT EXISTS usage_log ("
            "  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),"
            "  user_id UUID REFERENCES users(id) ON DELETE CASCADE,"
            "  action TEXT NOT NULL,"
            "  metadata JSONB DEFAULT '{}',"
            "  created_at TIMESTAMPTZ DEFAULT now()"
            ");"
        )
        try:
            await supabase_client.post(
                "/rest/v1/rpc/execute_sql",
                json={"query": ddl},
            )
        except (httpx.HTTPStatusError, RuntimeError, ValueError):
            pass
