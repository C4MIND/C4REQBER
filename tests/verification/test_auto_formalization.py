"""Tests for auto-formalization integration in verification clients."""
from __future__ import annotations

import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.verification.config import AutoFormalizationConfig, reset_auto_formalization_config
from src.verification.coq_client import CoqClient
from src.verification.lean4_client import Lean4Client
from src.verification.dafny_client import DafnyClient



class TestVerifyDiscoveryIntegration:
    def setup_method(self) -> None:
        reset_auto_formalization_config()

    def teardown_method(self) -> None:
        reset_auto_formalization_config()

    @pytest.mark.anyio(backend="asyncio")
    async def test_disabled_returns_early(self) -> None:
        with patch(
            "src.verification.config.get_auto_formalization_config",
            return_value=AutoFormalizationConfig(enabled=False),
        ):
            client = CoqClient()
            result = await client.verify_discovery("hypothesis")

        assert result["success"] is False
        assert "disabled" in result["output"].lower()

    @pytest.mark.anyio(backend="asyncio")
    async def test_not_formalizable(self) -> None:
        mock_formal = MagicMock()
        mock_formal.formalizability_score = 0.1
        mock_formal.not_formalizable_reason = "Too vague"
        mock_formal.theorem_statement = ""

        with patch(
            "src.verification.config.get_auto_formalization_config",
            return_value=AutoFormalizationConfig(enabled=True, min_score=0.3),
        ):
            with patch(
                "src.verification.formalization_engine.FormalizationEngine.formalize",
                new_callable=AsyncMock,
                return_value=mock_formal,
            ):
                client = Lean4Client()
                result = await client.verify_discovery("Something vague")

        assert result["success"] is False
        assert "Too vague" in result["output"]

    @pytest.mark.anyio(backend="asyncio")
    async def test_verified_with_consensus(self) -> None:
        mock_formal = MagicMock()
        mock_formal.formalizability_score = 0.9
        mock_formal.not_formalizable_reason = None
        mock_formal.theorem_statement = "forall x, x = x"

        mock_consensus = MagicMock()
        mock_consensus.status = "verified"
        mock_consensus.confidence = 1.0
        mock_consensus.languages = {
            "lean4": {"valid": True, "iterations": 2, "error": None, "total_time_ms": 1000, "proof": "theorem"},
        }
        mock_consensus.human_review_recommended = False
        mock_consensus.theorem_statement = "forall x, x = x"
        mock_consensus.to_dict = MagicMock(return_value={"status": "verified"})

        with patch(
            "src.verification.config.get_auto_formalization_config",
            return_value=AutoFormalizationConfig(
                enabled=True,
                min_score=0.3,
                languages=["lean4"],
                min_agreement=1,
                semantic_alignment_check=False,
            ),
        ):
            with patch(
                "src.verification.formalization_engine.FormalizationEngine.formalize",
                new_callable=AsyncMock,
                return_value=mock_formal,
            ):
                with patch(
                    "src.verification.consensus_engine.ConsensusEngine.verify_with_consensus",
                    new_callable=AsyncMock,
                    return_value=mock_consensus,
                ):
                    client = DafnyClient()
                    result = await client.verify_discovery("All things equal themselves")

        assert result["success"] is True

    @pytest.mark.anyio(backend="asyncio")
    async def test_partial_status(self) -> None:
        mock_formal = MagicMock()
        mock_formal.formalizability_score = 0.8
        mock_formal.not_formalizable_reason = None
        mock_formal.theorem_statement = "theorem"

        mock_consensus = MagicMock()
        mock_consensus.status = "partial"
        mock_consensus.confidence = 0.33
        mock_consensus.languages = {
            "lean4": {"valid": True, "iterations": 1, "error": None, "total_time_ms": 500, "proof": ""},
            "coq": {"valid": False, "iterations": 0, "error": "fail", "total_time_ms": 0, "proof": ""},
        }
        mock_consensus.human_review_recommended = True
        mock_consensus.theorem_statement = "theorem"
        mock_consensus.to_dict = MagicMock(return_value={"status": "partial"})

        with patch(
            "src.verification.config.get_auto_formalization_config",
            return_value=AutoFormalizationConfig(
                enabled=True,
                min_score=0.3,
                languages=["lean4", "coq"],
                min_agreement=2,
                semantic_alignment_check=False,
            ),
        ):
            with patch(
                "src.verification.formalization_engine.FormalizationEngine.formalize",
                new_callable=AsyncMock,
                return_value=mock_formal,
            ):
                with patch(
                    "src.verification.consensus_engine.ConsensusEngine.verify_with_consensus",
                    new_callable=AsyncMock,
                    return_value=mock_consensus,
                ):
                    client = CoqClient()
                    result = await client.verify_discovery("hypothesis")

        assert result["success"] is False  # partial is not verified
        assert "partial" in str(result["output"]).lower()

    def test_all_clients_have_same_interface(self) -> None:
        """Verify all three clients have async verify_discovery."""
        for client_cls in [CoqClient, Lean4Client, DafnyClient]:
            method = getattr(client_cls, "verify_discovery")
            assert inspect.iscoroutinefunction(method), f"{client_cls.__name__}.verify_discovery must be async"
