"""NOWPayments crypto payment provider client.

NOWPayments is a non-custodial crypto payment gateway supporting
345+ cryptocurrencies with auto-conversion to stablecoins or fiat.

Docs: https://nowpayments.io/help/
API:  https://documenter.getpostman.com/view/7907941/S1a32n38
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from typing import Any


logger = logging.getLogger(__name__)


class NOWPaymentsClient:
    """Client for NOWPayments crypto gateway.

    Features:
      - 345+ cryptocurrencies accepted
      - Auto-conversion to RUB / USDT / BTC
      - Fixed-rate and floating-rate invoices
      - Payouts to external wallets
      - Low commission (~0.5%)

    Environment:
        NOWPAYMENTS_API_KEY   — API key from dashboard
        NOWPAYMENTS_IPN_SECRET — Optional IPN signature secret
    """

    API_BASE = "https://api.nowpayments.io/v1"
    SANDBOX_BASE = "https://api-sandbox.nowpayments.io/v1"

    def __init__(
        self,
        api_key: str | None = None,
        ipn_secret: str | None = None,
        test_mode: bool = True,
    ) -> None:
        self.api_key = api_key or os.environ.get("NOWPAYMENTS_API_KEY")
        self.ipn_secret = ipn_secret or os.environ.get("NOWPAYMENTS_IPN_SECRET")
        self.test_mode = test_mode
        self.enabled = bool(self.api_key)
        self._base_url = self.SANDBOX_BASE if test_mode else self.API_BASE

        if not self.enabled:
            logger.warning("NOWPaymentsClient: missing API key")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_payment(
        self,
        price_amount: float,
        price_currency: str = "RUB",
        pay_currency: str = "btc",
        order_id: str | None = None,
        order_description: str = "",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create a crypto payment invoice.

        Args:
            price_amount: Amount in price_currency.
            price_currency: Fiat currency (RUB, USD, EUR).
            pay_currency: Crypto currency user pays with (btc, eth, usdt_trc20).
            order_id: Your internal order ID.
            order_description: Human-readable description.
            **kwargs: Extra API fields (e.g. case, payout_address).

        Returns:
            Invoice dict with payment_address, pay_amount, etc.
        """
        if not self.enabled:
            raise RuntimeError("NOWPayments is not configured")

        payload = {
            "price_amount": price_amount,
            "price_currency": price_currency,
            "pay_currency": pay_currency,
            "order_id": order_id,
            "order_description": order_description,
        }
        payload.update(kwargs)

        logger.debug("NOWPayments: create_payment payload=%s", payload)
        return {
            "status": "coming_soon",
            "provider": "nowpayments",
            "message": "NOWPayments create_payment: coming soon. Contact the developer or configure a real payment gateway.",
            "payload_preview": {k: v for k, v in payload.items() if v is not None},
        }

    def create_fixed_rate_payment(
        self,
        price_amount: float,
        price_currency: str = "RUB",
        pay_currency: str = "usdt",
        order_id: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create a fixed-rate invoice (rate locked for ~15 min).

        Use this when you want the user to pay exactly the quoted crypto amount.
        """
        return self.create_payment(
            price_amount=price_amount,
            price_currency=price_currency,
            pay_currency=pay_currency,
            order_id=order_id,
            **kwargs,
        )

    def get_minimum_payment_amount(
        self,
        currency_from: str = "btc",
        currency_to: str = "usdt",
    ) -> dict[str, Any]:
        """Fetch the minimum amount required for a payment pair."""
        if not self.enabled:
            raise RuntimeError("NOWPayments is not configured")

        return {
            "status": "coming_soon",
            "provider": "nowpayments",
            "message": "NOWPayments get_minimum_payment_amount: coming soon. Contact the developer or configure a real payment gateway.",
        }

    def verify_ipn_signature(
        self,
        payload: Any,
        signature_header: str,
    ) -> bool:
        """Verify an IPN (Instant Payment Notification) callback signature.

        Args:
            payload: JSON body of the IPN request.
            signature_header: X-NOWPayments-Sig header value.

        Returns:
            True if the signature is valid.
        """
        if not self.ipn_secret:
            logger.warning("NOWPayments: ipn_secret not set; skipping verification")
            return False

        if isinstance(payload, dict):
            body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        else:
            body = str(payload)

        expected = hmac.new(
            self.ipn_secret.encode(),
            body.encode(),
            hashlib.sha512,
        ).hexdigest()
        return hmac.compare_digest(expected, signature_header)

    def get_payment_status(self, payment_id: str) -> dict[str, Any]:
        """Fetch current status of a payment by ID."""
        if not self.enabled:
            raise RuntimeError("NOWPayments is not configured")

        return {
            "status": "coming_soon",
            "provider": "nowpayments",
            "message": "NOWPayments get_payment_status: coming soon. Contact the developer or configure a real payment gateway.",
        }

    def test_connection(self) -> dict[str, Any]:
        """Return a lightweight health-check dict."""
        return {
            "provider": "nowpayments",
            "available": self.enabled,
            "test_mode": self.test_mode,
            "base_url": self._base_url,
            "has_ipn_secret": bool(self.ipn_secret),
        }
