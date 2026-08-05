"""Windows console encoding + mascot ASCII fallback."""

from __future__ import annotations

from src.cli.cube_mascot import CUBE_STATES_ASCII, CubeMascot, inject_mascot_status
from src.cli.win_console import ensure_cli_utf8, stdout_supports_unicode


def test_ensure_cli_utf8_is_idempotent() -> None:
    ensure_cli_utf8()
    ensure_cli_utf8()  # must not raise


def test_mascot_ascii_fallback_when_unicode_unsupported(monkeypatch) -> None:
    monkeypatch.setattr("src.cli.win_console.stdout_supports_unicode", lambda: False)
    m = CubeMascot()
    m.set_state("done")
    m.comment = "flash complete. 1 verified sources."
    out = m.render()
    assert CUBE_STATES_ASCII["done"] in out
    assert "◈" not in out


def test_mascot_inject_status_encodable_on_ascii(monkeypatch) -> None:
    monkeypatch.setattr("src.cli.win_console.stdout_supports_unicode", lambda: False)
    line = inject_mascot_status(mode="flash", state="done", sources=1)
    # Must be encodable as cp1251 (common Windows RU console) without error
    line.encode("cp1251", errors="strict")
    assert "[OK]" in line or "flash" in line


def test_stdout_supports_unicode_smoke() -> None:
    # Just ensure the probe returns a bool on this host
    assert isinstance(stdout_supports_unicode(), bool)
