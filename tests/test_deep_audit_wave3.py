"""Deep audit wave-3 regression locks (honesty, security, sim provenance)."""

from __future__ import annotations

from pathlib import Path

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


def test_doaj_encodes_query_path() -> None:
    src = Path("src/knowledge/sources/doaj.py").read_text(encoding="utf-8")
    assert "quote(query" in src
    assert 'f"{url}/{query}"' not in src


def test_hybrid_verifier_compile_is_compiled_not_verified() -> None:
    src = Path("src/verification/hybrid_verifier.py").read_text(encoding="utf-8")
    assert 'status="compiled"' in src
    assert "COMPILED" in src
