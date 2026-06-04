"""CloudPayments payment provider client.

CloudPayments is a Russian payment service provider (PSP) for
accepting card payments, Apple Pay, Google Pay, SberPay, SBP.

Docs: https://developers.cloudpayments.ru/
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
from typing import Any


logger = logging.getLogger(__name__)


class CloudPaymentsClient:
    """Client for CloudPayments (Russian PSP).

    Features:
      - Bank cards (Visa, Mastercard, MIR)
      - Apple Pay / Google Pay
      - SberPay, SBP (Fast Payment System)
      - Recurring payments / subscriptions
      - 3-D Secure support
      - Webhook notifications

    Authentication:
      HTTP Basic Auth with public_id (username) and api_secret (password).
      Webhooks use password2 for HMAC-SHA256 signature verification.

    Environment:
        CLOUDPAYMENTS_PUBLIC_ID   — Public ID from dashboard
        CLOUDPAYMENTS_API_SECRET  — API secret
        CLOUDPAYMENTS_PASSWORD2   — Webhook signature password
    """

    API_BASE = "https://api.cloudpayments.ru"
    API_BASE_TEST = "https://api.cloudpayments.ru"  # Same endpoint; use test cards

    def __init__(
        self,
        public_id: str | None = None,
        api_secret: str | None = None,
        password2: str | None = None,
        test_mode: bool = True,
    ) -> None:
        self.public_id = public_id or os.environ.get("CLOUDPAYMENTS_PUBLIC_ID")
        self.api_secret = api_secret or os.environ.get("CLOUDPAYMENTS_API_SECRET")
        self.password2 = password2 or os.environ.get("CLOUDPAYMENTS_PASSWORD2")
        self.test_mode = test_mode
        self.enabled = all([self.public_id, self.api_secret])

        if not self.enabled:
            logger.warning("CloudPaymentsClient: missing public_id or api_secret")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def charge_card(
        self,
        amount: float,
        currency: str = "RUB",
        invoice_id: str | None = None,
        description: str = "",
        account_id: str | None = None,
        card_cryptogram_packet: str | None = None,
        token: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Charge a card (one-step payment).

        Args:
            amount: Payment amount.
            currency: ISO currency code (default RUB).
            invoice_id: Your internal order/invoice ID.
            description: Payment description.
            account_id: Customer identifier in your system.
            card_cryptogram_packet: Encrypted card data from CloudPayments widget.
            token: Saved card token for repeat payments.
            **kwargs: Extra API fields.

        Returns:
            API response dict (success, model, message, etc.).
        """
        if not self.enabled:
            raise RuntimeError("CloudPayments is not configured")

        payload = {
            "Amount": amount,
            "Currency": currency,
            "InvoiceId": invoice_id,
            "Description": description,
            "AccountId": account_id,
            "CardCryptogramPacket": card_cryptogram_packet,
            "Token": token,
        }
        payload.update(kwargs)

        logger.debug("CloudPayments: charge_card payload=%s", payload)
        return {
            "status": "coming_soon",
            "provider": "cloudpayments",
            "message": "CloudPayments charge_card: coming soon. Contact the developer or configure a real payment gateway.",
            "payload_preview": {k: v for k, v in payload.items() if v is not None},
        }

    def auth_card(
        self,
        amount: float,
        currency: str = "RUB",
        invoice_id: str | None = None,
        card_cryptogram_packet: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Authorize a card amount (two-step payment).

        Use :meth:`confirm_3ds` or :meth:`post3ds` after 3-D Secure.
        """
        if not self.enabled:
            raise RuntimeError("CloudPayments is not configured")

        payload = {
            "Amount": amount,
            "Currency": currency,
            "InvoiceId": invoice_id,
            "CardCryptogramPacket": card_cryptogram_packet,
        }
        payload.update(kwargs)

        return {
            "status": "coming_soon",
            "provider": "cloudpayments",
            "message": "CloudPayments auth_card: coming soon. Contact the developer or configure a real payment gateway.",
            "payload_preview": {k: v for k, v in payload.items() if v is not None},
        }

    def confirm_3ds(
        self,
        transaction_id: int,
        pa_res: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Complete a 3-D Secure payment.

        Args:
            transaction_id: CloudPayments transaction ID.
            pa_res: PaRes / CRes from ACS.
            **kwargs: Extra fields.

        Returns:
            API response dict.
        """
        if not self.enabled:
            raise RuntimeError("CloudPayments is not configured")

        payload = {
            "TransactionId": transaction_id,
            "PaRes": pa_res,
        }
        payload.update(kwargs)

        return {
            "status": "coming_soon",
            "provider": "cloudpayments",
            "message": "CloudPayments confirm_3ds: coming soon. Contact the developer or configure a real payment gateway.",
            "payload_preview": {k: v for k, v in payload.items() if v is not None},
        }

    def get_transaction(self, transaction_id: int) -> dict[str, Any]:
        """Fetch a transaction by ID."""
        if not self.enabled:
            raise RuntimeError("CloudPayments is not configured")

        return {
            "status": "coming_soon",
            "provider": "cloudpayments",
            "message": "CloudPayments get_transaction: coming soon. Contact the developer or configure a real payment gateway.",
        }

    def refund(self, transaction_id: int, amount: float) -> dict[str, Any]:
        """Refund a transaction (partial or full)."""
        if not self.enabled:
            raise RuntimeError("CloudPayments is not configured")

        return {
            "status": "coming_soon",
            "provider": "cloudpayments",
            "message": "CloudPayments refund: coming soon. Contact the developer or configure a real payment gateway.",
        }

    def create_subscription(
        self,
        token: str,
        account_id: str,
        amount: float,
        currency: str = "RUB",
        description: str = "",
        interval: str = "Month",
        period: int = 1,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create a recurring subscription.

        Args:
            token: Saved card token.
            account_id: Customer ID.
            amount: Recurring amount.
            currency: Currency code.
            description: Subscription description.
            interval: Day, Week, Month.
            period: How many intervals between charges.
            **kwargs: Extra fields.

        Returns:
            Subscription dict.
        """
        if not self.enabled:
            raise RuntimeError("CloudPayments is not configured")

        payload = {
            "Token": token,
            "AccountId": account_id,
            "Amount": amount,
            "Currency": currency,
            "Description": description,
            "Interval": interval,
            "Period": period,
        }
        payload.update(kwargs)

        return {
            "status": "coming_soon",
            "provider": "cloudpayments",
            "message": "CloudPayments create_subscription: coming soon. Contact the developer or configure a real payment gateway.",
            "payload_preview": {k: v for k, v in payload.items() if v is not None},
        }

    def cancel_subscription(self, subscription_id: str) -> dict[str, Any]:
        """Cancel an active subscription."""
        if not self.enabled:
            raise RuntimeError("CloudPayments is not configured")

        return {
            "status": "coming_soon",
            "provider": "cloudpayments",
            "message": "CloudPayments cancel_subscription: coming soon. Contact the developer or configure a real payment gateway.",
        }

    def verify_webhook(
        self,
        body: str,
        signature_header: str,
    ) -> bool:
        """Verify a webhook signature (HMAC-SHA256).

        Args:
            body: Raw request body string.
            signature_header: Content-HMAC header value.

        Returns:
            True if signature is valid.
        """
        if not self.password2:
            logger.warning("CloudPayments: password2 not set; skipping verification")
            return False

        expected = hmac.new(
            self.password2.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature_header)

    def test_connection(self) -> dict[str, Any]:
        """Return a lightweight health-check dict."""
        return {
            "provider": "cloudpayments",
            "available": self.enabled,
            "test_mode": self.test_mode,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _basic_auth_header(self) -> str:
        """Build HTTP Basic Auth header value."""
        creds = base64.b64encode(
            f"{self.public_id}:{self.api_secret}".encode()
        ).decode()
        return f"Basic {creds}"
