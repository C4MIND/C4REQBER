"""Tests for ConsensusEngine."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.verification.consensus_engine import ConsensusEngine, ConsensusResult


class TestConsensusResult:
    def test_to_dict(self) -> None:
        r = ConsensusResult(
            status="verified",
            confidence=0.67,
            languages={"lean4": {"valid": True, "iterations": 2}},
            cost_estimate_usd=0.036,
        )
        d = r.to_dict()
        assert d["status"] == "verified"
        assert d["confidence"] == 0.67
        assert d["cost_estimate_usd"] == 0.036


class TestConsensusEngine:
    @pytest.mark.anyio(backend="asyncio")
    async def test_verified_when_all_agree(self) -> None:
        engine = ConsensusEngine()
        mock_result = MagicMock()
        mock_result.valid = True
        mock_result.iterations = [MagicMock()]
        mock_result.error = ""
        mock_result.total_time_ms = 1000
        mock_result.proof = "theorem test : True := by trivial"

        with patch.object(
            engine._prover, "prove", new_callable=AsyncMock, return_value=mock_result
        ):
            result = await engine.verify_with_consensus(
                "forall x, x = x",
                languages=["lean4", "coq", "dafny"],
                min_agreement=2,
            )

        assert result.status == "verified"
        assert result.confidence == 1.0
        assert result.human_review_recommended is False
        assert result.cost_estimate_usd > 0

    @pytest.mark.anyio(backend="asyncio")
    async def test_partial_when_one_agrees(self) -> None:
        engine = ConsensusEngine()
        mock_valid = MagicMock()
        mock_valid.valid = True
        mock_valid.iterations = [MagicMock()]
        mock_valid.error = ""
        mock_valid.total_time_ms = 1000
        mock_valid.proof = "proof"

        mock_invalid = MagicMock()
        mock_invalid.valid = False
        mock_invalid.iterations = []
        mock_invalid.error = "syntax error"
        mock_invalid.total_time_ms = 500
        mock_invalid.proof = ""

        with patch.object(
            engine._prover, "prove", new_callable=AsyncMock, side_effect=[mock_valid, mock_invalid, mock_invalid]
        ):
            result = await engine.verify_with_consensus(
                "forall x y z, (x + y + z = x + (y + z)",
                languages=["lean4", "coq", "dafny"],
                min_agreement=2,
            )

        assert result.status == "partial"
        assert result.confidence == pytest.approx(0.333, abs=0.01)
        assert result.human_review_recommended is True

    @pytest.mark.anyio(backend="asyncio")
    async def test_failed_when_none_agree(self) -> None:
        engine = ConsensusEngine()
        mock_invalid = MagicMock()
        mock_invalid.valid = False
        mock_invalid.iterations = []
        mock_invalid.error = "failed"
        mock_invalid.total_time_ms = 500
        mock_invalid.proof = ""

        with patch.object(
            engine._prover, "prove", new_callable=AsyncMock, return_value=mock_invalid
        ):
            result = await engine.verify_with_consensus(
                "forall x, x = x",
                languages=["lean4", "coq"],
                min_agreement=2,
            )

        assert result.status == "failed"
        assert result.confidence == 0.0
        assert result.human_review_recommended is True

    @pytest.mark.anyio(backend="asyncio")
    async def test_insufficient_for_empty_theorem(self) -> None:
        engine = ConsensusEngine()
        result = await engine.verify_with_consensus(
            "",
            languages=["lean4"],
            min_agreement=1,
        )
        assert result.status == "insufficient"
        assert result.confidence == 0.0
        assert result.human_review_recommended is True

    @pytest.mark.anyio(backend="asyncio")
    async def test_default_languages(self) -> None:
        engine = ConsensusEngine()
        mock_result = MagicMock()
        mock_result.valid = True
        mock_result.iterations = []
        mock_result.error = ""
        mock_result.total_time_ms = 0
        mock_result.proof = ""

        with patch.object(
            engine._prover, "prove", new_callable=AsyncMock, return_value=mock_result
        ) as mock_prove:
            result = await engine.verify_with_consensus("forall x, x = x")

        assert mock_prove.call_count == 3  # default languages
        assert result.status == "verified"

    @pytest.mark.anyio(backend="asyncio")
    async def test_prover_error_handled(self) -> None:
        engine = ConsensusEngine()
        with patch.object(
            engine._prover, "prove", new_callable=AsyncMock, side_effect=RuntimeError("boom")
        ):
            result = await engine.verify_with_consensus(
                "forall x, x = x",
                languages=["lean4"],
                min_agreement=1,
            )

        assert result.status == "failed"
        assert result.languages["lean4"]["valid"] is False
        assert "boom" in result.languages["lean4"]["error"]
