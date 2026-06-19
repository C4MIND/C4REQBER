"""Universal Problem-Solving Pipeline.

Orchestrator — delegates to step modules.
"""
from __future__ import annotations


__all__ = [
    "PipelineStage",
    "PipelineStep",
    "PipelineEvent",
    "SolvePipelineResult",
    "UniversalSolvePipeline",
]

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Literal, TypedDict

from src.agents.mp_llm_generator import MPLLMDynamicGenerator
from src.agents.pipeline.steps.base import PipelineStage, PipelineStep
from src.c4.engine import C4Space
from src.c4.observer import ObserverController
from src.c4.transformer import DomainTransformer
from src.discovery.gap_analyzer import AutoGapAnalyzer
from src.llm.multi_provider import OpenRouterClient as AsyncLLMClient
from src.llm.multi_provider import ProviderRouter
from src.memory.bank import StructuralMemoryBank
from src.metamodels.impact import ImpactEngine
from src.metamodels.matrix_dream import MatrixDreamLibrary
from src.metamodels.mp.library import MPLibrary
from src.metamodels.mp.profiles import MPRotationEngine
from src.metamodels.qzrf.operators import QzrfLibrary
from src.pipeline.base import BasePipeline
from src.pipeline.config import PipelineConfig


class PipelineEvent(TypedDict, total=False):
    """PipelineEvent."""
    event: Literal["start", "step_start", "step_complete", "complete", "error", "done"]
    problem: str
    mode: str
    stage: str
    status: str
    duration_ms: float
    data: dict[str, Any]
    error: str
    result: dict[str, Any]


@dataclass
class SolvePipelineResult:
    """SolvePipelineResult."""
    problem: str
    mode: str
    steps: list[PipelineStep] = field(default_factory=list)
    final_solution: str = ""
    confidence: float = 0.0
    c4_path: list[str] = field(default_factory=list)
    mp_perspectives: list[Any] = field(default_factory=list)
    prior_art_summary: str | None = None
    qzrf_recommendations: list[str] = field(default_factory=list)
    isomorphism_found: bool = False
    total_duration_ms: float = 0.0
    cost_usd: float = 0.0
    observer_insights: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "problem": self.problem,
            "mode": self.mode,
            "final_solution": self.final_solution,
            "confidence": self.confidence,
            "c4_path": self.c4_path,
            "total_duration_ms": self.total_duration_ms,
            "isomorphism_found": self.isomorphism_found,
            "steps": [
                {
                    "stage": s.stage.value,
                    "status": s.status,
                    "duration_ms": s.duration_ms,
                    "error": s.error,
                    "input_data": s.input_data,
                    "output_data": s.output_data,
                }
                for s in self.steps
            ],
            "mp_perspectives": [p.to_dict() for p in self.mp_perspectives],
            "observer_insights": self.observer_insights,
        }


class UniversalSolvePipeline(BasePipeline):
    """Universal Problem-Solving Pipeline — inherits config, events, observer from BasePipeline."""

    def __init__(self, provider_router: ProviderRouter | None = None, config: PipelineConfig | None = None) -> None:
        super().__init__(config=config)
        if provider_router is None:
            from src.llm.config import ProviderPreset
            from src.llm.router import ProviderRouter
            provider_router = ProviderRouter.from_preset(ProviderPreset.C4REQBER)
        self.c4_space = C4Space()
        self.transformer = DomainTransformer(self.c4_space)
        self.observer = ObserverController(self.c4_space)
        self.impact = ImpactEngine()
        self.qzrf = QzrfLibrary()
        self.mp_lib = MPLibrary()
        self.mp_rotation = MPRotationEngine(self.mp_lib)
        self._llm_client: AsyncLLMClient | None = None
        self.mp_llm_generator = MPLLMDynamicGenerator(
            provider_router=provider_router,
        )
        self.matrix_dream = MatrixDreamLibrary()
        self.memory = StructuralMemoryBank()
        from src.knowledge.orchestrator import MultiSourceSearcher
        self.prior_art = MultiSourceSearcher(
            sources={
                "openalex", "crossref", "pubmed", "europe_pmc",
                "dblp", "datacite", "zenodo", "figshare", "doaj",
                "inspire_hep", "arxiv",
            },
            max_concurrent=8,
            cache_enabled=True,
            cache_ttl=300.0,
        )
        self.gap_analyzer = AutoGapAnalyzer()
        self.provider_router = provider_router
        self._logger = logging.getLogger("c4_cdi_turbo.pipeline")
        self._llm_lock = asyncio.Lock()
        self._selected_plugins: list[str] = []
        self._selected_pattern: str | None = None
        self._cost_tracker = None
        self._prior_art_confidence = 0.0
        self.multi_searcher = None

    def set_plugins(self, plugin_ids: list[str]) -> None:
        self._selected_plugins = plugin_ids

    def set_pattern(self, pattern_id: str | None) -> None:
        self._selected_pattern = pattern_id

    async def close(self) -> None:
        """Close."""
        if self._llm_client is not None:
            await self._llm_client.close()
            self._llm_client = None
        if self.provider_router is not None:
            await self.provider_router.close_all()

    async def __aenter__(self) -> Any:
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    async def solve(
        self,
        problem: str,
        mode: str = "autopilot",
        domain_hint: str | None = None,
        max_depth: int = 6,
    ) -> SolvePipelineResult:
        """Solve."""
        from src.llm.cost_tracker import get_cost_tracker

        self._cost_tracker = get_cost_tracker()
        self._cost_tracker.reset()
        result = SolvePipelineResult(problem=problem, mode=mode)
        async for event in self.solve_streaming(problem, mode, domain_hint, max_depth):
            if event["event"] == "error":
                result.final_solution = f"Pipeline error: {event.get('error', 'Unknown')}"
                result.confidence = 0.0
                return result
            if event["event"] == "complete" and "result" in event:
                data = event["result"]
                result.final_solution = data.get("final_solution", "")
                result.confidence = data.get("confidence", 0.5)
                result.c4_path = data.get("c4_path", [])
                result.prior_art_summary = data.get("prior_art_summary", "")
                result.isomorphism_found = data.get("isomorphism_found", False)
                result.qzrf_recommendations = data.get("qzrf_recommendations", [])
                result.total_duration_ms = data.get("total_duration_ms", 0)
                # Restore observer data
                result.observer_insights = data.get("observer_insights", [])
                # Restore steps
                from src.agents.pipeline.steps.base import PipelineStage, PipelineStepResult
                for s in data.get("steps", []):
                    try:
                        result.steps.append(PipelineStepResult(
                            stage=PipelineStage(s["stage"]),
                            status=s["status"],
                            input_data=s.get("input_data", {}),
                            output_data=s.get("output_data", {}),
                            duration_ms=s.get("duration_ms", 0),
                            error=s.get("error"),
                        ))
                    except Exception:
                        pass
        result.cost_usd = self._cost_tracker.get_session_cost()
        return result

    def _create_result(self, problem: str, mode: str) -> SolvePipelineResult:
        """Factory for result objects."""
        return SolvePipelineResult(problem=problem, mode=mode)

    async def solve_streaming(
        self,
        problem: str,
        mode: str = "autopilot",
        domain_hint: str | None = None,
        max_depth: int = 6,
    ) -> None:
        """Solve streaming."""
        from src.agents.pipeline.executor import PipelineExecutor

        executor = PipelineExecutor(self)
        async for event in executor.execute(problem, mode, domain_hint, max_depth):
            yield event
