"""Deep tests for Alloy analyzer client."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.verification.alloy_client import AlloyClient


MINIMAL_ALLOY = """
sig Node {}
fact noDup { all n: Node | lone n }
assert emptyOK { no Node }
check emptyOK for 3
"""


class TestAlloyNormalization:
    def test_adds_run_when_missing(self) -> None:
        code = "sig A {}"
        out = AlloyClient._normalize_code(code)
        assert "run" in out.lower()

    def test_preserves_existing_run(self) -> None:
        out = AlloyClient._normalize_code(MINIMAL_ALLOY)
        assert "check emptyOK" in out


# Realistic Alloy CLI success (positive token required by honesty contract).
ALLOY_SAT_OK = "00. run   run$1                    0    1/1     SAT\n"


class TestAlloyParsing:
    def test_success_no_errors(self) -> None:
        assert AlloyClient._parse_result(ALLOY_SAT_OK, "", 0) is True

    def test_executing_done_alone_is_not_success(self) -> None:
        # Honesty: returncode/Done without positive tokens ≠ verified.
        assert AlloyClient._parse_result("Executing...\nDone.", "", 0) is False

    def test_syntax_error_fails(self) -> None:
        assert AlloyClient._parse_result("", "Syntax error at line 3", 1) is False

    def test_counterexample_fails(self) -> None:
        out = "Counterexample found. Skolemizing..."
        assert AlloyClient._parse_result(out, "", 0) is False

    def test_assertion_no_counterexample_passes(self) -> None:
        out = "Checking assertion emptyOK: No counterexample found."
        assert AlloyClient._parse_result(out, "", 0) is True


class TestAlloyClientMocked:
    def test_not_installed(self) -> None:
        client = AlloyClient(alloy_path=None, jar_path=None)
        client._available = False
        result = client.verify(MINIMAL_ALLOY)
        assert result["valid"] is False
        assert "not installed" in result["error"].lower()

    def test_verify_via_alloy_binary(self) -> None:
        client = AlloyClient(alloy_path="/usr/bin/alloy")
        client._available = True
        cmd_holder: list[list[str]] = []

        def capture(cmd: list[str], **kwargs: object) -> MagicMock:
            cmd_holder.append(cmd)
            return MagicMock(returncode=0, stdout=ALLOY_SAT_OK, stderr="")

        with patch("src.verification.alloy_client.safe_subprocess_run", side_effect=capture):
            result = client.verify(MINIMAL_ALLOY)
        assert result["valid"] is True
        assert cmd_holder[0][:2] == ["/usr/bin/alloy", "exec"]

    def test_verify_via_java_jar(self) -> None:
        client = AlloyClient(alloy_path=None, jar_path="/fake/alloy.jar")
        client._available = True
        client.java_path = "/usr/bin/java"
        mock_result = MagicMock(returncode=0, stdout=ALLOY_SAT_OK, stderr="")
        with patch("src.verification.alloy_client.safe_subprocess_run", return_value=mock_result):
            result = client.verify(MINIMAL_ALLOY)
        assert result["valid"] is True

    def test_check_proof_api(self) -> None:
        client = AlloyClient(alloy_path="/usr/bin/alloy")
        client._available = True
        mock_result = MagicMock(
            returncode=0,
            stdout="Checking assertion emptyOK: No counterexample found.",
            stderr="",
        )
        with patch("src.verification.alloy_client.safe_subprocess_run", return_value=mock_result):
            result = client.check_proof(MINIMAL_ALLOY)
        assert result["success"] is True


class TestAlloyJarResolver:
    def test_alloy_jar_from_env(self, monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
        from pathlib import Path

        jar = Path(str(tmp_path)) / "org.alloytools.alloy.dist.jar"
        jar.write_text("fake", encoding="utf-8")
        monkeypatch.setenv("ALLOY_JAR", str(jar))
        from src.verification.jar_resolver import alloy_jar

        assert alloy_jar() == str(jar.resolve())
