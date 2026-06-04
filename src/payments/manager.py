"""Unified payment manager.

Routes payment operations across Robokassa, CloudPayments, and NOWPayments.
Picks the best provider based on currency, payment method, and user preference.

Usage:
    manager = PaymentManager()
    result = manager.create_payment(
        provider="robokassa",
        amount=1000.00,
        currency="RUB",
        invoice_id=42,
        description="Pro plan",
    )
"""

from __future__ import annotations

import logging
from typing import Any

from .providers import CloudPaymentsClient, NOWPaymentsClient, RobokassaClient


logger = logging.getLogger(__name__)


class PaymentManager:
    """Central manager for all payment providers.

    Attributes:
        robokassa: RobokassaClient instance (cards, SBP, SberPay, e-wallets).
        cloudpayments: CloudPaymentsClient instance (cards, Apple/Google Pay, subscriptions).
        nowpayments: NOWPaymentsClient instance (345+ cryptocurrencies).
    """

    def __init__(self) -> None:
        self.robokassa = RobokassaClient()
        self.cloudpayments = CloudPaymentsClient()
        self.nowpayments = NOWPaymentsClient()

    # ------------------------------------------------------------------
    # Unified API
    # ------------------------------------------------------------------

    def create_payment(
        self,
        provider: str,
        amount: float,
        currency: str = "RUB",
        invoice_id: int | str | None = None,
        description: str = "",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create a payment through the specified provider.

        Args:
            provider: One of "robokassa", "cloudpayments", "nowpayments".
            amount: Payment amount.
            currency: ISO currency code (default RUB).
            invoice_id: Internal invoice/order ID.
            description: Human-readable description.
            **kwargs: Provider-specific arguments.

        Returns:
            Provider response dict.
        """
        if provider == "robokassa":
            if not self.robokassa.enabled:
                raise RuntimeError("Robokassa is not configured")
            link = self.robokassa.generate_payment_link(
                out_sum=amount,
                inv_id=int(invoice_id or 0),
                description=description,
                **kwargs,
            )
            return {"provider": "robokassa", "redirect_url": link}

        if provider == "cloudpayments":
            return self.cloudpayments.charge_card(
                amount=amount,
                currency=currency,
                invoice_id=str(invoice_id) if invoice_id else None,
                description=description,
                **kwargs,
            )

        if provider == "nowpayments":
            return self.nowpayments.create_payment(
                price_amount=amount,
                price_currency=currency,
                order_id=str(invoice_id) if invoice_id else None,
                order_description=description,
                **kwargs,
            )

        raise ValueError(f"Unknown provider: {provider}")

    def verify_callback(
        self,
        provider: str,
        **kwargs: Any,
    ) -> bool:
        """Verify a callback/webhook signature.

        Args:
            provider: One of "robokassa", "cloudpayments", "nowpayments".
            **kwargs: Provider-specific verification arguments.

        Returns:
            True if the callback is authentic.
        """
        if provider == "robokassa":
            return self.robokassa.check_signature(
                signature=kwargs["signature"],
                out_sum=kwargs["out_sum"],
                inv_id=kwargs["inv_id"],
            )

        if provider == "cloudpayments":
            return self.cloudpayments.verify_webhook(
                body=kwargs["body"],
                signature_header=kwargs["signature_header"],
            )

        if provider == "nowpayments":
            return self.nowpayments.verify_ipn_signature(
                payload=kwargs["payload"],
                signature_header=kwargs["signature_header"],
            )

        raise ValueError(f"Unknown provider: {provider}")

    def get_provider(self, provider: str) -> Any:
        """Return the raw provider client for advanced use."""
        mapping = {
            "robokassa": self.robokassa,
            "cloudpayments": self.cloudpayments,
            "nowpayments": self.nowpayments,
        }
        if provider not in mapping:
            raise ValueError(f"Unknown provider: {provider}")
        return mapping[provider]

    def health_check(self) -> dict[str, Any]:
        """Return health status for all providers."""
        return {
            "robokassa": self.robokassa.test_connection(),
            "cloudpayments": self.cloudpayments.test_connection(),
            "nowpayments": self.nowpayments.test_connection(),
        }

    def auto_select_provider(
        self,
        currency: str = "RUB",
        method: str | None = None,
    ) -> str:
        """Heuristic provider selection.

        Args:
            currency: Target currency.
            method: Preferred payment method (card, crypto, sbp, sberpay).

        Returns:
            Recommended provider key.
        """
        method = (method or "").lower()

        if method in ("btc", "eth", "usdt", "crypto"):
            return "nowpayments"

        if method in ("sbp", "sberpay", "wallet"):
            if self.robokassa.enabled:
                return "robokassa"
            return "cloudpayments"

        if currency.upper() == "RUB":
            if self.cloudpayments.enabled:
                return "cloudpayments"
            if self.robokassa.enabled:
                return "robokassa"

        # Fallback
        if self.nowpayments.enabled:
            return "nowpayments"

        raise RuntimeError("No payment provider is configured")
