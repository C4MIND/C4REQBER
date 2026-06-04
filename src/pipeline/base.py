"""
BasePipeline — shared pipeline infrastructure for all discovery pipelines.

HILDiscoveryPipeline and UniversalSolvePipeline inherit from this.
Provides: config loading, event bus, quality gates, observer, discovery memory.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.core.user_profile import UserProfile
from src.pipeline.config import PipelineConfig
from src.pipeline.events import event_bus
from src.pipeline.quality import QualityGates, QualityReport


logger = logging.getLogger(__name__)


@dataclass
class DiscoveryRecord:
    """Shared discovery state across pipeline phases."""
    topic: str
    config: PipelineConfig = field(default_factory=PipelineConfig)
    user_profile: UserProfile | None = None
    sources: list[dict[str, Any]] = field(default_factory=list)
    gaps: list[dict[str, Any]] = field(default_factory=list)
    hypotheses: list[dict[str, Any]] = field(default_factory=list)
    c4_state: str = ""
    simulation: dict[str, Any] = field(default_factory=dict)
    verification: dict[str, Any] = field(default_factory=dict)
    bibliography: list[dict[str, Any]] = field(default_factory=list)
    quality_report: QualityReport | None = None
    plugins_context: dict[str, Any] = field(default_factory=dict)
    usp_context: dict[str, Any] = field(default_factory=dict)
    abort_reasons: list[str] = field(default_factory=list)
    refinement_history: list[dict[str, Any]] = field(default_factory=list)
    saga_id: str = ""


class BasePipeline:
    """Base class for all discovery pipelines.

    Provides shared infrastructure:
    - Quality gates (with redundant N-version voting)
    - Event bus for phase notifications + EventStore for replay
    - Saga orchestration for transactional discovery
    - CQRS command dispatch for pipeline stages
    - Pipeline observer (stagnation detection)
    - Discovery memory (fingerprint-based dedup)
    """

    def __init__(
        self,
        config: PipelineConfig | None = None,
        user_profile: UserProfile | None = None,
        quality_gates: QualityGates | None = None,
    ) -> None:
        self.config = config or PipelineConfig()
        self.user_profile = user_profile
        self.quality = quality_gates or QualityGates()
        self.quality_gates = self.quality
        self._observer = None
        self._event_store = None
        self._saga = None
        self._cqrs_bus = None

    @property
    def event_store(self):
        """Lazy-init EventStore for pipeline replay."""
        if self._event_store is None:
            from src.architecture.event_sourcing import get_event_store
            self._event_store = get_event_store()
        return self._event_store

    @property
    def saga(self):
        """Lazy-init Saga for transactional orchestration."""
        if self._saga is None:
            from src.architecture.saga import DiscoverySaga
            self._saga = DiscoverySaga()
        return self._saga

    @saga.setter
    def saga(self, value):
        self._saga = value

    @property
    def cqrs_bus(self):
        """Lazy-init CQRS bus for command dispatch."""
        if self._cqrs_bus is None:
            from src.architecture.cqrs import CqrsBus
            self._cqrs_bus = CqrsBus()
        return self._cqrs_bus

    @cqrs_bus.setter
    def cqrs_bus(self, value):
        self._cqrs_bus = value

    @property
    def observer(self):
        """Observer."""
        if self._observer is None:
            from src.pipeline.observer import PipelineObserver
            self._observer = PipelineObserver()
        return self._observer

    @observer.setter
    def observer(self, value):
        self._observer = value

    @staticmethod
    def _log_phase(phase: str, name: str) -> None:
        logger.info("Phase %s: %s started", phase, name)

    async def emit_event(self, event_type: str, data: dict[str, Any], mode: str = "turbo") -> None:
        try:
            await event_bus.emit(event_type, data, mode=mode)
        except Exception:
            logger.debug("Event bus emission skipped for %s", event_type)
        try:
            from src.architecture.event_sourcing import DomainEvent
            from src.architecture.event_sourcing import EventType as ArchEventType
            mapping = {
                "pipeline_start": ArchEventType.PIPELINE_STARTED,
                "pipeline_complete": ArchEventType.PIPELINE_COMPLETED,
                "pipeline_fail": ArchEventType.PIPELINE_FAILED,
                "phase_complete": ArchEventType.PATTERN_APPLIED,
                "hypothesis_generated": ArchEventType.DISCOVERY_CREATED,
                "hypothesis_validated": ArchEventType.DISCOVERY_VALIDATED,
            }
            evt_type = mapping.get(event_type, ArchEventType.DISCOVERY_UPDATED)
            event = DomainEvent.create(
                event_type=evt_type,
                aggregate_id=data.get("topic", "unknown"),
                aggregate_type="DiscoveryRecord",
                version=1,
                payload=data,
                metadata={"mode": mode, "source": "BasePipeline.emit_event"},
            )
            self.event_store.append(event)
        except Exception:
            logger.debug("EventStore append skipped for %s", event_type)

    def create_record(self, topic: str) -> DiscoveryRecord:
        return DiscoveryRecord(topic=topic, config=self.config, user_profile=self.user_profile)

    @staticmethod
    def _check_input(topic: str) -> str:
        cleaned = topic.strip()
        if not cleaned:
            raise ValueError("Topic cannot be empty")
        if len(cleaned) < 3:
            raise ValueError(f"Topic too short (min 3 characters): '{cleaned}'")
        return cleaned
