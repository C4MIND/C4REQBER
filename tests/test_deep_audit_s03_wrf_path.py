"""Suite 03 — WRF wrfout path must use validate_sim_path (no /etc traversal)."""

from __future__ import annotations

import pytest

from src.simulations.base_adapter import SimStatus


def test_wrf_rejects_path_outside_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.simulations.wrf_bridge import WrfBridge

    bridge = WrfBridge()
    monkeypatch.setattr(bridge, "is_available", lambda: True)

    out = bridge.run({"wrfout": "/etc/passwd"})
    assert out.status != SimStatus.SUCCESS
    blob = f"{out.error_message} {out.data}".lower()
    assert "allowlist" in blob or "outside" in blob or "traversal" in blob
