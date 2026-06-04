"""
C4REQBER: CQRS (Command Query Responsibility Segregation)

Separates read and write operations for the C4REQBER engine.
Commands mutate state via event sourcing; queries read from projections.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from src.architecture.event_sourcing import (
    Aggregate,
    EventStore,
    get_event_store,
)


# ============================================================================
# Commands
# ============================================================================

@dataclass(frozen=True)
class Command:
    """Base command."""

    command_id: str = ""
    aggregate_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class CommandHandler(ABC):
    """Command handler base class."""

    def __init__(self, event_store: EventStore | None = None) -> None:
        self._event_store = event_store or get_event_store()

    @abstractmethod
    def handle(self, command: Command) -> None:
        """Handle command."""
        raise NotImplementedError

    def _load_aggregate(self, aggregate: Aggregate) -> None:
        """Load aggregate from event store."""
        events = self._event_store.get_events(aggregate.id)
        aggregate.load_from_history(events)

    def _save_aggregate(self, aggregate: Aggregate) -> None:
        """Save aggregate to event store."""
        aggregate.commit(self._event_store)


# ============================================================================
# Queries
# ============================================================================

@dataclass(frozen=True)
class Query:
    """Base query."""

    query_id: str
    filters: dict[str, Any]


T = TypeVar("T")


class QueryHandler(ABC, Generic[T]):
    """Query handler base class."""

    @abstractmethod
    def handle(self, query: Query) -> T:
        """Handle query and return result."""
        raise NotImplementedError


# ============================================================================
# CQRS Bus
# ============================================================================

class CqrsBus:
    """CQRS command and query bus."""

    def __init__(self) -> None:
        self._command_handlers: dict[type[Command], CommandHandler] = {}
        self._query_handlers: dict[type[Query], QueryHandler[Any]] = {}

    def register_command(
        self,
        command_type: type[Command],
        handler: CommandHandler,
    ) -> None:
        self._command_handlers[command_type] = handler

    def register_query(
        self,
        query_type: type[Query],
        handler: QueryHandler[T],
    ) -> None:
        self._query_handlers[query_type] = handler

    def execute(self, command: Command) -> Any:
        """Execute command and return handler result."""
        handler = self._command_handlers.get(type(command))
        if not handler:
            raise ValueError(f"No handler for {type(command).__name__}")
        return handler.handle(command)

    def query(self, query: Query) -> Any:
        """Query."""
        handler = self._query_handlers.get(type(query))
        if not handler:
            raise ValueError(f"No handler for {type(query).__name__}")
        return handler.handle(query)


# ============================================================================
# C4REQBER Specific Commands and Queries
# ============================================================================

@dataclass(frozen=True)
class StartDiscoveryCommand(Command):
    """Command to start a discovery process."""

    problem_statement: str = ""
    domain: str = ""
    complexity_level: int = 1


@dataclass(frozen=True)
class ApplyPatternCommand(Command):
    """Command to apply a pattern to a discovery."""

    pattern_id: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ValidateDiscoveryCommand(Command):
    """Command to validate a discovery."""

    validation_rules: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class GetDiscoveryQuery(Query):
    """Query to get discovery by ID."""

    discovery_id: str


@dataclass(frozen=True)
class ListDiscoveriesQuery(Query):
    """Query to list discoveries."""

    status: str | None = None
    limit: int = 10
    offset: int = 0


@dataclass(frozen=True)
class GetMetricsQuery(Query):
    """Query to get system metrics."""

    metric_names: list[str] | None = None
    time_range: tuple[str, str] | None = None
