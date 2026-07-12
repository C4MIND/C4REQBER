"""End-to-end integration tests with real installed verifier binaries."""
from __future__ import annotations

import pytest

from src.config.paths import load_verifiers_env

load_verifiers_env()

BOUNDED_TLA = """---- MODULE Counter ----
EXTENDS Naturals
VARIABLE x
Init == x = 0
Next == /\\ x < 5 /\\ x' = x + 1
====
"""


@pytest.mark.integration
class TestRealVerifierBackends:
    def test_cvc5_live(self) -> None:
        from src.verification.cvc5_client import CVC5Client

        client = CVC5Client()
        if not client.test_connection():
            pytest.skip("cvc5 not installed")
        assert client.verify("(declare-const x Int)\n(assert (> x 0))\n(check-sat)\n")["valid"] is True

    def test_tla_live(self) -> None:
        from src.verification.tla_client import TLAClient

        client = TLAClient()
        if not client.test_connection():
            pytest.skip("TLA+ TLC not installed")
        result = client.verify(BOUNDED_TLA)
        assert result["valid"] is True, result.get("error", result.get("output"))

    def test_alloy_live(self) -> None:
        from src.verification.alloy_client import AlloyClient

        client = AlloyClient()
        if not client.test_connection():
            pytest.skip("Alloy not installed")
        result = client.verify("sig Node {}\nrun {} for 3\n")
        assert result["valid"] is True, result.get("error", result.get("output"))
