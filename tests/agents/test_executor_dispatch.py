"""Fast characterization net for PipelineExecutor's step DISPATCH (P2-B step 0).

This pins the executor's *orchestration* behavior — the exact ordered event
stream, the mode branches (turbo skips validation), the early-exit, the
interleaved plugin/pattern steps, the deep-work extra steps, and the
``on_complete`` side-effects on the result — INDEPENDENT of what each step
computes. Every step is replaced with a deterministic recording stub, so this
runs in milliseconds (no ImpactEngine, embeddings, network, or subprocess) and
can run on every commit, unlike the opt-in ~49s e2e (tests/e2e/test_pipeline_fake_llm.py).

It is the equivalence gate for P2-B: the upcoming switch from the
free-fn + importlib + STEP_PLAN dispatch to a direct PipelineStep registry must
keep this green byte-for-byte. The expected stage sequences are hard-coded
(not derived from STEP_PLAN) on purpose — STEP_PLAN itself goes away in P2-B, so
the net must outlive it.

Injection seam: ``executor._get_step_fn`` (pre-P2-B). When P2-B replaces the
dispatch, repoint the stub here to the new seam; the ASSERTIONS stay fixed.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.agents.pipeline import executor as ex_mod
from src.agents.pipeline.steps.base import PipelineStage, PipelineStepResult
from src.agents.solve_pipeline import SolvePipelineResult
from src.c4.state import C4State


# ── canned per-step outputs the on_complete callbacks read ─────────────────
_CANNED_OUTPUT: dict[str, dict] = {
    "step_prior_art": {"recommendation": "REC", "merged_sources": [], "sources": []},
    "step_synthesis": {"solution": "SOL", "confidence": 0.8},
    "step_mp_rotation": {"perspectives": []},
    "step_qzrf_select": {"operators": ["op-a", "op-b"]},
    "step_isomorphism_search": {"found": True},
    "step_validation": {"needs_revision": False},
}
# fn name -> PipelineStage, taken from the live plan (the result object the stub
# returns must carry the right stage; some on_complete callbacks check it).
_NAME_STAGE: dict[str, PipelineStage] = {sd["fn"]: sd["stage"] for sd in ex_mod.STEP_PLAN}


class _FakePath:
    operators: list = []


class _FakeC4Space:
    def shortest_path(self, a, b):  # noqa: ANN001
        return _FakePath()


def _make_fake_pipeline() -> SimpleNamespace:
    """A pipeline stand-in exposing only what executor + build_args touch."""
    p = SimpleNamespace()
    # collaborators referenced by STEP_PLAN build_args — values are inert
    # sentinels because the steps themselves are stubbed out.
    for attr in (
        "impact", "prior_art", "multi_searcher", "gap_analyzer", "quality_gates",
        "mp_rotation", "mp_llm_generator", "provider_router", "qzrf",
        "transformer", "memory",
    ):
        setattr(p, attr, object())
    p._cost_tracker = None
    p._prior_art_confidence = 0.0
    p._selected_plugins = []
    p._selected_pattern = None
    p.observer = None  # keep observer O₀→O₂ branches out of the core net
    p.c4_space = _FakeC4Space()

    def _create_result(problem: str, mode: str) -> SolvePipelineResult:
        res = SolvePipelineResult(problem=problem, mode=mode)
        p._last_result = res
        return res

    p._create_result = _create_result
    return p


def _install_step_stubs(monkeypatch, recorder: list[str], *, prior_art_conf: float = 0.3) -> None:
    """Replace executor._get_step_fn with a recording stub factory."""

    async def _stub(name: str, *args, **kwargs):  # noqa: ANN002, ANN003
        recorder.append(name)
        if name == "step_prior_art":  # unwrap_tuple step → (result, extra)
            res = PipelineStepResult(
                stage=PipelineStage.PRIOR_ART, status="completed",
                output_data=_CANNED_OUTPUT["step_prior_art"],
            )
            return res, prior_art_conf
        if name == "step_plugins":  # special inline branch → (results, status)
            return [{"plugin": "p1", "ok": True}], "completed"
        if name == "step_simulation":  # special post-loop branch → (results, status)
            return [], "completed"
        return PipelineStepResult(
            stage=_NAME_STAGE.get(name, PipelineStage.SYNTHESIS),
            status="completed",
            output_data=_CANNED_OUTPUT.get(name, {}),
        )

    def _fake_get_step_fn(name: str):
        async def _bound(*args, **kwargs):  # noqa: ANN002, ANN003
            return await _stub(name, *args, **kwargs)
        return _bound

    monkeypatch.setattr(ex_mod, "_get_step_fn", _fake_get_step_fn)


async def _drive(pipeline, mode: str) -> list[dict]:
    executor = ex_mod.PipelineExecutor(pipeline, mode=mode)
    return [ev async for ev in executor.execute("PROBLEM", mode=mode)]


def _completed_stages(events: list[dict]) -> list[str]:
    return [e["stage"] for e in events if e.get("event") == "step_complete"]


# expected step_complete stage order (LITERAL — must outlive STEP_PLAN's deletion)
_FULL_ORDER = [
    "impact_identify", "prior_art", "gap_analysis", "quality_gate", "reality_check",
    "c4_fingerprint", "cross_domain_transfer", "mp_rotation", "qzrf_select",
    "isomorphism_search", "synthesis", "validation",
]
_TURBO_ORDER = [s for s in _FULL_ORDER if s != "validation"]  # turbo skips s9


@pytest.mark.asyncio
async def test_autopilot_runs_full_stage_sequence(monkeypatch):
    rec: list[str] = []
    _install_step_stubs(monkeypatch, rec)
    p = _make_fake_pipeline()
    events = await _drive(p, "autopilot")

    assert events[0]["event"] == "start"
    assert events[-1]["event"] == "complete"
    assert _completed_stages(events) == _FULL_ORDER
    # synthesis on_complete (_on_s8) wired solution + confidence onto the result
    assert p._last_result.final_solution == "SOL"
    assert p._last_result.confidence == 0.8


@pytest.mark.asyncio
async def test_turbo_skips_validation(monkeypatch):
    rec: list[str] = []
    _install_step_stubs(monkeypatch, rec)
    events = await _drive(_make_fake_pipeline(), "turbo")
    assert _completed_stages(events) == _TURBO_ORDER
    assert "step_validation" not in rec  # s9 free-fn never resolved/called


@pytest.mark.asyncio
async def test_on_complete_side_effects_populate_result(monkeypatch):
    _install_step_stubs(monkeypatch, [])
    p = _make_fake_pipeline()
    await _drive(p, "autopilot")
    r = p._last_result
    assert r.qzrf_recommendations == ["op-a", "op-b"]   # _on_s5
    assert r.isomorphism_found is True                   # _on_s6
    assert r.prior_art_summary == "REC"                  # _on_s2
    assert r.mp_perspectives == []                       # _on_s4
    assert r.c4_path == []                               # finalize via c4_space


@pytest.mark.asyncio
async def test_high_confidence_prior_art_early_exits(monkeypatch):
    rec: list[str] = []
    _install_step_stubs(monkeypatch, rec, prior_art_conf=0.95)
    p = _make_fake_pipeline()
    events = await _drive(p, "autopilot")

    # stops right after reality_check (s2d); synthesis/validation never run
    assert _completed_stages(events) == [
        "impact_identify", "prior_art", "gap_analysis", "quality_gate", "reality_check",
    ]
    assert events[-1]["event"] == "complete"
    assert "step_synthesis" not in rec
    assert "High-confidence prior art" in p._last_result.final_solution
    assert p._last_result.confidence == 0.95


@pytest.mark.asyncio
async def test_selected_plugins_interleave_before_synthesis(monkeypatch):
    rec: list[str] = []
    _install_step_stubs(monkeypatch, rec)
    p = _make_fake_pipeline()
    p._selected_plugins = ["plugin-x"]
    events = await _drive(p, "autopilot")

    stages = [e.get("stage") for e in events]
    # plugin_execution fires after isomorphism_search, before synthesis
    assert "plugin_execution" in stages
    assert stages.index("plugin_execution") < stages.index("synthesis")
    assert "step_plugins" in rec


@pytest.mark.asyncio
async def test_selected_pattern_runs_simulation_after_loop(monkeypatch):
    rec: list[str] = []
    _install_step_stubs(monkeypatch, rec)
    p = _make_fake_pipeline()
    p._selected_pattern = "thermal"
    events = await _drive(p, "autopilot")

    stages = [e.get("stage") for e in events]
    assert "pattern_simulation" in stages
    assert stages.index("pattern_simulation") > stages.index("synthesis")
    assert "step_simulation" in rec


@pytest.mark.asyncio
async def test_deep_work_adds_formal_verification_and_theorem_export(monkeypatch):
    rec: list[str] = []
    _install_step_stubs(monkeypatch, rec)

    # deep-work calls the real LLMProver — stub it to keep this fast & offline.
    class _FakeProof:
        proof = "theorem stub"

    class _FakeProver:
        async def prove(self, *a, **k):  # noqa: ANN002, ANN003
            return _FakeProof()

    import src.verification.llm_prover as prover_mod
    monkeypatch.setattr(prover_mod, "LLMProver", _FakeProver)

    events = await _drive(_make_fake_pipeline(), "deep-work")
    stages = [e.get("stage") for e in events]
    assert "validation" in stages                 # deep-work does NOT skip s9
    assert "formal_verification" in stages
    assert "theorem_export" in stages
    assert stages.index("formal_verification") > stages.index("synthesis")
