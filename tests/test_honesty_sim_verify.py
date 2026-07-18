"""Honesty regression tests for simulation / verification / autoscanner."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.pipeline.config import PipelineConfig
from src.pipeline.quality import QualityGates
from src.simulations.base_adapter import BaseSimulationAdapter, SimStatus
from src.theorem.prover import ProofStatus, ProverBackend, TheoremProver


class _StubAdapter(BaseSimulationAdapter):
    _engine_name = "stub_test"
    _package_checks: list[str] = []
    _install_hint = "n/a"

    def is_available(self) -> bool:
        return True

    def run(self, input_data=None):
        def _run(_data):
            return {"status": "unavailable", "stub": True, "note": "no work"}

        return self._run_wrapped(_run, input_data)


def test_run_wrapped_stub_is_not_success():
    result = _StubAdapter().run({})
    assert result.status == SimStatus.UNAVAILABLE
    assert result.data.get("stub") is True


def test_verification_skipped_not_pass_when_required():
    cfg = PipelineConfig()
    cfg.require_verification = True
    gates = QualityGates(config=cfg)
    out = gates.check_verification({"status": "skipped", "backend": "none"})
    assert out.passed is False
    assert out.score < 1.0


def test_verification_skipped_soft_when_optional():
    cfg = PipelineConfig()
    cfg.require_verification = False
    gates = QualityGates(config=cfg)
    out = gates.check_verification({"status": "skipped", "backend": "none"})
    assert out.score < 1.0


@pytest.mark.asyncio
async def test_theorem_simulation_never_proved():
    prover = TheoremProver(backend=ProverBackend.SIMULATION)
    th = await prover.formalize_hypothesis("h1", "If A then B", domain="math")
    assert th.status != ProofStatus.PROVED
    out = await prover.attempt_proof(th.id)
    assert out.status != ProofStatus.PROVED
    assert out.status == ProofStatus.TIMEOUT
    assert "refuses fake" in (out.error_message or "").lower()


@pytest.mark.asyncio
async def test_autoscanner_from_papers_not_demo():
    from src.discovery.autoscanner import AutoScanner

    papers = [
        {
            "title": "An open problem in continual learning",
            "abstract": "Catastrophic forgetting remains an open problem for neural nets.",
            "year": 2024,
        }
    ]
    cands = await AutoScanner().scan_from_papers(papers)
    assert all(c.get("demo") is False for c in cands)


@pytest.mark.asyncio
async def test_run_autoscanner_pipeline_not_local_demo():
    from src.discovery.pipeline_logic import run_autoscanner

    out = await run_autoscanner([])
    assert out.get("demo") is False
    assert out.get("candidates_found", 0) == 0


@pytest.mark.asyncio
async def test_vastai_execute_refuses_simulated():
    from src.simulations.vastai_delegate import VastAIDelegate

    delegate = VastAIDelegate(api_key="test-key-not-real")
    inst = SimpleNamespace(instance_id="i-1")
    result = await delegate._execute_simulation(inst, {"engine": "newton"})
    assert result.get("status") == "unavailable"
    assert result.get("stub") is True
    assert result.get("executed") is False


@pytest.mark.asyncio
async def test_c4_simulate_propagates_stub(monkeypatch):
    from src.mcp_server import tools_analysis

    class FakeRunner:
        def run(self, pattern_id, hyp):
            return {"status": "unavailable", "stub": True, "note": "no engine"}

    monkeypatch.setattr(tools_analysis, "HAS_TOOLS", True)
    monkeypatch.setattr(
        "src.simulations.runner_v2.get_runner_v2",
        lambda: FakeRunner(),
    )
    out = await tools_analysis.c4_simulate("newtonian", {})
    assert out["status"] in {"unavailable", "error"}


def test_gromacs_without_tpr_is_unavailable():
    from src.simulations.base_adapter import SimStatus
    from src.simulations.gromacs_bridge import GromacsBridge

    bridge = GromacsBridge()
    if not bridge.is_available():
        pytest.skip("gmxapi not installed")
    result = bridge.run({})
    assert result.status == SimStatus.UNAVAILABLE
    assert result.data.get("stub") is True


def test_xarray_refuses_synthetic():
    from src.simulations.base_adapter import SimStatus
    from src.simulations.xarray_bridge import XarrayBridge

    bridge = XarrayBridge()
    if not bridge.is_available():
        pytest.skip("xarray not installed")
    result = bridge.run({})
    assert result.status == SimStatus.UNAVAILABLE
    assert result.data.get("stub") is True


def test_dempster_shafer_flagged_heuristic():
    from src.discovery.pipeline_logic import run_dempster_shafer

    out = run_dempster_shafer({"text": "novel improve synergy"}, [])
    assert out.get("heuristic") is True
    assert "error" not in out or out.get("belief_supported") is not None


def test_discovery_utils_bayesian_no_invented_samples():
    from src.api.v8_routers.discovery_utils import run_bayesian_conjugate_update

    out = run_bayesian_conjugate_update({})
    assert out.get("status") == "skipped"
    assert out.get("posterior_mean") is None


def test_z3_sat_not_verified_status():
    """Regression: hybrid verifier must not map SMT sat → verified."""
    from pathlib import Path

    src = Path("src/verification/hybrid_verifier.py").read_text(encoding="utf-8")
    z3_block = src.split('if backend == "z3":', 1)[-1].split('if backend == "cvc5":', 1)[0]
    assert 'norm_status = "verified"' not in z3_block
    assert 'norm_status = "sat"' in z3_block
