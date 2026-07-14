"""
Telegram Wallet / Telegram Login connector for c4reqber.

Provides zero-PII authentication and payment integration via Telegram.
Only telegram_id and username (public data) are stored. No first_name,
last_name, or photo_url — all PII under 152-FZ is dropped.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
import time
import uuid

import httpx


# ── constants ───────────────────────────────────────────────────────────────
DB_PATH = os.environ.get("C4REQBER_TELEGRAM_DB", os.path.join(os.path.dirname(__file__), "..", "..", "data", "telegram_auth.db"))
DEFAULT_BOT_API = "https://api.telegram.org/bot{token}/"
AUTH_DATE_TOLERANCE = 86400  # 24 hours


def _ensure_db(path: str) -> None:
    """Create SQLite DB and tables if they don't exist."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users_telegram (
            telegram_id BIGINT PRIMARY KEY,
            username TEXT,
            user_uuid TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS telegram_payments (
            payment_id TEXT PRIMARY KEY,
            user_uuid TEXT NOT NULL,
            telegram_id BIGINT NOT NULL,
            amount INTEGER NOT NULL,
            currency TEXT NOT NULL,
            status TEXT NOT NULL,
            provider_payload TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


class TelegramAuth:
    """Authenticate users via Telegram Login Widget (zero-PII)."""

    def __init__(self, bot_token: str | None = None) -> None:
        self.bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        _ensure_db(DB_PATH)
        self._db = DB_PATH

    # ------------------------------------------------------------------ #
    def is_configured(self) -> bool:
        """Check if a bot token has been configured."""
        return bool(self.bot_token)

    # ------------------------------------------------------------------ #
    def verify_login_widget(self, data: dict) -> dict:
        """
        Verify Telegram Login Widget hash using HMAC-SHA256.

        Input dict must contain keys from the Login Widget callback:
        id, username, first_name, last_name, photo_url, auth_date, hash.

        Returns {"telegram_id": str, "username": str} on success.
        Raises ValueError on verification failure or expired auth_date.
        """
        if not self.is_configured():
            raise RuntimeError("TelegramAuth is not configured — set TELEGRAM_BOT_TOKEN")

        required = {"id", "username", "auth_date", "hash"}
        missing = required - set(data.keys())
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        # Verify auth_date is recent (within 24h)
        try:
            auth_date = int(data["auth_date"])
        except (TypeError, ValueError) as exc:
            raise ValueError("auth_date must be an integer Unix timestamp") from exc

        now = int(time.time())
        if abs(now - auth_date) > AUTH_DATE_TOLERANCE:
            raise ValueError("auth_date is too old or from the future")

        # Build data_check_string from sorted key=value pairs, excluding hash
        data_check_items = sorted(
            (k, v) for k, v in data.items() if k != "hash" and v is not None
        )
        data_check_string = "\n".join(f"{k}={v}" for k, v in data_check_items)

        secret_key = hashlib.sha256(self.bot_token.encode()).digest()
        computed_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(computed_hash, data["hash"]):
            raise ValueError("Invalid hash — data may have been tampered with")

        # Return ONLY public data; drop PII fields
        return {
            "telegram_id": str(data["id"]),
            "username": str(data.get("username", "")),
        }

    # ------------------------------------------------------------------ #
    def get_or_create_user(self, telegram_id: str | int, username: str) -> str:
        """
        Return the existing UUID for *telegram_id*, creating one if new.
        Only telegram_id, username, and a generated UUID are stored.
        """
        tg_id = int(telegram_id)
        conn = sqlite3.connect(self._db)
        cur = conn.cursor()
        cur.execute(
            "SELECT user_uuid FROM users_telegram WHERE telegram_id = ?",
            (tg_id,),
        )
        row = cur.fetchone()
        if row:
            conn.close()
            return row[0]

        user_uuid = str(uuid.uuid4())
        now = int(time.time())
        cur.execute(
            "INSERT INTO users_telegram (telegram_id, username, user_uuid, created_at) VALUES (?, ?, ?, ?)",
            (tg_id, username, user_uuid, now),
        )
        conn.commit()
        conn.close()
        return user_uuid


class TelegramWalletPay:
    """Payment integration via Telegram Bot API (invoices + Stars)."""

    def __init__(
        self,
        bot_token: str | None = None,
        provider_token: str | None = None,
    ) -> None:
        self.bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.provider_token = provider_token or os.environ.get("TELEGRAM_PROVIDER_TOKEN", "")
        self.base_url = DEFAULT_BOT_API.format(token=self.bot_token)
        _ensure_db(DB_PATH)
        self._db = DB_PATH
        self._client = httpx.AsyncClient(timeout=30.0)

    # ------------------------------------------------------------------ #
    def is_configured(self) -> bool:
        """Check if both bot token and provider token are set."""
        return bool(self.bot_token) and bool(self.provider_token)

    # ------------------------------------------------------------------ #
    async def create_invoice(
        self,
        user_id: str | int,
        title: str,
        description: str,
        amount: int,
        currency: str = "USD",
    ) -> dict:
        """
        Create a payment invoice via Bot API createInvoiceLink.

        *amount* is the smallest currency unit (e.g. cents for USD).
        Returns {"invoice_url": str, "payload": str}.
        """
        if not self.is_configured():
            raise RuntimeError(
                "TelegramWalletPay is not configured — set TELEGRAM_BOT_TOKEN and TELEGRAM_PROVIDER_TOKEN"
            )

        payload = json.dumps(
            {"u": str(user_id), "t": int(time.time()), "r": uuid.uuid4().hex[:8]}
        )

        params = {
            "title": title,
            "description": description,
            "payload": payload,
            "provider_token": self.provider_token,
            "currency": currency,
            "prices": json.dumps([{"label": title, "amount": amount}]),
        }

        url = f"{self.base_url}createInvoiceLink"
        response = await self._client.post(url, json=params)
        response.raise_for_status()
        result = response.json()

        if not result.get("ok"):
            raise RuntimeError(f"Telegram API error: {result.get('description')}")

        invoice_url = result["result"]
        return {"invoice_url": invoice_url, "payload": payload}

    # ------------------------------------------------------------------ #
    async def process_payment_update(self, update: dict) -> dict:
        """
        Handle pre_checkout_query and successful_payment from a webhook update.

        Verifies payment, credits user balance, and persists a record.
        Returns {"status": str, "user_id": str, "amount": int, "currency": str}.
        """
        if "pre_checkout_query" in update:
            query = update["pre_checkout_query"]
            query_id = query["id"]

            # Acknowledge pre-checkout
            url = f"{self.base_url}answerPreCheckoutQuery"
            ack = await self._client.post(
                url, json={"pre_checkout_query_id": query_id, "ok": True}
            )
            ack.raise_for_status()
            ack_data = ack.json()
            if not ack_data.get("ok"):
                raise RuntimeError(
                    f"answerPreCheckoutQuery failed: {ack_data.get('description')}"
                )

            return {
                "status": "pre_checkout_ok",
                "user_id": None,
                "amount": None,
                "currency": None,
            }

        if "message" in update and "successful_payment" in update["message"]:
            payment = update["message"]["successful_payment"]
            payload_raw = payment.get("invoice_payload", "{}")
            try:
                payload = json.loads(payload_raw)
            except json.JSONDecodeError:
                payload = {}

            user_id = payload.get("u")
            amount = payment.get("total_amount", 0)
            currency = payment.get("currency", "")
            telegram_charge_id = payment.get("telegram_payment_charge_id", "")

            # Lookup user_uuid from telegram_id if user_id looks like a telegram id
            user_uuid: str | None = None
            conn = sqlite3.connect(self._db)
            cur = conn.cursor()
            if user_id and user_id.isdigit():
                cur.execute(
                    "SELECT user_uuid FROM users_telegram WHERE telegram_id = ?",
                    (int(user_id),),
                )
                row = cur.fetchone()
                if row:
                    user_uuid = row[0]

            # Persist payment record
            now = int(time.time())
            cur.execute(
                """
                INSERT OR REPLACE INTO telegram_payments
                (payment_id, user_uuid, telegram_id, amount, currency, status, provider_payload, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    telegram_charge_id or uuid.uuid4().hex,
                    user_uuid or "",
                    int(user_id) if user_id and user_id.isdigit() else 0,
                    amount,
                    currency,
                    "success",
                    payload_raw,
                    now,
                    now,
                ),
            )
            conn.commit()
            conn.close()

            return {
                "status": "success",
                "user_id": user_uuid or user_id,
                "amount": amount,
                "currency": currency,
            }

        return {
            "status": "ignored",
            "user_id": None,
            "amount": None,
            "currency": None,
        }

    # ------------------------------------------------------------------ #
    async def create_stars_invoice(
        self,
        user_id: str | int,
        title: str,
        description: str,
        star_count: int,
    ) -> dict:
        """
        Create an invoice for Telegram Stars (native mini-app currency).

        Telegram Stars use a special currency "XTR" and do not require a
        provider_token. Returns {"invoice_url": str, "payload": str}.
        """
        if not self.bot_token:
            raise RuntimeError(
                "TelegramWalletPay is not configured — set TELEGRAM_BOT_TOKEN"
            )

        payload = json.dumps(
            {"u": str(user_id), "t": int(time.time()), "r": uuid.uuid4().hex[:8]}
        )

        params = {
            "title": title,
            "description": description,
            "payload": payload,
            "currency": "XTR",
            "prices": json.dumps([{"label": title, "amount": star_count}]),
        }

        url = f"{self.base_url}createInvoiceLink"
        response = await self._client.post(url, json=params)
        response.raise_for_status()
        result = response.json()

        if not result.get("ok"):
            raise RuntimeError(f"Telegram API error: {result.get('description')}")

        invoice_url = result["result"]
        return {"invoice_url": invoice_url, "payload": payload}
