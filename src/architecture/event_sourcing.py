"""
C4REQBER: Event Sourcing Core

Provides event store, aggregates, and projection infrastructure
for the C4REQBER cognitive discovery engine.
"""
from __future__ import annotations

import threading
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Callable, Generic, TypeVar

from src.compat import UTC


class EventType(StrEnum):
    """Domain event types for C4REQBER."""

    DISCOVERY_CREATED = "discovery.created"
    DISCOVERY_UPDATED = "discovery.updated"
    DISCOVERY_VALIDATED = "discovery.validated"
    PATTERN_APPLIED = "pattern.applied"
    PIPELINE_STARTED = "pipeline.started"
    PIPELINE_COMPLETED = "pipeline.completed"
    PIPELINE_FAILED = "pipeline.failed"
    AGENT_INVOKED = "agent.invoked"
    AGENT_COMPLETED = "agent.completed"
    LLM_CALLED = "llm.called"
    LLM_RESPONSE = "llm.response"
    VALIDATION_PASSED = "validation.passed"
    VALIDATION_FAILED = "validation.failed"
    METRIC_RECORDED = "metric.recorded"


@dataclass(frozen=True)
class DomainEvent:
    """Immutable domain event."""

    event_id: str
    event_type: EventType
    aggregate_id: str
    aggregate_type: str
    version: int
    timestamp: datetime
    payload: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        event_type: EventType,
        aggregate_id: str,
        aggregate_type: str,
        version: int,
        payload: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> DomainEvent:
        return cls(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            version=version,
            timestamp=datetime.now(UTC),
            payload=payload,
            metadata=metadata or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DomainEvent:
        return cls(
            event_id=data["event_id"],
            event_type=EventType(data["event_type"]),
            aggregate_id=data["aggregate_id"],
            aggregate_type=data["aggregate_type"],
            version=data["version"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            payload=data["payload"],
            metadata=data.get("metadata", {}),
        )


T = TypeVar("T")


class EventStore(ABC):
    """Abstract event store."""

    @abstractmethod
    def append(self, event: DomainEvent) -> None:
        """Append event to store."""
        raise NotImplementedError

    @abstractmethod
    def get_events(
        self,
        aggregate_id: str,
        from_version: int = 0,
    ) -> list[DomainEvent]:
        """Get events for aggregate."""
        raise NotImplementedError

    @abstractmethod
    def get_all_events(
        self,
        event_types: list[EventType] | None = None,
        after_position: int | None = None,
        limit: int = 100,
    ) -> list[DomainEvent]:
        """Get all events (for projections)."""
        raise NotImplementedError

    @abstractmethod
    def get_latest_version(self, aggregate_id: str) -> int:
        """Get latest version for aggregate."""
        raise NotImplementedError


class InMemoryEventStore(EventStore):
    """In-memory event store for testing."""

    def __init__(self) -> None:
        self._events: list[DomainEvent] = []
        self._lock = threading.RLock()

    def append(self, event: DomainEvent) -> None:
        with self._lock:
            self._events.append(event)

    def get_events(
        self,
        aggregate_id: str,
        from_version: int = 0,
    ) -> list[DomainEvent]:
        with self._lock:
            return [
                e for e in self._events
                if e.aggregate_id == aggregate_id and e.version >= from_version
            ]

    def get_all_events(
        self,
        event_types: list[EventType] | None = None,
        after_position: int | None = None,
        limit: int = 100,
    ) -> list[DomainEvent]:
        with self._lock:
            events = self._events
            if after_position is not None:
                events = events[after_position:]
            if event_types:
                events = [e for e in events if e.event_type in event_types]
            return events[:limit]

    def get_latest_version(self, aggregate_id: str) -> int:
        with self._lock:
            versions = [
                e.version for e in self._events
                if e.aggregate_id == aggregate_id
            ]
            return max(versions) if versions else 0


class Aggregate(ABC):  # noqa: B024
    """Event-sourced aggregate root."""

    def __init__(self, aggregate_id: str) -> None:
        self._id = aggregate_id
        self._version = 0
        self._uncommitted_events: list[DomainEvent] = []

    @property
    def id(self) -> str:
        return self._id

    @property
    def version(self) -> int:
        return self._version

    @property
    def uncommitted_events(self) -> list[DomainEvent]:
        return list(self._uncommitted_events)

    def apply_event(self, event: DomainEvent) -> None:
        """Apply event to mutate state."""
        handler = getattr(self, f"_on_{event.event_type.name.lower()}", None)
        if handler:
            handler(event.payload)
        else:
            raise NotImplementedError(
                f"No handler for event type '{event.event_type.name}'. "
                f"Expected method: _on_{event.event_type.name.lower()}"
            )
        self._version = event.version

    def _create_event(
        self,
        event_type: EventType,
        payload: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> DomainEvent:
        """Create and stage a new event."""
        self._version += 1
        event = DomainEvent.create(
            event_type=event_type,
            aggregate_id=self._id,
            aggregate_type=self.__class__.__name__,
            version=self._version,
            payload=payload,
            metadata=metadata,
        )
        self._uncommitted_events.append(event)
        self.apply_event(event)
        return event

    def load_from_history(self, events: list[DomainEvent]) -> None:
        """Rehydrate aggregate from event history."""
        for event in events:
            self.apply_event(event)
        self._uncommitted_events.clear()

    def commit(self, store: EventStore) -> None:
        """Commit uncommitted events to store."""
        for event in self._uncommitted_events:
            store.append(event)
        self._uncommitted_events.clear()


class Projection(ABC, Generic[T]):
    """Read model projection."""

    def __init__(self) -> None:
        self._state: dict[str, T] = {}
        self._position = 0

    @abstractmethod
    def handle(self, event: DomainEvent) -> None:
        """Handle single event."""
        raise NotImplementedError

    def project(self, events: list[DomainEvent]) -> None:
        """Project multiple events."""
        for event in events:
            self.handle(event)
            self._position += 1

    def get_state(self, aggregate_id: str) -> T | None:
        return self._state.get(aggregate_id)

    @property
    def position(self) -> int:
        return self._position


class EventBus:
    """Simple in-memory event bus."""

    def __init__(self) -> None:
        self._subscribers: dict[EventType, list[Callable[[DomainEvent], None]]] = {}
        self._lock = threading.RLock()

    def subscribe(
        self,
        event_type: EventType,
        handler: Callable[[DomainEvent], None],
    ) -> None:
        with self._lock:
            self._subscribers.setdefault(event_type, []).append(handler)

    def publish(self, event: DomainEvent) -> None:
        with self._lock:
            handlers = self._subscribers.get(event.event_type, [])
            for handler in handlers:
                handler(event)


def get_event_store() -> EventStore:
    """Get global event store (backed by DI container)."""
    from src.di.container import get_container
    return get_container().get_or_register("event_store", InMemoryEventStore)


def set_event_store(store: EventStore) -> None:
    """Set global event store (for testing)."""
    from src.di.container import get_container
    get_container().register("event_store", store)
