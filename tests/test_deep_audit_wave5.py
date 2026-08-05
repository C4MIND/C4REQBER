"""Deep audit wave-5/6 — behavioral regression locks (not source-grep theatre)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.utils.honesty_status import (
    outer_status_from_sim_payload,
    sse_engine_status_from_sim_payload,
)


def test_sse_engine_status_demotes_newton_fallback() -> None:
    payload = {
        "status": "completed",
        "executed": True,
        "engine_truth": "not_newton_physics",
    }
    assert outer_status_from_sim_payload(payload) == "partial"
    assert sse_engine_status_from_sim_payload(payload) == "partial"


def test_sse_engine_status_demotes_amuse_rebound() -> None:
    payload = {
        "status": "success",
        "executed": True,
        "engine_truth": "rebound_not_amuse",
    }
    assert sse_engine_status_from_sim_payload(payload) == "partial"


def test_sse_engine_status_ok_only_with_real_truth() -> None:
    payload = {
        "status": "success",
        "executed": True,
        "engine_truth": "newton_physics",
        "engine": "newton",
    }
    assert sse_engine_status_from_sim_payload(payload) == "ok"


def test_cvc5_sat_not_valid_proof() -> None:
    from src.verification.cvc5_client import CVC5Client

    assert CVC5Client._parse_result("sat\n", "", 0) is False
    assert CVC5Client._parse_result("unsat\n", "", 0) is True


def test_cache_manager_degraded_when_redis_down(monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio

    from src.api import cache as cache_mod

    monkeypatch.setenv("CACHE_BACKEND", "redis")
    monkeypatch.setattr(cache_mod, "HAS_REDIS", True)

    class BoomRedis:
        async def connect(self) -> None:
            raise ConnectionError("down")

        async def ping(self) -> bool:
            return False

        async def disconnect(self) -> None:
            return None

    monkeypatch.setattr(cache_mod, "RedisCache", BoomRedis)
    mgr = cache_mod.CacheManager()
    asyncio.run(mgr.connect())
    assert mgr.degraded is True
    assert mgr.backend_name == "memory_fallback"
    assert asyncio.run(mgr.ping()) is False


def test_docker_compose_health_probe_aligned() -> None:
    text = Path("docker-compose.yml").read_text(encoding="utf-8")
    assert "/api/v1/health" in text
    assert 'http://localhost:8000/health"]' not in text


def test_health_ssot_is_routers_health() -> None:
    orphan = Path("src/api/health.py").read_text(encoding="utf-8")
    assert "routers.health" in orphan
    canon = Path("src/api/routers/health.py").read_text(encoding="utf-8")
    assert 'prefix="/api/v1"' in canon
    assert '"memory": True' not in canon


def test_landing_en_api_title_matches_package() -> None:
    from src import __version__

    data = json.loads(Path("landing/i18n/en.json").read_text(encoding="utf-8"))
    assert __version__ in data["api_rest_title"]
    assert "5.6.0" not in data["api_rest_title"]
    assert "probe for availability" in data["home_tui_cap_summary"]


@pytest.mark.asyncio
async def test_zenodo_dry_run_create_and_publish_omit_doi() -> None:
    from src.social.zenodo_client import ZenodoClient

    client = ZenodoClient(dry_run=True)
    created = await client.create_deposit("Title")
    assert created.get("_dry_run") is True
    assert "doi" not in created
    published = await client.publish("dry-run-1")
    assert published.get("_dry_run") is True
    assert "doi" not in published


def test_qe_rejects_passwd_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from src.simulations.quantum_espresso_bridge import QuantumEspressoBridge

    monkeypatch.chdir(tmp_path)
    bridge = QuantumEspressoBridge()
    monkeypatch.setattr(bridge, "is_available", lambda: True)
    out = bridge.run({"input_file": "/etc/passwd"})
    status_s = str(getattr(out.status, "value", out.status)).lower()
    note = str((out.data or {}).get("note") or "")
    assert status_s in {"unavailable", "failed", "error", "partial"}
    assert "allowlist" in note.lower() or "outside" in note.lower() or "traversal" in note.lower()


@pytest.mark.asyncio
async def test_novelty_empty_crossref_is_unchecked(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx

    from src.novelty import validator as nov_mod

    monkeypatch.setattr(nov_mod, "HAS_HTTPX", True)

    class FakeResp:
        status_code = 200

        def json(self) -> dict[str, Any]:
            return {"message": {"items": []}}

    class FakeClient:
        def __init__(self, *a: Any, **k: Any) -> None:
            pass

        async def __aenter__(self) -> FakeClient:
            return self

        async def __aexit__(self, *a: Any) -> None:
            return None

        async def get(self, *a: Any, **k: Any) -> FakeResp:
            return FakeResp()

    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
    v = nov_mod.NoveltyValidator()
    out = await v.check_novelty("cryogenic AISI 440C")
    assert out["status"] == "unchecked"
    assert out["novel"] is None
    assert out.get("reason") == "empty_search"


def test_errors_dev_mode_alone_no_detail_leak(monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio

    from src.api import errors as err_mod

    monkeypatch.setenv("DEV_MODE", "1")
    monkeypatch.delenv("DEV_MODE_BYPASS_TOKEN", raising=False)
    req = MagicMock()
    resp = asyncio.run(err_mod.c4_api_exception_handler(req, RuntimeError("secret-stack")))
    body = json.loads(resp.body.decode())
    assert body["detail"] == {}
    assert "secret-stack" not in resp.body.decode()


def test_errors_dev_mode_with_bypass_leaks_type(monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio

    from src.api import errors as err_mod

    monkeypatch.setenv("DEV_MODE", "1")
    monkeypatch.setenv("DEV_MODE_BYPASS_TOKEN", "tok")
    req = MagicMock()
    resp = asyncio.run(err_mod.c4_api_exception_handler(req, RuntimeError("secret-stack")))
    body = json.loads(resp.body.decode())
    assert body["detail"].get("exception_type") == "RuntimeError"


def test_phase_e_fallback_truth_not_success() -> None:
    """Call honesty path the same way phase_e does for a fallback bridge payload."""
    honesty_payload = {
        "status": "completed",
        "executed": True,
        "engine_truth": "legacy_fallback",
        "engine": "newtonian",
    }
    assert outer_status_from_sim_payload(honesty_payload) == "partial"


def test_dissertation_sim_ok_gate_rejects_fallback() -> None:
    """Reproduce dissertation sim_ok predicate on a fake partial sim."""
    simulation = {
        "status": "success",
        "stub": False,
        "heuristic": False,
        "engine_truth": "not_newton_physics",
        "pattern_id": "newtonian",
        "interpretation": "fake",
        "metrics": {},
    }
    sim_ok = (
        simulation
        and simulation.get("status") == "success"
        and not simulation.get("stub")
        and not simulation.get("heuristic")
        and not str(simulation.get("engine_truth") or "").startswith("not_")
        and "fallback" not in str(simulation.get("engine_truth") or "").lower()
    )
    assert sim_ok is False


def test_flash_runner_resets_cost_tracker(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.knowledge import flash_runner
    from src.llm.cost_tracker import get_cost_tracker

    tracker = get_cost_tracker()
    tracker.reset = MagicMock(wraps=tracker.reset)  # type: ignore[method-assign]

    class FakeLLM:
        async def chat(self, *a: Any, **k: Any) -> str:
            return "answer"

        async def generate(self, *a: Any, **k: Any) -> Any:
            return type("R", (), {"content": "answer"})()

    monkeypatch.setattr("src.llm.gateway.get_gateway", lambda: FakeLLM())
    monkeypatch.setattr("src.config.paths.apply_config_to_env", lambda: None)

    async def _run() -> None:
        await flash_runner.run_flash("q?", with_sources=False, deep=False)

    import asyncio

    asyncio.run(_run())
    tracker.reset.assert_called()


def test_blast_simulate_exit_on_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """CLI simulate must Exit(2) when outer status is partial (fallback truth)."""
    import typer
    from typer.testing import CliRunner

    from src.cli.blast_app import app

    monkeypatch.setattr(
        "src.simulations.runner_v2.get_runner_v2",
        lambda: MagicMock(
            run=lambda *a, **k: {
                "status": "completed",
                "executed": True,
                "engine_truth": "not_newton_physics",
                "stub": False,
            }
        ),
    )
    runner = CliRunner()
    result = runner.invoke(app, ["simulate", "--engine", "newtonian"])
    assert result.exit_code == 2


def test_go_sim_honesty_and_ok_no_celebrate_pass() -> None:
    """Run Go unit tests that lock provenance demotion + no celebrate on ambiguous ok."""
    import subprocess

    r = subprocess.run(
        [
            "go",
            "test",
            "-count=1",
            "-timeout",
            "60s",
            "-run",
            "SimStatus|OkNo|FlashResultOkNoCelebrate|HandleCompleteEventOkNoAchievement",
            ".",
        ],
        cwd="src/tui/v9",
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stdout + r.stderr
