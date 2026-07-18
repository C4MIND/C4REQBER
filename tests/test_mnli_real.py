"""Real MNLI (bart-large-mnli) stance tests — requires transformers + model cache."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
VENV_PY = ROOT / ".venv" / "bin" / "python"


def _mnli_ready() -> bool:
    if not VENV_PY.is_file():
        return False
    model_dir = ROOT / ".cache" / "huggingface" / "hub" / "models--facebook--bart-large-mnli"
    if not model_dir.is_dir():
        # also accept home cache
        home = Path.home() / ".cache" / "huggingface" / "hub" / "models--facebook--bart-large-mnli"
        if not home.is_dir():
            return False
    r = subprocess.run(
        [str(VENV_PY), "-c", "import transformers"],
        capture_output=True,
        timeout=30,
    )
    return r.returncode == 0


@pytest.mark.skipif(not _mnli_ready(), reason="bart-large-mnli / transformers not ready")
def test_real_mnli_refute_and_fuse():
    env = {
        **os.environ,
        "HF_HOME": str(ROOT / ".cache" / "huggingface"),
        "C4_DEMPSTER_NLI": "1",
        "PYTHONPATH": str(ROOT),
    }
    # Prefer token file without printing it
    tok_path = Path.home() / ".cache" / "huggingface" / "token"
    if tok_path.is_file():
        env["HF_TOKEN"] = tok_path.read_text(encoding="utf-8").strip()

    script = r"""
from src.discovery.dempster_literature import paper_stance_mnli, fuse_dempster_from_papers

hyp = "continual learning improves retention"
support_paper = {
    "title": "Evidence for continual learning methods that improve retention",
    "abstract": "We demonstrate and support improved memory retention under continual learning.",
}
refute_paper = {
    "title": "Replay fails catastrophically",
    "abstract": "Results refute naive replay and contradict claims of improved retention.",
}
s1 = paper_stance_mnli(support_paper, hyp)
s2 = paper_stance_mnli(refute_paper, hyp)
assert s1 is not None and s2 is not None, (s1, s2)
assert s1["method"] == "nli_mnli"
assert s2["method"] == "nli_mnli"
# Refute paper must lean refuted
assert s2["refuted"] > s2["supported"], s2
out = fuse_dempster_from_papers(
    {"text": hyp},
    [support_paper, refute_paper],
    prefer_nli=True,
)
assert out["papers_used"] == 2
assert out["heuristic"] is False
assert out["method"] == "nli_dempster"
assert any(m == "nli_mnli" for m in out["stance_methods"])
print("MNLI_OK", out["belief_supported"], out["stance_methods"])
"""
    r = subprocess.run(
        [str(VENV_PY), "-c", script],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert r.returncode == 0, r.stderr + "\n" + r.stdout
    assert "MNLI_OK" in r.stdout
