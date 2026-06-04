"""Robokassa payment provider client.

Robokassa is a Russian payment aggregator supporting bank cards,
SberPay, SBP (Fast Payment System), e-wallets, and cash.

Docs: https://docs.robokassa.ru/
"""

from __future__ import annotations

import hashlib
import logging
import os
from typing import Any


logger = logging.getLogger(__name__)


class RobokassaClient:
    """Client for Robokassa payment gateway (Russian/CIS market).

    Robokassa uses a two-password system:
      - password1 (Pass1) — for payment link generation
      - password2 (Pass2) — for result/callback verification

    Signatures:
      - Payment : md5(f"{login}:{sum}:{inv_id}:{pass1}")
      - Callback: md5(f"{out_sum}:{inv_id}:{pass2}")

    Test mode uses a sandbox URL and separate test credentials.
    """

    BASE_URL = "https://auth.robokassa.ru/Merchant/Index.aspx"
    TEST_URL = "https://auth.robokassa.ru/Merchant/Index.aspx?IsTest=1"

    def __init__(
        self,
        merchant_login: str | None = None,
        password1: str | None = None,
        password2: str | None = None,
        test_mode: bool = True,
    ) -> None:
        self.merchant_login = merchant_login or os.environ.get("ROBOKASSA_LOGIN")
        self.password1 = password1 or os.environ.get("ROBOKASSA_PASSWORD1")
        self.password2 = password2 or os.environ.get("ROBOKASSA_PASSWORD2")
        self.test_mode = test_mode
        self.enabled = all([self.merchant_login, self.password1])

        if not self.enabled:
            logger.warning("RobokassaClient: missing merchant_login or password1")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_payment_link(
        self,
        out_sum: float,
        inv_id: int,
        description: str,
        **kwargs: Any,
    ) -> str:
        """Build a signed Robokassa payment URL.

        Args:
            out_sum: Payment amount.
            inv_id: Unique invoice ID.
            description: Payment description (shown to user).
            **kwargs: Extra parameters (e.g. Receipt JSON, Culture, Email).

        Returns:
            Full URL to redirect the payer to Robokassa.
        """
        if not self.enabled:
            raise RuntimeError("Robokassa is not configured")

        signature = self._sign(out_sum, inv_id)
        params = {
            "MerchantLogin": self.merchant_login,
            "OutSum": str(out_sum),
            "InvoiceID": str(inv_id),
            "Description": description,
            "SignatureValue": signature,
        }
        if self.test_mode:
            params["IsTest"] = "1"
        params.update(kwargs)

        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.BASE_URL}?{query}"

    def check_signature(self, signature: str, out_sum: float, inv_id: int) -> bool:
        """Verify a callback/result signature from Robokassa.

        Args:
            signature: SignatureValue received in callback.
            out_sum: Amount from callback.
            inv_id: Invoice ID from callback.

        Returns:
            True if the signature is valid.
        """
        if not self.password2:
            logger.warning("Robokassa: password2 not set; cannot verify callbacks")
            return False
        expected = hashlib.md5(
            f"{out_sum}:{inv_id}:{self.password2}".encode()
        ).hexdigest()
        return signature.lower() == expected.lower()

    def test_connection(self) -> dict[str, Any]:
        """Return a lightweight health-check dict."""
        return {
            "provider": "robokassa",
            "available": self.enabled,
            "test_mode": self.test_mode,
            "has_password2": bool(self.password2),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _sign(self, out_sum: float, inv_id: int) -> str:
        """Generate MD5 signature for payment link."""
        raw = f"{self.merchant_login}:{out_sum}:{inv_id}:{self.password1}"
        return hashlib.md5(raw.encode()).hexdigest()
