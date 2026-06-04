from __future__ import annotations


"""
FunctorOrchestrator: Parallel multi-functor discovery system.

Uses asyncio.gather for parallel execution of functor agents.
Spawns up to agent_count agents, cycling through base + composite functors.
Results are synthesized by vector type (discover/invent/transform).
"""
import asyncio
import time
from typing import Any, Optional

from src.agents.functors import (
    AbstractionAgent,
    ConcretizationAgent,
    ContextAgent,
    DistinctionAgent,
    FunctorAgent,
    IntegrationAgent,
    InversionAgent,
    MetaReflectionAgent,
    ResonanceAgent,
    TemporalAgent,
    generate_all_composites,
)
from src.llm.async_client import AsyncLLMClient


class FunctorOrchestrator:
    """Orchestrates parallel functor-agent execution for turbo discovery."""

    def __init__(self, llm_client: AsyncLLMClient | None = None) -> None:
        from src.llm.router import ProviderRouter
        self.llm_client = llm_client or ProviderRouter()
        self.base_functors: list[FunctorAgent] = [
            TemporalAgent(llm_client=self.llm_client),
            IntegrationAgent(llm_client=self.llm_client),
            DistinctionAgent(llm_client=self.llm_client),
            ResonanceAgent(llm_client=self.llm_client),
            InversionAgent(llm_client=self.llm_client),
            AbstractionAgent(llm_client=self.llm_client),
            ConcretizationAgent(llm_client=self.llm_client),
            ContextAgent(llm_client=self.llm_client),
            MetaReflectionAgent(llm_client=self.llm_client),
        ]
        self.composite_functors: list[FunctorAgent] = generate_all_composites(self.base_functors)
        self.all_functors: list[FunctorAgent] = self.base_functors + self.composite_functors

    async def run_turbo(
        self,
        problem: str,
        agent_count: int = 25,
        vector: str = "discover",
    ) -> dict[str, Any]:
        """Run turbo discovery with parallel functor agents.

        Args:
            problem: The problem statement to analyze.
            agent_count: Number of agents to spawn in parallel.
            vector: Output type — "discover", "invent", or "transform".

        Returns:
            Dict with agent_results, synthesis, and metadata.
        """
        start_time = time.perf_counter()

        # Select functors (cycle through all available)
        selected = [self.all_functors[i % len(self.all_functors)] for i in range(agent_count)]

        # Run all analyses in parallel
        tasks = [
            self._run_functor_safe(functor, problem, vector, idx)
            for idx, functor in enumerate(selected)
        ]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        agent_results: list[dict[str, Any]] = []
        for idx, (functor, result) in enumerate(zip(selected, raw_results, strict=False)):
            if isinstance(result, Exception):
                agent_results.append({
                    "agent": functor.symbol,
                    "index": idx,
                    "operation": f"error_{functor.symbol}",
                    "insight": f"Error: {str(result)}",
                    "contradiction": None,
                    "novel": False,
                    "confidence": 0.0,
                    "error": str(result),
                })
            else:
                result["index"] = idx
                result["operation"] = f"{vector}_{functor.symbol}"
                agent_results.append(result)

        # Synthesize by vector
        synthesis = self._synthesize(problem, vector, agent_results)

        total_time = time.perf_counter() - start_time

        return {
            "agent_results": agent_results,
            "synthesis": synthesis,
            "total_agents": len(agent_results),
            "base_functors_used": len(self.base_functors),
            "composite_functors_used": len(self.composite_functors),
            "vector": vector,
            "mode": "real",
            "total_time_seconds": round(total_time, 3),
        }

    async def _run_functor_safe(
        self,
        functor: FunctorAgent,
        problem: str,
        vector: str,
        index: int,
    ) -> dict[str, Any]:
        """Run a single functor with error handling."""
        try:
            return await functor.analyze(
                problem,
                context={"vector": vector, "index": index},
            )
        except Exception as e:
            return {
                "agent": functor.symbol,
                "problem": problem,
                "insight": f"Functor {functor.symbol} failed: {str(e)}",
                "confidence": 0.0,
                "contradiction": None,
                "novel": False,
                "error": str(e),
            }

    def _synthesize(
        self,
        problem: str,
        vector: str,
        agent_results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Synthesize agent results into a coherent response based on vector."""
        insights = [r["insight"] for r in agent_results if r.get("insight") and not r.get("error")]
        contradictions = [r["contradiction"] for r in agent_results if r.get("contradiction")]
        novel_count = sum(1 for r in agent_results if r.get("novel"))
        avg_confidence = sum(r.get("confidence", 0) for r in agent_results) / max(len(agent_results), 1)

        if vector == "discover":
            return {
                "type": "hypothesis",
                "problem": problem,
                "hypothesis": self._build_hypothesis(problem, insights),
                "key_insights": insights[:5],
                "contradictions": [c for c in contradictions if c][:5],
                "novelty_count": novel_count,
                "confidence": round(avg_confidence, 3),
                "supporting_agents": len(agent_results),
            }
        elif vector == "invent":
            return {
                "type": "blueprint",
                "problem": problem,
                "blueprint": self._build_blueprint(problem, insights),
                "components": insights[:10],
                "contradictions": [c for c in contradictions if c][:5],
                "novelty_count": novel_count,
                "confidence": round(avg_confidence, 3),
            }
        else:  # transform
            return {
                "type": "dissertation",
                "problem": problem,
                "theory": self._build_theory(problem, insights, contradictions),
                "paradigm_shift_score": self._compute_shift_score(agent_results),
                "axiomatic_contradictions": [
                    {"agent": r.get("agent", "?"), "contradiction": c}
                    for r in agent_results
                    if (c := r.get("contradiction"))
                ],
                "novelty_count": novel_count,
                "confidence": round(avg_confidence, 3),
            }

    def _build_hypothesis(self, problem: str, insights: list[str]) -> str:
        """Build an integrated hypothesis from insights."""
        if not insights:
            return f"No insights generated for: {problem}"
        joined = " ".join(insights[:3])
        return (
            f"Integrated hypothesis for '{problem}': {joined} "
            f"Synthesis of {len(insights)} functor perspectives suggests a novel explanatory model."
        )

    def _build_blueprint(self, problem: str, insights: list[str]) -> str:
        """Build an invention blueprint from insights."""
        if not insights:
            return f"No blueprint components for: {problem}"
        return (
            f"Blueprint for '{problem}': integrates {len(insights)} functional transformations. "
            f"Core approach: {insights[0]}"
        )

    def _build_theory(self, problem: str, insights: list[str], contradictions: list[str]) -> str:
        """Build a transformative theory from insights and contradictions."""
        if not insights:
            return f"No theory generated for: {problem}"
        contradiction_count = len([c for c in contradictions if c])
        return (
            f"Theory for '{problem}': {insights[0]} "
            f"Identified {contradiction_count} axiomatic tensions resolved through "
            f"{len(insights)} functional transformations."
        )

    def _compute_shift_score(self, results: list[dict[str, Any]]) -> float:
        """Compute paradigm shift score from agent results."""
        if not results:
            return 0.0
        contradiction_count = sum(1 for r in results if r.get("contradiction"))
        novelty_count = sum(1 for r in results if r.get("novel"))
        return round((contradiction_count * 0.6 + novelty_count * 0.4) / len(results), 3)
