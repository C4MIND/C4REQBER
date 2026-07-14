"""
Tests for TURBO-CDI Architecture Patterns
"""
from __future__ import annotations

import pytest

from src.architecture import (
    Aggregate,
    ApplyPatternCommand,
    Command,
    CommandHandler,
    CqrsBus,
    DiscoverySaga,
    DomainEvent,
    EventBus,
    EventType,
    FunctionSagaStep,
    GetDiscoveryQuery,
    InMemoryEventStore,
    ListDiscoveriesQuery,
    PatternApplicationSaga,
    Projection,
    Query,
    QueryHandler,
    Saga,
    SagaContext,
    SagaStatus,
    StartDiscoveryCommand,
    ValidateDiscoveryCommand,
    create_discovery_saga,
    get_event_store,
    set_event_store,
)


# ============================================================================
# Event Sourcing Tests
# ============================================================================

class TestDomainEvent:
    def test_event_creation(self) -> None:
        event = DomainEvent.create(
            event_type=EventType.DISCOVERY_CREATED,
            aggregate_id="disc-001",
            aggregate_type="Discovery",
            version=1,
            payload={"problem": "test"},
        )
        assert event.event_type == EventType.DISCOVERY_CREATED
        assert event.aggregate_id == "disc-001"
        assert event.version == 1

    def test_event_serialization(self) -> None:
        event = DomainEvent.create(
            event_type=EventType.DISCOVERY_CREATED,
            aggregate_id="disc-001",
            aggregate_type="Discovery",
            version=1,
            payload={"problem": "test"},
        )
        data = event.to_dict()
        restored = DomainEvent.from_dict(data)
        assert restored.event_id == event.event_id
        assert restored.event_type == event.event_type


class TestInMemoryEventStore:
    def test_append_and_get(self) -> None:
        store = InMemoryEventStore()
        event = DomainEvent.create(
            event_type=EventType.DISCOVERY_CREATED,
            aggregate_id="disc-001",
            aggregate_type="Discovery",
            version=1,
            payload={},
        )
        store.append(event)
        events = store.get_events("disc-001")
        assert len(events) == 1
        assert events[0].event_id == event.event_id

    def test_get_latest_version(self) -> None:
        store = InMemoryEventStore()
        for v in range(1, 4):
            store.append(
                DomainEvent.create(
                    event_type=EventType.DISCOVERY_UPDATED,
                    aggregate_id="disc-001",
                    aggregate_type="Discovery",
                    version=v,
                    payload={"v": v},
                )
            )
        assert store.get_latest_version("disc-001") == 3
        assert store.get_latest_version("disc-999") == 0

    def test_get_all_events_with_filter(self) -> None:
        store = InMemoryEventStore()
        store.append(
            DomainEvent.create(
                event_type=EventType.DISCOVERY_CREATED,
                aggregate_id="disc-001",
                aggregate_type="Discovery",
                version=1,
                payload={},
            )
        )
        store.append(
            DomainEvent.create(
                event_type=EventType.PIPELINE_STARTED,
                aggregate_id="disc-001",
                aggregate_type="Discovery",
                version=2,
                payload={},
            )
        )
        events = store.get_all_events(event_types=[EventType.DISCOVERY_CREATED])
        assert len(events) == 1
        assert events[0].event_type == EventType.DISCOVERY_CREATED


class SampleAggregate(Aggregate):
    """Test aggregate."""

    def __init__(self, aggregate_id: str) -> None:
        super().__init__(aggregate_id)
        self.problem_statement = ""
        self.status = "pending"

    def create(self, problem: str) -> None:
        self._create_event(
            EventType.DISCOVERY_CREATED,
            {"problem": problem},
        )

    def update_status(self, status: str) -> None:
        self._create_event(
            EventType.DISCOVERY_UPDATED,
            {"status": status},
        )

    def _on_discovery_created(self, payload: dict) -> None:
        self.problem_statement = payload["problem"]

    def _on_discovery_updated(self, payload: dict) -> None:
        self.status = payload.get("status", self.status)


class TestAggregate:
    def test_create_and_apply(self) -> None:
        agg = SampleAggregate("disc-001")
        agg.create("Test problem")
        assert agg.problem_statement == "Test problem"
        assert agg.version == 1
        assert len(agg.uncommitted_events) == 1

    def test_load_from_history(self) -> None:
        store = InMemoryEventStore()
        agg = SampleAggregate("disc-001")
        agg.create("Test problem")
        agg.update_status("active")
        agg.commit(store)

        new_agg = SampleAggregate("disc-001")
        new_agg.load_from_history(store.get_events("disc-001"))
        assert new_agg.problem_statement == "Test problem"
        assert new_agg.status == "active"
        assert new_agg.version == 2
        assert len(new_agg.uncommitted_events) == 0


class TestEventBus:
    def test_subscribe_and_publish(self) -> None:
        bus = EventBus()
        received: list[DomainEvent] = []

        def handler(event: DomainEvent) -> None:
            received.append(event)

        bus.subscribe(EventType.DISCOVERY_CREATED, handler)
        event = DomainEvent.create(
            event_type=EventType.DISCOVERY_CREATED,
            aggregate_id="disc-001",
            aggregate_type="Discovery",
            version=1,
            payload={},
        )
        bus.publish(event)
        assert len(received) == 1


