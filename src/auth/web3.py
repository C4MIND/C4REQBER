"""
Web3 wallet connector (MetaMask / WalletConnect-compatible) for c4reqber.

Authenticates users via EIP-191 personal sign without storing any personal data.
Only wallet_address (lowercase) -> uuid mapping is persisted in SQLite.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
import time
import uuid
from typing import Any


# ── optional web3.py ────────────────────────────────────────────────────────
try:
    from eth_account.messages import encode_defunct
    from eth_utils import to_checksum_address
    from web3 import Web3

    _HAS_WEB3 = True
except (ImportError, ModuleNotFoundError):
    _HAS_WEB3 = False

# ── optional ecdsa fallback ─────────────────────────────────────────────────
try:
    import ecdsa
    from ecdsa import BadSignatureError, SECP256k1, VerifyingKey

    _HAS_ECDSA = True
except (ImportError, ModuleNotFoundError):
    _HAS_ECDSA = False

# ── optional PyJWT ──────────────────────────────────────────────────────────
try:
    import jwt as _jwt_lib

    _HAS_JWT = True
except (ImportError, ModuleNotFoundError):
    _HAS_JWT = False

# ── constants ───────────────────────────────────────────────────────────────
DEFAULT_RPC = "https://eth.llamarpc.com"
DB_PATH = os.environ.get("C4REQBER_WEB3_DB", os.path.join(os.path.dirname(__file__), "..", "..", "data", "web3_auth.db"))
_JWT_SECRET: str | None = None


def _get_jwt_secret(_self: Any = None) -> str:
    """Lazy-load JWT secret to avoid import-time crashes in dev mode."""
    global _JWT_SECRET
    if _JWT_SECRET is None:
        _JWT_SECRET = os.environ.get("C4REQBER_JWT_SECRET") or os.environ.get("JWT_SECRET")
        dev = os.environ.get("DEV_MODE", "").lower() in ("1", "true", "yes")
        if not _JWT_SECRET:
            if dev:
                _JWT_SECRET = "dev-secret-do-not-use-in-production-min-32-chars"
            else:
                raise RuntimeError(
                    "JWT_SECRET (or C4REQBER_JWT_SECRET) must be set in production"
                )
        elif len(_JWT_SECRET) < 32 and not dev:
            raise RuntimeError("JWT_SECRET must be at least 32 characters in production")
    return _JWT_SECRET


JWT_SECRET = property(_get_jwt_secret)  # type: ignore[assignment]
JWT_ALGORITHM = "HS256"
JWT_EXP_SECONDS = 86400 * 7  # 7 days


def _ensure_db(path: str) -> None:
    """Create SQLite DB and table if they don't exist."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS web3_users (
            wallet_address TEXT PRIMARY KEY,
            user_uuid TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            last_seen INTEGER NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS web3_sessions (
            wallet_address TEXT PRIMARY KEY,
            token TEXT NOT NULL,
            expires_at INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def _eip191_message_hash(message: str) -> bytes:  # type: ignore[return]
    """Return keccak256 hash of the EIP-191 prefixed message."""
    prefix = f"\x19Ethereum Signed Message:\n{len(message)}{message}"
    prefix_bytes = prefix.encode("utf-8")
    try:
        from eth_hash.auto import keccak
        return keccak(prefix_bytes)
    except (ImportError, ModuleNotFoundError):
        # fallback via hashlib.sha3_256 (NOT keccak, but we warn)
        # In production without web3/ecdsa this is a degraded path.
        return hashlib.sha3_256(prefix_bytes).digest()


def _recover_address_from_signature(message: str, signature: str) -> str | None:
    """
    Recover Ethereum address from EIP-191 personal signature.
    Supports web3.py (preferred) and ecdsa fallback.
    """
    if not signature.startswith("0x"):
        signature = "0x" + signature
    sig_bytes = bytes.fromhex(signature[2:])
    if len(sig_bytes) != 65:
        return None

    r = sig_bytes[:32]
    s = sig_bytes[32:64]
    v = sig_bytes[64]
    if v < 27:
        v += 27

    if _HAS_WEB3:
        try:
            w3 = Web3()
            message_hash = encode_defunct(text=message)
            recovered = w3.eth.account.recover_message(message_hash, signature=signature)
            return recovered.lower()
        except (ValueError, TypeError, KeyError):
            pass

    if _HAS_ECDSA:
        try:
            msg_hash = _eip191_message_hash(message)
            # ecdsa recovery: try both recovery ids (27/28 -> 0/1)
            for rec_id in (0, 1):
                try:
                    vk = VerifyingKey.from_public_key_recovery_with_digest(
                        (r, s), msg_hash, SECP256k1, sigdecode=ecdsa.util.sigdecode_string, hashfunc=None, allow_truncate=False, recovery_id=rec_id
                    )
                    pub = vk.to_string("uncompressed")
                    # Derive address: keccak256(pub[1:])[-20:]
                    try:
                        from eth_hash.auto import keccak
                        pub_hash = keccak(pub[1:])
                    except (ImportError, ModuleNotFoundError):
                        pub_hash = hashlib.sha3_256(pub[1:]).digest()
                    addr = "0x" + pub_hash[-20:].hex()
                    return addr.lower()
                except (ValueError, TypeError, KeyError):
                    continue
        except (ValueError, TypeError, KeyError):
            pass

    return None


class Web3AuthManager:
    """Authenticate users via Ethereum wallet (EIP-191 personal sign)."""

    def __init__(self, rpc_url: str | None = None) -> None:
        self.rpc_url = rpc_url or DEFAULT_RPC
        self._w3: Web3 | None = None
        if _HAS_WEB3:
            try:
                self._w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            except (ConnectionError, TimeoutError, OSError):
                self._w3 = None
        _ensure_db(DB_PATH)
        self._db = DB_PATH

    # ------------------------------------------------------------------ #
    def generate_nonce(self) -> str:  # noqa: E501
        """Generate a random nonce for sign-in."""
        return uuid.uuid4().hex + uuid.uuid4().hex

    # ------------------------------------------------------------------ #
    def verify_signature(self, wallet_address: str, nonce: str, signature: str) -> bool:
        """
        Verify an EIP-191 personal signature.
        Returns True if the signature was produced by *wallet_address*.
        """
        if not wallet_address or not signature:
            return False
        message = f"c4reqber login: {nonce}"
        recovered = _recover_address_from_signature(message, signature)
        if recovered is None:
            return False
        return recovered == wallet_address.lower()

    # ------------------------------------------------------------------ #
    def get_or_create_user(self, wallet_address: str) -> str:
        """
        Return the existing UUID for *wallet_address*, creating one if new.
        Only the lowercase wallet address and a generated UUID are stored.
        """
        addr = wallet_address.lower()
        conn = sqlite3.connect(self._db)
        cur = conn.cursor()
        cur.execute(
            "SELECT user_uuid FROM web3_users WHERE wallet_address = ?",
            (addr,),
        )
        row = cur.fetchone()
        now = int(time.time())
        if row:
            user_uuid = row[0]
            cur.execute(
                "UPDATE web3_users SET last_seen = ? WHERE wallet_address = ?",
                (now, addr),
            )
            conn.commit()
            conn.close()
            return user_uuid

        user_uuid = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO web3_users (wallet_address, user_uuid, created_at, last_seen) VALUES (?, ?, ?, ?)",
            (addr, user_uuid, now, now),
        )
        conn.commit()
        conn.close()
        return user_uuid

    # ------------------------------------------------------------------ #
    def is_authenticated(self, wallet_address: str) -> bool:
        """Check whether *wallet_address* has an active (non-expired) session."""
        addr = wallet_address.lower()
        now = int(time.time())
        conn = sqlite3.connect(self._db)
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM web3_sessions WHERE wallet_address = ? AND expires_at > ?",
            (addr, now),
        )
        row = cur.fetchone()
        conn.close()
        return row is not None

    # ------------------------------------------------------------------ #
    def create_session(self, wallet_address: str) -> str:
        """
        Create a new JWT session for *wallet_address* and persist it.
        Returns the JWT token string.
        """
        user_id = self.get_or_create_user(wallet_address)
        payload = {
            "sub": user_id,
            "wallet": wallet_address.lower(),
            "iat": int(time.time()),
            "exp": int(time.time()) + JWT_EXP_SECONDS,
        }
        if _HAS_JWT:
            token = _jwt_lib.encode(payload, _get_jwt_secret(), algorithm=JWT_ALGORITHM)
        else:
            # Fallback: simple HMAC-signed JSON token (not standard JWT, but self-contained)
            header = json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":"))
            body = json.dumps(payload, separators=(",", ":"))
            enc_header = _b64url(header.encode())
            enc_body = _b64url(body.encode())
            sig = _b64url(hmac.new(_get_jwt_secret().encode(), f"{enc_header}.{enc_body}".encode(), hashlib.sha256).digest())
            token = f"{enc_header}.{enc_body}.{sig}"

        conn = sqlite3.connect(self._db)
        conn.execute(
            "INSERT OR REPLACE INTO web3_sessions (wallet_address, token, expires_at) VALUES (?, ?, ?)",
            (wallet_address.lower(), token, payload["exp"]),
        )
        conn.commit()
        conn.close()
        return token

    # ------------------------------------------------------------------ #
    def revoke_session(self, wallet_address: str) -> None:
        """Delete the active session for *wallet_address*."""
        conn = sqlite3.connect(self._db)
        conn.execute(
            "DELETE FROM web3_sessions WHERE wallet_address = ?",
            (wallet_address.lower(),),
        )
        conn.commit()
        conn.close()


