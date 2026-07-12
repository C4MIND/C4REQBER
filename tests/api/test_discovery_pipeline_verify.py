"""discovery_pipeline formal verification must resolve real client classes."""
from __future__ import annotations

import importlib
import types

import pytest

from src.api.v8_routers import discovery_pipeline as dp


class _FakeLean4Client:
    async def verify_discovery(self, hypothesis: str, evidence: list[str]) -> dict:
        return {"success": True, "output": f"ok:{hypothesis[:10]}"}


class _FakeCoqClient:
    async def verify_discovery(self, hypothesis: str, evidence: list[str]) -> dict:
        return {"success": False, "output": "skip"}


class _FakeDafnyClient:
    async def verify_discovery(self, hypothesis: str, evidence: list[str]) -> dict:
        return {"success": False, "output": "skip"}


def _fake_import_module(name: str) -> types.ModuleType:
    mod = types.ModuleType(name)
    if name == "src.verification.lean4_client":
        mod.Lean4Client = _FakeLean4Client  # type: ignore[attr-defined]
    elif name == "src.verification.coq_client":
        mod.CoqClient = _FakeCoqClient  # type: ignore[attr-defined]
    elif name == "src.verification.dafny_client":
        mod.DafnyClient = _FakeDafnyClient  # type: ignore[attr-defined]
    else:
        raise ImportError(name)
    return mod


@pytest.mark.asyncio
async def test_run_formal_verification_resolves_lean4_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(importlib, "import_module", _fake_import_module)
    results = {"hypothesis": {"text": "forall n, n + 0 = n"}}
    await dp._run_formal_verification(results, [], [])
    assert results["verification"]["lean4"]["verified"] is True
