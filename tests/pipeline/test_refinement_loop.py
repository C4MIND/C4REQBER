"""Tests for the refinement loop control flow in one_click_discovery pipeline.

Tests the decision logic inline in src/api/v8_routers/discovery/pipeline.py lines ~1037-1154.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def thresholds():
    return {
        "min_papers_for_discovery": 5,
        "min_papers_for_paradigm_shift": 20,
        "min_gap_miner_potential": 0.15,
        "min_novelty_score": 0.5,
        "min_contradictions_found": 3,
        "require_already_shifted_check": True,
        "require_self_critique": True,
    }


@pytest.fixture
def base_results():
    return {
        "problem": "test problem",
        "domain": "test",
        "hypothesis": {"text": "A test hypothesis about novel mechanism"},
        "novelty": {"status": "checked"},
        "competing_hypotheses": [],
        "proof": {},
    }


def simulate_loop_body(
    *,
    hypothesis_text: str,
    papers_found: int,
    gap_potential: float,
    thresholds: dict,
    already_shifted: bool = False,
    refined_no_improvement: bool = False,
    recheck_shifted: bool | None = None,
    iteration: int = 1,
    max_iterations: int = 3,
    abort_reasons: list[str] | None = None,
    refinement_history: list[dict] | None = None,
    papers: list[dict] | None = None,
) -> dict:
    """Isolated simulation of one refinement loop body iteration.

    Replicates the control flow from pipeline.py lines 1043-1146 without
    importing external modules (LLM, GapMiner, MultiSourceSearcher, etc.).
    """
    if abort_reasons is None:
        abort_reasons = []
    if refinement_history is None:
        refinement_history = []
    if papers is None:
        papers = [{"title": f"Paper {i}", "abstract": f"Abstract {i}"} for i in range(30)]

    refinement_history.append(
        {
            "iteration": iteration,
            "hypothesis": hypothesis_text[:300],
            "abort_reasons": list(abort_reasons),
            "gap_miner_score": gap_potential,
            "papers_found": papers_found,
        }
    )

    if refined_no_improvement:
        return {
            "break": True,
            "reason": "no_improvement",
            "abort_reasons": abort_reasons,
            "refinement_history": refinement_history,
        }

    if recheck_shifted is True:
        abort_reasons[:] = [
            f"ALREADY_SHIFTED(iter{iteration}): ALREADY_SHIFTED. Seminal: []. Consensus: 0.85."
        ]
        return {
            "break": True,
            "reason": "already_shifted",
            "abort_reasons": abort_reasons,
            "refinement_history": refinement_history,
        }

    if recheck_shifted is False:
        abort_reasons = [r for r in abort_reasons if "ALREADY_SHIFTED" not in r]

    if gap_potential < thresholds["min_gap_miner_potential"]:
        reason = (
            f"LOW_DISCOVERY_POTENTIAL(iter{iteration}): GapMiner score = "
            f"{gap_potential:.2f} (minimum {thresholds['min_gap_miner_potential']})."
        )
        if not any("LOW_DISCOVERY_POTENTIAL" in r for r in abort_reasons):
            abort_reasons.append(reason)

    if papers_found < thresholds["min_papers_for_discovery"]:
        reason = f"INSUFFICIENT_DATA(iter{iteration}): Found only {papers_found} papers."
        if not any("INSUFFICIENT_DATA" in r for r in abort_reasons):
            abort_reasons.append(reason)

    return {
        "abort_reasons": abort_reasons,
        "refinement_history": refinement_history,
        "should_continue": bool(abort_reasons) and iteration < max_iterations,
        "break": False,
    }


class TestRefinementLoop:
    """Tests for the refinement loop control flow in one_click_discovery."""

    def test_refinement_breaks_on_already_shifted(self, thresholds):
        """Loop exits when AlreadyShiftedDetector returns shifted."""
        result = simulate_loop_body(
            hypothesis_text="test hypothesis",
            papers_found=100,
            gap_potential=0.5,
            thresholds=thresholds,
            recheck_shifted=True,
            abort_reasons=["LOW_NOVELTY: some reason"],
        )
        assert result["break"] is True
        assert result["reason"] == "already_shifted"
        assert any("ALREADY_SHIFTED" in r for r in result["abort_reasons"])

    def test_refinement_breaks_on_already_shifted_no_prior_reasons(self, thresholds):
        """AlreadyShifted fires even when there were no prior abort reasons."""
        result = simulate_loop_body(
            hypothesis_text="test hypothesis",
            papers_found=100,
            gap_potential=0.5,
            thresholds=thresholds,
            recheck_shifted=True,
            abort_reasons=[],
        )
        assert result["break"] is True
        assert result["reason"] == "already_shifted"

    def test_refinement_abort_on_low_potential(self, thresholds):
        """Low gap_miner score below threshold triggers LOW_DISCOVERY_POTENTIAL abort."""
        result = simulate_loop_body(
            hypothesis_text="test hypothesis",
            papers_found=100,
            gap_potential=0.05,
            thresholds=thresholds,
            abort_reasons=["SELF_CRITIQUE_REJECT: needs work"],
        )
        assert any("LOW_DISCOVERY_POTENTIAL" in r for r in result["abort_reasons"])

    def test_refinement_abort_on_insufficient_data(self, thresholds):
        """Too few papers triggers INSUFFICIENT_DATA abort."""
        result = simulate_loop_body(
            hypothesis_text="test hypothesis",
            papers_found=2,
            gap_potential=0.5,
            thresholds=thresholds,
            abort_reasons=["SELF_CRITIQUE_REJECT: needs work"],
        )
        assert any("INSUFFICIENT_DATA" in r for r in result["abort_reasons"])

    def test_refinement_no_abort_with_good_scores(self, thresholds):
        """High scores do not add new abort reasons."""
        result = simulate_loop_body(
            hypothesis_text="test hypothesis",
            papers_found=100,
            gap_potential=0.8,
            thresholds=thresholds,
            recheck_shifted=False,
            abort_reasons=["SELF_CRITIQUE_REJECT: existing reason that keeps loop alive"],
        )
        assert not any("LOW_DISCOVERY_POTENTIAL" in r for r in result["abort_reasons"])
        assert not any("INSUFFICIENT_DATA" in r for r in result["abort_reasons"])

    def test_refinement_accumulates_history(self, thresholds):
        """refinement_history grows with each iteration."""
        history: list[dict] = []
        abort_reasons = ["LOW_NOVELTY: initial"]

        for i in range(1, 4):
            result = simulate_loop_body(
                hypothesis_text=f"hypothesis v{i}",
                papers_found=100,
                gap_potential=0.5,
                thresholds=thresholds,
                abort_reasons=abort_reasons,
                refinement_history=history,
                iteration=i,
            )
            history = result["refinement_history"]
            abort_reasons = result["abort_reasons"]

        assert len(history) == 3
        assert history[0]["iteration"] == 1
        assert history[1]["iteration"] == 2
        assert history[2]["iteration"] == 3
        assert history[0]["hypothesis"] == "hypothesis v1"[:300]
        assert history[1]["hypothesis"] == "hypothesis v2"[:300]
        assert history[2]["hypothesis"] == "hypothesis v3"[:300]

    def test_refinement_max_iterations(self, thresholds):
        """Loop does not exceed max_iterations=3."""
        history: list[dict] = []
        abort_reasons = ["LOW_NOVELTY: initial"]
        iterations_run = 0

        for i in range(1, 5):
            result = simulate_loop_body(
                hypothesis_text=f"hypothesis v{i}",
                papers_found=100,
                gap_potential=0.5,
                thresholds=thresholds,
                abort_reasons=abort_reasons,
                refinement_history=history,
                iteration=i,
                max_iterations=3,
            )
            iterations_run += 1
            history = result["refinement_history"]
            abort_reasons = result["abort_reasons"]
            if not result.get("should_continue"):
                break

        assert iterations_run <= 3

    def test_refinement_no_improvement_breaks(self, thresholds):
        """When refined result has no_improvement=True, loop breaks."""
        result = simulate_loop_body(
            hypothesis_text="stuck hypothesis",
            papers_found=100,
            gap_potential=0.5,
            thresholds=thresholds,
            refined_no_improvement=True,
            abort_reasons=["LOW_NOVELTY: some reason"],
        )
        assert result["break"] is True
        assert result["reason"] == "no_improvement"

    def test_refinement_clears_already_shifted_when_not_shifted(self, thresholds):
        """When recheck shows NOT shifted, ALREADY_SHIFTED is removed from reasons."""
        result = simulate_loop_body(
            hypothesis_text="test hypothesis",
            papers_found=100,
            gap_potential=0.5,
            thresholds=thresholds,
            recheck_shifted=False,
            abort_reasons=[
                "ALREADY_SHIFTED: previous false positive",
                "SELF_CRITIQUE_REJECT: needs work",
            ],
        )
        assert not any("ALREADY_SHIFTED" in r for r in result["abort_reasons"])
        assert any("SELF_CRITIQUE_REJECT" in r for r in result["abort_reasons"])

    def test_refinement_noop_with_empty_abort_reasons(self, thresholds):
        """When abort_reasons is empty, should_continue is False."""
        result = simulate_loop_body(
            hypothesis_text="test hypothesis",
            papers_found=100,
            gap_potential=0.8,
            thresholds=thresholds,
            abort_reasons=[],
        )
        assert result.get("should_continue") is False

    def test_refinement_loop_does_not_duplicate_abort_reasons(self, thresholds):
        """Same abort reason type is not duplicated across iterations."""
        abort_reasons = ["SELF_CRITIQUE_REJECT: initial"]
        result1 = simulate_loop_body(
            hypothesis_text="h1",
            papers_found=2,
            gap_potential=0.05,
            thresholds=thresholds,
            abort_reasons=list(abort_reasons),
            iteration=1,
        )
        low_potential_count = sum(
            1 for r in result1["abort_reasons"] if "LOW_DISCOVERY_POTENTIAL" in r
        )
        assert low_potential_count == 1

        result2 = simulate_loop_body(
            hypothesis_text="h2",
            papers_found=2,
            gap_potential=0.05,
            thresholds=thresholds,
            abort_reasons=list(result1["abort_reasons"]),
            iteration=2,
        )
        low_potential_count2 = sum(
            1 for r in result2["abort_reasons"] if "LOW_DISCOVERY_POTENTIAL" in r
        )
        assert low_potential_count2 == 1
