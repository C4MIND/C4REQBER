from __future__ import annotations

import pytest

from src.c4.injection_hook import _run_check, _run_status, process_injections


class TestProcessInjections:
    def test_plain_text_unchanged(self) -> None:
        result = process_injections("This is a normal prompt without injections.")
        assert result == "This is a normal prompt without injections."

    def test_c4_status_injection(self) -> None:
        result = process_injections("!c4 status")
        assert "[C4 status]" in result
        assert "!c4" not in result

    def test_c4_check_ok(self) -> None:
        result = process_injections('!c4 check "all things are good"')
        assert "[C4 check:OK]" in result

    def test_c4_check_warn_contradiction(self) -> None:
        result = process_injections('!c4 check "always X and never X"')
        assert "always+never pair" in result

    def test_mixed_text_with_injections(self) -> None:
        result = process_injections("Hello\n!c4 status\nAnd continue")
        assert "Hello" in result
        assert "[C4 status]" in result
        assert "!c4" not in result


class TestRunCheck:
    def test_no_contradiction(self) -> None:
        result = _run_check("the sky is blue and grass is green")
        assert result == "[C4 check:OK] No obvious surface contradictions detected"

    def test_always_never_pair(self) -> None:
        result = _run_check("we must always do X and never do Y")
        assert result == "[C4 check:WARN] Potential contradictions: always+never pair"

    def test_all_none_pair(self) -> None:
        result = _run_check("all cases pass and none fail")
        assert result == "[C4 check:WARN] Potential contradictions: all+none pair"

    def test_both_pairs(self) -> None:
        result = _run_check("always good and never bad, all pass and none fail")
        assert "[C4 check:WARN]" in result
        assert "always+never pair" in result
        assert "all+none pair" in result


class TestRunStatus:
    def test_returns_c4_status_string(self) -> None:
        result = _run_status()
        assert "[C4 status]" in result
        assert "C4" in result
        assert "!c4" not in result
