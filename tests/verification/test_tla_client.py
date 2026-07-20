"""Deep tests for TLA+ TLC client."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.verification.tla_client import CFG_SEPARATOR, TLAClient


MINIMAL_TLA = """---- MODULE Counter ----
EXTENDS Naturals
VARIABLE x
Init == x = 0
Next == /\\ x < 5 /\\ x' = x + 1
====
"""

TEMPORAL_TLA = MINIMAL_TLA.replace("====", "Spec == Init /\\ [][Next]_x\n====\n")

TLA_WITH_CFG = MINIMAL_TLA + CFG_SEPARATOR + "INIT Init\nNEXT Next\n"


UNBOUNDED_TLA = """---- MODULE Counter ----
EXTENDS Naturals
VARIABLE x
Init == x = 0
Next == x' = x + 1
====
"""

BOUNDED_TLA_WITH_CFG = MINIMAL_TLA + CFG_SEPARATOR + "INIT Init\nNEXT Next\n"


class TestTLABoundedness:
    def test_detect_unbounded_naturals_counter(self) -> None:
        msg = TLAClient._detect_unbounded(UNBOUNDED_TLA, "")
        assert msg is not None
        assert "Unbounded" in msg

    def test_bounded_counter_not_flagged(self) -> None:
        assert TLAClient._detect_unbounded(MINIMAL_TLA, "") is None

    def test_constant_max_in_cfg_is_bounded(self) -> None:
        cfg = "CONSTANT MAX = 5\nINIT Init\nNEXT Next\n"
        tla = UNBOUNDED_TLA.replace("Next == x' = x + 1", "Next == /\\ x < MAX /\\ x' = x + 1")
        assert TLAClient._detect_unbounded(tla, cfg) is None

    def test_unbounded_rejected_without_running_tlc(self) -> None:
        client = TLAClient()
        client._available = True
        with patch("src.verification.tla_client.safe_subprocess_run") as mock_run:
            result = client.verify(UNBOUNDED_TLA)
        mock_run.assert_not_called()
        assert result["valid"] is False
        assert "Unbounded" in result["error"]

    def test_parse_65536_behavior_limit_fails(self) -> None:
        out = (
            "Error: TLC threw an unexpected exception.\n"
            "The specification contains one or more behaviors with 65536 or more states\n"
        )
        assert TLAClient._parse_result(out, "", 1) is False

    def test_first_error_maps_behavior_limit_to_hint(self) -> None:
        out = "behaviors with 65536 or more states"
        err = TLAClient._first_error(out, "")
        assert "Unbounded" in err


class TestTLAParsing:
    def test_extract_module_name(self) -> None:
        assert TLAClient._extract_module_name(MINIMAL_TLA) == "Counter"

    def test_missing_module_returns_none(self) -> None:
        assert TLAClient._extract_module_name("VARIABLE x") is None

    def test_split_cfg_block(self) -> None:
        tla, cfg = TLAClient._split_input(TLA_WITH_CFG)
        assert "MODULE Counter" in tla
        assert cfg.strip() == "INIT Init\nNEXT Next"

    def test_auto_cfg_from_init_next(self) -> None:
        cfg = TLAClient._auto_cfg(MINIMAL_TLA)
        assert "INIT Init" in cfg
        assert "NEXT Next" in cfg

    def test_auto_cfg_uses_specification_for_temporal(self) -> None:
        cfg = TLAClient._auto_cfg(TEMPORAL_TLA)
        assert "SPECIFICATION Spec" in cfg

    def test_success_output_parsing(self) -> None:
        out = "Model checking completed. No error found."
        assert TLAClient._parse_result(out, "", 0) is True

    def test_counterexample_fails(self) -> None:
        out = "Error: invariant violated. Counterexample found."
        assert TLAClient._parse_result(out, "", 12) is False

    def test_finished_with_deadlock_is_not_valid(self) -> None:
        # Honesty: "Error: Deadlock" is a soft failure, not verified success.
        out = (
            "Error: Deadlock reached.\n"
            "6 states generated, 6 distinct states found.\n"
            "Finished in 00s at (2026-07-12 02:04:00)\n"
        )
        assert TLAClient._parse_result(out, "", 11) is False

    def test_finished_with_states_no_error_is_valid(self) -> None:
        out = (
            "6 states generated, 6 distinct states found.\n"
            "Finished in 00s at (2026-07-12 02:04:00)\n"
        )
        assert TLAClient._parse_result(out, "", 0) is True


class TestTLAClientMocked:
    def test_not_installed(self) -> None:
        client = TLAClient(jar_path=None, tlc_path=None)
        client._available = False
        result = client.verify(MINIMAL_TLA)
        assert result["valid"] is False
        assert "not installed" in result["error"].lower()

    def test_missing_module_error(self) -> None:
        client = TLAClient()
        client._available = True
        result = client.verify("VARIABLE x\nInit == TRUE")
        assert result["valid"] is False
        assert "MODULE" in result["error"]

    def test_verify_success_via_java_tlc(self) -> None:
        client = TLAClient(tlc_path=None, jar_path="/fake/tla2tools.jar")
        client._available = True
        client.java_path = "/usr/bin/java"
        mock_result = MagicMock(returncode=0, stdout="Model checking completed.", stderr="")
        with patch("src.verification.tla_client.safe_subprocess_run", return_value=mock_result):
            result = client.verify(MINIMAL_TLA)
        assert result["valid"] is True
        assert result["module"] == "Counter"

    def test_verify_uses_tlc_binary_when_available(self) -> None:
        client = TLAClient(tlc_path="/usr/bin/tlc")
        client._available = True
        cmd_holder: list[list[str]] = []

        def capture(cmd: list[str], **kwargs: object) -> MagicMock:
            cmd_holder.append(cmd)
            return MagicMock(
                returncode=0,
                stdout="Model checking completed. No error found.",
                stderr="",
            )

        with patch("src.verification.tla_client.safe_subprocess_run", side_effect=capture):
            result = client.verify(MINIMAL_TLA)
        assert result["valid"] is True
        assert cmd_holder[0][0] == "/usr/bin/tlc"
        assert "-modelcheck" in cmd_holder[0]
        assert "-depth" in cmd_holder[0]
        depth_idx = cmd_holder[0].index("-depth")
        assert cmd_holder[0][depth_idx + 1] == str(TLAClient.DEFAULT_DEPTH)

    def test_check_proof_api(self) -> None:
        client = TLAClient(tlc_path=None, jar_path="/fake/tla2tools.jar")
        client._available = True
        client.java_path = "/usr/bin/java"
        mock_result = MagicMock(returncode=0, stdout="Model checking completed.", stderr="")
        with patch("src.verification.tla_client.safe_subprocess_run", return_value=mock_result):
            result = client.check_proof(MINIMAL_TLA)
        assert result["success"] is True


class TestJarResolver:
    def test_tla_jar_from_env(self, monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
        from pathlib import Path

        jar = Path(str(tmp_path)) / "tla2tools.jar"
        jar.write_text("fake", encoding="utf-8")
        monkeypatch.setenv("TLA_TOOLS_JAR", str(jar))
        from src.verification.jar_resolver import tla_tools_jar

        assert tla_tools_jar() == str(jar.resolve())