# ============================================================================
# CQRS Tests
# ============================================================================

class TestCommand:
    def test_command_creation(self) -> None:
        cmd = StartDiscoveryCommand(
            command_id="cmd-001",
            aggregate_id="disc-001",
            metadata={},
            problem_statement="Test",
            domain="physics",
        )
        assert cmd.problem_statement == "Test"
        assert cmd.domain == "physics"


class TestQuery:
    def test_query_creation(self) -> None:
        query = GetDiscoveryQuery(
            query_id="q-001",
            filters={},
            discovery_id="disc-001",
        )
        assert query.discovery_id == "disc-001"


class TestCqrsBus:
    def test_register_and_execute(self) -> None:
        bus = CqrsBus()
        executed: list[Command] = []

        class DummyHandler(CommandHandler):
            def handle(self, command: Command) -> None:
                executed.append(command)

        cmd = StartDiscoveryCommand(
            command_id="cmd-001",
            aggregate_id="disc-001",
            metadata={},
            problem_statement="Test",
            domain="physics",
        )
        bus.register_command(StartDiscoveryCommand, DummyHandler())
        bus.execute(cmd)
        assert len(executed) == 1

    def test_register_and_query(self) -> None:
        bus = CqrsBus()

        class DummyQueryHandler(QueryHandler[dict]):
            def handle(self, query: Query) -> dict:
                return {"result": "ok"}

        query = GetDiscoveryQuery(
            query_id="q-001",
            filters={},
            discovery_id="disc-001",
        )
        bus.register_query(GetDiscoveryQuery, DummyQueryHandler())
        result = bus.query(query)
        assert result == {"result": "ok"}


# ============================================================================
# Saga Tests
# ============================================================================

class TestSagaContext:
    def test_log_entries(self) -> None:
        ctx = SagaContext(saga_id="saga-001")
        ctx.log("step1", "execute", "success")
        assert len(ctx.execution_log) == 1
        assert ctx.execution_log[0].step_name == "step1"


class TestFunctionSagaStep:
    def test_execute(self) -> None:
        ctx = SagaContext(saga_id="saga-001")
        step = FunctionSagaStep(
            "test",
            lambda c: c.data.update({"key": "value"}),
        )
        step.execute(ctx)
        assert ctx.data["key"] == "value"

    def test_compensate(self) -> None:
        ctx = SagaContext(saga_id="saga-001")
        step = FunctionSagaStep(
            "test",
            lambda c: None,
            lambda c: c.data.update({"compensated": True}),
        )
        step.compensate(ctx)
        assert ctx.data["compensated"] is True


class TestSaga:
    def test_successful_execution(self) -> None:
        saga = Saga("test")
        saga.add_step(
            FunctionSagaStep("step1", lambda c: c.results.update({"a": 1}))
        )
        saga.add_step(
            FunctionSagaStep("step2", lambda c: c.results.update({"b": 2}))
        )
        ctx = saga.execute()
        assert saga.status == SagaStatus.COMPLETED
        assert ctx.results == {"a": 1, "b": 2}

    def test_failed_execution_with_compensation(self) -> None:
        saga = Saga("test")
        saga.add_step(
            FunctionSagaStep(
                "step1",
                lambda c: c.results.update({"a": 1}),
                lambda c: c.results.update({"a_compensated": True}),
            )
        )
        saga.add_step(
            FunctionSagaStep(
                "step2",
                lambda c: (_ for _ in ()).throw(ValueError("fail")),
                lambda c: None,
            )
        )
        ctx = saga.execute()
        assert saga.status == SagaStatus.FAILED
        assert ctx.results["a_compensated"] is True


class TestDiscoverySaga:
    def test_create_discovery_saga(self) -> None:
        def mock_llm(prompt: str) -> str:
            return "analysis result"

        def mock_pattern(domain: str, params: dict) -> dict:
            return {"pattern": "result"}

        def mock_validate(results: dict) -> bool:
            return True

        saga = create_discovery_saga(
            "Test problem",
            "physics",
            mock_llm,
            mock_pattern,
            mock_validate,
        )
        ctx = saga.execute()
        assert saga.status == SagaStatus.COMPLETED
        assert "analysis" in ctx.results
        assert "patterns" in ctx.results

    def test_discovery_saga_validation_failure(self) -> None:
        def mock_llm(prompt: str) -> str:
            return "analysis"

        def mock_pattern(domain: str, params: dict) -> dict:
            return {"pattern": "result"}

        def mock_validate(results: dict) -> bool:
            return False

        saga = create_discovery_saga(
            "Test problem",
            "physics",
            mock_llm,
            mock_pattern,
            mock_validate,
        )
        ctx = saga.execute()
        assert saga.status == SagaStatus.FAILED


class TestPatternApplicationSaga:
    def test_pattern_saga(self) -> None:
        saga = PatternApplicationSaga()
        saga.add_step(
            FunctionSagaStep(
                "apply_pattern",
                lambda c: c.results.update({"applied": True}),
                lambda c: c.results.update({"applied": False}),
            )
        )
        ctx = saga.execute()
        assert saga.status == SagaStatus.COMPLETED
        assert ctx.results["applied"] is True