# ── helpers ─────────────────────────────────────────────────────────────────

def _b64url(data: bytes) -> str:
    """URL-safe base64 encode without padding."""
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def create_jwt(user_id: str, wallet_address: str = "") -> str:
    """
    Standalone helper to create a JWT for a user.
    Used by the framework integration helper below.
    """
    payload = {
        "sub": user_id,
        "wallet": wallet_address.lower(),
        "iat": int(time.time()),
        "exp": int(time.time()) + JWT_EXP_SECONDS,
    }
    if _HAS_JWT:
        return _jwt_lib.encode(payload, _get_jwt_secret(), algorithm=JWT_ALGORITHM)
    header = json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":"))
    body = json.dumps(payload, separators=(",", ":"))
    enc_header = _b64url(header.encode())
    enc_body = _b64url(body.encode())
    sig = _b64url(hmac.new(_get_jwt_secret().encode(), f"{enc_header}.{enc_body}".encode(), hashlib.sha256).digest())
    return f"{enc_header}.{enc_body}.{sig}"


# ── Flask / FastAPI integration helper ──────────────────────────────────────

async def web3_login_endpoint(request) -> tuple[dict[str, str], int] | dict[str, str]:
    """
    Generic async login endpoint helper.
    Works with FastAPI/Quart/any ASGI framework that exposes `request.json`.

    Usage (FastAPI):
        from fastapi import Request
        from auth.web3 import web3_login_endpoint

        @app.post("/auth/web3/login")
        async def login(request: Request):
            return await web3_login_endpoint(request)
    """
    try:
        data = await request.json()
    except (ValueError, TypeError, KeyError):
        return {"error": "Invalid JSON body"}, 400

    wallet = data.get("wallet")
    nonce = data.get("nonce")
    signature = data.get("signature")

    if not wallet or not nonce or not signature:
        return {"error": "Missing wallet, nonce or signature"}, 400

    auth = Web3AuthManager()
    if auth.verify_signature(wallet, nonce, signature):
        user_id = auth.get_or_create_user(wallet)
        token = create_jwt(user_id, wallet)
        auth.create_session(wallet)  # persists session in DB
        return {"token": token, "user_id": user_id}

    return {"error": "Invalid signature"}, 401
