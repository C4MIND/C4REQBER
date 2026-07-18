"""Anti-fraud: MCP outer status must follow HONESTY_CONTRACT (provenance, not stubs)."""

from __future__ import annotations

from src.mcp_server.honesty import (
    bma_outer_status,
    causal_outer_status,
    outer_status_from_hil_like,
    outer_status_from_plugin_result,
    outer_status_from_sim_payload,
    record_field_status,
    search_outer_status,
)


def test_sim_partial_and_engine_truth_not_success():
    assert (
        outer_status_from_sim_payload(
            {"status": "partial", "engine_truth": "not_schr", "accelerated": False}
        )
        == "partial"
    )
    assert outer_status_from_sim_payload({"status": "success", "stub": True}) == "unavailable"
    assert (
        outer_status_from_sim_payload(
            {"status": "success", "engine": "schr", "engine_truth": "schr", "executed": True}
        )
        == "success"
    )


def test_sim_bare_success_without_provenance_is_partial():
    assert outer_status_from_sim_payload({"status": "success"}) == "partial"
    assert outer_status_from_sim_payload({"metrics": {}}) == "partial"


def test_plugin_requires_positive_provenance():
    # Bare self-declared success is refused (not demoted via stub flag).
    assert outer_status_from_plugin_result({"status": "success"}) == "partial"
    assert outer_status_from_plugin_result({"ideas": ["a"]}) == "partial"
    # Real LLM work
    assert (
        outer_status_from_plugin_result({"status": "success", "llm_backed": True, "ideas": ["a"]})
        == "success"
    )
    # Real compute
    assert outer_status_from_plugin_result({"p_value": 0.03, "executed": True}) == "success"
    # LLM missing but payload kept
    assert (
        outer_status_from_plugin_result({"status": "partial", "llm_backed": False, "strengths": []})
        == "partial"
    )
    assert outer_status_from_plugin_result(None) == "partial"


def test_search_empty_is_partial():
    assert search_outer_status(total_found=0, sources_requested=False) == "partial"
    assert search_outer_status(total_found=3, sources_requested=True) == "success"


def test_hil_like_gate_fail():
    assert (
        outer_status_from_hil_like(
            quality_passed_all=False, quality_score=90, sim_status="completed"
        )
        == "partial"
    )
    assert (
        outer_status_from_hil_like(
            quality_passed_all=True, quality_score=90, sim_status="completed"
        )
        == "success"
    )


def test_bma_and_causal_provenance():
    assert bma_outer_status({"models": [{"name": "a"}]}) == "partial"
    assert (
        bma_outer_status(
            {
                "weighted_prediction": 1.0,
                "models": [{"name": "a", "posterior_prob": 1.0}],
            }
        )
        == "success"
    )
    assert causal_outer_status(identifiable=False, formula=None) == "success"
    assert causal_outer_status(identifiable=None, formula=None) == "partial"


def test_record_field_status_dict_and_none():
    assert record_field_status({"status": "partial"}) == "partial"
    assert record_field_status(None) == "N/A"


def test_finalize_empty_structure_is_partial():
    from src.plugins._llm_base import finalize_plugin_result

    out = finalize_plugin_result({"problem": "x", "observe": [], "orient": []}, "raw llm text")
    assert out["llm_backed"] is True
    assert out["status"] == "partial"
