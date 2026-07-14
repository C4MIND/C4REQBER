"""Dispatch and integration tests for CVC5 / TLA+ / Alloy backends."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.verification.calibrator import VerificationCalibrator, VerificationContext
from src.verification.hybrid_verifier import HybridVerifier
from src.verification.timer import BACKEND_TIMEOUTS


SMT_SAMPLE = "(declare-const x Int)\n(assert (> x 0))\n(check-sat)\n"
TLA_SAMPLE = "---- MODULE M ----\nInit == TRUE\nNext == TRUE\n====\n"
ALLOY_SAMPLE = "sig A {}\nrun {} for 3\n"


class TestBackendTimeouts:
    def test_new_backends_have_timeouts(self) -> None:
        for backend in ("cvc5", "tla", "alloy"):
            assert backend in BACKEND_TIMEOUTS
            soft, hard = BACKEND_TIMEOUTS[backend]
            assert 0 < soft < hard


class TestCalibratorDispatch:
    def test_selects_cvc5_for_smtlib(self) -> None:
        cal = VerificationCalibrator()
        backend = cal.select_backend(SMT_SAMPLE, VerificationContext())
        assert backend == "cvc5"

    def test_selects_tla_for_module_syntax(self) -> None:
        cal = VerificationCalibrator()
        backend = cal.select_backend(TLA_SAMPLE, VerificationContext())
        assert backend == "tla"

    def test_selects_alloy_for_sig_syntax(self) -> None:
        cal = VerificationCalibrator()
        backend = cal.select_backend(ALLOY_SAMPLE, VerificationContext())
        assert backend == "alloy"

    def test_domain_hint_cvc5(self) -> None:
        cal = VerificationCalibrator()
        ctx = VerificationContext(domain_hint="cvc5")
        assert cal.select_backend("anything", ctx) == "cvc5"

    def test_domain_hint_tla(self) -> None:
        cal = VerificationCalibrator()
        ctx = VerificationContext(domain_hint="tla")
        assert cal.select_backend("anything", ctx) == "tla"


class TestHybridVerifierCompile:
    def test_compile_cvc5_success(self) -> None:
        hv = HybridVerifier()
        with patch("src.verification.cvc5_client.CVC5Client") as mock_cls:
            inst = mock_cls.return_value
            inst.available = True
            inst.verify.return_value = {"valid": True}
            result = hv._compile_cvc5(SMT_SAMPLE)
        assert result["status"] == "success"

    def test_compile_cvc5_not_installed(self) -> None:
        hv = HybridVerifier()
        with patch("src.verification.cvc5_client.CVC5Client") as mock_cls:
            mock_cls.return_value.available = False
            result = hv._compile_cvc5(SMT_SAMPLE)
        assert result["status"] == "not_installed"

    def test_compile_tla_success(self) -> None:
        hv = HybridVerifier()
        with patch("src.verification.tla_client.TLAClient") as mock_cls:
            inst = mock_cls.return_value
            inst.available = True
            inst.verify.return_value = {"valid": True}
            result = hv._compile_tla(TLA_SAMPLE)
        assert result["status"] == "success"

    def test_compile_alloy_error(self) -> None:
        hv = HybridVerifier()
        with patch("src.verification.alloy_client.AlloyClient") as mock_cls:
            inst = mock_cls.return_value
            inst.available = True
            inst.verify.return_value = {"valid": False, "error": "syntax error"}
            result = hv._compile_alloy(ALLOY_SAMPLE)
        assert result["status"] == "error"
        assert "syntax" in result["error"]

    def test_compile_dispatch_routes_cvc5(self) -> None:
        hv = HybridVerifier()
        with patch.object(hv, "_compile_cvc5", return_value={"status": "success", "error": ""}) as mock:
            result = hv._compile(SMT_SAMPLE, "cvc5")
        mock.assert_called_once()
        assert result["status"] == "success"


class TestLLMProverDispatch:
    @pytest.mark.asyncio
    async def test_get_verifier_cvc5(self) -> None:
        from src.verification.llm_prover import LLMProver

        prover = LLMProver()
        with patch("src.verification.cvc5_client.CVC5Client") as mock_cls:
            inst = mock_cls.return_value
            inst.verify.return_value = {"valid": True, "language": "cvc5"}
            verifier = prover._get_verifier("cvc5")
            result = await verifier(SMT_SAMPLE)
        assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_get_verifier_tla(self) -> None:
        from src.verification.llm_prover import LLMProver

        prover = LLMProver()
        with patch("src.verification.tla_client.TLAClient") as mock_cls:
            inst = mock_cls.return_value
            inst.verify.return_value = {"valid": True, "language": "tla"}
            verifier = prover._get_verifier("tla")
            result = await verifier(TLA_SAMPLE)
        assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_get_verifier_alloy(self) -> None:
        from src.verification.llm_prover import LLMProver

        prover = LLMProver()
        with patch("src.verification.alloy_client.AlloyClient") as mock_cls:
            inst = mock_cls.return_value
            inst.verify.return_value = {"valid": True, "language": "alloy"}
            verifier = prover._get_verifier("alloy")
            result = await verifier(ALLOY_SAMPLE)
        assert result["valid"] is True


class TestHybridBackendSelection:
    def test_select_backend_cvc5_for_smt_keywords(self) -> None:
        hv = HybridVerifier()
        claim = "Verify SMT-LIB2 (declare-const x Int) (check-sat)"
        assert hv._select_backend(claim) == "cvc5"

    def test_select_backend_tla_for_temporal(self) -> None:
        hv = HybridVerifier()
        claim = "TLA+ module with Init == and liveness []<>"
        assert hv._select_backend(claim) == "tla"

    def test_select_backend_alloy_for_relational(self) -> None:
        hv = HybridVerifier()
        claim = "Alloy sig Node fun parent: Node -> Node assert acyclic"
        assert hv._select_backend(claim) == "alloy"

    def test_preferred_backends_whitepaper_fallback_to_first(self) -> None:
        hv = HybridVerifier()
        preferred = ["z3", "cvc5", "tla", "alloy", "hoare"]
        claim = "Microservice deployment topology under sustained load"
        assert hv._select_backend(claim, preferred=preferred) == "z3"

    def test_preferred_backends_respects_strong_auto_signal(self) -> None:
        hv = HybridVerifier()
        preferred = ["z3", "cvc5", "alloy", "hoare"]
        claim = "Alloy sig Node fun parent: Node -> Node assert acyclic"
        assert hv._select_backend(claim, preferred=preferred) == "alloy"

    def test_preferred_backends_article_stays_z3_for_numeric(self) -> None:
        hv = HybridVerifier()
        preferred = ["z3", "cvc5", "dafny", "hoare"]
        claim = "Reaction rate increases 15% when temperature rises 10°C"
        assert hv._select_backend(claim, preferred=preferred) == "z3"
