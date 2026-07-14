"""
Disclosure Filter: Filters C4 engine output based on user complexity level
This module takes raw engine results and simplifies them based on disclosure config
"""
from __future__ import annotations

from typing import Any

from src.core.complexity_adapter import DisclosureConfig


def filter_solve_result(
    raw_result: dict[str, Any], config: DisclosureConfig
) -> dict[str, Any]:
    """
    Take raw C4 pipeline output and filter it based on user complexity level

    Args:
        raw_result: Full output from PipelineOrchestrator (contains everything)
        config: DisclosureConfig specifying what to show/hide

    Returns:
        Simplified dict containing only fields visible at user's level
    """
    # Always include core hypothesis data (the actual value to user)
    simplified = {
        "hypotheses": raw_result.get("hypotheses", []),
        "confidence_scores": raw_result.get("confidence_scores", {}),
        "sources": raw_result.get("sources", []),
    }

    # Optional: Include raw query for reference
    if "query" in raw_result:
        simplified["query"] = raw_result["query"]

    # Optional fields shown based on config
    if config.show_pipeline_steps and "c4_path" in raw_result:
        simplified["pipeline_path"] = raw_result["c4_path"]

    if config.show_c4_coordinates and "c4_states" in raw_result:
        simplified["c4_states"] = raw_result["c4_states"]

    if config.show_agent_details and "mp_reasoning" in raw_result:
        simplified["agent_reasoning"] = raw_result["mp_reasoning"]

    if config.show_agent_details and "mp_rotations" in raw_result:
        simplified["mp_rotations"] = raw_result["mp_rotations"]

    if config.show_operators and "operators_used" in raw_result:
        simplified["operators_used"] = raw_result["operators_used"]

    if config.show_troubleshooting and "debug_info" in raw_result:
        simplified["debug_info"] = raw_result["debug_info"]

    if config.show_troubleshooting and "validation_logs" in raw_result:
        simplified["validation_logs"] = raw_result["validation_logs"]

    # For Advanced/Expert: Show partial pipeline data
    if config.show_pipeline_steps:
        if "impact_analysis" in raw_result:
            simplified["impact_analysis"] = raw_result["impact_analysis"]
        if "prior_art" in raw_result:
            simplified["prior_art"] = raw_result["prior_art"]
        if "qarf_selection" in raw_result:
            simplified["qarf_selection"] = raw_result["qarf_selection"]
        if "isomorphism_results" in raw_result:
            simplified["isomorphisms"] = raw_result["isomorphism_results"]
        if "synthesis_steps" in raw_result:
            simplified["synthesis"] = raw_result["synthesis_steps"]
        if "validation_results" in raw_result:
            simplified["validation"] = raw_result["validation_results"]

    # For Expert: Show everything, including unsafe fields
    if config.allow_custom_operators or config.allow_wasm_upload:
        # Include raw engine state for debugging
        if "raw_engine_state" in raw_result:
            simplified["_engine_state"] = raw_result["raw_engine_state"]
        if "wasm_traces" in raw_result:
            simplified["wasm_traces"] = raw_result["wasm_traces"]

    return simplified


def filter_search_result(
    raw_result: dict[str, Any], config: DisclosureConfig
) -> dict[str, Any]:
    """
    Filter literature search results based on complexity level

    Args:
        raw_result: Full search results with metadata
        config: DisclosureConfig

    Returns:
        Simplified search results
    """
    simplified = {
        "results": raw_result.get("results", []),
        "total_count": raw_result.get("total_count", 0),
    }

    if config.show_c4_coordinates and "c4_fingerprints" in raw_result:
        simplified["result_fingerprints"] = raw_result["c4_fingerprints"]

    if config.show_agent_details and "agent_queries" in raw_result:
        simplified["search_strategy"] = raw_result["agent_queries"]

    return simplified


def filter_validation_result(
    raw_result: dict[str, Any], config: DisclosureConfig
) -> dict[str, Any]:
    """
    Filter validation/experiment results based on complexity level

    Args:
        raw_result: Full validation results
        config: DisclosureConfig

    Returns:
        Simplified validation results
    """
    simplified = {
        "experiments": raw_result.get("experiments", []),
        "overall_status": raw_result.get("overall_status", "pending"),
    }

    if config.show_troubleshooting and "logs" in raw_result:
        simplified["logs"] = raw_result["logs"]

    if config.show_troubleshooting and "errors" in raw_result:
        simplified["errors"] = raw_result["errors"]

    if config.show_pipeline_steps and "validation_chain" in raw_result:
        simplified["validation_steps"] = raw_result["validation_chain"]

    return simplified


def create_lite_response(raw_result: dict[str, Any]) -> dict[str, Any]:
    """
    Convenience function: Create Lite response from raw result
    Uses LITE_CONFIG automatically
    """
    from src.core.complexity_adapter import LITE_CONFIG

    return filter_solve_result(raw_result, LITE_CONFIG)


def create_advanced_response(raw_result: dict[str, Any]) -> dict[str, Any]:
    """
    Convenience function: Create Advanced response from raw result
    Uses ADVANCED_CONFIG automatically
    """
    from src.core.complexity_adapter import ADVANCED_CONFIG

    return filter_solve_result(raw_result, ADVANCED_CONFIG)


def create_expert_response(raw_result: dict[str, Any]) -> dict[str, Any]:
    """
    Convenience function: Create Expert response from raw result
    Uses EXPERT_CONFIG automatically
    """
    from src.core.complexity_adapter import EXPERT_CONFIG

    return filter_solve_result(raw_result, EXPERT_CONFIG)
