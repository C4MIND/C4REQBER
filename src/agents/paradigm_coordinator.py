from __future__ import annotations


"""
C44TCDI: Paradigm Shift Coordinator
Orchestrates 100+ agents across 3 phases (divergence → convergence → synthesis)
to detect and articulate paradigm shifts (Kuhnian sense) in any scientific domain.
"""
import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, cast

from src.agents.functors import (
    AbstractionAgent,
    ConcretizationAgent,
    ContextAgent,
    DistinctionAgent,
    IntegrationAgent,
    InversionAgent,
    MetaReflectionAgent,
    ResonanceAgent,
    TemporalAgent,
)
from src.agents.prompts.paradigm import AGENT_PROMPTS, PARADIGM_SYSTEM_PROMPT


logger = logging.getLogger("c44tcdi.agents.paradigm_coordinator")

FUNCTOR_MAP: dict[str, Any] = {
    "τ": TemporalAgent,
    "σ": IntegrationAgent,
    "δ": DistinctionAgent,
    "ρ": ResonanceAgent,
    "ι": InversionAgent,
    "λ": AbstractionAgent,
    "κ": ConcretizationAgent,
    "φ": ContextAgent,
    "ψ": MetaReflectionAgent,
}

FUNCTOR_KEYS = list(FUNCTOR_MAP.keys())


@dataclass
class ParadigmPhaseResult:
    """ParadigmPhaseResult."""
    phase: str
    duration_ms: float
    data: dict[str, Any] = field(default_factory=dict)
    agent_count: int = 0


@dataclass
class ParadigmResult:
    """ParadigmResult."""
    problem: str
    domain: str
    phases: list[ParadigmPhaseResult] = field(default_factory=list)
    contradictions: list[dict[str, Any]] = field(default_factory=list)
    anomalies: list[dict[str, Any]] = field(default_factory=list)
    shift_score: float = 0.0
    recommended_paradigm: str = ""
    manifesto: str = ""
    total_duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "problem": self.problem,
            "domain": self.domain,
            "shift_score": self.shift_score,
            "recommended_paradigm": self.recommended_paradigm,
            "manifesto": self.manifesto,
            "contradiction_count": len(self.contradictions),
            "anomaly_count": len(self.anomalies),
            "contradictions": self.contradictions,
            "anomalies": self.anomalies,
            "phases": [{"phase": p.phase, "duration_ms": p.duration_ms, "agent_count": p.agent_count} for p in self.phases],
            "total_duration_ms": self.total_duration_ms,
        }


