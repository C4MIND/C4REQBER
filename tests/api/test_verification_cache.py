"""Verification cache must not grow without bound."""
from __future__ import annotations

import time

from src.api.v8_routers import verification_v8 as vv


def test_verify_cache_prunes_expired_and_caps_size(monkeypatch) -> None:
    monkeypatch.setattr(vv, "_VERIFY_CACHE_MAX", 3)
    monkeypatch.setattr(vv, "_VERIFY_CACHE_TTL", 1)
    vv._verify_cache.clear()

    for i in range(5):
        vv._set_verify_cache(f"id-{i}", {"status": "completed", "verified": True})

    assert len(vv._verify_cache) <= 3

    vv._verify_cache["old"] = {"updated_at": time.time() - 10, "status": "completed"}
    vv._set_verify_cache("new", {"status": "completed"})
    assert "old" not in vv._verify_cache
