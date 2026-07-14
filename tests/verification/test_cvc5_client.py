"""Deep tests for CVC5 SMT-LIB2 client."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.verification.cvc5_client import CVC5Client


SAT_SMT = """(set-logic QF_LIA)
(declare-const x Int)
(assert (> x 0))
(check-sat)
"""

UNSAT_SMT = """(set-logic QF_LIA)
(declare-const x Int)
(assert (> x 0))
(assert (< x 0))
(check-sat)
"""

ERROR_SMT = "(set-logic QF_LIA)\n(assert (> x 0))\n(check-sat)\n"


class TestCVC5Normalization:
    def test_adds_check_sat_when_missing(self) -> None:
        code = "(declare-const x Int)"
        out = CVC5Client._normalize_smtlib(code)
        assert "(check-sat)" in out.lower()

    def test_adds_set_logic_when_missing(self) -> None:
        code = "(declare-const x Int)\n(check-sat)"
        out = CVC5Client._normalize_smtlib(code)
        assert "(set-logic" in out.lower()

    def test_empty_code_gets_defaults(self) -> None:
        out = CVC5Client._normalize_smtlib("")
        assert "(check-sat)" in out
        assert "(set-logic" in out


class TestCVC5Parsing:
    def test_sat_is_valid(self) -> None:
        assert CVC5Client._parse_result("sat\n", "", 0) is True
        assert CVC5Client._extract_sat_status("sat", "") == "sat"

    def test_unsat_is_valid(self) -> None:
        assert CVC5Client._parse_result("unsat\n", "", 0) is True
        assert CVC5Client._extract_sat_status("unsat", "") == "unsat"

    def test_unknown_is_invalid(self) -> None:
        assert CVC5Client._parse_result("unknown\n", "", 0) is False

    def test_error_output_is_invalid(self) -> None:
        assert CVC5Client._parse_result("", "error: parse failed", 1) is False

    def test_nonzero_exit_invalid_even_with_sat(self) -> None:
        assert CVC5Client._parse_result("sat", "", 1) is False


class TestCVC5ClientMocked:
    def test_not_installed_returns_error(self) -> None:
        client = CVC5Client(cvc5_path="/nonexistent/cvc5")
        client._available = False
        result = client.verify(SAT_SMT)
        assert result["valid"] is False
        assert "not installed" in result["error"].lower()

    def test_verify_sat_success(self) -> None:
        client = CVC5Client()
        client._available = True
        mock_result = MagicMock(returncode=0, stdout="sat\n", stderr="")
        with patch("src.verification.cvc5_client.safe_subprocess_run", return_value=mock_result):
            result = client.verify(SAT_SMT)
        assert result["valid"] is True
        assert result["status"] == "sat"
        assert result["language"] == "cvc5"

    def test_verify_unsat_success(self) -> None:
        client = CVC5Client()
        client._available = True
        mock_result = MagicMock(returncode=0, stdout="unsat\n", stderr="")
        with patch("src.verification.cvc5_client.safe_subprocess_run", return_value=mock_result):
            result = client.verify(UNSAT_SMT)
        assert result["valid"] is True
        assert result["status"] == "unsat"

    def test_verify_parse_error(self) -> None:
        client = CVC5Client()
        client._available = True
        mock_result = MagicMock(returncode=1, stdout="", stderr="error: undeclared identifier x")
        with patch("src.verification.cvc5_client.safe_subprocess_run", return_value=mock_result):
            result = client.verify(ERROR_SMT)
        assert result["valid"] is False
        assert result["error"]

    def test_check_proof_mirrors_verify(self) -> None:
        client = CVC5Client()
        client._available = True
        mock_result = MagicMock(returncode=0, stdout="sat\n", stderr="")
        with patch("src.verification.cvc5_client.safe_subprocess_run", return_value=mock_result):
            result = client.check_proof(SAT_SMT)
        assert result["success"] is True
        assert result["errors"] == []


@pytest.mark.integration
class TestCVC5Integration:
    def test_real_cvc5_sat_if_installed(self) -> None:
        client = CVC5Client()
        if not client.test_connection():
            pytest.skip("cvc5 not installed")
        result = client.verify(SAT_SMT)
        assert result["valid"] is True
        assert result["status"] == "sat"

    def test_real_cvc5_unsat_if_installed(self) -> None:
        client = CVC5Client()
        if not client.test_connection():
            pytest.skip("cvc5 not installed")
        result = client.verify(UNSAT_SMT)
        assert result["valid"] is True
        assert result["status"] == "unsat"
