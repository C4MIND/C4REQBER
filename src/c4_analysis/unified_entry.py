# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import logging
from typing import Any

from src.c4.cognitive_router import CognitiveRouter
from src.c4_analysis.multi_prompt_router import MultiPromptRouter
from src.c4_analysis.system_analyzer import SystemAnalyzer
from src.c4_analysis.system_synthesizer import SystemSynthesizer


logger = logging.getLogger(__name__)


def unified_entry(query: str) -> dict[str, Any]:
    """Run Phase A SystemAnalyzer, then route to appropriate handler.

    Args:
        query: Raw user query string.

    Returns:
        Unified result dict with:
        - phase_a_analysis: SystemAnalyzer.analyze() output
        - routing_result: output from chosen router
        - router_used: name of the router that handled the query
    """
    # Phase A: Universal system analysis
    analyzer = SystemAnalyzer()
    phase_a = analyzer.analyze(query)
    systemicity = phase_a.get("systemicity", 0.0)

    logger.debug(
        "Phase A complete — systemicity=%.2f, entities=%d, depth=%s",
        systemicity,
        len(phase_a.get("entities", [])),
        phase_a.get("analysis_depth", "unknown"),
    )

    # Decision: systemic & interconnected → SystemSynthesizer
    synthesizer = SystemSynthesizer()
    if systemicity > 0.5 and synthesizer.is_systemic(query):
        logger.debug("Routing through SystemSynthesizer (systemic problem)")
        routing_result = synthesizer.decompose_and_merge(query)
        return {
            "phase_a_analysis": phase_a,
            "routing_result": routing_result,
            "router_used": "SystemSynthesizer",
        }

    # Decision: multi-problem prompt → MultiPromptRouter
    separators = [" and ", " & ", " also ", "; ", ". ", " furthermore ", " moreover ", " plus ", " AND ", " And "]
    if any(sep in query for sep in separators):
        logger.debug("Routing through MultiPromptRouter (multi-problem prompt)")
        router = MultiPromptRouter()
        routing_result = router.route(query)
        return {
            "phase_a_analysis": phase_a,
            "routing_result": routing_result,
            "router_used": "MultiPromptRouter",
        }

    # Decision: single, non-systemic problem → CognitiveRouter direct
    logger.debug("Routing through CognitiveRouter (direct)")
    cognitive_router = CognitiveRouter()
    routing_result = cognitive_router.route(query)
    return {
        "phase_a_analysis": phase_a,
        "routing_result": routing_result,
        "router_used": "CognitiveRouter",
    }


__all__ = ["unified_entry"]
