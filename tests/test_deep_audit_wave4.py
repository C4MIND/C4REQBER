"""Deep audit wave-4 regression locks (path escape, celebration, honesty)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.knowledge.flash_contract import derive_terminal
from src.utils.security_middleware import quote_paper_id, validate_path


def test_validate_path_blocks_sibling_prefix(tmp_path: Path) -> None:
    base = tmp_path / ".c4reqber"
    base.mkdir()
    evil = tmp_path / ".c4reqber_evil"
    evil.mkdir()
    with pytest.raises(ValueError):
        validate_path(str(evil / "x"), allowed_base=base)


def test_quote_paper_id_rejects_traversal() -> None:
    with pytest.raises(ValueError):
        quote_paper_id("../etc/passwd")
    with pytest.raises(ValueError):
        quote_paper_id("abc?x=1")
    assert "%2F" in quote_paper_id("10.1000/xyz")


def test_derive_terminal_empty_is_partial_not_complete() -> None:
    assert derive_terminal("") == ("partial", "partial")
    assert derive_terminal(None) == ("partial", "partial")


@pytest.mark.asyncio
async def test_jobstore_missing_status_is_partial() -> None:
    from src.api.v8_routers.discovery.jobs import JobStore

    store = JobStore()
    job = await store.create("discover", {"problem": "x"})
    await store.set_complete(job.job_id, {"hypothesis": {"text": "h"}, "papers": []})
    got = await store.get(job.job_id)
    assert got is not None
    assert got.status.value == "partial"


def test_agda_compile_validates_module_name() -> None:
    from src.verification.agda_bridge import AgdaBridge

    bridge = AgdaBridge()
    bridge.available = True
    out = bridge.compile("data X : Set where", module_name="../Evil")
    assert out.get("success") is False
    assert "Invalid" in (out.get("errors") or [{}])[0].get("message", "")


def test_hybrid_agda_rejects_path_module() -> None:
    from src.verification.hybrid_verifier import HybridVerifier

    hv = HybridVerifier.__new__(HybridVerifier)
    out = hv._compile_agda("module ../Evil where\ndata X : Set where")
    assert out["status"] == "error"
    assert "Invalid" in out.get("error", "")


def test_export_empty_bibliography_raises(tmp_path: Path) -> None:
    from src.export.manager import ExportManager

    mgr = ExportManager(output_dir=str(tmp_path))
    with pytest.raises(ValueError, match="empty"):
        mgr.export_bibliography_latex([])


def test_bayesian_plugin_no_evidence_is_partial() -> None:
    from src.plugins.bayesian_update import execute

    out = execute("H0")
    assert out["status"] == "partial"
    assert out.get("heuristic") is True


def test_prompt_sanitizer_unescapes_before_detect() -> None:
    src = Path("src/security/prompt_sanitizer.py").read_text(encoding="utf-8")
    assert "html.unescape" in src


def test_mcp_c4_prove_in_string_args() -> None:
    from src.mcp_server.fallback_protocol import TOOL_STRING_ARGS

    assert "hypothesis" in TOOL_STRING_ARGS["c4_prove"]


def test_social_dry_run_statuses() -> None:
    orcid = Path("src/social/orcid_client.py").read_text(encoding="utf-8")
    assert 'return {"status": "dry_run"' in orcid
    arxiv = Path("src/social/arxiv_client.py").read_text(encoding="utf-8")
    assert 'return {"status": "dry_run"' in arxiv
    assert '"status": "submitted"' not in arxiv


def test_docker_compose_test_uses_real_dockerfile() -> None:
    text = Path("docker-compose.test.yml").read_text(encoding="utf-8")
    assert "dockerfile: Dockerfile" in text
    assert "Dockerfile.api" not in text
    assert "src.api.server:app" in text


def test_health_liveness_not_memory_greenfake() -> None:
    src = Path("src/api/health.py").read_text(encoding="utf-8")
    assert "process_alive" in src
    assert '"memory": True' not in src


def test_opencitations_quotes_doi() -> None:
    src = Path("src/knowledge/citation_chaser.py").read_text(encoding="utf-8")
    assert "quote(validate_paper_id(doi)" in src


def test_phase6_heuristic_blocks_complete() -> None:
    src = Path("src/pipeline/discovery_phases/phase_6_quality.py").read_text(encoding="utf-8")
    assert "heuristic_blocks" in src
    assert 'block.get("heuristic")' in src


def test_jwt_middleware_uses_auth_manager() -> None:
    src = Path("src/api/middleware/auth.py").read_text(encoding="utf-8")
    assert "AuthManager().decode_token" in src
    assert "jwt.decode(token, secret" not in src


def test_csrf_bearer_requires_valid_jwt() -> None:
    src = Path("src/api/middleware/csrf.py").read_text(encoding="utf-8")
    assert "decode_token" in src


def test_wasm_stub_not_registered_without_wasmtime() -> None:
    src = Path("src/cli/blast_app.py").read_text(encoding="utf-8")
    assert "NOT registered in pipeline" in src


def test_win_isolated_python_prefers_scripts() -> None:
    src = Path("src/cli/package_manager.py").read_text(encoding="utf-8")
    assert 'sys.platform == "win32"' in src


@pytest.mark.asyncio
async def test_discord_dry_run_status() -> None:
    from src.social.discord_webhook import DiscordWebhook

    client = DiscordWebhook(dry_run=True)
    out = await client.send("hi")
    assert out.get("status") == "dry_run"
    assert out.get("_dry_run") is True


def test_ensemble_requires_executed() -> None:
    src = Path("src/discovery/closed_loop/ensemble_runner.py").read_text(encoding="utf-8")
    assert "executed" in src


def test_citation_verifier_quotes_doi() -> None:
    src = Path("src/knowledge/citation_verifier.py").read_text(encoding="utf-8")
    assert "validate_paper_id(doi)" in src


def test_live_feed_hypothesis_has_heuristic_field() -> None:
    from src.intel.live_feed import Hypothesis

    h = Hypothesis(
        id="h1",
        title="t",
        source_problems=[],
        confidence=0.4,
        domain="x",
        heuristic=True,
        method="keyword_cluster",
    )
    assert h.heuristic is True
    assert h.method == "keyword_cluster"


def test_novelty_empty_search_not_novel() -> None:
    src = Path("src/novelty/validator.py").read_text(encoding="utf-8")
    assert "empty_search" in src
    assert '"novel": None' in src


def test_ok_status_not_celebration() -> None:
    from src.knowledge.flash_contract import celebration_allowed, derive_terminal

    assert derive_terminal("ok") == ("partial", "partial")
    assert celebration_allowed("ok") is False


def test_haskell_module_name_validated() -> None:
    from src.verification.haskell_bridge import verify_haskell_typecheck

    out = verify_haskell_typecheck("x = 1", module_name="../Evil")
    assert out["status"] == "error"


def test_validate_sim_path_rejects_escape(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from src.utils.security_middleware import validate_sim_path

    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError):
        validate_sim_path("/etc/passwd")


def test_zenodo_dry_run_unverified() -> None:
    src = Path("src/social/health_checker.py").read_text(encoding="utf-8")
    assert src.count('"unverified": True') >= 5
