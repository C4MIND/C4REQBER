"""W3: Dempster-Shafer must fuse papers, not ignore them."""

from __future__ import annotations

import os

import pytest

from src.discovery.dempster_literature import fuse_dempster_from_papers
from src.discovery.pipeline_logic import run_dempster_shafer


def test_dempster_uses_papers_not_ignored():
    hyp = {"text": "continual learning catastrophic forgetting"}
    papers = [
        {
            "title": "Evidence for continual learning methods that improve retention",
            "abstract": "We demonstrate and support improved memory retention under continual learning.",
        },
        {
            "title": "A study that contradicts simple replay",
            "abstract": "Results refute naive replay and show inconsistent performance.",
        },
    ]
    out = fuse_dempster_from_papers(hyp, papers)
    assert out["papers_used"] == 2
    assert "papers_ignored" not in out
    assert "paper" in out["note"].lower()
    assert 0.0 <= out["belief_supported"] <= 1.0
    # Prefer NLI when transformers+model available; else keyword heuristic.
    if out.get("method") == "nli_dempster":
        assert out["heuristic"] is False
    else:
        assert out["heuristic"] is True
        assert out.get("method") == "keyword_overlap_dempster"


def test_dempster_pipeline_wrapper_uses_literature():
    out = run_dempster_shafer(
        {"text": "protein folding stability"},
        [
            {
                "title": "Confirming stability in folded proteins",
                "abstract": "Experiments support and validate the stability hypothesis.",
            }
        ],
    )
    assert out.get("papers_used", 0) >= 1
    if out.get("method") == "nli_dempster":
        assert out.get("heuristic") is False
    else:
        assert out.get("heuristic") is True


def test_dempster_keyword_path_when_nli_disabled(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("C4_DEMPSTER_NLI", "0")
    out = fuse_dempster_from_papers(
        {"text": "continual learning catastrophic forgetting"},
        [
            {
                "title": "Evidence for continual learning methods that improve retention",
                "abstract": "We demonstrate and support improved memory retention.",
            }
        ],
    )
    assert out["papers_used"] == 1
    assert out["heuristic"] is True
    assert out.get("method") == "keyword_overlap_dempster"


def test_dempster_no_papers_is_explicit_fallback():
    out = fuse_dempster_from_papers({"text": "novel improve synergy"}, [])
    assert out["papers_used"] == 0
    assert out["heuristic"] is True
