"""Suite 08 — HybridVerifier CVC5/TLA/Alloy must not stamp verified."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.pipeline.quality import QualityGates
from src.verification.hybrid_verifier import HybridVerifier


@pytest.mark.asyncio
async def test_hybrid_cvc5_sat_not_verified() -> None:
    hv = HybridVerifier()
    hv._cache = {}

    fake_client = MagicMock()
    fake_client.is_available.return_value = True
    fake_client.verify.return_value = {
        "valid": True,
        "satisfiable": True,
        "status": "sat",
        "output": "sat",
        "error": None,
    }

    with (
        patch.object(hv, "_select_backend", return_value="cvc5"),
        patch.object(hv, "_extract_embedded_code", return_value="(check-sat)"),
        patch.object(hv, "_looks_like_smt", return_value=True),
        patch("src.verification.cvc5_client.CVC5Client", return_value=fake_client),
    ):
        out = await hv.verify(
            {"title": "SMT claim", "description": "(declare-const x Int)"},
            context={"preferred_backends": ["cvc5"]},
        )

    assert out.status != "verified"
    assert out.status in {"sat", "unsat", "checked", "failed", "skipped"}
    assert (out.timing_info or {}).get("not_a_proof") is True
    assert (out.timing_info or {}).get("verification_aligned") is False

    gate = QualityGates().check_verification({"status": out.status, "backend": "cvc5"})
    # Soft at most — never full formal PASS 1.0
    assert not (gate.passed and gate.score >= 1.0 and "PASS" in gate.message)


@pytest.mark.asyncio
async def test_hybrid_tla_checked_not_verified() -> None:
    hv = HybridVerifier()
    hv._cache = {}

    fake_client = MagicMock()
    fake_client.is_available.return_value = True
    fake_client.verify.return_value = {"valid": True, "output": "ok", "error": None}

    with (
        patch.object(hv, "_select_backend", return_value="tla"),
        patch.object(
            hv,
            "_extract_embedded_code",
            return_value="---- MODULE M ----\nInit == TRUE\nNext == TRUE\n====\n",
        ),
        patch("src.verification.tla_client.TLAClient", return_value=fake_client),
    ):
        out = await hv.verify(
            {"title": "TLA claim", "description": "temporal fairness"},
            context={"preferred_backends": ["tla"]},
        )

    assert out.status == "checked"
    assert out.status != "verified"
    assert (out.timing_info or {}).get("verification_aligned") is False
