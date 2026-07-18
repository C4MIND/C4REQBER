"""Full physics integration — Newton XPBD, Rebound N-body, Dempster NLI inject, Vast runner."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
VENV_PY = ROOT / ".venv" / "bin" / "python"


def _venv_has(mod: str) -> bool:
    if not VENV_PY.is_file():
        return False
    r = subprocess.run(
        [str(VENV_PY), "-c", f"import {mod}"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return r.returncode == 0


@pytest.mark.skipif(not _venv_has("newton"), reason="newton not in .venv")
def test_newton_runner_real_xpbd_drop():
    env = {
        **os.environ,
        "WARP_CACHE_DIR": str(ROOT / ".cache" / "warp"),
        "WARP_CACHE_PATH": str(ROOT / ".cache" / "warp"),
    }
    r = subprocess.run(
        [
            str(VENV_PY),
            str(ROOT / "src" / "simulations" / "newton_runner.py"),
            json.dumps({"type": "rigid_body", "num_steps": 40, "dt": 1 / 60, "height": 2.0}),
        ],
        capture_output=True,
        text=True,
        timeout=180,
        env=env,
        cwd=str(ROOT),
    )
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout.strip().splitlines()[-1])
    assert out["backend"] == "newton_physics"
    assert out["engine_truth"] == "newton_physics"
    assert out["executed"] is True
    assert out["stub"] is False
    assert out["status"] == "success"
    assert out["data"]["fell"] is True


@pytest.mark.skipif(not _venv_has("newton"), reason="newton not in .venv")
def test_newton_bridge_accelerate_real():
    # Ensure bridge uses .venv
    os.environ["NEWTON_PYTHON"] = str(VENV_PY)
    from src.simulations.newton_bridge import NewtonBridge

    bridge = NewtonBridge()
    assert bridge.is_available()
    result = bridge.run_simulation({"type": "rigid_body", "num_steps": 30, "dt": 1 / 60})
    assert result.status == "success"
    assert (result.data or {}).get("backend") == "newton_physics"
    assert (result.data or {}).get("fell") is True


@pytest.mark.skipif(not _venv_has("rebound"), reason="rebound not in .venv")
def test_amuse_bridge_rebound_hypothesis_bodies():
    # Import rebound into this interpreter OR run via subprocess if system py lacks it
    try:
        import rebound  # noqa: F401
    except ImportError:
        pytest.skip("rebound not importable in test interpreter")

    from src.simulations.amuse_bridge import AmuseBridge
    from src.simulations.base_adapter import SimStatus

    bridge = AmuseBridge()
    assert bridge.is_available()
    out = bridge.run(
        {
            "masses": [1.0, 3e-6],
            "positions": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
            "velocities": [[0.0, 0.0, 0.0], [0.0, 6.28, 0.0]],
            "evolve_time_yr": 0.25,
        }
    )
    assert out.status == SimStatus.SUCCESS
    assert out.data["executed"] is True
    assert out.data["hypothesis_driven"] is True
    assert out.data["backend"] in {"amuse", "rebound"}
    assert out.data["n_particles"] == 2
    assert out.data["final_separation_au"] > 0


def test_dempster_nli_injected_not_heuristic():
    from src.discovery.dempster_literature import fuse_dempster_from_papers

    def fake_llm(prompt: str) -> str:
        if "contradict" in prompt.lower() or "refute" in prompt.lower():
            return '{"label":"refuted","confidence":0.9}'
        return '{"label":"supported","confidence":0.85}'

    out = fuse_dempster_from_papers(
        {"text": "continual learning improves retention"},
        [
            {
                "title": "Evidence for continual learning",
                "abstract": "We demonstrate improved retention under continual learning.",
            },
            {
                "title": "Replay fails",
                "abstract": "Results refute naive replay and contradict simple buffers.",
            },
        ],
        prefer_nli=True,
        llm_generate=fake_llm,
    )
    assert out["papers_used"] == 2
    assert out["heuristic"] is False
    assert out["method"] == "nli_dempster"
    assert any(m.startswith("nli") for m in out["stance_methods"])


def test_vast_remote_runner_module_json(tmp_path):
    cfg = tmp_path / "c4_sim_config.json"
    cfg.write_text(
        json.dumps(
            {
                "engine": "newton",
                "type": "rigid_body",
                "num_steps": 20,
                "force_numpy_fallback": True,
                "num_particles": 8,
            }
        ),
        encoding="utf-8",
    )
    # force numpy path works without newton in system python
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "src" / "simulations" / "vast_remote_runner.py"),
            "--config",
            str(cfg),
        ],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(ROOT),
        env={**os.environ, "PYTHONPATH": str(ROOT)},
    )
    # may exit 2 if stub; parse stdout
    line = (r.stdout or "").strip().splitlines()[-1] if r.stdout.strip() else "{}"
    out = json.loads(line)
    assert "status" in out
    assert out.get("stub") is not True or out.get("status") == "unavailable"


@pytest.mark.skipif(not _venv_has("newton"), reason="newton not in .venv")
def test_vast_standalone_runner_with_venv(tmp_path):
    cfg = tmp_path / "c4_sim_config.json"
    cfg.write_text(
        json.dumps({"engine": "newton", "type": "rigid_body", "num_steps": 25, "dt": 1 / 60}),
        encoding="utf-8",
    )
    standalone = ROOT / "docker" / "vast-sim-runner" / "vast_remote_runner_standalone.py"
    env = {
        **os.environ,
        "WARP_CACHE_DIR": str(ROOT / ".cache" / "warp"),
        "PYTHONPATH": str(ROOT / "docker" / "vast-sim-runner"),
    }
    r = subprocess.run(
        [str(VENV_PY), str(standalone), "--config", str(cfg)],
        capture_output=True,
        text=True,
        timeout=180,
        env=env,
        cwd=str(ROOT / "docker" / "vast-sim-runner"),
    )
    assert r.returncode == 0, r.stderr + r.stdout
    out = json.loads(r.stdout.strip().splitlines()[-1])
    assert out["executed"] is True
    assert out["backend"] == "newton_physics"
