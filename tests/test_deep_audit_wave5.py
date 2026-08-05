"""Deep audit wave-5/6 regression locks (TUI/SSE dual-path, health, sims, verify)."""

from __future__ import annotations

from pathlib import Path

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


def test_pipeline_logic_uses_sse_mapper() -> None:
    src = Path("src/discovery/pipeline_logic.py").read_text(encoding="utf-8")
    assert "sse_engine_status_from_sim_payload" in src
    assert 'data.get("engine_truth") == "not_newton_physics"' not in src


def test_go_sim_status_checks_engine_truth() -> None:
    src = Path("src/tui/v9/model.go").read_text(encoding="utf-8")
    assert "EngineTruth" in src
    assert "fallbackTruth" in src or "not_" in src


def test_health_ssot_is_routers_health() -> None:
    """Orphan shim re-exports mounted router — tests must not invent process_alive there."""
    orphan = Path("src/api/health.py").read_text(encoding="utf-8")
    assert "routers.health" in orphan
    canon = Path("src/api/routers/health.py").read_text(encoding="utf-8")
    assert 'prefix="/api/v1"' in canon
    assert '"memory": True' not in canon


def test_docker_compose_health_probe_aligned() -> None:
    text = Path("docker-compose.yml").read_text(encoding="utf-8")
    assert "/api/v1/health" in text
    assert 'http://localhost:8000/health"]' not in text


def test_qe_and_vina_use_validate_sim_path() -> None:
    qe = Path("src/simulations/quantum_espresso_bridge.py").read_text(encoding="utf-8")
    vina = Path("src/simulations/vina_bridge.py").read_text(encoding="utf-8")
    assert "validate_sim_path" in qe
    assert "validate_sim_path" in vina


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

    async def _run() -> None:
        await mgr.connect()

    asyncio.run(_run())
    assert mgr.degraded is True
    assert mgr.backend_name == "memory_fallback"
    assert asyncio.run(mgr.ping()) is False


def test_landing_en_version_matches_package() -> None:
    from src import __version__

    en = Path("landing/i18n/en.json").read_text(encoding="utf-8")
    assert f"v{__version__}" in en or __version__ in en
    assert "v5.6.0" not in en.split("api_rest_title")[1][:80]
    assert "probe for availability" in en


def test_zenodo_dry_run_omits_doi() -> None:
    src = Path("src/social/zenodo_client.py").read_text(encoding="utf-8")
    assert "10.5281/zenodo.dry-run" not in src


def test_phase_e_uses_honesty_mapper() -> None:
    src = Path("src/pipeline/hil_phases/phase_e_simulation.py").read_text(encoding="utf-8")
    assert "outer_status_from_sim_payload" in src


def test_dissertation_gates_sim_success() -> None:
    src = Path("src/publishing/dissertation.py").read_text(encoding="utf-8")
    assert "sim_ok" in src
    assert "engine_truth" in src


def test_agent_knowledge_search_not_llm_stub() -> None:
    src = Path("src/agent/core.py").read_text(encoding="utf-8")
    assert "gather_flash_sources" in src
    assert "Search knowledge for:" not in src


def test_errors_dev_mode_requires_bypass_token() -> None:
    src = Path("src/api/errors.py").read_text(encoding="utf-8")
    assert "DEV_MODE_BYPASS_TOKEN" in src


def test_flash_surface_defaults_documented() -> None:
    src = Path("src/knowledge/flash_contract.py").read_text(encoding="utf-8")
    assert "with_sources=False" in src
    assert "with_sources=True" in src


def test_run_flash_resets_cost_tracker() -> None:
    src = Path("src/knowledge/flash_runner.py").read_text(encoding="utf-8")
    assert "get_cost_tracker().reset()" in src


def test_blast_simulate_uses_outer_status() -> None:
    src = Path("src/cli/blast_app.py").read_text(encoding="utf-8")
    assert "outer_status_from_sim_payload" in src
