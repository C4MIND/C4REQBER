from __future__ import annotations


"""Phase D: Cognitive Agents — Functors (9 perspectives) and Plugins (24 methods)."""

import importlib
import logging
from typing import Any

from src.plugins.unified_registry import PLUGIN_REGISTRY


# Note: FunctorOrchestrator (agents layer) is resolved by LATE BINDING inside
# run_functors (see below), not imported statically. This pipeline phase invokes
# the agent layer only at runtime, so the generic pipeline engine has no static
# (import-time) dependency on the agents package — it stays independently
# importable/type-checkable. The runtime invocation is guarded by try/except.


logger = logging.getLogger(__name__)


class PhaseD_CognitiveAgents:
    """Run functor agents and cognitive plugins."""

    async def run_functors(self, topic: str, hypotheses: list[dict[str, Any]]) -> dict[str, Any]:
        """Run 9 cognitive functor agents in parallel, extract novel insights."""
        print("\n[3.5/7] Running 9 cognitive functor agents...")
        try:
            FunctorOrchestrator = importlib.import_module(
                "src.agents.functor_orchestrator"
            ).FunctorOrchestrator
            orchestrator = FunctorOrchestrator()
            result = await orchestrator.run_turbo(topic, agent_count=9, vector="discover")

            agent_results = result.get("agent_results", [])
            novel_hypotheses: list[dict[str, Any]] = []

            for r in agent_results:
                if r.get("novel") and r.get("confidence", 0) > 0.6:
                    insight = r.get("insight", "")
                    if insight and len(insight) > 20:
                        novel_hypotheses.append({
                            "title": f"[{r.get('agent', '?')}] {insight[:100]}",
                            "description": insight,
                            "testability_score": r.get("confidence", 0.7),
                            "source": "functor",
                            "agent": r.get("agent", ""),
                        })

            # Deduplicate against existing hypotheses
            existing_titles = {h["title"].lower()[:50] for h in hypotheses}
            unique_novel = [
                h for h in novel_hypotheses
                if h["title"].lower()[:50] not in existing_titles
            ]

            return {
                "novel_hypotheses": unique_novel[:5],  # Max 5 from functors
                "total_agents": result.get("total_agents", 0),
                "total_time": result.get("total_time_seconds", 0),
            }
        except Exception as e:
            logger.warning("Functor analysis failed: %s", e)
            return {"novel_hypotheses": [], "total_agents": 0, "total_time": 0}

    async def run_plugins(self, topic: str, query_type: str) -> dict[str, Any]:
        """Run cognitive plugins based on query type."""
        print("\n[3.6/7] Running cognitive plugins...")
        try:
            selected = self._select_plugins(query_type, topic)
            results: dict[str, Any] = {}
            for plugin_id in selected:
                if plugin_id not in PLUGIN_REGISTRY:
                    continue
                try:
                    info = PLUGIN_REGISTRY[plugin_id]
                    result = info.execute_fn({"problem": topic})
                    results[plugin_id] = {
                        "name": info.name,
                        "result": result,
                    }
                except Exception as e:
                    logger.debug("Plugin %s failed: %s", plugin_id, e)
            return results
        except Exception as e:
            logger.warning("Plugins failed: %s", e)
            return {}

    def _select_plugins(self, query_type: str, topic: str) -> list[str]:
        """Auto-select plugins by query type."""
        if query_type == "practical":
            return ["swot", "pareto", "pre_mortem"]
        elif any(kw in topic.lower() for kw in ["safety", "risk", "security"]):
            return ["inversion", "red_team", "pre_mortem"]
        elif any(kw in topic.lower() for kw in ["product", "design", "innovation"]):
            return ["scamper", "six_hats", "first_principles"]
        elif any(kw in topic.lower() for kw in ["career", "business", "startup"]):
            return ["swot", "ooda", "second_order"]
        else:
            return ["first_principles", "five_whys", "second_order"]