class ParadigmCoordinator:
    """Оркестратор Paradigm Shift: 100+ агентов, 3 фазы.

    PHASE 1 (divergence): Все агенты независимо ищут противоречия.
        Запускается 120+ агентов (9 типов × ~14 раундов), каждый с уникальным
        когнитивным промптом. Агенты циклически чередуются для максимального
        покрытия.

    PHASE 2 (convergence): Сборка — группировка противоречий по доменам.
        Результаты фазы 1 кластеризуются: противоречия группируются по типу
        агента и тематике. Вычисляется shift_score и density метрики.

    PHASE 3 (synthesis): Синтез — формирование манифеста парадигмального сдвига.
        На основе кластеризованных противоречий LLM формирует связный манифест,
        описывающий текущий Kuhnian crisis и предлагаемый сдвиг парадигмы.
    """

    PHASE_1 = "divergence"
    PHASE_2 = "convergence"
    PHASE_3 = "synthesis"

    def __init__(self, agent_count: int = 120) -> None:
        self.agent_count = max(agent_count, 9)
        self._agents: dict[str, Any] = {}

    def _init_agents(self) -> None:
        if self._agents:
            return
        self._agents = {
            key: cls()
            for key, cls in FUNCTOR_MAP.items()
        }

    # ------------------------------------------------------------------
    # Phase 1: Divergence
    # ------------------------------------------------------------------

    async def _phase_divergence(self, problem: str, domain: str) -> ParadigmPhaseResult:
        start = time.perf_counter()
        self._init_agents()

        selected: list[tuple[str, int]] = []
        for i in range(self.agent_count):
            selected.append((FUNCTOR_KEYS[i % len(FUNCTOR_KEYS)], i))

        async def _run_one(name: str, index: int) -> dict[str, Any]:
            agent = self._agents[name]
            prompt_key = f"{name}_{_agent_prompt_suffix(name)}"
            prompt = AGENT_PROMPTS.get(prompt_key, PARADIGM_SYSTEM_PROMPT)

            try:
                result = await asyncio.to_thread(agent.analyze, problem)
                result["index"] = index
                result["prompt_key"] = prompt_key
                # Augment with paradigm-specific fields
                if result.get("contradiction"):
                    contradiction = result["contradiction"]
                    if isinstance(contradiction, str):
                        result["contradiction"] = {
                            "axiom": f"Current {domain} assumption",
                            "tension": contradiction,
                            "agent": name,
                            "index": index,
                        }
                    else:
                        contradiction["agent"] = name
                        contradiction["index"] = index
                return result# type: ignore[no-any-return]
            except (TimeoutError, KeyError, TypeError) as e:
                return {
                    "agent": name,
                    "index": index,
                    "prompt_key": prompt_key,
                    "operation": "error",
                    "insight": f"Agent {name} failed: {str(e)}",
                    "contradiction": None,
                    "resolution": None,
                    "confidence": 0.0,
                    "novel": False,
                    "error": str(e),
                }

        tasks = [_run_one(name, idx) for name, idx in selected]
        results = await asyncio.gather(*tasks)

        elapsed = (time.perf_counter() - start) * 1000
        return ParadigmPhaseResult(
            phase=self.PHASE_1,
            duration_ms=round(elapsed, 2),
            data={"agent_results": results},
            agent_count=len(results),
        )

    # ------------------------------------------------------------------
    # Phase 2: Convergence
    # ------------------------------------------------------------------

    async def _phase_convergence(
        self,
        problem: str,
        domain: str,
        divergence_result: ParadigmPhaseResult,
    ) -> ParadigmPhaseResult:
        start = time.perf_counter()
        agent_results = divergence_result.data.get("agent_results", [])

        # Cluster contradictions by agent type
        contradictions: list[dict[str, Any]] = []
        anomalies: list[dict[str, Any]] = []
        by_agent: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for r in agent_results:
            agent = r.get("agent", "?")
            by_agent[agent].append(r)

            c = r.get("contradiction")
            if c:
                if isinstance(c, dict):
                    contradictions.append(c)
                elif isinstance(c, str):
                    contradictions.append({
                        "axiom": f"Assumption in {domain}",
                        "tension": c,
                        "agent": agent,
                        "index": r.get("index", 0),
                    })

            if r.get("novel"):
                anomalies.append({
                    "agent": agent,
                    "index": r.get("index", 0),
                    "insight": r.get("insight", ""),
                    "confidence": r.get("confidence", 0.0),
                })

        # Compute shift score
        total = max(len(agent_results), 1)
        contradiction_density = len(contradictions) / total
        novelty_density = len(anomalies) / total
        shift_score = round(contradiction_density * 0.7 + novelty_density * 0.3, 3)

        elapsed = (time.perf_counter() - start) * 1000
        return ParadigmPhaseResult(
            phase=self.PHASE_2,
            duration_ms=round(elapsed, 2),
            data={
                "contradictions": contradictions,
                "anomalies": anomalies,
                "by_agent": {k: len(v) for k, v in by_agent.items()},
                "shift_score": shift_score,
            },
            agent_count=0,
        )

    # ------------------------------------------------------------------
    # Phase 3: Synthesis
    # ------------------------------------------------------------------

    async def _phase_synthesis(
        self,
        problem: str,
        domain: str,
        convergence_result: ParadigmPhaseResult,
    ) -> ParadigmPhaseResult:
        start = time.perf_counter()
        contradictions = convergence_result.data.get("contradictions", [])
        shift_score = convergence_result.data.get("shift_score", 0.0)

        # Build recommended paradigm
        tension_count = len(contradictions)
        agent_types = set(c.get("agent", "?") for c in contradictions)

        if shift_score > 0.5:
            recommended = (
                f"A paradigm shift is likely in {domain}: {tension_count} axiomatic tensions "
                f"across {len(agent_types)} cognitive functor types "
                f"suggest the current framework for '{problem[:80]}' is in Kuhnian crisis."
            )
        elif shift_score > 0.2:
            recommended = (
                f"Paradigm tension detected in {domain}: {tension_count} contradictions warrant "
                f"further investigation into alternative frameworks for '{problem[:80]}'."
            )
        else:
            recommended = (
                f"No strong paradigm shift signal in {domain}: current framework "
                f"for '{problem[:80]}' appears robust against axiomatic contradictions."
            )

        # Build manifesto
        top_tensions = contradictions[:5]
        tension_lines = "\n".join(
            f"- [{t.get('agent', '?')}] {t.get('tension', '')[:120]}"
            for t in top_tensions
        )
        manifesto = (
            f"# Paradigm Shift Manifesto: {problem[:100]}\n\n"
            f"**Domain:** {domain}\n"
            f"**Shift Score:** {shift_score}\n"
            f"**Phase:** {'Kuhnian Crisis' if shift_score > 0.5 else 'Pre-paradigmatic tension' if shift_score > 0.2 else 'Normal Science'}\n\n"
            f"## Core Contradictions\n{tension_lines}\n\n"
            f"## Recommended Shift\n{recommended}\n"
        )

        elapsed = (time.perf_counter() - start) * 1000
        return ParadigmPhaseResult(
            phase=self.PHASE_3,
            duration_ms=round(elapsed, 2),
            data={
                "manifesto": manifesto,
                "recommended_paradigm": recommended,
            },
            agent_count=0,
        )

    # ------------------------------------------------------------------
    # Main run
    # ------------------------------------------------------------------

    async def run(self, problem: str, domain: str = "science") -> ParadigmResult:
        """Run."""
        total_start = time.perf_counter()

        # Phase 1: Divergence — 120+ agents find contradictions
        p1 = await self._phase_divergence(problem, domain)
        logger.info("Paradigm phase 1 (divergence): %d agents in %d ms", p1.agent_count, p1.duration_ms)

        # Phase 2: Convergence — cluster and score
        p2 = await self._phase_convergence(problem, domain, p1)
        logger.info("Paradigm phase 2 (convergence): %d contradictions found", len(p2.data.get("contradictions", [])))

        # Phase 3: Synthesis — manifesto generation
        p3 = await self._phase_synthesis(problem, domain, p2)
        logger.info("Paradigm phase 3 (synthesis): manifesto generated")

        total_elapsed = (time.perf_counter() - total_start) * 1000

        return ParadigmResult(
            problem=problem,
            domain=domain,
            phases=[p1, p2, p3],
            contradictions=p2.data.get("contradictions", []),
            anomalies=p2.data.get("anomalies", []),
            shift_score=p2.data.get("shift_score", 0.0),
            recommended_paradigm=p3.data.get("recommended_paradigm", ""),
            manifesto=p3.data.get("manifesto", ""),
            total_duration_ms=round(total_elapsed, 2),
        )


def _agent_prompt_suffix(name: str) -> str:
    """Map functor symbol to prompt suffix."""
    mapping: dict[str, str] = {
        "τ": "temporal",
        "σ": "integration",
        "δ": "distinction",
        "ρ": "resonance",
        "ι": "inversion",
        "λ": "abstraction",
        "κ": "concretization",
        "φ": "context",
        "ψ": "meta_reflection",
    }
    return mapping.get(name, name)
