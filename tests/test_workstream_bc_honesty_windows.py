"""Workstream B+C regression locks: models SSOT, synthesis, retry, honesty, Windows packaging."""

from __future__ import annotations

import ast
import inspect
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.llm.async_client import AsyncLLMClient
from src.llm.config import LLMProvider, get_default_model
from src.llm.model_assignment import ModelAssignment, get_model_for_phase
from src.llm.retry_pkg.policies import ProviderRetryManager


# ─── F3: AsyncLLMClient uses ModelAssignment / models.json ───────────────────


def test_async_client_resolve_model_uses_get_model_for_phase(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg = tmp_path / "models.json"
    assignment = ModelAssignment.create_default("budget")
    assignment.phases["D"].model = "test-provider/assigned-model-d"
    assignment.save(cfg)
    monkeypatch.setattr("src.llm.model_assignment.CONFIG_FILE", cfg)
    monkeypatch.setattr("src.config.paths.MODELS_JSON", cfg)

    client = AsyncLLMClient.__new__(AsyncLLMClient)
    client.DEFAULT_MODEL = "qwen/qwen-2.5-72b-instruct"
    client.default_phase = "D"

    with patch("src.llm.model_assignment.ModelAssignment.load", return_value=assignment):
        resolved = client._resolve_model(None, phase="D")
    assert resolved == "test-provider/assigned-model-d"


def test_async_client_task_alias_maps_to_phase(monkeypatch: pytest.MonkeyPatch) -> None:
    assignment = ModelAssignment.create_default("balanced")
    assignment.phases["F"].model = "assigned/synthesis-model"

    client = AsyncLLMClient.__new__(AsyncLLMClient)
    client.DEFAULT_MODEL = "fallback"
    client.default_phase = "D"

    with patch(
        "src.llm.model_assignment.get_model_for_phase", return_value="assigned/synthesis-model"
    ) as mock_g:
        resolved = client._resolve_model("synthesis")
    mock_g.assert_called()
    assert resolved == "assigned/synthesis-model"


def test_get_model_for_phase_reads_assignment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg = tmp_path / "models.json"
    ma = ModelAssignment.create_default("premium")
    ma.save(cfg)
    monkeypatch.setattr("src.llm.model_assignment.CONFIG_FILE", cfg)
    model = get_model_for_phase("A", assignment=ma)
    assert model == ma.get_model("A")
    assert model  # non-empty


# ─── F4: synthesis init-before-branch (no UnboundLocal) ──────────────────────


def test_step_08_synthesis_inits_response_and_usage_before_branch() -> None:
    src = Path("src/agents/pipeline/steps/step_08_synthesis.py").read_text(encoding="utf-8")
    assert "response = None" in src
    assert "usage: dict[str, Any] = {}" in src or "usage: dict[" in src
    # cost_tracker comes from context before the try that may fail
    assert 'cost_tracker: Any = context.get("cost_tracker")' in src


@pytest.mark.asyncio
async def test_synthesis_provider_fail_sync_fallback_no_unboundlocal() -> None:
    from src.agents.pipeline.steps.step_08_synthesis import SynthesisStep
    from src.c4.state import C4State

    step = SynthesisStep()
    tracker = MagicMock()
    router = MagicMock()
    router.generate = AsyncMock(side_effect=RuntimeError("provider down"))

    long_solution = "word " * 450  # ≥400 words to pass length gate

    context: dict[str, Any] = {
        "problem": "test problem for synthesis honesty",
        "c4_state": C4State(0, 0, 0),
        "plugin_results": [],
        "gap_results": [],
        "quality_gate_results": {"all_passed": True},
        "perspectives": [],
        "provider_router": router,
        "cost_tracker": tracker,
        "sources": [],
        "max_tokens": 500,
    }

    with (
        patch("src.llm.get_gateway") as mock_gw,
        patch("src.agents.pipeline.steps.step_08_synthesis.CitationVerifier") as mock_cv,
        patch("src.agents.pipeline.steps.step_08_synthesis.NoveltyScorer") as mock_ns,
    ):
        mock_gw.return_value.generate_sync.return_value = long_solution
        mock_cv.return_value.verify = AsyncMock(return_value=[])
        mock_cv.return_value.close = AsyncMock()
        mock_ns.return_value.score.side_effect = RuntimeError("no ST")
        mock_ns.return_value.flag.return_value = "NOVELTY_UNCHECKED"

        result = await step.execute(context)

    assert result.status == "completed"
    assert result.output_data.get("novelty", {}).get("score") is None
    assert result.output_data.get("novelty", {}).get("flag") == "NOVELTY_UNCHECKED"
    # cost_tracker.track_request should be callable without UnboundLocal
    tracker.track_request.assert_called()


@pytest.mark.asyncio
async def test_synthesis_empty_solution_marks_failed() -> None:
    from src.agents.pipeline.steps.step_08_synthesis import SynthesisStep
    from src.c4.state import C4State

    step = SynthesisStep()
    router = MagicMock()
    router.generate = AsyncMock(side_effect=RuntimeError("down"))

    context: dict[str, Any] = {
        "problem": "empty synth test",
        "c4_state": C4State(0, 0, 0),
        "plugin_results": [],
        "gap_results": [],
        "quality_gate_results": {},
        "perspectives": [],
        "provider_router": router,
        "cost_tracker": None,
        "sources": [],
    }

    with patch("src.llm.get_gateway") as mock_gw:
        mock_gw.return_value.generate_sync.return_value = ""
        result = await step.execute(context)

    assert result.status == "failed"
    assert result.output_data.get("solution") == ""


# ─── F11: retry _model_for_provider uses per-provider defaults ────────────────


def test_retry_model_for_provider_never_passes_foreign_org_model() -> None:
    primary = LLMProvider.OPENROUTER
    foreign = "anthropic/claude-sonnet-4.6"
    # Non-OpenRouter fallback must get that provider's default, not org/model string
    for provider in (
        LLMProvider.XAI,
        LLMProvider.MISTRAL,
        LLMProvider.DEEPSEEK,
        LLMProvider.MOONSHOT,
    ):
        model = ProviderRetryManager._model_for_provider(provider, primary, foreign)
        assert (
            "/" not in model
            or model == get_default_model(provider)
            or model.startswith(provider.value) is False
        )
        assert model == get_default_model(provider)
        assert model != foreign


def test_retry_model_for_provider_keeps_primary_model() -> None:
    primary = LLMProvider.OPENROUTER
    stage = "qwen/qwen-2.5-72b-instruct"
    assert ProviderRetryManager._model_for_provider(primary, primary, stage) == stage


# ─── F12: unchecked novelty null ─────────────────────────────────────────────


def test_novelty_validator_unchecked_returns_null() -> None:
    src = Path("src/discovery/novelty_validator.py").read_text(encoding="utf-8")
    assert 'return {"semantic_novelty": None}' in src
    assert 'result.get("novelty_score", 0.5)' not in src


def test_step_08_default_novelty_is_null_not_half() -> None:
    src = Path("src/agents/pipeline/steps/step_08_synthesis.py").read_text(encoding="utf-8")
    assert "novelty_score: float | None = None" in src
    assert "novelty_score = 0.5" not in src


# ─── F7: secrets_store ship lock ─────────────────────────────────────────────


def test_secrets_store_gitignore_allowlisted_and_tracked() -> None:
    gi = Path(".gitignore").read_text(encoding="utf-8")
    assert "!src/config/secrets_store.py" in gi
    path = Path("src/config/secrets_store.py")
    assert path.is_file()
    # Importable product module
    from src.config import secrets_store

    assert hasattr(secrets_store, "set_secret") or hasattr(secrets_store, "list_key_status")


# ─── F8: Windows TUI binary names ────────────────────────────────────────────


def test_tui_binary_names_prefer_exe_on_win32(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.cli import tui_binary

    monkeypatch.setattr(tui_binary.sys, "platform", "win32")
    names = tui_binary._binary_names()
    assert names[0] == "c4tui-v9.exe"


def test_find_tui_binary_checks_sibling_of_executable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.cli import tui_binary

    fake_exe = tmp_path / "python"
    fake_exe.write_text("")
    sibling = tmp_path / "c4tui-v9"
    sibling.write_text("#!/bin/sh\n")
    sibling.chmod(0o755)
    monkeypatch.setattr(tui_binary.sys, "executable", str(fake_exe))
    monkeypatch.setattr(tui_binary.sys, "platform", "linux")
    monkeypatch.setattr(tui_binary, "_package_bin_dir", lambda: tmp_path / "missing")
    monkeypatch.setattr(tui_binary, "_repo_root", lambda: tmp_path / "repo")
    monkeypatch.setattr(tui_binary, "_cache_bin_dir", lambda: tmp_path / "cache")
    monkeypatch.setattr(tui_binary.shutil, "which", lambda _n: None)
    found = tui_binary.find_tui_v9_binary()
    assert found == sibling


def test_gitlab_ci_prod_publish_no_prepare_or_true() -> None:
    ci = Path(".gitlab-ci.yml").read_text(encoding="utf-8")
    start = ci.index("pypi-publish-prod:")
    # next top-level job or EOF
    rest = ci[start + 1 :]
    next_job = rest.find("\n\n")
    block = ci[start : start + 1 + next_job] if next_job > 0 else ci[start:]
    # Command must not swallow prepare failure
    assert "prepare_tui_wheel.sh || true" not in block
    assert "C4REQBER_TUI_WHEEL_STRICT=1" in block
    assert "test -f src/tui/v9/bin/c4tui-v9" in block


# ─── F9: package_manager uses sys.executable -m pip ───────────────────────────


def test_package_manager_install_argv_is_python_m_pip() -> None:
    from src.cli import package_manager

    src = inspect.getsource(package_manager._install_direct)
    assert '[sys.executable, "-m", "pip", "install"' in src or (
        "sys.executable" in src and '"-m"' in src and '"pip"' in src
    )
    assert "pip pip" not in src


def test_package_manager_install_direct_cmd_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.cli import package_manager

    pkg = MagicMock()
    pkg.pip_name = "numpy"
    pkg.name = "NumPy"
    captured: list[list[str]] = []

    def fake_run(cmd: list[str], **_kwargs: Any) -> MagicMock:
        captured.append(list(cmd))
        m = MagicMock()
        m.returncode = 0
        m.stderr = ""
        m.stdout = ""
        return m

    monkeypatch.setattr(package_manager.subprocess, "run", fake_run)
    monkeypatch.setattr(package_manager.sys, "platform", "darwin")
    ok, msg = package_manager._install_direct(pkg)
    assert ok
    assert captured
    assert captured[0][:4] == [sys.executable, "-m", "pip", "install"]


# ─── F10: blast config --health ───────────────────────────────────────────────


def test_config_health_prints_lines(capsys: pytest.CaptureFixture[str]) -> None:
    from src.cli.config_keys import handle_keys_command

    with patch(
        "src.cli.config_keys.list_key_status",
        return_value=[
            {
                "env_name": "OPENROUTER_API_KEY",
                "configured": True,
                "required": True,
                "category": "llm",
            },
        ],
    ):
        try:
            handle_keys_command(health=True)
        except SystemExit as exc:
            # exit 0 or missing other required keys — either way stdout must have content
            assert exc.code in (0, 1, None)

    out = capsys.readouterr().out
    assert "Key health" in out or "OPENROUTER" in out
    assert len(out.strip()) > 0


# ─── F15: newton paths + win32 verifier honest skip ───────────────────────────


def test_newton_bridge_candidates_include_windows_scripts() -> None:
    src = Path("src/simulations/newton_bridge.py").read_text(encoding="utf-8")
    assert (
        'Scripts", "python.exe"' in src
        or "Scripts/python.exe" in src
        or 'Scripts", "python.exe"' in src
    )
    assert "bin" in src and "python" in src


def test_install_verifiers_win32_honest_skip() -> None:
    from src.cli import blast_app

    src = inspect.getsource(blast_app._install_verifiers)
    assert 'sys.platform == "win32"' in src
    assert "skipped on Windows" in src or "skip" in src.lower()
    # Must return before painting green success on win32
    tree = ast.parse(src)
    assert any(isinstance(n, ast.Return) for n in ast.walk(tree))
