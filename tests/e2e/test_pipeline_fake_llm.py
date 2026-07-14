"""End-to-end coverage for the LLM-driven UniversalSolvePipeline.

The rest of the suite covers units and the no-LLM solve path; the full
LLM-enhanced pipeline (turbo/deep-work/full modes that call the provider
router) had NO automated coverage — the only e2e file (test_pipeline_e2e.py)
is a manual print-script with no asserts that needs a real API key.

This test injects a deterministic FAKE provider router (no network) and runs
the whole pipeline in an LLM-using mode, asserting it streams to completion,
actually exercises the LLM path, and returns a structured result. Scope is
*orchestration wiring*, not LLM output quality.

It runs in a FRESH subprocess on purpose: in-process, after the full suite,
sys.modules is polluted by other tests (something clobbers the
``src.agents.pipeline`` namespace), so the pipeline's lazy
``from src.agents.pipeline.executor import PipelineExecutor`` fails with
"'src.agents.pipeline' is not a package". A clean interpreter sees the real
state. (The app itself is fine — a live `blast solve` and this test run
standalone both work; the breakage is purely test-ordering global state.)
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

import pytest


# Opt-in only. This runs the full 10-step pipeline in a subprocess (~40s
# locally, and slower on constrained CI runners — enough to blow the default
# 120s per-test timeout). CI runs `pytest tests/` with no marker filter, so a
# @slow/@e2e marker alone wouldn't keep it out; gate it on an env flag instead.
# The pipeline's import/wiring is already covered in CI by the unit suite and
# the import guard — this e2e adds local confidence in the LLM-driven run.
# Run it with:  RUN_PIPELINE_E2E=1 pytest tests/e2e/test_pipeline_fake_llm.py
pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_PIPELINE_E2E"),
    reason="opt-in heavy pipeline e2e; set RUN_PIPELINE_E2E=1 to run",
)

_REPO = pathlib.Path(__file__).resolve().parent.parent.parent

# Runs in a clean interpreter. argv: <repo_root> <out_json>.
_RUN = r"""
import asyncio, json, pathlib, sys
repo = pathlib.Path(sys.argv[1]); out = pathlib.Path(sys.argv[2])
sys.path.insert(0, str(repo / "src")); sys.path.insert(0, str(repo))

from src.agents.pipeline import UniversalSolvePipeline


class _Resp:
    def __init__(self, content): self.content = content; self.usage = {"prompt_tokens": 1, "completion_tokens": 1}

class FakeProviderRouter:
    def __init__(self): self.calls = []
    async def generate(self, stage_name, prompt, system_prompt=None, use_retry=True):
        self.calls.append(stage_name)
        return _Resp(f"[fake-llm:{stage_name}] Deterministic stub.\n\n## Conclusion\nStubbed.\n")
    async def generate_batch(self, stage_name, prompts):
        self.calls.append(stage_name)
        return [_Resp(f"[fake-llm:{stage_name}] perspective {i}") for i, _ in enumerate(prompts)]
    async def close_all(self): return None


async def run():
    fake = FakeProviderRouter()
    pipeline = UniversalSolvePipeline(provider_router=fake)
    pipeline.set_pattern("thermal")
    completed = False; result_keys = []; n_events = 0
    try:
        async for ev in pipeline.solve_streaming(
            "How to reduce energy consumption in data centers", mode="turbo"
        ):
            n_events += 1
            if ev.get("event") == "complete":
                completed = True
                r = ev.get("result")
                r = r.to_dict() if hasattr(r, "to_dict") else r
                if isinstance(r, dict): result_keys = sorted(r.keys())
    finally:
        await pipeline.close()
    return {"completed": completed, "n_events": n_events,
            "llm_calls": fake.calls, "result_keys": result_keys}

out.write_text(json.dumps(asyncio.run(run())))
"""


@pytest.mark.slow  # full 10-step pipeline run, ~40s — skipped by `-m "not slow"`
def test_pipeline_streams_to_completion_with_fake_llm(tmp_path):
    out = tmp_path / "result.json"
    proc = subprocess.run(
        [sys.executable, "-c", _RUN, str(_REPO), str(out)],
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert out.exists(), (
        f"pipeline subprocess produced no result (rc={proc.returncode}):\n"
        f"stderr:\n{proc.stderr[-2500:]}"
    )
    res = json.loads(out.read_text())

    # 1. Streamed events and reached completion.
    assert res["n_events"] > 0, "pipeline yielded no events"
    assert res["completed"], (
        f"pipeline never reached a 'complete' event; stderr:\n{proc.stderr[-1500:]}"
    )
    # 2. The LLM path was actually exercised (turbo routes synthesis/perspectives
    #    through the injected provider router).
    assert res["llm_calls"], "the fake LLM was never called — LLM-dependent steps did not run"
    # 3. A structured final result came back.
    assert "final_solution" in res["result_keys"] or "confidence" in res["result_keys"], (
        f"final result missing expected keys; got: {res['result_keys'][:12]}"
    )


# NOTE: we intentionally do NOT assert that every LLM-driven step *succeeds*.
# A generic fake returns plain text while some steps (e.g. mp_rotation) expect
# step-specific JSON and degrade gracefully when it isn't — by design. Pinning
# the fake to each step's bespoke schema would make this brittle and is out of
# scope. Also note: step_03_c4_fingerprint uses its own global LLM classifier
# (src.c4_analysis.llm_classifier), not the injected router; it fails safe.
