"""c4-cdi-turbo Architecture module."""
from src.architecture.cqrs import (
    ApplyPatternCommand,
    Command,
    CommandHandler,
    CqrsBus,
    GetDiscoveryQuery,
    GetMetricsQuery,
    ListDiscoveriesQuery,
    Query,
    QueryHandler,
    StartDiscoveryCommand,
    ValidateDiscoveryCommand,
)
from src.architecture.event_sourcing import (
    Aggregate,
    DomainEvent,
    EventBus,
    EventStore,
    EventType,
    InMemoryEventStore,
    Projection,
    get_event_store,
    set_event_store,
)
from src.architecture.saga import (
    DiscoverySaga,
    FunctionSagaStep,
    PatternApplicationSaga,
    Saga,
    SagaContext,
    SagaLogEntry,
    SagaStatus,
    SagaStep,
    create_discovery_saga,
)


__all__ = [
    # Event Sourcing
    "Aggregate",
    "DomainEvent",
    "EventBus",
    "EventStore",
    "EventType",
    "InMemoryEventStore",
    "Projection",
    "get_event_store",
    "set_event_store",
    # CQRS
    "Command",
    "CommandHandler",
    "Query",
    "QueryHandler",
    "CqrsBus",
    "StartDiscoveryCommand",
    "ApplyPatternCommand",
    "ValidateDiscoveryCommand",
    "GetDiscoveryQuery",
    "ListDiscoveriesQuery",
    "GetMetricsQuery",
    # Saga
    "Saga",
    "SagaStep",
    "FunctionSagaStep",
    "SagaContext",
    "SagaStatus",
    "SagaLogEntry",
    "DiscoverySaga",
    "PatternApplicationSaga",
    "create_discovery_saga",
]
