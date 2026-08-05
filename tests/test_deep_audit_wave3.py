"""Deep audit wave-3 regression locks (honesty, security, sim provenance)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.config.draft_paths import safe_draft_dir
from src.llm.error_shaped import is_error_shaped_llm
from src.utils.honesty_status import outer_status_from_sim_payload


def test_legacy_fallback_engine_truth_is_partial() -> None:
    status = outer_status_from_sim_payload(
        {
            "status": "completed",
            "executed": True,
            "engine_truth": "legacy_fallback",
        }
    )
    assert status == "partial"


def test_bare_executed_without_engine_truth_is_partial() -> None:
    status = outer_status_from_sim_payload(
        {"status": "completed", "executed": True, "engine": "custom_bridge"}
    )
    assert status == "partial"


def test_error_shaped_llm_helper() -> None:
    assert is_error_shaped_llm("[MLX Error] boom")
    assert is_error_shaped_llm("Batch error: timeout")
    assert not is_error_shaped_llm("Normal scientific answer")


def test_safe_draft_dir_blocks_traversal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.config.draft_paths.CONFIG_DIR", tmp_path / ".c4reqber")
    with pytest.raises(ValueError):
        safe_draft_dir("../../.ssh")
    with pytest.raises(ValueError):
        safe_draft_dir("foo/bar")
    ok = safe_draft_dir("draft_abc123")
    assert ok.name == "draft_abc123"
    assert "drafts" in str(ok)


@pytest.mark.asyncio
async def test_c4_verify_rejects_sorry() -> None:
    from src.mcp_server.tools_verify import c4_verify

    out = await c4_verify("theorem T : True := by sorry", language="lean4")
    assert out["valid"] is False
    assert out["status"] == "error"
    assert "sorry" in (out.get("error") or "").lower()


@pytest.mark.asyncio
async def test_doaj_encodes_query_path() -> None:
    """Path segment must be URL-encoded — raw '/' or spaces must not appear unescaped."""
    from src.knowledge.sources.doaj import DoajAdapter

    captured: dict[str, str] = {}

    class FakeResp:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"results": []}

    class FakeClient:
        async def __aenter__(self) -> FakeClient:
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def get(self, url: str, params: dict | None = None) -> FakeResp:
            captured["url"] = url
            return FakeResp()

    with patch("src.knowledge.sources.doaj.httpx.AsyncClient", return_value=FakeClient()):
        await DoajAdapter().search("foo/bar baz", limit=5)

    assert "url" in captured
    # Encoded path segment — not a raw slash splice into the API path
    assert "foo/bar" not in captured["url"].split("articles/", 1)[-1]
    assert "foo%2Fbar" in captured["url"] or "foo%2Fbar%20baz" in captured["url"]


@pytest.mark.asyncio
async def test_hybrid_verifier_compile_is_compiled_not_verified() -> None:
    """Compile/typecheck success must stamp COMPILED, never paint verified."""
    from src.verification.hybrid_verifier import HybridVerifier

    hv = HybridVerifier()
    hv.reasoner = MagicMock()
    hv.reasoner.generate_proof = AsyncMock(return_value="theorem T : True := by trivial")
    hv._compile = MagicMock(return_value={"status": "success"})  # type: ignore[method-assign]

    out = await hv.verify(
        {"title": "lemma algebra identity", "description": "number theory proof"},
        context={"preferred_backends": ["lean4"]},
    )
    assert out.status == "compiled"
    assert out.status != "verified"
    assert (out.timing_info or {}).get("stamp") == "COMPILED"
    assert (out.timing_info or {}).get("verification_aligned") is False
    assert "COMPILED" in (out.proof_text or "")
