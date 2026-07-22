"""W9: Agda missing → unavailable (not verified success)."""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest

from src.utils.honesty_status import outer_status_from_verification
from src.verification.hybrid_verifier import HybridVerifier
from src.verification.llm_prover import LLMProver


def test_outer_status_from_verification_agda_not_installed() -> None:
    assert outer_status_from_verification("not_installed", backend="agda") == "unavailable"
    assert outer_status_from_verification("unavailable", backend="agda") == "unavailable"
    assert outer_status_from_verification("verified", backend="agda") == "success"


def test_hybrid_verifier_agda_missing_returns_unavailable() -> None:
    verifier = HybridVerifier()
    hypothesis = {"title": "Test", "description": "A simple theorem about natural numbers."}

    with (
        patch.object(verifier, "_select_backend", return_value="agda"),
        patch.object(verifier, "_check_executable", return_value=False),
    ):
        result = asyncio.run(verifier.verify(hypothesis))

    assert result.backend == "agda"
    assert result.status == "unavailable"
    assert "not found" in (result.error_message or "").lower()


@pytest.mark.asyncio
async def test_llm_prover_agda_not_installed_honest_skip() -> None:
    with patch("src.verification.agda_bridge.AgdaBridge") as mock_bridge:
        mock_bridge.return_value.available = False
        result = await LLMProver().prove("1+1=2", "agda")

    assert result.valid is False
    assert (
        "unavailable" in (result.error or "").lower()
        or "not installed" in (result.error or "").lower()
    )
    payload = result.to_dict()
    assert payload["status"] == "unavailable"


@pytest.mark.skipif(
    __import__("shutil").which("agda") is not None,
    reason="Agda installed — optional scaffold only checks missing-backend path",
)
def test_agda_scaffold_module_boundaries_documented() -> None:
    """CI-skippable stub: ADR + bridge remain when Agda absent."""
    from pathlib import Path

    adr = Path("docs/adr/0001-agda-core-rewrite-scaffold.md")
    bridge = Path("src/verification/agda_bridge.py")
    assert adr.is_file()
    assert bridge.is_file()
    assert "non-goal" in adr.read_text(encoding="utf-8").lower()
